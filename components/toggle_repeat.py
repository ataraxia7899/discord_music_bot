import discord
from discord.ext import commands

# /반복 명령어 컴포넌트

# /반복 - 대기열 반복, 현재 곡 반복, 반복 없음 상태를 순환합니다.
@commands.command(name="반복", description="현재 곡 반복, 대기열 반복, 반복 없음 상태를 순환합니다.")
async def toggle_repeat(ctx):
    """
    현재 곡 반복, 대기열 반복, 반복 없음 상태를 순환하는 명령어.
    """
    if ctx.bot.repeat_mode == "none":
        ctx.bot.repeat_mode = "queue"  # 대기열 반복
        await ctx.send("🔂 대기열이 반복됩니다.")
    elif ctx.bot.repeat_mode == "queue":
        ctx.bot.repeat_mode = "current"  # 현재 곡 반복
        await ctx.send("🔁 현재 곡이 반복됩니다.")
    elif ctx.bot.repeat_mode == "current":
        ctx.bot.repeat_mode = "none"  # 반복 없음
        await ctx.send("⏹️ 반복이 해제되었습니다.")

# 슬래시 명령어 정의
async def toggle_repeat_slash(interaction: discord.Interaction):
    """
    현재 곡 반복, 대기열 반복, 반복 없음 상태를 순환하는 명령어.
    """
    if interaction.client.repeat_mode == "none":
        interaction.client.repeat_mode = "queue"  # 대기열 반복
        await interaction.response.send_message("🔂 대기열이 반복됩니다.")
    elif interaction.client.repeat_mode == "queue":
        interaction.client.repeat_mode = "current"  # 현재 곡 반복
        await interaction.response.send_message("🔁 현재 곡이 반복됩니다.")
    elif interaction.client.repeat_mode == "current":
        interaction.client.repeat_mode = "none"  # 반복 없음
        await interaction.response.send_message("⏹️ 반복이 해제되었습니다.")
