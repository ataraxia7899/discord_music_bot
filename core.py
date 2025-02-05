"""
봇의 핵심 기능을 담당하는 모듈
음악 재생과 관련된 상태를 관리합니다.
"""

from collections import deque

class ServerMusicState:
    def __init__(self):
        self.music_queue = deque()
        self.current_track = None
        self.current_track_start_time = None
        self.repeat_mode = "none"
        self.voice_client = None
        self.text_channel = None
        self.auto_play_enabled = False

class MusicBotCore:
    """
    음악 봇의 핵심 기능을 담당하는 클래스
    
    Attributes:
        music_queue (deque): 재생 대기열
        current_track: 현재 재생 중인 트랙
        current_track_start_time: 현재 트랙 재생 시작 시간
        repeat_mode (str): 반복 모드 ("none", "current", "queue")
        auto_play_enabled (bool): 자동 재생 활성화 여부
    """
    
    def __init__(self):
        """MusicBotCore 초기화"""
        self.music_queue = deque()
        self.current_track = None
        self.current_track_start_time = None
        self.repeat_mode = "none"  # none, current, queue
        self.auto_play_enabled = False  # 기본값을 False로 변경
        self.server_states = {}  # 서버별 상태 관리 추가

    def clear_queue(self):
        """재생 대기열을 초기화합니다."""
        self.music_queue.clear()

    def add_to_queue(self, track):
        """트랙을 재생 대기열에 추가합니다."""
        self.music_queue.append(track)

    def get_next_track(self):
        """다음 트랙을 반환합니다."""
        return self.music_queue.popleft() if self.music_queue else None

    def get_server_state(self, guild_id: int) -> ServerMusicState:
        """서버별 상태를 반환하거나 새로 생성합니다."""
        if guild_id not in self.server_states:
            self.server_states[guild_id] = ServerMusicState()
        return self.server_states[guild_id]

music_bot = MusicBotCore()