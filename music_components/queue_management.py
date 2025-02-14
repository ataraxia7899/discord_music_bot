import discord
from discord.ext import commands
import time
from music_components.play_commands import YTDLSource
from config import global_config
from functools import lru_cache
from typing import List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
from config import Track

"""
대기열 관리 관련 명령어들을 포함하는 모듈
현재 재생 중인 곡 정보, 대기열 관리 등의 기능을 제공합니다.
"""

# /현재곡 - 현재 재생 중인 곡 정보 표시
@commands.command(name="현재곡", description="현재 재생 중인 곡의 정보를 표시합니다.")
async def now_playing(ctx):
    """
    현재 재생 중인 곡의 정보를 표시합니다.
    
    Args:
        ctx: 명령어 컨텍스트
        
    표시 정보:
        - 곡 제목과 URL
        - 재생 시간 (현재/전체)
        - 대기열 상태
    """
    if not ctx.bot.current_track:
        await ctx.send("현재 재생 중인 곡이 없습니다.")
        return

    try:
        title = ctx.bot.current_track.title
        url = ctx.bot.current_track.data.get('webpage_url', 'https://www.youtube.com')
        duration = ctx.bot.current_track.data.get('duration', 0)
        minutes_total, seconds_total = divmod(duration, 60)

        if ctx.bot.current_track_start_time:
            elapsed_time_seconds = int(time.time() - ctx.bot.current_track_start_time)
        else:
            elapsed_time_seconds = 0

        minutes_current, seconds_current = divmod(elapsed_time_seconds, 60)

        embed = discord.Embed(
            title="🎵 현재 재생 중인 곡",
            description=f"[{title}]({url})",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="⏱️ 재생 시간",
            value=f"{minutes_current:02}:{seconds_current:02} / {minutes_total:02}:{seconds_total:02}",
            inline=False
        )
        embed.add_field(
            name="📂 대기열",
            value=f"{len(ctx.bot.music_queue)}곡 남음" if ctx.bot.music_queue else "대기열이 비어 있습니다.",
            inline=False
        )
        embed.set_thumbnail(url="https://img.youtube.com/vi/{}/hqdefault.jpg".format(ctx.bot.current_track.data.get('id', '')))
        embed.set_footer(text="음악 분위기를 즐겨보세요! 🎶")

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"현재 곡 정보를 가져오는 중 오류가 발생했습니다: {e}")

# 슬래시 명령어 정의
async def now_playing_slash(interaction: discord.Interaction):
    if not interaction.client.current_track:
        await interaction.response.send_message("현재 재생 중인 곡이 없습니다.", ephemeral=True)
        return

    try:
        title = interaction.client.current_track.title
        url = interaction.client.current_track.data.get('webpage_url', 'https://www.youtube.com')
        duration = interaction.client.current_track.data.get('duration', 0)
        minutes_total, seconds_total = divmod(duration, 60)

        if interaction.client.current_track_start_time:
            elapsed_time_seconds = int(time.time() - interaction.client.current_track_start_time)
        else:
            elapsed_time_seconds = 0

        minutes_current, seconds_current = divmod(elapsed_time_seconds, 60)

        embed = discord.Embed(
            title="🎵 현재 재생 중인 곡",
            description=f"[{title}]({url})",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="⏱️ 재생 시간",
            value=f"{minutes_current:02}:{seconds_current:02} / {minutes_total:02}:{seconds_total:02}",
            inline=False
        )
        embed.add_field(
            name="📂 대기열",
            value=f"{len(interaction.client.music_queue)}곡 남음" if interaction.client.music_queue else "대기열이 비어 있습니다.",
            inline=False
        )
        embed.set_thumbnail(url="https://img.youtube.com/vi/{}/hqdefault.jpg".format(interaction.client.current_track.data.get('id', '')))
        embed.set_footer(text="음악 분위기를 즐겨보세요! 🎶")

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(f"현재 곡 정보를 가져오는 중 오류가 발생했습니다: {e}", ephemeral=True)

# /이동 - 대기열에서 특정 곡을 이동합니다.
@commands.command(name="이동", description="대기열에서 특정 곡의 순서를 변경합니다.")
async def move_in_queue(ctx, 바꾸실곡순서: int, 원하시는순서: int):
    if 바꾸실곡순서 < 1 or 바꾸실곡순서 > len(ctx.bot.music_queue) or 원하시는순서 < 1 or 원하시는순서 > len(ctx.bot.music_queue):
        await ctx.send("유효한 순서 번호를 입력해주세요.")
        return

    track = ctx.bot.music_queue[바꾸실곡순서 - 1]
    del ctx.bot.music_queue[바꾸실곡순서 - 1]
    ctx.bot.music_queue.insert(원하시는순서 - 1, track)

    embed = discord.Embed(
        title="곡 순서 변경됨",
        description=f"[{track.title}]({track.data.get('webpage_url', 'https://www.youtube.com')})의 순서를 {바꾸실곡순서}번에서 {원하시는순서}번으로 변경했습니다.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

# 슬래시 명령어 정의
async def move_in_queue_slash(interaction: discord.Interaction, 바꾸실곡순서: int, 원하시는순서: int):
    if 바꾸실곡순서 < 1 or 바꾸실곡순서 > len(interaction.client.music_queue) or 원하시는순서 < 1 or 원하시는순서 > len(interaction.client.music_queue):
        await interaction.response.send_message("유효한 순서 번호를 입력해주세요.", ephemeral=True)
        return

    track = interaction.client.music_queue[바꾸실곡순서 - 1]
    del interaction.client.music_queue[바꾸실곡순서 - 1]
    interaction.client.music_queue.insert(원하시는순서 - 1, track)

    embed = discord.Embed(
        title="곡 순서 변경됨",
        description=f"[{track.title}]({track.data.get('webpage_url', 'https://www.youtube.com')})의 순서를 {바꾸실곡순서}번에서 {원하시는순서}번으로 변경했습니다.",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

# /대기열초기화 - 대기열을 초기화합니다.
@commands.command(name="대기열초기화", description="대기열을 초기화합니다.")
async def clear_queue(ctx):
    ctx.bot.music_queue.clear()
    embed = discord.Embed(
        title="대기열 초기화됨",
        description="대기열이 초기화되었습니다.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

# 슬래시 명령어 정의
async def clear_queue_slash(interaction: discord.Interaction):
    interaction.client.music_queue.clear()
    embed = discord.Embed(
        title="대기열 초기화됨",
        description="대기열이 초기화되었습니다.",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)

# /대기열 - 현재 대기열 표시
@commands.command(name="대기열", description="현재 대기열을 표시합니다.")
async def show_queue(ctx):
    guild_id = ctx.guild.id
    queue = global_config.get_guild_queue(guild_id)
    
    if not queue:
        embed = discord.Embed(
            title="대기열",
            description="대기열이 비어 있습니다.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        return

    queue_list = []
    for i, track in enumerate(queue, 1):
        queue_list.append(f"{i}. [{track.title}]({track.data.get('webpage_url', 'https://www.youtube.com')})")

    embed = discord.Embed(
        title="🎵 대기열",
        description="\n".join(queue_list),
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"총 {len(queue)}곡")
    await ctx.send(embed=embed)

# 슬래시 명령어 정의
async def show_queue_slash(interaction: discord.Interaction):
    if not interaction.client.music_queue:
        embed = discord.Embed(
            title="대기열",
            description="대기열이 비어 있습니다.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
        return

    queue_list = []
    for i, track in enumerate(interaction.client.music_queue, 1):
        queue_list.append(f"{i}. [{track.title}]({track.data.get('webpage_url', 'https://www.youtube.com')})")

    embed = discord.Embed(
        title="🎵 대기열",
        description="\n".join(queue_list),
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"총 {len(interaction.client.music_queue)}곡")
    await interaction.response.send_message(embed=embed)

logger = logging.getLogger(__name__)

class QueueManager:
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="queue_worker")
        self._cache = {}
        self._lock = asyncio.Lock()

    async def add_track(self, guild_id: int, track: Track):
        """트랙을 대기열에 안전하게 추가"""
        async with self._lock:
            state = await global_config.get_guild_state(guild_id)
            state.music_queue.append(track)

    async def remove_track(self, guild_id: int, index: int) -> Optional[Track]:
        """대기열에서 트랙을 안전하게 제거"""
        async with self._lock:
            state = await global_config.get_guild_state(guild_id)
            if 0 <= index < len(state.music_queue):
                return state.music_queue.pop(index)
            return None

    async def clear_queue(self, guild_id: int):
        """대기열을 안전하게 초기화"""
        async with self._lock:
            state = await global_config.get_guild_state(guild_id)
            state.music_queue.clear()

    def __del__(self):
        """리소스 정리"""
        self._executor.shutdown(wait=True)

# setup 함수 정의
async def setup(bot):
    bot.add_command(now_playing)
    bot.add_command(move_in_queue)
    bot.add_command(clear_queue)
    bot.add_command(show_queue)
    
    @bot.tree.command(name="현재곡", description="현재 재생 중인 곡의 정보를 표시합니다.")
    async def now_playing_slash_command(interaction: discord.Interaction):
        await now_playing_slash(interaction)
    
    @bot.tree.command(name="이동", description="대기열에서 특정 곡의 순서를 변경합니다.")
    async def move_slash_command(interaction: discord.Interaction, 바꾸실곡순서: int, 원하시는순서: int):
        await move_in_queue_slash(interaction, 바꾸실곡순서, 원하시는순서)
    
    @bot.tree.command(name="대기열초기화", description="대기열을 초기화합니다.")
    async def clear_queue_slash_command(interaction: discord.Interaction):
        await clear_queue_slash(interaction)
    
    @bot.tree.command(name="대기열", description="현재 대기열을 표시합니다.")
    async def queue_slash_command(interaction: discord.Interaction):
        await show_queue_slash(interaction)
