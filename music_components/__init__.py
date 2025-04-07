"""
음악 관련 컴포넌트들을 관리하는 패키지
"""

from .music_core import get_music_manager
from .music_player import MusicPlayer
from .queue_manager import QueueManager, get_queue_manager

__all__ = [
    'get_music_manager',
    'MusicPlayer',
    'QueueManager',
    'get_queue_manager'
]