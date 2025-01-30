from collections import deque

class MusicBotCore:
    def __init__(self):
        self.music_queue = deque()
        self.current_track = None
        self.current_track_start_time = None
        self.repeat_mode = "none"  # none, current, queue
        self.auto_play_enabled = False  # 기본값을 False로 변경

    def clear_queue(self):
        self.music_queue.clear()

    def add_to_queue(self, track):
        self.music_queue.append(track)

    def get_next_track(self):
        return self.music_queue.popleft() if self.music_queue else None

music_bot = MusicBotCore()