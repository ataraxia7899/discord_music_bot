import discord
from discord.ext import commands
import time

# /현재곡 명령어 컴포넌트

# /현재곡 - 현재 재생 중인 곡 정보 표시
@commands.command(name="현재곡", description="현재 재생 중인 곡의 정보를 표시합니다.")
async def now_playing(ctx):
    """
    현재 재생 중인 곡의 정보를 Discord Embed 메시지로 표시합니다.
    """
    if not ctx.bot.current_track:
        await ctx.send("현재 재생 중인 곡이 없습니다.")
        return

    try:
        # 현재 곡 정보 가져오기
        title = ctx.bot.current_track.title
        url = ctx.bot.current_track.data.get('webpage_url', 'https://www.youtube.com')
        duration = ctx.bot.current_track.data.get('duration', 0)  # 전체 길이 (초 단위)
        minutes_total, seconds_total = divmod(duration, 60)

        # 현재 재생 시간 계산
        if ctx.bot.current_track_start_time:
            elapsed_time_seconds = int(time.time() - ctx.bot.current_track_start_time)  # 경과 시간 계산
        else:
            elapsed_time_seconds = 0

        minutes_current, seconds_current = divmod(elapsed_time_seconds, 60)

        # Embed 메시지 생성
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

        # 메시지 전송
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"현재 곡 정보를 가져오는 중 오류가 발생했습니다: {e}")

# 슬래시 명령어 정의
async def now_playing_slash(interaction: discord.Interaction):
    """
    현재 재생 중인 곡의 정보를 Discord Embed 메시지로 표시합니다.
    """
    if not interaction.client.current_track:
        await interaction.response.send_message("현재 재생 중인 곡이 없습니다.", ephemeral=True)
        return

    try:
        # 현재 곡 정보 가져오기
        title = interaction.client.current_track.title
        url = interaction.client.current_track.data.get('webpage_url', 'https://www.youtube.com')
        duration = interaction.client.current_track.data.get('duration', 0)  # 전체 길이 (초 단위)
        minutes_total, seconds_total = divmod(duration, 60)

        # 현재 재생 시간 계산
        if interaction.client.current_track_start_time:
            elapsed_time_seconds = int(time.time() - interaction.client.current_track_start_time)  # 경과 시간 계산
        else:
            elapsed_time_seconds = 0

        minutes_current, seconds_current = divmod(elapsed_time_seconds, 60)

        # Embed 메시지 생성
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

        # 메시지 전송
        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(f"현재 곡 정보를 가져오는 중 오류가 발생했습니다: {e}", ephemeral=True)
