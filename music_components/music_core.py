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
import discord
from config import Track, settings

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
            logger.info(f"트랙이 대기열에 추가됨: {track.title} (대기열 크기: {len(self.music_queue)})")
            logger.info(f"DEBUG: add_track - GuildState ID: {id(self)}, Queue ID: {id(self.music_queue)}")
    
    async def clear_queue(self):
        """대기열 초기화"""
        async with self._lock:
            self.music_queue.clear()
            self._previous_queue.clear()
            logger.info("대기열이 초기화되었습니다.")

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
            # 메모리 누수 방지를 위해 최대 50곡으로 제한
            if len(self._previous_queue) > 50:
                self._previous_queue.pop(0)
            
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
            logger.info(f"play_next_song 함수 시작 - guild_id: {guild_id}")
            logger.info(f"DEBUG: play_next_song - MusicManager ID: {id(self)}, GuildState ID: {id(guild_state)}, Queue ID: {id(guild_state.music_queue)}")
            logger.info(f"현재 대기열 크기: {len(guild_state.music_queue)}")
            logger.info(f"현재 트랙: {guild_state.current_track.title if guild_state.current_track else 'None'}")
            
            if not voice_client or not voice_client.is_connected():
                logger.error("Voice client is not connected")
                return

            repeat_track = await guild_state.handle_repeat_mode()
            next_track = repeat_track or (guild_state.music_queue.popleft() if guild_state.music_queue else None)
            
            if next_track:
                logger.info(f"재생할 트랙 발견: {next_track.title}")
                guild_state.current_track = next_track
                guild_state.start_time = datetime.now()
                guild_state._is_playing = True

                try:
                    # Track 객체에 이미 source가 있는지 확인
                    if not next_track.source:
                        # 새로운 음원 생성 (최적화된 옵션 사용)
                        logger.info(f"음원 소스 생성 시작: {next_track.title}")
                        logger.info(f"음원 URL: {next_track.url}")
                        
                        source = await discord.FFmpegOpusAudio.from_probe(
                            next_track.url,
                            method='fallback',
                            **settings.ffmpeg_options
                        )
                        next_track.source = source  # 소스 저장
                        logger.info(f"음원 소스 생성 완료: {next_track.title}")
                    else:
                        source = next_track.source
                        logger.info(f"기존 음원 소스 사용: {next_track.title}")

                    # 음성 클라이언트 상태 재확인
                    if not voice_client.is_connected():
                        logger.error("재생 시작 전 음성 클라이언트 연결 끊어짐")
                        guild_state._is_playing = False
                        return

                    logger.info(f"재생 시작 직전 - 음성 클라이언트 상태: 연결={voice_client.is_connected()}, 재생={voice_client.is_playing()}")

                    def after_playing(error):
                        if error:
                            logger.error(f"재생 중 오류 발생: {error}")
                        else:
                            logger.info(f"재생 완료: {next_track.title}")
                        
                        # 재생 완료 후 다음 곡이 있는지 확인
                        logger.info(f"DEBUG: after_playing - GuildState ID: {id(guild_state)}, Queue ID: {id(guild_state.music_queue)}, Queue Len: {len(guild_state.music_queue)}")
                        if guild_state.music_queue:
                            logger.info("다음 곡이 대기열에 있음, 자동 재생")
                            # 다음 곡 재생
                            asyncio.run_coroutine_threadsafe(
                                self.play_next_song(voice_client, guild_id),
                                self.bot.loop
                            )
                        else:
                            logger.info("대기열이 비어있음, 재생 종료")
                            guild_state._is_playing = False

                    # 재생 시작
                    voice_client.play(source, after=after_playing)
                    logger.info(f"재생 시작 명령 실행: {next_track.title}")

                except Exception as e:
                    logger.error(f"음원 생성 중 오류: {e}")
                    guild_state._is_playing = False
                    # 오류 발생 시 다음 곡으로 넘어가기
                    await asyncio.sleep(1)  # 잠시 대기
                    await self.play_next_song(voice_client, guild_id)

            else:
                logger.info("재생할 트랙이 없음")
                logger.info(f"대기열 상태: 크기={len(guild_state.music_queue)}, 현재트랙={guild_state.current_track.title if guild_state.current_track else 'None'}")
                guild_state._is_playing = False
                if guild_state.text_channel:
                    await guild_state.text_channel.send("🎵 재생할 곡이 없습니다.")

        except Exception as e:
            logger.error(f"재생 처리 중 오류: {e}")
            guild_state._is_playing = False

    async def update_voice_state(self, guild_id: int, voice_client, text_channel=None):
        """서버의 음성 상태를 업데이트"""
        state = self.get_server_state(guild_id)
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
import discord
from config import Track, settings

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
            logger.info(f"트랙이 대기열에 추가됨: {track.title} (대기열 크기: {len(self.music_queue)})")
            logger.info(f"DEBUG: add_track - GuildState ID: {id(self)}, Queue ID: {id(self.music_queue)}")
    
    async def clear_queue(self):
        """대기열 초기화"""
        async with self._lock:
            self.music_queue.clear()
            self._previous_queue.clear()
            logger.info("대기열이 초기화되었습니다.")

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
            # 메모리 누수 방지를 위해 최대 50곡으로 제한
            if len(self._previous_queue) > 50:
                self._previous_queue.pop(0)
            
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
            logger.info(f"play_next_song 함수 시작 - guild_id: {guild_id}")
            logger.info(f"DEBUG: play_next_song - MusicManager ID: {id(self)}, GuildState ID: {id(guild_state)}, Queue ID: {id(guild_state.music_queue)}")
            logger.info(f"현재 대기열 크기: {len(guild_state.music_queue)}")
            logger.info(f"현재 트랙: {guild_state.current_track.title if guild_state.current_track else 'None'}")
            
            if not voice_client or not voice_client.is_connected():
                logger.error("Voice client is not connected")
                return

            repeat_track = await guild_state.handle_repeat_mode()
            next_track = repeat_track or (guild_state.music_queue.popleft() if guild_state.music_queue else None)
            
            if next_track:
                logger.info(f"재생할 트랙 발견: {next_track.title}")
                guild_state.current_track = next_track
                guild_state.start_time = datetime.now()
                guild_state._is_playing = True

                try:
                    # Track 객체에 이미 source가 있는지 확인
                    if not next_track.source:
                        # 새로운 음원 생성 (최적화된 옵션 사용)
                        logger.info(f"음원 소스 생성 시작: {next_track.title}")
                        logger.info(f"음원 URL: {next_track.url}")
                        
                        source = await discord.FFmpegOpusAudio.from_probe(
                            next_track.url,
                            method='fallback',
                            **settings.ffmpeg_options
                        )
                        next_track.source = source  # 소스 저장
                        logger.info(f"음원 소스 생성 완료: {next_track.title}")
                    else:
                        source = next_track.source
                        logger.info(f"기존 음원 소스 사용: {next_track.title}")

                    # 음성 클라이언트 상태 재확인
                    if not voice_client.is_connected():
                        logger.error("재생 시작 전 음성 클라이언트 연결 끊어짐")
                        guild_state._is_playing = False
                        return

                    logger.info(f"재생 시작 직전 - 음성 클라이언트 상태: 연결={voice_client.is_connected()}, 재생={voice_client.is_playing()}")

                    def after_playing(error):
                        if error:
                            logger.error(f"재생 중 오류 발생: {error}")
                        else:
                            logger.info(f"재생 완료: {next_track.title}")
                        
                        # 재생 완료 후 다음 곡이 있는지 확인
                        logger.info(f"DEBUG: after_playing - GuildState ID: {id(guild_state)}, Queue ID: {id(guild_state.music_queue)}, Queue Len: {len(guild_state.music_queue)}")
                        if guild_state.music_queue:
                            logger.info("다음 곡이 대기열에 있음, 자동 재생")
                            # 다음 곡 재생
                            asyncio.run_coroutine_threadsafe(
                                self.play_next_song(voice_client, guild_id),
                                self.bot.loop
                            )
                        else:
                            logger.info("대기열이 비어있음, 재생 종료")
                            guild_state._is_playing = False

                    # 재생 시작
                    voice_client.play(source, after=after_playing)
                    logger.info(f"재생 시작 명령 실행: {next_track.title}")

                except Exception as e:
                    logger.error(f"음원 생성 중 오류: {e}")
                    guild_state._is_playing = False
                    # 오류 발생 시 다음 곡으로 넘어가기
                    await asyncio.sleep(1)  # 잠시 대기
                    await self.play_next_song(voice_client, guild_id)

            else:
                logger.info("재생할 트랙이 없음")
                logger.info(f"대기열 상태: 크기={len(guild_state.music_queue)}, 현재트랙={guild_state.current_track.title if guild_state.current_track else 'None'}")
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
    
    # 봇 인스턴스에 이미 매니저가 있다면 그것을 반환
    if hasattr(bot, 'music_manager') and bot.music_manager is not None:
        if music_manager is None:
            music_manager = bot.music_manager
        return bot.music_manager
        
    if music_manager is None:
        music_manager = MusicManager(bot)
        
    return music_manager

async def setup(bot):
    """봇 설정에 필요한 초기화를 수행합니다."""
    music_manager = get_music_manager(bot)
    bot.music_manager = music_manager