"""
봇의 설정값들을 관리하는 모듈
유튜브 다운로드, FFmpeg 옵션 등의 설정을 포함합니다.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional, Any, Dict
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class Track:
    """음악 트랙 정보를 담는 데이터 클래스"""
    title: str
    url: str
    duration: int
    webpage_url: str
    thumbnail_url: Optional[str] = None
    author: Optional[str] = None
    source: Optional[Any] = None  # FFmpeg 소스 저장용 필드

class Settings:
    """
    봇의 설정을 관리하는 싱글톤 클래스
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """설정 초기화"""
        self.bot_token = os.getenv("DISCORD_BOT_TOKEN")
        self.default_prefix = os.getenv("BOT_PREFIX", "!")
        
        if not self.bot_token:
            logger.warning("DISCORD_BOT_TOKEN이 환경 변수에 설정되지 않았습니다.")

    @property
    def ytdl_options(self) -> Dict[str, Any]:
        """YouTube 다운로드 옵션 (최적화됨)"""
        return {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch',
            'extract_flat': True,
            'skip_download': True,
            'force_generic_extractor': False,
            'cachedir': './.cache',
            'prefer_ffmpeg': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                'preferredquality': '96'
            }],
            'compat_opts': {'no-youtube-unavailable-videos': True},
            'geo_bypass': True,
            'socket_timeout': 10,
        }

    @property
    def ffmpeg_options(self) -> Dict[str, Any]:
        """FFmpeg 실행 옵션 (최적화됨)"""
        return {
            'before_options': (
                '-reconnect 1 '
                '-reconnect_streamed 1 '
                '-reconnect_delay_max 5 '
                '-analyzeduration 500000 '
                '-probesize 500000'
            ),
            'options': '-vn -ar 48000 -ac 2 -f opus -b:a 96k -bufsize 96k'
        }

# 전역 설정 인스턴스
settings = Settings()
