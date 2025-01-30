import discord
from discord.ext import commands
from yt_dlp import YoutubeDL, DownloadError
import asyncio
import time
import sys
import os

# 상위 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_ytdl_options, ffmpeg_options

# 유튜브 동영상을 디스코드 봇에서 재생하기 위한 클래스 정의
class YTDLSource:
    _cache = {}
    def __init__(self, source, *, data, start_time=0):
        self.source = source
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self._start_time = start_time

    @classmethod
    async def from_query(cls, query, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        ytdl = YoutubeDL(get_ytdl_options())

        if query in cls._cache:
            data = cls._cache[query]
        else:
            try:
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=not stream))
                cls._cache[query] = data
            except DownloadError as e:
                raise ValueError(f"동영상을 다운로드하는 중 오류가 발생했습니다: {e}")

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        start_time = int(data.get('start_time', 0))
        return cls(discord.FFmpegOpusAudio(filename, **ffmpeg_options), data=data, start_time=start_time)

# 다음 곡 재생 함수 정의 수정
async def play_next_song(voice_client, bot, disconnect_on_empty=True):
    try:
        if not voice_client or not voice_client.is_connected():
            return

        if bot.repeat_mode == "current" and bot.current_track:
            bot.current_track_start_time = time.time()
            if voice_client.is_playing():
                voice_client.stop()
            voice_client.cleanup()
            audio = await discord.FFmpegOpusAudio.from_probe(bot.current_track.url, **ffmpeg_options)
            voice_client.play(audio, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client, bot), bot.loop))
        elif bot.music_queue:
            if bot.repeat_mode == "queue":
                bot.music_queue.append(bot.current_track)
            bot.current_track = bot.music_queue.popleft()
            bot.current_track_start_time = time.time()
            if voice_client.is_playing():
                voice_client.stop()
            voice_client.cleanup()
            audio = await discord.FFmpegOpusAudio.from_probe(bot.current_track.url, **ffmpeg_options)
            voice_client.play(audio, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client, bot), bot.loop))
        else:
            if disconnect_on_empty and voice_client.is_connected():
                await voice_client.disconnect()
            print("대기열이 비어 있어 봇이 음성 채널에서 나갔습니다.")
    except Exception as e:
        print(f"재생 중 오류 발생: {e}")
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()

# /재생 명령어 정의 수정
@commands.command(name="재생", description="유튜브 URL 또는 검색어를 통해 음악을 재생합니다.")
async def play(ctx, query: str):
    if not ctx.author.voice:
        embed = discord.Embed(
            title="오류",
            description="먼저 음성 채널에 입장해야 합니다.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    channel = ctx.author.voice.channel  
    voice_client = ctx.guild.voice_client  # 수정된 부분

    try:
        # 이미 연결되어 있으면 이동
        if voice_client:
            await voice_client.move_to(channel)
        else:
            # 새로 연결
            voice_client = await channel.connect()
            # 연결 상태 확인
            await asyncio.sleep(1)
            if not voice_client.is_connected():
                raise Exception("음성 채널 연결 실패")

        async with ctx.typing():
            try:
                player = await YTDLSource.from_query(query, loop=ctx.bot.loop, stream=True)
                ctx.bot.music_queue.append(player)  
                
                if not voice_client.is_playing() and not voice_client.is_paused():
                    ctx.bot.current_track = ctx.bot.music_queue.popleft()
                    ctx.bot.current_track_start_time = time.time()
                    
                    # FFmpeg 프로세스 정리
                    if hasattr(voice_client, 'cleanup'):
                        voice_client.cleanup()
                    
                    # 새로운 오디오 소스 생성
                    audio = await discord.FFmpegOpusAudio.from_probe(ctx.bot.current_track.url, **ffmpeg_options)
                    voice_client.play(audio, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client, ctx.bot), ctx.bot.loop))
                    
                    embed = discord.Embed(
                        title="재생 중",
                        description=f"[{ctx.bot.current_track.title}]({ctx.bot.current_track.data.get('webpage_url', 'https://www.youtube.com')})",
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="대기열에 추가됨",
                        description=f"[{player.title}]({player.data.get('webpage_url', 'https://www.youtube.com')})",
                        color=discord.Color.blue()
                    )
                    await ctx.send(embed=embed)
            
            except ValueError as e:
                embed = discord.Embed(
                    title="오류 발생",
                    description=f"동영상을 다운로드하는 중 오류가 발생했습니다: {e}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                print(f"오류 발생: {e}")
            except Exception as e:
                embed = discord.Embed(
                    title="오류 발생",
                    description=f"알 수 없는 오류가 발생했습니다: {e}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                print(f"오류 발생: {e}")
    except Exception as e:
        print(f"음성 채널 연결 오류: {e}")
        embed = discord.Embed(
            title="오류 발생",
            description="음성 채널 연결에 실패했습니다. 잠시 후 다시 시도해주세요.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# 슬래시 명령어 정의도 같은 방식으로 수정
async def play_slash(interaction: discord.Interaction, query: str):
    if not interaction.user.voice:
        embed = discord.Embed(
            title="오류",
            description="먼저 음성 채널에 입장해야 합니다.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    channel = interaction.user.voice.channel  
    voice_client = interaction.guild.voice_client  # 수정된 부분

    try:
        # 이미 연결되어 있으면 이동
        if voice_client:
            await voice_client.move_to(channel)
        else:
            # 새로 연결
            voice_client = await channel.connect()
            # 연결 상태 확인
            await asyncio.sleep(1)
            if not voice_client.is_connected():
                raise Exception("음성 채널 연결 실패")

        await interaction.response.defer()
        try:
            player = await YTDLSource.from_query(query, loop=interaction.client.loop, stream=True)
            interaction.client.music_queue.append(player)  
            
            if not voice_client.is_playing() and not voice_client.is_paused():
                interaction.client.current_track = interaction.client.music_queue.popleft()
                interaction.client.current_track_start_time = time.time()

                source = discord.FFmpegOpusAudio(interaction.client.current_track.url, **ffmpeg_options)
                voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client, interaction.client), interaction.client.loop))
                embed = discord.Embed(
                    title="재생 중",
                    description=f"[{interaction.client.current_track.title}]({interaction.client.current_track.data.get('webpage_url', 'https://www.youtube.com')})",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="대기열에 추가됨",
                    description=f"[{player.title}]({player.data.get('webpage_url', 'https://www.youtube.com')})",
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed)
        
        except ValueError as e:
            embed = discord.Embed(
                title="오류 발생",
                description=f"동영상을 다운로드하는 중 오류가 발생했습니다: {e}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            print(f"오류 발생: {e}")
        except Exception as e:
            embed = discord.Embed(
                title="오류 발생",
                description=f"알 수 없는 오류가 발생했습니다: {e}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            print(f"오류 발생: {e}")
    except Exception as e:
        print(f"음성 채널 연결 오류: {e}")
        embed = discord.Embed(
            title="오류 발생",
            description="음성 채널 연결에 실패했습니다. 잠시 후 다시 시도해주세요.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)

# 미리 대기열에 있는 노래들을 준비하는 함수 정의
async def prepare_next_song(bot):
    if bot.music_queue:
        next_track = bot.music_queue[0]
        if not next_track.source:
            next_track.source = discord.FFmpegOpusAudio(next_track.url, **ffmpeg_options)

# setup 함수 추가 (파일 끝에)
async def setup(bot):
    bot.add_command(play)
    
    @bot.tree.command(name="재생", description="유튜브 URL 또는 검색어를 통해 음악을 재생합니다.")
    async def play_slash_command(interaction: discord.Interaction, query: str):
        await play_slash(interaction, query)
