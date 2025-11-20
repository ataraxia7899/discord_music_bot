"""
음악 재생과 관련된 기능을 담당하는 모듈입니다.
YouTube 다운로드와 오디오 처리를 담당합니다.
"""

import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from config import settings, Track
from .music_core import get_music_manager
from .queue_manager import get_queue_manager

logger = logging.getLogger(__name__)

class AudioPlayerError(Exception):
    """오디오 플레이어 관련 예외"""
    pass

class YTDLSource:
    """YouTube 다운로더와 음원 처리를 담당하는 클래스"""
    _cache: Dict[str, Any] = {}
    _ytdl = YoutubeDL(settings.ytdl_options)

    def __init__(self, source, *, data):
        self.source = source
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.webpage_url = data.get('webpage_url', '')
        self.duration = data.get('duration', 0)

    @classmethod
    async def create_source(cls, query: str, *, loop=None, stream=True) -> Track:
        """URL 또는 검색어로부터 음원 소스를 생성"""
        loop = loop or asyncio.get_event_loop()
        
        # 캐시 확인
        cache_key = query.lower().strip()
        if cache_key in cls._cache:
            cached_track = cls._cache[cache_key]
            logger.info(f"캐시에서 트랙 로드: {cached_track.title}")
            return cached_track
        
        try:
            # 검색어 처리
            if not query.startswith(('http://', 'https://')):
                query = f"ytsearch:{query}"

            # 타임아웃과 함께 음원 정보 추출
            data = await asyncio.wait_for(
                loop.run_in_executor(None, 
                    lambda: cls._ytdl.extract_info(query, download=False)),
                timeout=30.0  # 30초 타임아웃
            )

            if 'entries' in data:
                data = data['entries'][0]

            # Track 객체 생성 (source 없이)
            track = Track(
                title=data.get('title', 'Unknown'),
                url=data.get('url', ''),
                duration=int(data.get('duration', 0)),
                webpage_url=data.get('webpage_url', ''),
                thumbnail_url=data.get('thumbnail', None),
                author=data.get('uploader', None)
            )
            
            # 캐시에 저장 (source 없이)
            cls._cache[cache_key] = track
            
            # 캐시 크기 제한 (메모리 누수 방지)
            if len(cls._cache) > 100:
                # 가장 오래된 항목 제거
                oldest_key = next(iter(cls._cache))
                del cls._cache[oldest_key]
            
            logger.info(f"트랙 생성 완료: {track.title}")
            return track

        except asyncio.TimeoutError:
            logger.error(f"음원 검색 타임아웃: {query}")
            raise AudioPlayerError("음원 검색이 시간 초과되었습니다. 다시 시도해주세요.")
        except Exception as e:
            logger.error(f"음원 생성 중 오류: {e}")
            raise AudioPlayerError(f"음원 처리 실패: {str(e)}")

class MusicPlayer:
    """음악 재생과 관련된 모든 명령어를 관리하는 클래스"""
    
"""
음악 재생과 관련된 기능을 담당하는 모듈입니다.
YouTube 다운로드와 오디오 처리를 담당합니다.
"""

import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from config import settings, Track
from .music_core import get_music_manager
from .queue_manager import get_queue_manager

logger = logging.getLogger(__name__)

class AudioPlayerError(Exception):
    """오디오 플레이어 관련 예외"""
    pass

class YTDLSource:
    """YouTube 다운로더와 음원 처리를 담당하는 클래스"""
    _cache: Dict[str, Any] = {}
    _ytdl = YoutubeDL(settings.ytdl_options)

    def __init__(self, source, *, data):
        self.source = source
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.webpage_url = data.get('webpage_url', '')
        self.duration = data.get('duration', 0)

    @classmethod
    async def create_source(cls, query: str, *, loop=None, stream=True) -> Track:
        """URL 또는 검색어로부터 음원 소스를 생성"""
        loop = loop or asyncio.get_event_loop()
        
        # 캐시 확인
        cache_key = query.lower().strip()
        if cache_key in cls._cache:
            cached_track = cls._cache[cache_key]
            logger.info(f"캐시에서 트랙 로드: {cached_track.title}")
            return cached_track
        
        try:
            # 검색어 처리
            if not query.startswith(('http://', 'https://')):
                query = f"ytsearch:{query}"

            # 타임아웃과 함께 음원 정보 추출
            data = await asyncio.wait_for(
                loop.run_in_executor(None, 
                    lambda: cls._ytdl.extract_info(query, download=False)),
                timeout=30.0  # 30초 타임아웃
            )

            if 'entries' in data:
                data = data['entries'][0]

            # Track 객체 생성 (source 없이)
            track = Track(
                title=data.get('title', 'Unknown'),
                url=data.get('url', ''),
                duration=int(data.get('duration', 0)),
                webpage_url=data.get('webpage_url', ''),
                thumbnail_url=data.get('thumbnail', None),
                author=data.get('uploader', None)
            )
            
            # 캐시에 저장 (source 없이)
            cls._cache[cache_key] = track
            
            # 캐시 크기 제한 (메모리 누수 방지)
            if len(cls._cache) > 100:
                # 가장 오래된 항목 제거
                oldest_key = next(iter(cls._cache))
                del cls._cache[oldest_key]
            
            logger.info(f"트랙 생성 완료: {track.title}")
            return track

        except asyncio.TimeoutError:
            logger.error(f"음원 검색 타임아웃: {query}")
            raise AudioPlayerError("음원 검색이 시간 초과되었습니다. 다시 시도해주세요.")
        except Exception as e:
            logger.error(f"음원 생성 중 오류: {e}")
            raise AudioPlayerError(f"음원 처리 실패: {str(e)}")

class MusicPlayer:
    """음악 재생과 관련된 모든 명령어를 관리하는 클래스"""
    
    def __init__(self, bot):
        self.bot = bot
        self._lock = asyncio.Lock()
        self.music_manager = get_music_manager(bot)
        self.queue_manager = get_queue_manager(bot)
        
    # 슬래시 커맨드 핸들러들
    async def play(self, interaction: discord.Interaction, query: str):
        """슬래시 명령어 버전의 재생 명령어"""
        try:
            # 사용자가 음성 채널에 있는지 확인
            if not interaction.user.voice:
                await interaction.response.send_message("먼저 음성 채널에 입장해주세요!", ephemeral=True)
                return

            voice_channel = interaction.user.voice.channel
            voice_client = interaction.guild.voice_client

            await interaction.response.defer()

            # 음성 채널 연결
            if not voice_client:
                voice_client = await voice_channel.connect()
            elif voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)

            # 음성 클라이언트 상태 확인
            if not voice_client.is_connected():
                logger.error("음성 클라이언트가 연결되지 않음")
                await interaction.followup.send("음성 채널에 연결할 수 없습니다.")
                return

            # 음원 소스 생성
            try:
                track = await YTDLSource.create_source(query, loop=self.bot.loop)
            except Exception as e:
                await interaction.followup.send(f"음원을 불러오는 중 오류가 발생했습니다: {str(e)}")
                return

            guild_id = interaction.guild_id
            guild_state = self.music_manager.get_server_state(guild_id)

            # 트랙 추가 및 재생
            if not voice_client.is_playing():
                # 현재 재생 중이 아니므로 바로 재생
                # 트랙을 대기열에 추가하고 play_next_song으로 재생
                await guild_state.add_track(track)
                logger.info(f"트랙을 대기열에 추가: {track.title}")
                
                # play_next_song 함수 호출
                try:
                    await self.music_manager.play_next_song(voice_client, guild_id)
                    logger.info(f"play_next_song 함수 호출 완료: {track.title}")
                except Exception as e:
                    logger.error(f"play_next_song 함수 호출 실패: {e}")
                    await interaction.followup.send(f"재생 시작에 실패했습니다: {str(e)}")
                    return
                
                # 재생 상태 확인
                await asyncio.sleep(3)  # 대기 시간 증가
                if voice_client.is_playing():
                    await interaction.followup.send(f"🎵 재생 시작: **{track.title}**")
                    logger.info(f"재생 성공 확인: {track.title}")
                else:
                    # 재생이 실패한 경우 직접 재생 시도
                    logger.warning(f"play_next_song으로 재생 실패, 직접 재생 시도: {track.title}")
                    try:
                        # 직접 음원 소스 생성 및 재생
                        source = await discord.FFmpegOpusAudio.from_probe(
                            track.url,
                            method='fallback',
                            **settings.ffmpeg_options
                        )
                        
                        def after_playing(error):
                            if error:
                                logger.error(f"직접 재생 중 오류: {error}")
                            else:
                                logger.info(f"직접 재생 완료: {track.title}")
                        
                        voice_client.play(source, after=after_playing)
                        await interaction.followup.send(f"🎵 재생 시작 (직접 재생): **{track.title}**")
                        logger.info(f"직접 재생 시작: {track.title}")
                    except Exception as e:
                        logger.error(f"직접 재생도 실패: {e}")
                        await interaction.followup.send(f"⚠️ 재생 시작에 실패했습니다: **{track.title}**")
                        logger.error(f"재생 실패: {track.title}")
                        # 실패 원인 추적
                        logger.error(f"음성 클라이언트 상태: 연결={voice_client.is_connected()}, 재생={voice_client.is_playing()}")
            else:
                # 현재 재생 중이므로 대기열에 추가
                position = await self.queue_manager.add_track(guild_id, track)
                await interaction.followup.send(f"🎵 대기열 {position}번에 추가됨: **{track.title}**")

        except Exception as e:
            logger.error(f"재생 명령어 처리 중 오류 발생: {e}")
            await interaction.followup.send(f"재생 중 오류가 발생했습니다: {str(e)}")

    async def skip(self, interaction: discord.Interaction):
        """슬래시 명령어 버전의 다음곡 명령어"""
        try:
            voice_client = interaction.guild.voice_client
            if not voice_client or not voice_client.is_playing():
                await interaction.response.send_message("현재 재생 중인 곡이 없습니다.", ephemeral=True)
                return

            # 현재 곡 스킵
            voice_client.stop()
            await interaction.response.send_message("⏭️ 다음 곡으로 넘어갑니다.")

        except Exception as e:
            logger.error(f"다음곡 명령어 처리 중 오류 발생: {e}")
            await interaction.response.send_message(f"다음곡 재생 중 오류가 발생했습니다: {str(e)}", ephemeral=True)

    async def shuffle(self, interaction: discord.Interaction):
        """슬래시 명령어 버전의 셔플 명령어"""
        try:
            voice_client = interaction.guild.voice_client
            if not voice_client:
                await interaction.response.send_message("음성 채널에 연결되어 있지 않습니다.", ephemeral=True)
                return

            guild_id = interaction.guild_id
            await self.queue_manager.shuffle_queue(guild_id)
            await interaction.response.send_message("🔀 대기열이 섞였습니다!")

        except Exception as e:
            logger.error(f"셔플 명령어 처리 중 오류 발생: {e}")
            await interaction.response.send_message(f"셔플 중 오류가 발생했습니다: {str(e)}", ephemeral=True)

    async def remove(self, interaction: discord.Interaction, index: int):
        """슬래시 명령어 버전의 삭제 명령어"""
        try:
            guild_id = interaction.guild_id
            removed_track = await self.queue_manager.remove_track(guild_id, index - 1)
            
            if removed_track:
                await interaction.response.send_message(f"✂️ 제거됨: **{removed_track.title}**")
            else:
                await interaction.response.send_message("해당 위치에 곡이 없습니다.", ephemeral=True)

        except Exception as e:
            logger.error(f"삭제 명령어 처리 중 오류 발생: {e}")
            await interaction.response.send_message(f"삭제 중 오류가 발생했습니다: {str(e)}", ephemeral=True)

    async def toggle_repeat(self, interaction: discord.Interaction):
        """슬래시 명령어 버전의 반복 명령어"""
        try:
            guild_id = interaction.guild_id
            state = self.music_manager.get_server_state(guild_id)
            
            # 반복 모드 전환: none -> single -> all -> none
            current_mode = state._repeat_mode
            if current_mode == "none":
                state._repeat_mode = "single"
                await interaction.response.send_message("🔂 한곡 반복 모드가 설정되었습니다.")
            elif current_mode == "single":
                state._repeat_mode = "all"
                await interaction.response.send_message("🔁 전체 반복 모드가 설정되었습니다.")
            else:
                state._repeat_mode = "none"
                await interaction.response.send_message("➡️ 반복 모드가 해제되었습니다.")

        except Exception as e:
            logger.error(f"반복 명령어 처리 중 오류 발생: {e}")
            await interaction.response.send_message(f"반복 모드 설정 중 오류가 발생했습니다: {str(e)}", ephemeral=True)

    async def stop(self, interaction: discord.Interaction):
        """슬래시 명령어 버전의 정지 명령어"""
        try:
            voice_client = interaction.guild.voice_client
            if not voice_client:
                await interaction.response.send_message("이미 음성 채널에서 나와있습니다.", ephemeral=True)
                return

            guild_id = interaction.guild_id
            state = self.music_manager.get_server_state(guild_id)
            
            # 재생 중지 및 대기열 초기화
            if voice_client.is_playing():
                voice_client.stop()
            await state.clear_queue()
            await voice_client.disconnect()
            await interaction.response.send_message("👋 재생을 멈추고 채널에서 나갔습니다.")

        except Exception as e:
            logger.error(f"정지 명령어 처리 중 오류 발생: {e}")
            await interaction.response.send_message(f"정지 중 오류가 발생했습니다: {str(e)}", ephemeral=True)

async def setup(bot):
    """봇에 음악 관련 명령어들을 등록"""
    player = MusicPlayer(bot)
    
    # 슬래시 명령어 등록
    @bot.tree.command(name="재생", description="유튜브 URL 또는 검색어로 음악을 재생합니다.")
    async def play_slash_command(interaction: discord.Interaction, query: str):
        await player.play(interaction, query)
    
    @bot.tree.command(name="다음곡", description="현재 곡을 건너뛰고 다음 곡을 재생합니다.")
    async def skip_slash_command(interaction: discord.Interaction):
        await player.skip(interaction)
    
    @bot.tree.command(name="셔플", description="대기열을 무작위로 섞습니다.")
    async def shuffle_slash_command(interaction: discord.Interaction):
        await player.shuffle(interaction)
    
    @bot.tree.command(name="삭제", description="대기열에서 특정 곡을 삭제합니다.")
    async def remove_slash_command(interaction: discord.Interaction, 곡번호: int):
        await player.remove(interaction, 곡번호)
    
    @bot.tree.command(name="반복", description="반복 모드를 전환합니다.")
    async def repeat_slash_command(interaction: discord.Interaction):
        await player.toggle_repeat(interaction)
    
    @bot.tree.command(name="정지", description="재생을 멈추고 음성 채널에서 나갑니다.")
    async def stop_slash_command(interaction: discord.Interaction):
        await player.stop(interaction)

    print("Music player commands are ready!")