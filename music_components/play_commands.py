import discord
from discord.ext import commands
from yt_dlp import YoutubeDL, DownloadError
import asyncio
import time
import sys
import os
import functools  # 추가

# 상위 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_ytdl_options, ffmpeg_options
# StreamPlayer import 추가
from music_components.music.player import StreamPlayer
from music_components.music.player import YTDLSource

# 유튜브 동영상을 디스코드 봇에서 재생하기 위한 클래스 정의
def get_optimized_ytdl_options():
    return {
        'format': 'bestaudio',  # 'bestaudio/best' 대신 'bestaudio'만 사용
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',  # 더 빠른 검색
        'extract_flat': True,
        'skip_download': True,
        'force_generic_extractor': False,
        'cachedir': False,
        'prefer_ffmpeg': True,  # FFmpeg 선호
    }

class YTDLSource:
    """
    유튜브 음원을 디스코드에서 재생 가능한 형태로 변환하는 클래스
    
    Attributes:
        _cache (dict): 이미 처리된 트랙을 캐싱하는 딕셔너리
        _ytdl (YoutubeDL): 유튜브 다운로드 옵션이 설정된 객체
    """
    _cache = {}
    _ytdl = YoutubeDL({
        # ytdl 옵션 설정
        'format': 'bestaudio/best',  # 최고 품질의 오디오 포맷 선택
        'quiet': True,               # 불필요한 출력 숨기기
        'no_warnings': True,
        'default_search': 'ytsearch',  # YouTube 검색 활성화
        'extract_flat': False,         # 전체 정보 추출
        'force_generic_extractor': False,
        'cachedir': False,
        'skip_download': True,
        'playlistend': 50,
        'ignoreerrors': True,
        'no_check_certificate': True,  # 인증서 체크 비활성화
        'extract_flat': False,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
        }],
        'http_chunk_size': 1024 * 1024,  # 청크 크기 줄임
        'socket_timeout': 30,          # 타임아웃 증가
        'retries': 10,                # 재시도 횟수 증가
        'fragment_retries': 10,       # 조각 다운로드 재시도 증가
        'hls_prefer_native': True,    # 네이티브 HLS 사용
    })

    def __init__(self, source, *, data):
        self.source = source
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.webpage_url = data.get('webpage_url', '')
        self.duration = data.get('duration', 0)

    @classmethod
    async def from_query(cls, query, *, loop=None, stream=True):
        """
        URL 또는 검색어로부터 재생 가능한 트랙 생성
        
        Args:
            query (str): 유튜브 URL 또는 검색어
            loop: 비동기 이벤트 루프
            stream (bool): 스트리밍 모드 여부
        
        Returns:
            YTDLSource: 재생 가능한 트랙 객체
            
        Raises:
            ValueError: 트랙 생성 실패 시
        """
        loop = loop or asyncio.get_event_loop()
        
        try:
            if query in cls._cache:
                print(f"캐시된 트랙 사용: {query}")
                return cls._cache[query]

            # 먼저 URL에서 실제 스트림 URL 가져오기
            print(f"트랙 정보 가져오는 중: {query}")
            data = await loop.run_in_executor(None, 
                lambda: cls._ytdl.extract_info(query, download=False))
            
            if not data:
                raise ValueError("비디오 정보를 찾을 수 없습니다.")

            if data.get('is_private', False):
                raise ValueError("비공개 동영상입니다. 다른 동영상을 선택해주세요.")

            if 'entries' in data:
                # 플레이리스트에서 첫 번째 공개 동영상 찾기
                for entry in data['entries']:
                    if not entry.get('is_private', False):
                        data = entry
                        break
                else:
                    raise ValueError("재생 가능한 공개 동영상을 찾을 수 없습니다.")

            stream_url = None
            if 'url' in data:
                stream_url = data['url']
            elif 'formats' in data:
                # 최적의 오디오 포맷 찾기
                formats = data['formats']
                audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                if not audio_formats:  # 오디오 전용이 없으면 모든 포맷 검색
                    audio_formats = [f for f in formats if f.get('acodec') != 'none']
                if audio_formats:
                    stream_url = audio_formats[0]['url']

            if not stream_url:
                raise ValueError("스트림 URL을 찾을 수 없습니다.")

            try:
                # 직접 FFmpegOpusAudio 생성
                source = discord.FFmpegOpusAudio(
                    stream_url,
                    bitrate=128,
                    before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                    options='-vn'
                )
            except Exception as audio_error:
                print(f"FFmpeg 오디오 생성 실패: {audio_error}")
                # 대체 옵션으로 재시도
                source = discord.FFmpegOpusAudio(
                    stream_url,
                    bitrate=96,
                    before_options='-reconnect 1 -reconnect_streamed 1',
                    options='-vn -bufsize 64k'
                )

            track = cls(source, data=data)
            cls._cache[query] = track
            return track

        except Exception as e:
            error_msg = str(e)
            if "Private video" in error_msg:
                raise ValueError("비공개 동영상입니다. 다른 동영상을 선택해주세요.")
            elif "Sign in" in error_msg:
                raise ValueError("로그인이 필요한 동영상입니다. 다른 동영상을 선택해주세요.")
            print(f"트랙 처리 중 오류: {e}")
            raise ValueError(f"음악을 처리하는 중 오류가 발생했습니다: {str(e)}")

# 다음 곡 재생 함수 정의 수정
async def play_next_song(voice_client, bot, disconnect_on_empty=True):
    """
    대기열의 다음 곡을 재생하는 함수
    
    Args:
        voice_client: 디스코드 음성 클라이언트
        bot: 디스코드 봇 인스턴스
        disconnect_on_empty (bool): 대기열이 비었을 때 자동 퇴장 여부
    """
    try:
        if not voice_client or not voice_client.is_connected():
            print("Voice client is not connected")
            return

        next_track = None
        retry_count = 0
        max_retries = 3

        async def try_play_track(track):
            """
            트랙 재생을 시도하는 내부 함수
            
            Args:
                track: 재생할 트랙 객체
            
            Returns:
                bool: 재생 성공 여부
            """
            nonlocal retry_count
            try:
                if not voice_client.is_connected():
                    print("Voice client disconnected")
                    return False

                if voice_client.is_playing():
                    voice_client.stop()
                
                await asyncio.sleep(0.5)  # 재생 사이에 약간의 지연 추가
                
                # 새로운 스트림 URL 가져오기
                new_data = await bot.loop.run_in_executor(None, 
                    lambda: YTDLSource._ytdl.extract_info(track.webpage_url, download=False))
                
                if not new_data:
                    raise ValueError("Failed to get track data")

                stream_url = new_data.get('url')
                if not stream_url and 'formats' in new_data:
                    formats = new_data['formats']
                    audio_formats = [f for f in formats if f.get('acodec') != 'none']
                    if audio_formats:
                        stream_url = audio_formats[0]['url']

                if not stream_url:
                    raise ValueError("No valid stream URL found")

                # 직접 FFmpegOpusAudio 생성
                audio = discord.FFmpegOpusAudio(
                    stream_url,
                    bitrate=128,
                    before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                    options='-vn'
                )

                def after_playing(error):
                    if error:
                        print(f"Playback error: {error}")
                    asyncio.run_coroutine_threadsafe(
                        handle_playback_error(error),
                        bot.loop
                    )

                voice_client.play(audio, after=after_playing)
                return True

            except Exception as e:
                print(f"Play attempt failed: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    await asyncio.sleep(1)  # 재시도 전 대기
                    return await try_play_track(track)
                return False

        async def handle_playback_error(error):
            if error:
                print(f"Playback error occurred: {error}")
                await play_next_song(voice_client, bot)
            else:
                # 정상적으로 곡이 끝난 경우
                await play_next_song(voice_client, bot)

        # 다음 트랙 선택
        if bot.repeat_mode == "current" and bot.current_track:
            next_track = bot.current_track
        elif bot.music_queue:
            next_track = bot.music_queue.popleft()
            if isinstance(next_track, QueuedTrack) and not next_track._loaded:
                try:
                    await next_track.load(bot.loop)
                except Exception as e:
                    print(f"Failed to load next track: {e}")
                    return await play_next_song(voice_client, bot)

            if bot.repeat_mode == "queue":
                bot.music_queue.append(bot.current_track)

        if next_track:
            bot.current_track = next_track
            bot.current_track_start_time = time.time()
            
            success = await try_play_track(next_track)
            if success:
                # 재생 알림 전송
                embed = discord.Embed(
                    title="🎵 다음 곡 재생",
                    description=f"[{next_track.title}]({next_track.data.get('webpage_url', 'https://www.youtube.com')})",
                    color=discord.Color.green()
                )
                if len(bot.music_queue) > 0:
                    embed.set_footer(text=f"대기열: {len(bot.music_queue)}곡 남음")

                try:
                    text_channel = voice_client.channel.guild.text_channels[0]
                    await text_channel.send(embed=embed)
                except Exception as e:
                    print(f"Failed to send next track notification: {e}")
            else:
                print("Failed to play track, skipping to next")
                await play_next_song(voice_client, bot)
        else:
            if disconnect_on_empty and voice_client.is_connected():
                try:
                    text_channel = voice_client.channel.guild.text_channels[0]
                    await text_channel.send("🎵 모든 곡이 재생되었습니다.")
                except Exception as e:
                    print(f"Failed to send completion message: {e}")
                await voice_client.disconnect()

    except Exception as e:
        print(f"Error in play_next_song: {e}")
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()

# 서버별 음악 상태를 관리하는 클래스
class ServerMusicState:
    def __init__(self):
        self.voice_client = None
        self.text_channel = None
        self.current_track = None
        self.current_track_start_time = None
        self.music_queue = []
        self.repeat_mode = "off"  # off, current, queue

# 새로운 클래스 추가
class QueuedTrack:
    def __init__(self, title, url, id="", status="대기중", webpage_url=None):
        self.title = title
        self.url = url
        self.webpage_url = webpage_url or f"https://www.youtube.com/watch?v={id}"
        self.status = status
        self.source = None
        self.data = {
            "webpage_url": self.webpage_url,
            "title": title,
            "url": url  # URL도 data 딕셔너리에 추가
        }
        self._loaded = False
    
    async def load(self, loop):
        """실제 트랙 로드가 필요할 때 호출"""
        if not self._loaded:
            try:
                track = await YTDLSource.from_query(self.url, loop=loop, stream=True)
                self.__dict__.update(track.__dict__)
                self._loaded = True
            except Exception as e:
                print(f"트랙 로드 실패: {e}")
                raise

import sys
sys.stdout.reconfigure(encoding='utf-8')  # 콘솔 출력 인코딩을 UTF-8로 설정

async def process_playlist(query, bot, loop):
    ytdl = YoutubeDL({
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'extract_flat': True,  # 변경: 일단 기본 정보만 가져오기
        'force_generic_extractor': False,
        'cachedir': False,
        'skip_download': True,
        'playlistend': 50,
        'ignoreerrors': True,
        'no_check_certificate': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
        }],
    })
    
    print("플레이리스트 정보 확인 중...")
    try:
        # 검색어 처리
        if not query.startswith(('http://', 'https://')):
            query = f"ytsearch:{query}"  # YouTube 검색 쿼리로 변경
            
        # 기본 정보만 먼저 가져오기
        data = await loop.run_in_executor(None, 
            lambda: ytdl.extract_info(query, download=False, process=False))
        
        entries = []
        if 'entries' in data:  # 플레이리스트인 경우
            entries = [entry for entry in data['entries'] if entry is not None]
            if not entries:
                raise ValueError("재생 가능한 동영상이 없습니다.")
                
            # 첫 번째 트랙의 정보만 완전히 가져오기
            first_entry = entries[0]
            first_track = await YTDLSource.from_query(
                f"https://www.youtube.com/watch?v={first_entry['id']}", 
                loop=loop,
                stream=True
            )
            
            # 나머지는 기본 정보만으로 대기열에 추가
            for entry in entries[1:]:
                placeholder = QueuedTrack(
                    title=entry.get('title', 'Unknown'),
                    url=f"https://www.youtube.com/watch?v={entry['id']}",
                    id=entry.get('id', ''),
                    webpage_url=entry.get('webpage_url')
                )
                bot.music_queue.append(placeholder)
                print(f"대기열에 추가됨: {entry.get('title', 'Unknown')}")
            
            return [first_track], len(entries), 0
            
        else:  # 단일 트랙인 경우
            track = await YTDLSource.from_query(query, loop=loop, stream=True)
            return [track], 1, 0
            
    except Exception as e:
        print(f"플레이리스트 처리 중 오류: {e}")
        if "no video formats found" in str(e).lower():
            raise ValueError("재생할 수 없는 동영상입니다.")
        raise ValueError(str(e))

@commands.command(name="재생", description="유튜브 URL 또는 검색어를 통해 음악을 재생합니다.")
async def play(ctx, *, query: str):
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

        loading_msg = await ctx.send("🎵 음악을 불러오는 중...".encode('utf-8', errors='ignore').decode('utf-8'))
        
        # 비동기 작업 동시 실행
        async with asyncio.TaskGroup() as tg:
            tracks_task = tg.create_task(process_playlist(query, ctx.bot, ctx.bot.loop))
            # 다른 비동기 작업들도 여기에 추가 가능
        
        tracks, total_tracks, skipped_count = tracks_task.result()
        
        if not tracks:
            await loading_msg.edit(content="음악을 찾을 수 없습니다.")
            return
                
        first_track = tracks[0]
        if not first_track or not first_track.title:
            await loading_msg.edit(content="재생할 수 없는 트랙입니다.")
            return
        
        # 첫 번째 트랙 처리
        remaining_tracks = tracks[1:]
        
        if not voice_client.is_playing() and not voice_client.is_paused():
            ctx.bot.current_track = first_track
            ctx.bot.current_track_start_time = time.time()
            
            try:
                # 직접 FFmpegOpusAudio 생성
                audio = discord.FFmpegOpusAudio(
                    first_track.url,
                    bitrate=128,
                    before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                    options='-vn'
                )
                
                def after_playing(error):
                    if error:
                        print(f"재생 중 오류 발생: {error}")
                    coro = play_next_song(voice_client, ctx.bot)
                    fut = asyncio.run_coroutine_threadsafe(coro, ctx.bot.loop)
                    try:
                        fut.result()
                    except Exception as e:
                        print(f'재생 후 처리 중 오류 발생: {e}')

                voice_client.play(audio, after=after_playing)
                
            except Exception as e:
                print(f"오디오 생성 중 오류 발생: {e}")
                # 대체 옵션으로 재시도
                audio = discord.FFmpegOpusAudio(
                    first_track.url,
                    bitrate=96,
                    before_options='-reconnect 1 -reconnect_streamed 1',
                    options='-vn -bufsize 64k'
                )
                voice_client.play(audio, after=after_playing)

            embed = discord.Embed(
                title="재생 시작",
                description=f"[{first_track.title}]({first_track.data.get('webpage_url', 'https://www.youtube.com')})",
                color=discord.Color.green()
            )
            if 'entries' in first_track.data:
                embed.add_field(
                    name="플레이리스트 정보",
                    value="나머지 곡들은 백그라운드에서 로딩 중입니다...",
                    inline=False
                )
        else:
            ctx.bot.music_queue.append(first_track)
            embed = discord.Embed(
                title="대기열에 추가됨",
                description=f"[{first_track.title}]({first_track.data.get('webpage_url', 'https://www.youtube.com')})",
                color=discord.Color.blue()
            )
        
        # 나머지 트랙들을 대기열에 추가
        for track in remaining_tracks:
            ctx.bot.music_queue.append(track)
        
        if skipped_count > 0:
            embed.add_field(
                name="플레이리스트 정보",
                value=f"재생 가능: {total_tracks}곡 / 건너뛴 동영상: {skipped_count}곡",
                inline=False
            )
        
        await loading_msg.edit(content=None, embed=embed)
        
    except ValueError as e:
        await loading_msg.edit(content=f"오류 발생: {str(e)}")
    except Exception as e:
        await loading_msg.edit(content=f"처리 중 오류가 발생했습니다: {str(e)}")
            
    except Exception as e:
        print(f"재생 명령어 처리 중 오류 발생: {e}")
        await ctx.send("음악을 재생하는 중 오류가 발생했습니다.")

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

        await interaction.response.defer(thinking=True)
        
        try:
            tracks, total_tracks, skipped_count = await process_playlist(query, interaction.client, interaction.client.loop)
            
            if not tracks:
                await interaction.followup.send("음악을 찾을 수 없습니다.")
                return
                
            # 첫 번째 트랙 처리
            first_track = tracks[0]
            remaining_tracks = tracks[1:]
            
            if not voice_client.is_playing() and not voice_client.is_paused():
                interaction.client.current_track = first_track
                interaction.client.current_track_start_time = time.time()
                
                try:
                    # 직접 FFmpegOpusAudio 생성
                    audio = discord.FFmpegOpusAudio(
                        first_track.url,
                        bitrate=128,
                        before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                        options='-vn'
                    )
                    
                    def after_playing(error):
                        if error:
                            print(f"재생 중 오류 발생: {error}")
                        coro = play_next_song(voice_client, interaction.client)
                        fut = asyncio.run_coroutine_threadsafe(coro, interaction.client.loop)
                        try:
                            fut.result()
                        except Exception as e:
                            print(f'재생 후 처리 중 오류 발생: {e}')

                    voice_client.play(audio, after=after_playing)
                    
                except Exception as e:
                    print(f"오디오 생성 중 오류 발생: {e}")
                    # 대체 옵션으로 재시도
                    audio = discord.FFmpegOpusAudio(
                        first_track.url,
                        bitrate=96,
                        before_options='-reconnect 1 -reconnect_streamed 1',
                        options='-vn -bufsize 64k'
                    )
                    voice_client.play(audio, after=after_playing)

                embed = discord.Embed(
                    title="재생 시작",
                    description=f"[{first_track.title}]({first_track.data.get('webpage_url', 'https://www.youtube.com')})",
                    color=discord.Color.green()
                )
                if 'entries' in first_track.data:
                    embed.add_field(
                        name="플레이리스트 정보",
                        value="나머지 곡들은 백그라운드에서 로딩 중입니다...",
                        inline=False
                    )
            else:
                interaction.client.music_queue.append(first_track)
                embed = discord.Embed(
                    title="대기열에 추가됨",
                    description=f"[{first_track.title}]({first_track.data.get('webpage_url', 'https://www.youtube.com')})",
                    color=discord.Color.blue()
                )
            
            # 나머지 트랙들을 대기열에 추가
            for track in remaining_tracks:
                interaction.client.music_queue.append(track)
            
            if skipped_count > 0:
                embed.add_field(
                    name="플레이리스트 정보",
                    value=f"재생 가능: {total_tracks}곡 / 건너뛴 동영상: {skipped_count}곡",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except ValueError as e:
            await interaction.followup.send(f"오류 발생: {str(e)}")
        except Exception as e:
            await interaction.followup.send(f"처리 중 오류가 발생했습니다: {str(e)}")
            
    except Exception as e:
        print(f"재생 명령어 처리 중 오류 발생: {e}")
        await interaction.followup.send("음악을 재생하는 중 오류가 발생했습니다.")

# 미리 대기열에 있는 노래들을 준비하는 함수 정의
async def prepare_next_song(bot):
    if bot.music_queue:
        next_track = bot.music_queue[0]
        if not next_track.source:
            next_track.source = discord.FFmpegOpusAudio(next_track.url, **ffmpeg_options)

# show_queue 함수 수정
@commands.command(name="대기열")
async def show_queue(ctx):
    if not ctx.bot.music_queue:
        embed = discord.Embed(
            title="대기열",
            description="대기열이 비어 있습니다.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        return

    queue_list = []
    loading_count = 0
    
    for i, track in enumerate(ctx.bot.music_queue, 1):
        status_text = ""
        if isinstance(track, QueuedTrack):
            loading_count += 1
            status_text = " [대기중]"
        
        title = track.title or "로딩 중..."
        url = track.webpage_url or "https://www.youtube.com"
        queue_list.append(f"{i}. [{title}]({url}){status_text}")

    # 대기열 표시
    embed = discord.Embed(
        title="🎵 대기열",
        description="\n".join(queue_list),
        color=discord.Color.blue()
    )
    
    if loading_count > 0:
        embed.set_footer(text=f"총 {len(ctx.bot.music_queue)}곡 (로딩중: {loading_count}곡)")
    else:
        embed.set_footer(text=f"총 {len(ctx.bot.music_queue)}곡")

    await ctx.send(embed=embed)

# setup 함수 추가 (파일 끝에)
async def setup(bot):
    bot.add_command(play)
    
    @bot.tree.command(name="재생", description="유튜브 URL 또는 검색어를 통해 음악을 재생합니다.")
    async def play_slash_command(interaction: discord.Interaction, query: str):
        await play_slash(interaction, query)

# 추가: 서버별 재생 상태를 관리하는 함수들
async def get_guild_voice_state(ctx_or_interaction):
    """서버별 음성 상태와 음악 상태를 가져옵니다."""
    if isinstance(ctx_or_interaction, commands.Context):
        guild_id = ctx_or_interaction.guild.id
        guild = ctx_or_interaction.guild
        bot = ctx_or_interaction.bot
    else:  # Interaction
        guild_id = ctx_or_interaction.guild_id
        guild = ctx_or_interaction.guild
        bot = ctx_or_interaction.client

    # 서버 상태 가져오기
    server_state = bot.get_server_state(guild_id)
    
    # voice_client가 없으면 현재 voice_client 저장
    if not server_state.voice_client and guild.voice_client:
        server_state.voice_client = guild.voice_client

    return server_state

async def update_guild_voice_state(ctx_or_interaction, voice_client):
    """서버의 voice_client 상태를 업데이트합니다."""
    if isinstance(ctx_or_interaction, commands.Context):
        guild_id = ctx_or_interaction.guild.id
        bot = ctx_or_interaction.bot
    else:  # Interaction
        guild_id = ctx_or_interaction.guild_id
        bot = ctx_or_interaction.client

    server_state = bot.get_server_state(guild_id)
    server_state.voice_client = voice_client
