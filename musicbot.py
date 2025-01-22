import discord  # 디스코드 API를 사용하기 위한 모듈
from discord.ext import commands  # 디스코드 봇 명령어를 만들기 위한 확장 모듈
import yt_dlp  # 유튜브 동영상을 다운로드 및 스트리밍하기 위한 모듈
import asyncio  # 비동기 처리를 위한 모듈
from secret import token  # 디스코드 봇 토큰을 가져옴

# 디스코드 봇의 권한 설정
intents = discord.Intents.default()
intents.message_content = True  # 메시지 읽기 권한 활성화
bot = commands.Bot(command_prefix="!", intents=intents)  # 봇 객체 생성, 명령어 접두사는 "!"

# 유튜브 DL 옵션 설정
ytdl_format_options = {
    'format': 'bestaudio/best',  # 최고 음질 선택
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',  # 파일 이름 템플릿
    'restrictfilenames': True,  # 파일 이름 제한
    'noplaylist': False,  # 플레이리스트 다운로드 활성화 / 비활성화
    'nocheckcertificate': True,  # SSL 인증서 검사 비활성화
    'ignoreerrors': False,  # 오류 무시 비활성화
    'logtostderr': False,  # 표준 오류로 로그 출력 비활성화
    'quiet': True,  # 출력 최소화
    'no_warnings': True,  # 경고 메시지 비활성화
    'default_search': 'auto',  # 기본 검색 모드
    'source_address': '0.0.0.0'  # IPv6 문제 방지
}

# FFmpeg 옵션 설정
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',  # 재연결 옵션
    'options': '-vn'  # 비디오 스트림 비활성화
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)  # 유튜브 DL 객체 생성

# 유튜브 동영상을 디스코드 봇에서 재생하기 위한 클래스
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)  # 부모 클래스 초기화
        self.data = data  # 동영상 데이터 저장
        self.title = data.get('title')  # 동영상 제목 저장
        self.url = data.get('url')  # 동영상 URL 저장

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()  # 이벤트 루프 가져오기
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))  # 유튜브 동영상 정보 추출
        
        if 'entries' in data:
            data = data['entries'][0]  # 플레이리스트의 첫 번째 동영상 선택

        filename = data['url'] if stream else ytdl.prepare_filename(data)  # 파일 이름 준비
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)  # YTDLSource 객체 반환

# 봇이 명령어를 받으면 실행하는 부분
@bot.command(name="p")
async def play(ctx, url: str):
    if not ctx.message.author.voice:  # 사용자가 음성 채널에 있는지 확인
        await ctx.send("먼저 음성 채널에 입장해야 합니다.")  # 음성 채널에 없으면 메시지 전송
        return

    channel = ctx.message.author.voice.channel  # 사용자가 있는 음성 채널 가져오기
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)  # 봇의 음성 클라이언트 가져오기

    if not voice_client:  # 봇이 음성 채널에 없으면
        voice_client = await channel.connect()  # 음성 채널에 연결

    async with ctx.typing():  # 봇이 입력 중인 것처럼 보이게 함
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)  # 유튜브 동영상 스트리밍
        voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)  # 동영상 재생
    
    await ctx.send(f'재생 중: {player.title}')  # 재생 중인 동영상 제목 전송

@bot.command(name="stop")
async def stop(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)  # 봇의 음성 클라이언트 가져오기
    
    if voice_client and voice_client.is_connected():  # 봇이 음성 채널에 있으면
        await voice_client.disconnect()  # 음성 채널에서 연결 해제
        await ctx.send("음악을 멈추고 봇이 퇴장했습니다.")  # 메시지 전송
    else:
        await ctx.send("봇이 음성 채널에 있지 않습니다.")  # 봇이 음성 채널에 없으면 메시지 전송

# 토큰으로 봇 실행
bot.run(token)  # 봇 실행