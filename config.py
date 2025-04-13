"""
봇의 설정값들을 관리하는 모듈
유튜브 다운로드, FFmpeg 옵션 등의 설정을 포함합니다.
"""

from collections import deque
from typing import Dict, Optional, TypedDict, Any, Deque
from dataclasses import dataclass, field
import logging
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

logger = logging.getLogger(__name__)

# 1번은 secret.py 파일에서 토큰 가져오기, 2번은 환경변수로 토큰 지정하기 방법 중 하나를 선택해서 사용하세요.

# config.py 파일에서 토큰을 가져오기 위한 코드 (1번)
#from secret import token  # 디스코드 봇 토큰 가져오기

# 클라우드에서 환경변수로 토큰을 지정해서 사용하기 위한 코드 (2번)
import os
token = os.getenv("DISCORD_BOT_TOKEN")

@dataclass
class Track:
    """음악 트랙 정보를 담는 데이터 클래스"""
    title: str
    url: str
    duration: int
    webpage_url: str
    thumbnail_url: Optional[str] = None
    author: Optional[str] = None
    source: Optional[Any] = None  # FFmpeg 소스 저장용 필드 추가

def get_ytdl_options():
    return {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'source_address': '0.0.0.0',
        'force-ipv4': True,
        'extract_flat': False,
        'compat_opts': {'no-youtube-unavailable-videos': True},
        'geo_bypass': True,
        'cachedir': False
    }

def get_optimized_ffmpeg_options():
    """FFmpeg 최적화 옵션을 반환합니다."""
    return {
        'before_options': (
            '-reconnect 1 '
            '-reconnect_streamed 1 '
            '-reconnect_delay_max 5 '
            '-analyzeduration 2147483647 '
            '-probesize 2147483647'
        ),
        'options': '-vn -ar 48000 -ac 2 -f opus -b:a 96k'  # 오디오 설정 구체화
    }

def get_optimized_ytdl_options():
    return {
        'format': 'bestaudio',
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'extract_flat': True,
        'skip_download': True,
        'force_generic_extractor': False,
        'cachedir': './.cache',  # 로컬 캐시 디렉토리
        'prefer_ffmpeg': True,
        'postprocessors': [{  # 후처리 최적화
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
            'preferredquality': '96'
        }]
    }

ffmpeg_options = {
    'options': '-vn -c:a libopus -b:a 128k',  # 기본 오디오 옵션
    'before_options': (
        '-reconnect 1 '
        '-reconnect_streamed 1 '
        '-reconnect_delay_max 5 '
        '-nostdin '  # 표준 입력 비활성화
    )
}

# 봇 설정
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')  # 환경 변수에서 토큰 가져오기
DEFAULT_PREFIX = os.getenv('BOT_PREFIX', '!')  # 환경 변수에서 접두사 가져오기, 기본값 '!'

class GuildState:
    """서버별 상태를 관리하는 클래스"""
    def __init__(self):
        self.music_queue: deque[Track] = deque()
        self.current_track: Optional[Track] = None
        self.voice_client: Optional[Any] = None
        self.text_channel: Optional[Any] = None
        self.repeat_mode: str = "none"
        self.volume: float = 1.0
        self.start_time: Optional[datetime] = None

class GlobalConfig:
    def __init__(self):
        self._states: Dict[int, GuildState] = {}
        self._lock = asyncio.Lock()
        self._load_config()
    
    def _load_config(self):
        """환경 변수에서 설정을 로드합니다."""
        self.bot_token = os.getenv('DISCORD_BOT_TOKEN')
        self.default_prefix = os.getenv('BOT_PREFIX', '!')
    
    async def get_guild_state(self, guild_id: int) -> GuildState:
        """길드별 상태를 안전하게 가져오거나 생성"""
        async with self._lock:
            if guild_id not in self._states:
                self._states[guild_id] = GuildState()
            return self._states[guild_id]

    async def clear_guild_state(self, guild_id: int):
        """길드별 상태를 안전하게 초기화"""
        async with self._lock:
            if guild_id in self._states:
                self._states[guild_id] = GuildState()

    def get_guild_queue(self, guild_id: int) -> deque[Track]:
        return self._states.get(guild_id, GuildState()).music_queue

# 전역 설정 인스턴스 생성
global_config = GlobalConfig()

class BotConfig(TypedDict):
    token: str
    prefix: str
    ffmpeg_options: dict
    ytdl_options: dict

class ConfigManager:
    def __init__(self):
        self._config: Optional[BotConfig] = None
        self._load_config()

    def _load_config(self):
        """환경 변수에서 설정을 로드합니다."""
        self._config = {
            'token': os.getenv('DISCORD_BOT_TOKEN'),
            'prefix': os.getenv('BOT_PREFIX', '!'),
            'ffmpeg_options': get_optimized_ffmpeg_options(),
            'ytdl_options': {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'default_search': 'ytsearch'
            }
        }

    @property
    def ffmpeg_options(self) -> dict:
        return {
            'options': '-vn -c:a libopus -b:a 128k',
            'before_options': (
                '-reconnect 1 '
                '-reconnect_streamed 1 '
                '-reconnect_delay_max 5 '
                '-nostdin '
                '-analyzeduration 0 '
            )
        }
