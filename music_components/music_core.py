"""
봇의 핵심 기능을 담당하는 모듈
음악 재생과 관련된 상태를 관리합니다.
"""

from collections import deque
from dataclasses import dataclass
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
    
    @property
    def is_playing(self) -> bool:
        return self._is_playing and self.voice_client and self.voice_client.is_playing()
    
    async def add_track(self, track: Track):
        async with self._lock:
            self.music_queue.append(track)
    
    async def clear_queue(self):
        async with self._lock:
            self.music_queue.clear()

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
            if guild_state.music_queue:
                track = guild_state.music_queue.popleft()
                guild_state.current_track = track
                guild_state.start_time = datetime.now()
                
                try:
                    ffmpeg_options = get_optimized_ffmpeg_options()
                    audio = await discord.FFmpegOpusAudio.from_probe(
                        track.url,
                        **ffmpeg_options
                    )
                    
                    def after_playing(error):
                        if error:
                            logger.error(f"재생 중 오류 발생: {error}")
                        coro = self.play_next_song(voice_client, guild_id)
                        fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                        try:
                            fut.result()
                        except Exception as e:
                            logger.error(f'재생 후 처리 중 오류 발생: {e}')

                    voice_client.play(audio, after=after_playing)
                    
                except Exception as e:
                    logger.error(f"Error playing next song: {e}")
                    await self.play_next_song(voice_client, guild_id)
            else:
                # 모든 곡이 끝났을 때
                if voice_client and voice_client.is_connected():
                    text_channel = guild_state.text_channel
                    if text_channel:
                        embed = discord.Embed(
                            title="재생 종료",
                            description="모든 곡의 재생이 끝났습니다.",
                            color=discord.Color.blue()
                        )
                        await text_channel.send(embed=embed)
                    await voice_client.disconnect()

        except Exception as e:
            logger.error(f"Error in play_next_song: {e}")

    async def update_voice_state(self, guild_id: int, voice_client, text_channel=None):
        """서버의 음성 상태를 업데이트"""
        state = self.get_server_state(guild_id)
        state.voice_client = voice_client
        if text_channel:
            state.text_channel = text_channel

music_manager = None

def get_music_manager(bot) -> MusicManager:
    global music_manager
    if music_manager is None:
        music_manager = MusicManager(bot)
    return music_manager