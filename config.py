# config.py
from secret import token  # 디스코드 봇 토큰 가져오기

# 클라우드에서 환경변수로 토큰을 지정해서 사용하기 위한 코드
# import os
# token = os.getenv("DISCORD_BOT_TOKEN")

def get_ytdl_options():
    return {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

ffmpeg_options = {
    'options': '-vn -nostdin',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

# 봇 설정
BOT_TOKEN = token
DEFAULT_PREFIX = '!'
