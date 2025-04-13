"""
봇의 핵심 기능을 담당하는 모듈
음악 재생과 관련된 상태를 관리합니다.
"""

from collections import deque
from typing import Optional, Deque
from datetime import datetime
import asyncio
import logging
import discord
from config import Track, get_optimized_ffmpeg_options

logger = logging.getLogger(__name__)

class ServerMusicState:
    def __init__(self):
        self.music_queue: Deque[Track] = deque()
        self.current_track: Optional[Track] = None
        self.start_time: Optional[datetime] = None
        self.voice_client = None
        self.text_channel = None
        self._repeat_mode: str = "none"
        self._volume: float = 1.0
        self._is_playing: bool = False
        self._lock = asyncio.Lock()
        self._previous_queue = []
    
    @property
    def is_playing(self) -> bool:
        return self._is_playing and self.voice_client and self.voice_client.is_playing()
    
    async def add_track(self, track: Track):
        """트랙을 대기열에 추가"""
        async with self._lock:
            self.music_queue.append(track)
    
    async def clear_queue(self):
        """대기열 초기화"""
        async with self._lock:
            self.music_queue.clear()
            self._previous_queue.clear()

    async def handle_repeat_mode(self) -> Optional[Track]:
        """반복 모드 처리"""
        if not self.current_track:
            return None
            
        if self._repeat_mode == "single":
            return self.current_track
        elif self._repeat_mode == "all" and not self.music_queue:
            # 전체 반복 모드에서 대기열이 비었을 때
            self.music_queue.extend(self._previous_queue)
            self._previous_queue.clear()
            
        if self._repeat_mode == "all":
            self._previous_queue.append(self.current_track)
            
        return None

class MusicManager:
    def __init__(self, bot):
        self.bot = bot
        self._lock = asyncio.Lock()
        self.server_states = {}
    
    def get_server_state(self, guild_id: int) -> ServerMusicState:
        """서버별 상태를 가져오거나 생성"""
        if guild_id not in self.server_states:
            self.server_states[guild_id] = ServerMusicState()
        return self.server_states[guild_id]
    
    async def play_next_song(self, voice_client, guild_id: int):
        """다음 곡을 재생하는 함수"""
        guild_state = self.get_server_state(guild_id)
        
        try:
            if not voice_client or not voice_client.is_connected():
                logger.error("Voice client is not connected")
                return

            repeat_track = await guild_state.handle_repeat_mode()
            next_track = repeat_track or (guild_state.music_queue.popleft() if guild_state.music_queue else None)
            
            if next_track:
                guild_state.current_track = next_track
                guild_state.start_time = datetime.now()
                guild_state._is_playing = True

                try:
                    # 새로운 음원 생성
                    source = await discord.FFmpegOpusAudio.from_probe(
                        next_track.url,
                        method='fallback',
                        **get_optimized_ffmpeg_options()
                    )
                    next_track.source = source  # 소스 저장

                    def after_playing(error):
                        if error:
                            logger.error(f"재생 중 오류 발생: {error}")
                        asyncio.run_coroutine_threadsafe(
                            self.play_next_song(voice_client, guild_id),
                            self.bot.loop
                        )

                    voice_client.play(source, after=after_playing)
                    logger.info(f"재생 시작: {next_track.title}")

                except Exception as e:
                    logger.error(f"음원 생성 중 오류: {e}")
                    guild_state._is_playing = False
                    await self.play_next_song(voice_client, guild_id)

            else:
                guild_state._is_playing = False
                if guild_state.text_channel:
                    await guild_state.text_channel.send("🎵 재생할 곡이 없습니다.")

        except Exception as e:
            logger.error(f"재생 처리 중 오류: {e}")
            guild_state._is_playing = False

    async def update_voice_state(self, guild_id: int, voice_client, text_channel=None):
        """서버의 음성 상태를 업데이트"""
        state = self.get_server_state(guild_id)
        state.voice_client = voice_client
        if text_channel:
            state.text_channel = text_channel

music_manager = None

def get_music_manager(bot) -> MusicManager:
    """MusicManager 인스턴스를 가져오거나 생성"""
    global music_manager
    if music_manager is None:
        music_manager = MusicManager(bot)
    return music_manager

async def setup(bot):
    """봇 설정에 필요한 초기화를 수행합니다."""
    music_manager = get_music_manager(bot)
    bot.music_manager = music_manager