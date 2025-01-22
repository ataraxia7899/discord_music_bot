import discord  # 디스코드 API 모듈
from discord.ext import commands  # 확장 모듈
import yt_dlp  # 유튜브 다운로드 및 스트리밍 모듈
import asyncio  # 비동기 처리 모듈
from secret import token  # 디스코드 봇 토큰

# Python 출력 인코딩 설정 (글씨 깨짐 방지)
import sys
import io

# 디스코드 봇 객체 생성
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 유튜브 DL 옵션 설정
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}
ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

# 유튜브 동영상을 디스코드 봇에서 재생하기 위한 클래스
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# 봇 준비 이벤트
@bot.event
async def on_ready():
    print(f'봇이 로그인되었습니다: {bot.user}')
    try:
        synced = await bot.tree.sync()  # 슬래시 명령어 동기화
        print(f"동기화된 슬래시 명령어: {len(synced)}개")
    except Exception as e:
        print(f"명령어 동기화 중 오류 발생: {e}")

# /play 슬래시 명령어
@bot.tree.command(name="play", description="음악 재생")
async def play(interaction: discord.Interaction, url: str):
    await interaction.response.defer()  # 응답 지연

    if not interaction.user.voice:
        await interaction.followup.send("먼저 음성 채널에 입장해야 합니다.", ephemeral=True)
        return

    channel = interaction.user.voice.channel
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)

    if not voice_client:
        voice_client = await channel.connect()

    async with interaction.channel.typing():
        try:
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
            voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
            await interaction.followup.send(f'재생 중: {player.title}')  # 최종 응답
        except yt_dlp.utils.DownloadError as e:
            await interaction.followup.send(f"동영상을 다운로드하는 중 오류가 발생했습니다: {e}")

# /stop 슬래시 명령어
@bot.tree.command(name="stop", description="음악 정지")
async def stop(interaction: discord.Interaction):
    await interaction.response.defer()  # 응답 지연

    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)

    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await interaction.followup.send("음악을 멈추고 봇이 퇴장했습니다.")
    else:
        await interaction.followup.send("봇이 음성 채널에 있지 않습니다.")

# 봇 실행
bot.run(token)