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
from core import Track  # core.py의 Track 클래스를 사용

# 환경 변수 로드
load_dotenv()

logger = logging.getLogger(__name__)

# 1번은 secret.py 파일에서 토큰 가져오기, 2번은 환경변수로 토큰 지정하기 방법 중 하나를 선택해서 사용하세요.

# config.py 파일에서 토큰을 가져오기 위한 코드 (1번)
#from secret import token  # 디스코드 봇 토큰 가져오기

# 클라우드에서 환경변수로 토큰을 지정해서 사용하기 위한 코드 (2번)
import os
token = os.getenv("DISCORD_BOT_TOKEN")
YOUR_LOSTARK_API_KEY = os.getenv("YOUR_LOSTARK_API_KEY")

def get_ytdl_options():
    """
    yt-dlp 라이브러리 설정 옵션
    
    Returns:
        dict: yt-dlp 옵션 딕셔너리
        
    주요 설정:
        - 오디오 포맷과 품질
        - 캐시 및 다운로드 설정
        - 네트워크 관련 설정
    """
    return {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'extract_flat': True,
        'skip_unavailable_fragments': True,
        'ignoreerrors': True,
        'no_color': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'opus',
        }],
        'cachedir': False,  # Disabled cache to prevent issues
        'skip_download': True,
        'playlistend': 50,
        'no_check_certificate': True,
        'source_address': '0.0.0.0',  # 네트워크 성능 개선
        'concurrent_fragments': 5,     # 동시 다운로드 수 증가
        'buffersize': 16*1024,        # 버퍼 크기 증가
        'http_chunk_size': 10*1024*1024,  # 청크 크기 증가
        'force_encoding': 'utf-8',    # 강제로 UTF-8 인코딩 사용
        'encoding': 'utf-8',          # ytdl 인코딩 설정
        'console_encoding': 'utf-8',  # 콘솔 출력 인코딩
        'lazy_playlist': True,  # 플레이리스트 지연 로딩
        'playlist_items': '1-50',  # 최대 50개 항목으로 제한
        'match_filter': 'duration < 7200',  # 2시간 이상 영상 제외
    }

def get_optimized_ffmpeg_options():
    """FFmpeg 최적화 옵션을 반환합니다."""
    return {
        'options': '-vn -c:a libopus -b:a 96k -bufsize 2048k',  # 버퍼 크기 증가
        'before_options': (
            '-reconnect 1 '
            '-reconnect_streamed 1 '
            '-reconnect_delay_max 5 '
            '-probesize 1M '
            '-analyzeduration 1M '
            '-rw_timeout 15000000 '  # 읽기/쓰기 타임아웃 증가
            '-timeout 15000000'      # 전체 타임아웃 증가
        )
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
# BOT_TOKEN = token  # secret.py에서 가져온 토큰 사용
DEFAULT_PREFIX = os.getenv('BOT_PREFIX', '!')  # 환경 변수에서 접두사 가져오기, 기본값 '!'

@dataclass
class Track:
    """음악 트랙 정보를 담는 데이터 클래스"""
    title: str
    url: str
    duration: int
    webpage_url: str
    thumbnail_url: Optional[str] = None
    author: Optional[str] = None

@dataclass
class GuildState:
    """서버별 상태를 관리하는 데이터 클래스"""
    music_queue: deque[Track] = field(default_factory=deque)
    current_track: Optional[Track] = None
    voice_client: Optional[Any] = None
    text_channel: Optional[Any] = None
    repeat_mode: str = "none"
    volume: float = 1.0
    start_time: Optional[datetime] = None

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

    def get_guild_queue(self, guild_id: int):
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
