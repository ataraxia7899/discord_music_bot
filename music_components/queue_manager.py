"""
대기열 관리와 관련된 기능을 담당하는 모듈
대기열 추가, 삭제, 이동 등의 기능을 제공합니다.
"""

import discord
from discord.ext import commands
import asyncio
import random
import logging
from typing import Optional, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from .music_core import get_music_manager, Track

logger = logging.getLogger(__name__)
"""
대기열 관리와 관련된 기능을 담당하는 모듈
대기열 추가, 삭제, 이동 등의 기능을 제공합니다.
"""

import discord
from discord.ext import commands
import asyncio
import random
import logging
from typing import Optional, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from .music_core import get_music_manager, Track

logger = logging.getLogger(__name__)

class QueueCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue_manager = QueueManager(bot)

    # 슬래시 커맨드
    async def show_queue(self, interaction: discord.Interaction):
        """슬래시 명령어 버전의 대기열 보기"""
        try:
            guild_id = interaction.guild_id
            queue_info = await self.queue_manager.get_queue_info(guild_id)
            
            if not queue_info['current'] and not queue_info['queue']:
                await interaction.response.send_message("🎵 대기열이 비어있습니다.")
                return

            embed = discord.Embed(title="🎵 현재 대기열", color=discord.Color.blue())
            
            if queue_info['current']:
                current = queue_info['current']
                embed.add_field(
                    name="현재 재생 중",
                    value=f"🎵 **{current.title}**\n⏱️ 길이: {current.duration//60}:{current.duration%60:02d}",
                    inline=False
                )

            if queue_info['queue']:
                queue_text = ""
                for i, track in enumerate(queue_info['queue'], 1):
                    queue_text += f"{i}. {track.title} ({track.duration//60}:{track.duration%60:02d})\n"
                    if i >= 10:
                        remaining = len(queue_info['queue']) - 10
                        if remaining > 0:
                            queue_text += f"\n...그 외 {remaining}곡"
                        break
                embed.add_field(name="대기열", value=queue_text, inline=False)
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"대기열 표시 중 오류 발생: {e}")
            await interaction.response.send_message(
                f"대기열 정보를 가져오는 중 오류가 발생했습니다: {str(e)}",
                ephemeral=True
            )

    async def clear_queue(self, interaction: discord.Interaction):
        """슬래시 명령어 버전의 대기열 초기화"""
        try:
            guild_id = interaction.guild_id
            await self.queue_manager.clear_queue(guild_id)
            await interaction.response.send_message("🗑️ 대기열이 초기화되었습니다.")
        except Exception as e:
            logger.error(f"대기열 초기화 중 오류 발생: {e}")
            await interaction.response.send_message(
                f"대기열 초기화 중 오류가 발생했습니다: {str(e)}",
                ephemeral=True
            )

    async def move_track(self, interaction: discord.Interaction, from_pos: int, to_pos: int):
        """슬래시 명령어 버전의 곡 이동"""
        try:
            from_pos -= 1
            to_pos -= 1
            
            guild_id = interaction.guild_id
            if await self.queue_manager.move_track(guild_id, from_pos, to_pos):
                await interaction.response.send_message(
                    f"✅ {from_pos + 1}번 곡을 {to_pos + 1}번 위치로 이동했습니다."
                )
            else:
                await interaction.response.send_message(
                    "❌ 올바르지 않은 위치입니다.",
                    ephemeral=True
                )
        except Exception as e:
            logger.error(f"곡 이동 중 오류 발생: {e}")
            await interaction.response.send_message(
                f"곡 이동 중 오류가 발생했습니다: {str(e)}",
                ephemeral=True
            )

class QueueManager:
    def __init__(self, bot):
        self.bot = bot
        self.music_manager = get_music_manager(bot)
        self._executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="queue_worker")
        self._lock = asyncio.Lock()
        self._cache = {}

    async def add_track(self, guild_id: int, track: Track) -> int:
        """트랙을 대기열에 추가하고 위치를 반환"""
        state = self.music_manager.get_server_state(guild_id)
        async with self._lock:
            if len(state.music_queue) >= 50:
                raise ValueError("대기열이 가득 찼습니다 (최대 50곡)")
            
            position = len(state.music_queue)
            await state.add_track(track)
            self._update_queue_cache(guild_id)
            return position + 1

    def _update_queue_cache(self, guild_id: int):
        """대기열 캐시 업데이트"""
        state = self.music_manager.get_server_state(guild_id)
        if len(state.music_queue) > 0:
            self._cache[guild_id] = {
                'last_updated': datetime.now(),
                'queue': list(state.music_queue)
            }

    async def remove_track(self, guild_id: int, index: int) -> Optional[Track]:
        """대기열에서 특정 위치의 트랙을 제거"""
        state = self.music_manager.get_server_state(guild_id)
        async with self._lock:
            if 0 <= index < len(state.music_queue):
                return state.music_queue.pop(index)
            return None

    async def move_track(self, guild_id: int, from_pos: int, to_pos: int) -> bool:
        """대기열에서 트랙의 위치를 이동"""
        state = self.music_manager.get_server_state(guild_id)
        async with self._lock:
            if (0 <= from_pos < len(state.music_queue) and 
                0 <= to_pos < len(state.music_queue)):
                track = state.music_queue[from_pos]
                state.music_queue.remove(track)
                state.music_queue.insert(to_pos, track)
                return True
            return False

    async def shuffle_queue(self, guild_id: int):
        """대기열을 무작위로 섞음"""
        state = self.music_manager.get_server_state(guild_id)
        async with self._lock:
            # 현재 재생 중인 곡 제외
            current = state.current_track
            
            # 대기열을 리스트로 변환하여 섞기
            queue_list = list(state.music_queue)
            if len(queue_list) > 1:  # 2곡 이상일 때만 섞기
                random.shuffle(queue_list)
                
                # 섞인 대기열 적용
                state.music_queue.clear()
                state.music_queue.extend(queue_list)
                
                # 캐시 갱신
                self._update_queue_cache(guild_id)
                return True
            return False

    async def clear_queue(self, guild_id: int):
        """대기열을 비움"""
        state = self.music_manager.get_server_state(guild_id)
        await state.clear_queue()

    async def get_queue_info(self, guild_id: int) -> dict:
        """현재 대기열 정보를 가져옴"""
        state = self.music_manager.get_server_state(guild_id)
        current = state.current_track
        queue = list(state.music_queue)
        return {
            'current': current,
            'queue': queue,
            'queue_length': len(queue),
            'start_time': state.start_time,
            'is_playing': state.is_playing
        }

    def __del__(self):
        """리소스 정리"""
        self._executor.shutdown(wait=True)

queue_manager = None

def get_queue_manager(bot) -> QueueManager:
    """QueueManager 인스턴스를 가져오거나 생성"""
    global queue_manager
    if queue_manager is None:
        queue_manager = QueueManager(bot)
    return queue_manager

async def setup(bot):    
    """봇에 대기열 관련 명령어들을 등록"""
    queue_commands = QueueCommands(bot)
    
    # 슬래시 명령어 등록
    @bot.tree.command(name="대기열", description="현재 재생 대기열을 보여줍니다.")
    async def show_queue_slash_command(interaction: discord.Interaction):
        await queue_commands.show_queue(interaction)
    
    @bot.tree.command(name="대기열초기화", description="재생 대기열을 초기화합니다.")
    async def clear_queue_slash_command(interaction: discord.Interaction):
        await queue_commands.clear_queue(interaction)
    
    @bot.tree.command(name="이동", description="대기열에서 곡의 위치를 이동합니다.")
    async def move_track_slash_command(
        interaction: discord.Interaction,
        시작위치: int,
        도착위치: int
    ):
        await queue_commands.move_track(interaction, 시작위치, 도착위치)

    print("Queue manager commands are ready!")