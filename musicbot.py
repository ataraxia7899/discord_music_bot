import discord  # 디스코드 API 모듈
from discord.ext import commands  # 확장 모듈
import yt_dlp # 유튜브 다운로드 및 스트리밍 모듈
from yt_dlp import YoutubeDL  # 유튜브 다운로드 및 스트리밍 모듈
import asyncio  # 비동기 처리 모듈
import re  # URL 검증 및 정리를 위한 정규식 모듈
from urllib.parse import urlparse, parse_qs  # URL 파싱을 위한 모듈
from collections import deque  # 대기열 및 이전 곡 관리를 위한 deque 사용
from discord.ui import View, Button, Modal, TextInput  # 슬래시 명령어 UI 구성을 위한 모듈
import time  # 시간 추적을 위한 모듈 추가
import random # 랜덤 추천 노래를 위한 모듈 추가
# from secret import token  # 디스코드 봇 토큰 가져오기

# 타입클라우드에서 환경변수로 토큰을 지정해서 사용하기 위한 코드
import os
token = os.getenv("DISCORD_BOT_TOKEN")

# 디스코드 봇 객체 생성
intents = discord.Intents.default()
intents.message_content = True  # 메시지 읽기 권한 활성화
bot = commands.Bot(command_prefix="!", intents=intents)

# 대기열 및 현재 재생 중인 곡 관리
music_queue = deque()  # 대기열 저장소
current_track = None  # 현재 재생 중인 곡 정보
current_track_start_time = None  # 현재 곡 시작 시간 (초 단위)
auto_play_enabled = False  # 자동재생 기능 상태

# 봇 준비 이벤트 처리 및 슬래시 명령어 동기화
@bot.event
async def on_ready():
    """
    봇이 준비되었을 때 호출되는 이벤트 핸들러.
    """
    print(f'봇이 로그인되었습니다: {bot.user}')
    
    try:
        synced = await bot.tree.sync()  # 슬래시 명령어 동기화 시도
        print(f"동기화된 슬래시 명령어: {len(synced)}개")  
        
        commands = [command.name for command in bot.tree.get_commands()]
        print(f"등록된 슬래시 명령어 목록: {commands}")
    
    except Exception as e:
        print(f"명령어 동기화 중 오류 발생: {e}")

# /재생 슬래시 명령어 정의 - 기본적으로 최고 음질로 음악 재생
@bot.tree.command(name="재생", description="유튜브 URL 또는 검색어를 통해 음악을 재생합니다.")
async def play(interaction: discord.Interaction, query: str):
    """
    사용자가 입력한 YouTube URL 또는 검색어를 통해 음악을 재생합니다.
    """
    await interaction.response.defer()

    if not interaction.user.voice:
        embed = discord.Embed(
            title="오류",
            description="먼저 음성 채널에 입장해야 합니다.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    channel = interaction.user.voice.channel  
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)

    if not voice_client:
        voice_client = await channel.connect()

    async with interaction.channel.typing():
        try:
            player = await YTDLSource.from_query(query, loop=bot.loop, stream=True)
            music_queue.append(player)  
            
            if not voice_client.is_playing():
                global current_track, current_track_start_time
                current_track = music_queue.popleft()

                # 현재 곡 시작 시간 기록
                current_track_start_time = time.time()

                voice_client.play(current_track.source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client), bot.loop))
                embed = discord.Embed(
                    title="재생 중",
                    description=f"[{current_track.title}]({current_track.data.get('webpage_url', 'https://www.youtube.com')})",
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
        
        except Exception as e:
            embed = discord.Embed(
                title="오류 발생",
                description=f"오류가 발생했습니다: {e}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

# 다음 곡 재생 함수 정의
async def play_next_song(voice_client):
    """
    대기열에서 다음 곡을 가져와 재생하거나, 자동재생 상태라면 추천 노래를 재생합니다.
    """
    global current_track, current_track_start_time

    if music_queue:
        # 대기열에서 다음 곡 가져오기
        next_track = music_queue.popleft()
        current_track = next_track

        # 현재 곡 시작 시간 기록
        current_track_start_time = time.time()

        voice_client.play(
            next_track.source,
            after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client), bot.loop).result()
        )
    elif auto_play_enabled:
        # 자동재생 기능이 켜져 있을 때 추천 노래 재생
        try:
            recommended_track = await YTDLSource.from_query("추천 노래", loop=bot.loop, stream=True)
            current_track = recommended_track

            # 현재 곡 시작 시간 기록
            current_track_start_time = time.time()

            voice_client.play(
                recommended_track.source,
                after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client), bot.loop).result()
            )
        except Exception as e:
            print(f"자동재생 중 오류 발생: {e}")
    else:
        # 대기열이 비어 있고 자동재생이 꺼져 있을 때 봇이 나가지 않도록 함
        await asyncio.sleep(1)

# /다음곡 - 대기열의 다음 곡 재생하기
@bot.tree.command(name="다음곡", description="대기열의 다음 곡을 재생합니다.")
async def skip_to_next(interaction: discord.Interaction):
    """
    대기열의 다음 곡을 재생하거나, 자동재생이 켜져 있다면 추천 노래를 재생합니다.
    """
    await interaction.response.defer()

    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)

    if not voice_client or not voice_client.is_playing():
        embed = discord.Embed(
            title="오류",
            description="현재 재생 중인 음악이 없습니다.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
        return

    if not music_queue:
        if auto_play_enabled:
            try:
                recommended_track = await YTDLSource.from_query("추천 노래", loop=bot.loop, stream=True)
                global current_track
                current_track = recommended_track

                voice_client.stop()
                voice_client.play(
                    recommended_track.source,
                    after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client), bot.loop)
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

    voice_client.stop()
    embed = discord.Embed(
        title="다음 곡으로 넘어갑니다",
        description="다음 곡을 재생합니다.",
        color=discord.Color.blue()
    )
    await interaction.followup.send(embed=embed)

# /시간조절 - 현재 곡의 시간 확인 채팅
class TimeInputModal(Modal):
    """
    시간 입력을 위한 Modal 클래스
    """
    minutes = TextInput(
        label="분",
        placeholder="0",
        required=True,
        max_length=2
    )
    seconds = TextInput(
        label="초",
        placeholder="0",
        required=True,
        max_length=2
    )

    def __init__(self, voice_client, current_track):
        super().__init__(title="시간 조절")
        self.voice_client = voice_client
        self.current_track = current_track

    async def on_submit(self, interaction: discord.Interaction):
        """
        사용자가 시간을 입력한 후 호출되는 함수
        """
        try:
            # 입력된 분과 초를 합산하여 총 초(second)로 변환
            total_seconds = int(self.minutes.value) * 60 + int(self.seconds.value)

            # FFmpeg 옵션으로 특정 시간으로 이동
            source = discord.FFmpegPCMAudio(
                self.current_track.data['url'],
                before_options=f"-ss {total_seconds} -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 2",
                options="-vn"
            )

            # 현재 재생 중인 곡 정지 후 새 위치에서 재생
            self.voice_client.stop()
            self.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(self.voice_client), bot.loop))

            await interaction.response.send_message(f"음악을 {self.minutes.value}분 {self.seconds.value}초로 이동했습니다.")
        
        except Exception as e:
            await interaction.response.send_message(f"시간 조절 중 오류가 발생했습니다: {e}")

# /시간조절 - 현재 곡의 시간 조절 input창
class TimeControlView(View):
    """
    시간 조절 버튼을 포함하는 View 클래스
    """
    def __init__(self, voice_client, current_track):
        super().__init__()
        self.voice_client = voice_client
        self.current_track = current_track

    @discord.ui.button(label="시간 조절", style=discord.ButtonStyle.primary)
    async def time_control_button(self, interaction: discord.Interaction, button: Button):
        """
        "시간 조절" 버튼 클릭 시 호출되는 함수
        """
        try:
            modal = TimeInputModal(self.voice_client, self.current_track)
            await interaction.response.send_modal(modal)
        
        except Exception as e:
            await interaction.response.send_message(f"시간 조절 버튼 처리 중 오류가 발생했습니다: {e}")

# /시간조절 - 현재 곡의 시간을 조절하기 (버튼 포함)
@bot.tree.command(name="시간조절", description="현재 곡의 특정 시간으로 이동합니다.")
async def seek(interaction: discord.Interaction):
    """
    현재 재생 중인 곡의 특정 시간으로 이동합니다.
    """
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)

    if not voice_client or not voice_client.is_playing():
        embed = discord.Embed(
            title="오류",
            description="현재 재생 중인 음악이 없습니다.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return

    global current_track, current_track_start_time

    if not current_track:
        embed = discord.Embed(
            title="오류",
            description="현재 재생 중인 곡 정보를 가져올 수 없습니다.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return

    try:
        # 현재 곡의 길이와 현재 재생 시간을 계산
        duration = current_track.data.get('duration', 0)
        minutes_total, seconds_total = divmod(duration, 60)

        # 현재 재생 시간 계산
        if current_track_start_time:
            elapsed_time_seconds = int(time.time() - current_track_start_time)  # 경과 시간 계산
        else:
            elapsed_time_seconds = 0

        minutes_current, seconds_current = divmod(elapsed_time_seconds, 60)

        message = (
            f"현재 곡의 길이: {minutes_total}분 {seconds_total}초\n"
            f"현재 재생 시간: {minutes_current}분 {seconds_current}초\n"
            f"아래 버튼을 눌러 시간을 조절하세요."
        )

        # View 생성 및 메시지 전송
        view = TimeControlView(voice_client, current_track)
        embed = discord.Embed(
            title="시간 조절",
            description=message,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=view)
    
    except Exception as e:
        embed = discord.Embed(
            title="오류 발생",
            description=f"시간 조절 명령어 처리 중 오류가 발생했습니다: {e}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

# /일시정지 - 일시정지/재개 토글 명령어로 통합
@bot.tree.command(name="일시정지", description="현재 음악을 일시정지하거나 다시 재생합니다.")
async def pause_resume(interaction: discord.Interaction):
    """
    현재 음악을 일시정지하거나 다시 재생합니다.
    """
    await interaction.response.defer()

    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)

    if voice_client and voice_client.is_playing():
        voice_client.pause()
        embed = discord.Embed(
            title="일시정지",
            description="음악이 일시정지되었습니다.",
            color=discord.Color.orange()
        )
        await interaction.followup.send(embed=embed)
    elif voice_client and voice_client.is_paused():
        voice_client.resume()
        embed = discord.Embed(
            title="재생",
            description="음악이 다시 재생됩니다.",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)
    else:
        embed = discord.Embed(
            title="오류",
            description="현재 재생 중인 음악이 없습니다.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)

# /자동재생 - 자동재생 기능 켜기/끄기
@bot.tree.command(name="자동재생", description="자동재생 기능을 켜거나 끕니다.")
async def toggle_auto_play(interaction: discord.Interaction):
    """
    자동재생 기능을 켜거나 끕니다.
    """
    global auto_play_enabled
    auto_play_enabled = not auto_play_enabled
    status = "켜짐" if auto_play_enabled else "꺼짐"
    embed = discord.Embed(
        title="자동재생",
        description=f"자동재생 기능이 {status} 상태입니다.",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

# /대기열 - 현재 대기열 목록을 확인합니다.
@bot.tree.command(name="대기열", description="현재 대기열 목록을 확인합니다.")
async def show_queue(interaction: discord.Interaction):
    """
    현재 대기열의 목록을 표시합니다.
    """
    if not music_queue:
        embed = discord.Embed(
            title="대기열",
            description="대기열에 곡이 없습니다.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)
        return

    # 대기열 순번과 곡 제목 출력
    queue_list = "\n".join([f"{i + 1}. {track.title}" for i, track in enumerate(music_queue)])
    embed = discord.Embed(
        title="현재 대기열",
        description=queue_list,
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

# /정지 - 현재 음악 정지하기
@bot.tree.command(name="정지", description="현재 재생 중인 음악을 멈춥니다.")
async def stop(interaction: discord.Interaction):
    """
    현재 재생 중인 음악을 멈춥니다.
    """
    await interaction.response.defer()

    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)

    if voice_client and voice_client.is_connected():
        voice_client.stop()
        embed = discord.Embed(
            title="정지",
            description="음악을 멈추고 봇이 퇴장했습니다.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
    else:
        embed = discord.Embed(
            title="오류",
            description="봇이 음성 채널에 있지 않습니다.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)

# 유튜브 DL 옵션 설정 함수 정의
def get_ytdl_options():
    return {
        'format': 'bestaudio/best',  # 최고 음질 선택 (기본값)
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',  # 파일 이름 템플릿
        'restrictfilenames': True,  # 파일 이름 제한
        'noplaylist': True,  # 플레이리스트 다운로드 활성화
        'nocheckcertificate': True,  # SSL 인증서 검사 비활화
        'ignoreerrors': False,  # 오류 무시 비활성화
        'logtostderr': False,  # 표준 오류로 로그 출력 비활성화
        'quiet': True,  # 출력 최소화
        'no_warnings': True,  # 경고 메시지 비활성화
        'default_search': 'ytsearch',  # 기본 검색 모드로 YouTube 검색 활성화
        'source_address': '0.0.0.0'  # IPv6 문제 방지
    }

# FFmpeg 옵션 설정 (최적화)
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 2',  # 재연결 지연 시간 단축
    'options': '-vn'  # 비디오 스트림 비활성화 (오디오만 재생)
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
        ytdl = yt_dlp.YoutubeDL(get_ytdl_options())

        try:
            if is_valid_youtube_url(query):  
                cleaned_url = clean_youtube_url(query) 
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(cleaned_url, download=not stream))
            else:  
                search_results = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{query}", download=False))  
                if not search_results or 'entries' not in search_results or len(search_results['entries']) == 0:
                    raise ValueError("검색 결과를 찾을 수 없습니다.")
                first_result = search_results['entries'][0]  
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(first_result['webpage_url'], download=not stream))

            filename = data['url'] if stream else ytdl.prepare_filename(data)  
            start_time = int(data.get('start_time', 0))  # 시작 시간 설정
            return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data, start_time=start_time)  

        except yt_dlp.utils.DownloadError as e:
            raise ValueError(f"동영상을 다운로드하는 중 오류가 발생했습니다: {e}")

# 유튜브 URL 검증 함수 정의 (다양한 형식 지원)
def is_valid_youtube_url(url):
    """
    유튜브 URL이 유효한지 확인하는 함수.
    다양한 유튜브 URL 형식을 지원합니다.
    """
    youtube_regex = (
        r"^(https?:\/\/)?"  # http 또는 https 프로토콜 (선택적)
        r"(www\.)?"  # www. (선택적)
        r"(youtube\.com|youtu\.be)\/"  # youtube.com 또는 youtu.be
        r"((watch\?v=|embed\/|shorts\/|v\/|playlist\?list=)?([a-zA-Z0-9_-]+))"  # 다양한 형식의 경로
        r"(\?[a-zA-Z0-9_=&-]*)?$"  # 추가적인 쿼리 매개변수 (선택적)
    )

# 유튜브 URL 정리 함수 정의 (추가 매개변수 제거)
def clean_youtube_url(url):
    """
    유튜브 URL에서 불필요한 매개변수를 제거하고 순수한 동영상 또는 플레이리스트 ID를 추출합니다.
    """
    parsed_url = urlparse(url)

    # youtu.be 형식 (공유 URL)
    if "youtu.be" in parsed_url.netloc:
        video_id = parsed_url.path.lstrip("/")  # 동영상 ID 추출
        return f"https://www.youtube.com/watch?v={video_id}"

    # youtube.com 형식 (긴 URL)
    elif "youtube.com" in parsed_url.netloc:
        query_params = parse_qs(parsed_url.query)  # 쿼리 매개변수 파싱

        # 플레이리스트 URL 처리
        if "list" in query_params:
            playlist_id = query_params.get("list", [None])[0]  # "list" 매개변수에서 플레이리스트 ID 추출
            if "v" in query_params:  # 동영상 ID와 함께 제공된 경우
                video_id = query_params.get("v", [None])[0]
                return f"https://www.youtube.com/watch?v={video_id}&list={playlist_id}"
            return f"https://www.youtube.com/playlist?list={playlist_id}"

        # 단일 동영상 URL 처리
        elif "v" in query_params:
            video_id = query_params.get("v", [None])[0]
            return f"https://www.youtube.com/watch?v={video_id}"

    raise ValueError("유효한 YouTube URL이 아닙니다.")

# 음성 채널의 상태를 모니터링하여, 유저가 모두 떠났을 때 봇이 자동으로 음성 채널에서 나가도록 함함
@bot.event
async def on_voice_state_update(member, before, after):
    """
    음성 채널의 상태가 변경될 때 호출되는 이벤트.
    """
    # 봇이 음성 채널에 연결되어 있는지 확인
    voice_client = discord.utils.get(bot.voice_clients, guild=member.guild)
    if not voice_client:
        return

    # 봇이 연결된 음성 채널에 남아 있는 멤버 확인
    if before.channel == voice_client.channel and after.channel != voice_client.channel:
        # 해당 음성 채널에 남아 있는 멤버 수 확인
        remaining_members = [
            m for m in voice_client.channel.members if not m.bot
        ]  # 봇을 제외한 멤버만 계산

        if len(remaining_members) == 0:
            # 멤버가 아무도 남아 있지 않으면 음성 채널 떠남
            await voice_client.disconnect()
            print("음성 채널에 유저가 없어 봇이 나갔습니다.")

# /현재곡 - 현재 재생 중인 곡 정보 표시
@bot.tree.command(name="현재곡", description="현재 재생 중인 곡의 정보를 표시합니다.")
async def now_playing(interaction: discord.Interaction):
    """
    현재 재생 중인 곡의 정보를 Discord Embed 메시지로 표시합니다.
    """
    global current_track, current_track_start_time

    if not current_track:
        await interaction.response.send_message("현재 재생 중인 곡이 없습니다.", ephemeral=True)
        return

    try:
        # 현재 곡 정보 가져오기
        title = current_track.title
        url = current_track.data.get('webpage_url', 'https://www.youtube.com')
        duration = current_track.data.get('duration', 0)  # 전체 길이 (초 단위)
        minutes_total, seconds_total = divmod(duration, 60)

        # 현재 재생 시간 계산
        if current_track_start_time:
            elapsed_time_seconds = int(time.time() - current_track_start_time)  # 경과 시간 계산
        else:
            elapsed_time_seconds = 0

        minutes_current, seconds_current = divmod(elapsed_time_seconds, 60)

        # Embed 메시지 생성
        embed = discord.Embed(
            title="🎵 현재 재생 중인 곡",
            description=f"[{title}]({url})",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="⏱️ 재생 시간",
            value=f"{minutes_current:02}:{seconds_current:02} / {minutes_total:02}:{seconds_total:02}",
            inline=False
        )
        embed.add_field(
            name="📂 대기열",
            value=f"{len(music_queue)}곡 남음" if music_queue else "대기열이 비어 있습니다.",
            inline=False
        )
        embed.set_thumbnail(url="https://img.youtube.com/vi/{}/hqdefault.jpg".format(current_track.data.get('id', '')))
        embed.set_footer(text="음악 분위기를 즐겨보세요! 🎶")

        # 메시지 전송
        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(f"현재 곡 정보를 가져오는 중 오류가 발생했습니다: {e}", ephemeral=True)

# /셔플 - 대기열에 있는 노래들을 무작위로 섞습니다.
@bot.tree.command(name="셔플", description="대기열에 있는 노래들을 무작위로 섞습니다.")
async def shuffle_queue(interaction: discord.Interaction):
    """
    대기열을 셔플하는 명령어.
    """
    global music_queue

    if not music_queue:
        await interaction.response.send_message("대기열이 비어 있습니다.", ephemeral=True)
        return

    # 대기열 셔플
    random.shuffle(music_queue)

    # 셔플된 대기열 출력
    shuffled_list = "\n".join([f"{i + 1}. {track.title}" for i, track in enumerate(music_queue)])
    await interaction.response.send_message(f"🎶 대기열이 셔플되었습니다:\n{shuffled_list}")

async def play_next_song(voice_client):
    """
    대기열에서 다음 곡을 가져와 재생하거나, 반복 모드에 따라 동작을 조정합니다.
    """
    global current_track, repeat_mode

    if repeat_mode == "current":
        # 현재 곡을 다시 재생
        voice_client.play(
            current_track.source,
            after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client), bot.loop)
        )
        return

    if music_queue:
        # 대기열에서 다음 곡 가져오기
        next_track = music_queue.popleft()

        if repeat_mode == "queue":
            # 대기열 반복: 현재 곡을 다시 대기열 끝에 추가
            music_queue.append(next_track)

        current_track = next_track

        # 다음 곡 재생
        voice_client.play(
            next_track.source,
            after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client), bot.loop)
        )
    else:
        # 대기열이 비어 있고 반복 모드가 없으면 봇은 아무 작업도 하지 않음
        await asyncio.sleep(1)  # 봇이 멈추지 않도록 약간의 지연 추가

# /반복 - 현재 곡 반복, 대기열 반복, 반복 없음 상태를 순환합니다.
@bot.tree.command(name="반복", description="현재 곡 반복, 대기열 반복, 반복 없음 상태를 순환합니다.")
async def toggle_repeat(interaction: discord.Interaction):
    """
    현재 곡 반복, 대기열 반복, 반복 없음 상태를 순환하는 명령어.
    """
    global repeat_mode

    # 반복 상태 순환
    if repeat_mode == "none":
        repeat_mode = "current"  # 현재 곡 반복
        await interaction.response.send_message("🔁 현재 곡이 반복됩니다.")
    elif repeat_mode == "current":
        repeat_mode = "queue"  # 대기열 반복
        await interaction.response.send_message("🔂 대기열이 반복됩니다.")
    elif repeat_mode == "queue":
        repeat_mode = "none"  # 반복 없음
        await interaction.response.send_message("⏹️ 반복이 해제되었습니다.")


# 토큰으로 봇 실행 시작
bot.run(token)
