import discord  # 디스코드 API 모듈
from discord.ext import commands  # 확장 모듈
import yt_dlp  # 유튜브 다운로드 및 스트리밍 모듈
import asyncio  # 비동기 처리 모듈
import re  # URL 검증 및 정리를 위한 정규식 모듈
from urllib.parse import urlparse, parse_qs  # URL 파싱을 위한 모듈
from secret import token  # 디스코드 봇 토큰

# 디스코드 봇 객체 생성
intents = discord.Intents.default()
intents.message_content = True  # 메시지 읽기 권한 활성화
bot = commands.Bot(command_prefix="!", intents=intents)

# 유튜브 DL 옵션 설정 함수 정의
def get_ytdl_options():
    return {
        'format': 'bestaudio/best',  # 최고 음질 선택 (기본값)
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',  # 파일 이름 템플릿
        'restrictfilenames': True,  # 파일 이름 제한
        'noplaylist': False,  # 플레이리스트 다운로드 활성화 / 비활성화
        'nocheckcertificate': True,  # SSL 인증서 검사 비활성화
        'ignoreerrors': False,  # 오류 무시 비활성화
        'logtostderr': False,  # 표준 오류로 로그 출력 비활성화
        'quiet': True,  # 출력 최소화
        'no_warnings': True,  # 경고 메시지 비활성화
        'default_search': 'ytsearch',  # 기본 검색 모드로 YouTube 검색 활성화
        'source_address': '0.0.0.0'  # IPv6 문제 방지
    }

# FFmpeg 옵션 설정
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',  # 재연결 옵션 설정
    'options': '-vn'  # 비디오 스트림 비활성화 (오디오만 재생)
}

# 유튜브 동영상을 디스코드 봇에서 재생하기 위한 클래스 정의
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)  # 부모 클래스 초기화
        self.data = data  # 동영상 데이터 저장
        self.title = data.get('title')  # 동영상 제목 저장
        self.url = data.get('url')  # 동영상 URL 저장

    @classmethod
    async def from_query(cls, query, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()  # 이벤트 루프 가져오기
        ytdl = yt_dlp.YoutubeDL(get_ytdl_options())  

        try:
            if is_valid_youtube_url(query):  
                cleaned_url = clean_youtube_url(query)  # URL을 정리하여 유효한 형태로 변환
                search_result = cleaned_url  
            else:
                search_results = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{query}", download=False))  
                if not search_results or 'entries' not in search_results or len(search_results['entries']) == 0:
                    raise ValueError("검색 결과를 찾을 수 없습니다.")  
                search_result = search_results['entries'][0]['webpage_url']  

            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search_result, download=not stream))  
            filename = data['url'] if stream else ytdl.prepare_filename(data)  
            return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)  
        
        except yt_dlp.utils.DownloadError as e:
            raise ValueError(f"동영상을 다운로드하는 중 오류가 발생했습니다: {e}")  

# 유튜브 URL 검증 함수 정의 (올바른 URL인지 확인)
def is_valid_youtube_url(url):
    youtube_regex = r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/(watch\?v=|embed/|v/|.+\?v=)?[a-zA-Z0-9_-]{11}$"
    return re.match(youtube_regex, url) is not None

# 유튜브 URL 정리 함수 정의 (추가 매개변수 제거)
def clean_youtube_url(url):
    parsed_url = urlparse(url)
    if "youtu.be" in parsed_url.netloc:  
        video_id = parsed_url.path.lstrip("/")  
    elif "youtube.com" in parsed_url.netloc:  
        video_id = parse_qs(parsed_url.query).get("v", [None])[0]  
    else:
        video_id = None

    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"  
    else:
        raise ValueError("유효한 YouTube URL이 아닙니다.")  

# 봇 준비 이벤트 처리 및 슬래시 명령어 동기화
@bot.event
async def on_ready():
    print(f'봇이 로그인되었습니다: {bot.user}')  
    try:
        synced = await bot.tree.sync()  
        print(f"동기화된 슬래시 명령어: {len(synced)}개")  
    except Exception as e:
        print(f"명령어 동기화 중 오류 발생: {e}")  

# /재생 슬래시 명령어 정의 - URL 또는 검색어로 음악 재생 가능
@bot.tree.command(name="재생", description="유튜브 URL 또는 검색어를 통해 음악을 재생합니다.")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()  

    if not interaction.user.voice:  
        await interaction.followup.send("먼저 음성 채널에 입장해야 합니다.", ephemeral=True)  
        return

    channel = interaction.user.voice.channel  
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)  

    if not voice_client:  
        voice_client = await channel.connect()  

    async with interaction.channel.typing():  
        try:
            player = await YTDLSource.from_query(query, loop=bot.loop, stream=True)  
            voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)  
            await interaction.followup.send(f'재생 중: {player.title}')  
        
        except ValueError as e:
            await interaction.followup.send(str(e))  

# /정지 슬래시 명령어 정의 - 음악 정지 기능 구현
@bot.tree.command(name="정지", description="현재 재생 중인 음악을 멈춥니다.")
async def stop(interaction: discord.Interaction):
    await interaction.response.defer()  

    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)  

    if voice_client and voice_client.is_connected():  
        await voice_client.disconnect()  
        await interaction.followup.send("음악을 멈추고 봇이 퇴장했습니다.")  
    else:
        await interaction.followup.send("봇이 음성 채널에 있지 않습니다.")  

# 토큰으로 봇 실행 시작
bot.run(token)
