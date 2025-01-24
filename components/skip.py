import discord
from discord.ext import commands
import asyncio
import time
from yt_dlp import YoutubeDL, DownloadError

# 유튜브 DL 옵션 설정 함수 정의
def get_ytdl_options():
    return {
        'format': 'bestaudio/best',  # 최고 음질 선택 (기본값)
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',  # 파일 이름 템플릿
        'restrictfilenames': True,  # 파일 이름 제한
        'noplaylist': True,  # 플레이리스트 다운로드 비활성화
        'nocheckcertificate': True,  # SSL 인증서 검사 비활성화
        'ignoreerrors': False,  # 오류 무시 비활성화
        'logtostderr': False,  # 표준 오류로 로그 출력 비활성화
        'quiet': True,  # 출력 최소화
        'no_warnings': True,  # 경고 메시지 비활성화
        'default_search': 'ytsearch',  # 기본 검색 모드로 YouTube 검색 활성화
        'source_address': '0.0.0.0',  # IPv6 문제 방지
        'skip_download': True,  # 다운로드 건너뛰기
        'concurrent_fragments': 5  # 동시 다운로드 조각 수 설정
    }

# FFmpeg 옵션 설정 (최적화)
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 2 -reconnect_at_eof 1 -reconnect_streamed 1 -reconnect_delay_max 10 -loglevel verbose',  # 재연결 지연 시간 및 시도 횟수 증가, 로그 레벨 조정
    'options': '-vn -filter:a "volume=1.0"'  # 비디오 스트림 비활성화 및 볼륨 필터 추가
}

# 유튜브 동영상을 디스코드 봇에서 재생하기 위한 클래스 정의
class YTDLSource:
    def __init__(self, source, *, data, start_time=0):
        self.source = source  # 오디오 소스 (FFmpeg)
        self.data = data  # 동영상 데이터 저장
        self.title = data.get('title')  # 동영상 제목 저장
        self._start_time = start_time  # 시작 시간 저장

    @classmethod
    async def from_query(cls, query, *, loop=None, stream=False):
        """
        YouTube URL 또는 검색어를 처리하여 오디오 데이터를 반환하는 클래스 메서드.
        """
        loop = loop or asyncio.get_event_loop()
        ytdl = YoutubeDL(get_ytdl_options())

        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=not stream))
        except DownloadError as e:
            raise ValueError(f"동영상을 다운로드하는 중 오류가 발생했습니다: {e}")

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        start_time = int(data.get('start_time', 0))  # 시작 시간 설정
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data, start_time=start_time)

# 다음 곡 재생 함수 정의
async def play_next_song(voice_client, bot):
    """
    대기열의 다음 곡을 재생하거나, 자동재생이 켜져 있다면 추천 노래를 재생합니다.
    """
    if bot.music_queue:
        bot.current_track = bot.music_queue.popleft()
        bot.current_track_start_time = time.time()
        voice_client.play(bot.current_track.source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client, bot), bot.loop))
    elif bot.auto_play_enabled:
        try:
            if bot.current_track:
                genre = bot.current_track.data.get('genre', '')
                recommended_query = f"{bot.current_track.title} {genre} 비슷한 노래"
            else:
                recommended_query = "추천 노래"

            max_attempts = 5
            attempts = 0

            while attempts < max_attempts:
                recommended_track = await YTDLSource.from_query(recommended_query, loop=bot.loop, stream=True)
                
                if recommended_track.title != bot.current_track.title:
                    bot.current_track = recommended_track
                    break

                attempts += 1

            if attempts == max_attempts:
                recommended_track = await YTDLSource.from_query("추천 노래", loop=bot.loop, stream=True)
                bot.current_track = recommended_track

            bot.current_track_start_time = time.time()
            voice_client.play(bot.current_track.source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client, bot), bot.loop))
        except Exception as e:
            print(f"추천 노래를 재생하는 중 오류가 발생했습니다: {e}")
    else:
        await voice_client.disconnect()
        print("대기열이 비어 있고 자동재생이 꺼져 있어 봇이 음성 채널에서 나갔습니다.")

# /다음곡 - 대기열의 다음 곡 재생하기
@commands.command(name="다음곡", description="대기열의 다음 곡을 재생합니다.")
async def skip_to_next(ctx):
    """
    대기열의 다음 곡을 재생하거나, 자동재생이 켜져 있다면 추천 노래를 재생합니다.
    """
    voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)

    if not voice_client or not voice_client.is_connected():
        embed = discord.Embed(
            title="오류",
            description="현재 재생 중인 음악이 없습니다.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    if not ctx.bot.music_queue:
        if ctx.bot.auto_play_enabled:
            try:
                if ctx.bot.current_track:
                    genre = ctx.bot.current_track.data.get('genre', '')
                    recommended_query = f"{ctx.bot.current_track.title} {genre} 비슷한 노래"
                else:
                    recommended_query = "추천 노래"

                max_attempts = 5
                attempts = 0

                while attempts < max_attempts:
                    recommended_track = await YTDLSource.from_query(recommended_query, loop=ctx.bot.loop, stream=True)
                    
                    if recommended_track.title != ctx.bot.current_track.title:
                        ctx.bot.current_track = recommended_track
                        break

                    attempts += 1

                if attempts == max_attempts:
                    recommended_track = await YTDLSource.from_query("추천 노래", loop=ctx.bot.loop, stream=True)
                    ctx.bot.current_track = recommended_track

                ctx.bot.current_track_start_time = time.time()

                voice_client.stop()
                await asyncio.sleep(1)
                if voice_client.is_playing():
                    voice_client.stop()
                voice_client.cleanup()
                voice_client.play(
                    recommended_track.source,
                    after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client, ctx.bot), ctx.bot.loop)
                )
                embed = discord.Embed(
                    title="추천 노래 재생 중",
                    description=f"[{recommended_track.title}]({recommended_track.data.get('webpage_url', 'https://www.youtube.com')})",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(
                    title="오류 발생",
                    description=f"추천 노래를 재생하는 중 오류가 발생했습니다: {e}",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="알림",
                description="현재 곡이 마지막 곡입니다.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
        return

    ctx.bot.current_track = ctx.bot.music_queue.popleft()
    ctx.bot.current_track_start_time = time.time()

    voice_client.stop()
    await asyncio.sleep(1)
    if voice_client.is_playing():
        voice_client.stop()
    voice_client.cleanup()
    voice_client.play(
        ctx.bot.current_track.source,
        after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client, ctx.bot), ctx.bot.loop)
    )
    embed = discord.Embed(
        title="다음 곡으로 넘어갑니다",
        description=f"[{ctx.bot.current_track.title}]({ctx.bot.current_track.data.get('webpage_url', 'https://www.youtube.com')})",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

# 슬래시 명령어 정의
async def skip_to_next_slash(interaction: discord.Interaction):
    """
    대기열의 다음 곡을 재생하거나, 자동재생이 켜져 있다면 추천 노래를 재생합니다.
    """
    voice_client = discord.utils.get(interaction.client.voice_clients, guild=interaction.guild)

    if not voice_client or not voice_client.is_connected():
        embed = discord.Embed(
            title="오류",
            description="현재 재생 중인 음악이 없습니다.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if not interaction.client.music_queue:
        if interaction.client.auto_play_enabled:
            try:
                if interaction.client.current_track:
                    genre = interaction.client.current_track.data.get('genre', '')
                    recommended_query = f"{interaction.client.current_track.title} {genre} 비슷한 노래"
                else:
                    recommended_query = "추천 노래"

                max_attempts = 5
                attempts = 0

                while attempts < max_attempts:
                    recommended_track = await YTDLSource.from_query(recommended_query, loop=interaction.client.loop, stream=True)
                    
                    if recommended_track.title != interaction.client.current_track.title:
                        interaction.client.current_track = recommended_track
                        break

                    attempts += 1

                if attempts == max_attempts:
                    recommended_track = await YTDLSource.from_query("추천 노래", loop=interaction.client.loop, stream=True)
                    interaction.client.current_track = recommended_track

                interaction.client.current_track_start_time = time.time()

                voice_client.stop()
                await asyncio.sleep(1)
                if voice_client.is_playing():
                    voice_client.stop()
                voice_client.cleanup()
                voice_client.play(
                    recommended_track.source,
                    after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client, interaction.client), interaction.client.loop)
                )
                embed = discord.Embed(
                    title="추천 노래 재생 중",
                    description=f"[{recommended_track.title}]({recommended_track.data.get('webpage_url', 'https://www.youtube.com')})",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(
                    title="오류 발생",
                    description=f"추천 노래를 재생하는 중 오류가 발생했습니다: {e}",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="알림",
                description="현재 곡이 마지막 곡입니다.",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed)
        return

    interaction.client.current_track = interaction.client.music_queue.popleft()
    interaction.client.current_track_start_time = time.time()

    voice_client.stop()
    await asyncio.sleep(1)
    if voice_client.is_playing():
        voice_client.stop()
    voice_client.cleanup()
    voice_client.play(
        interaction.client.current_track.source,
        after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client, interaction.client), interaction.client.loop)
    )
    embed = discord.Embed(
        title="다음 곡으로 넘어갑니다",
        description=f"[{interaction.client.current_track.title}]({interaction.client.current_track.data.get('webpage_url', 'https://www.youtube.com')})",
        color=discord.Color.blue()
    )
    await interaction.followup.send(embed=embed)
