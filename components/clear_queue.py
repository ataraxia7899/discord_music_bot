import discord
from discord.ext import commands

# /대기열초기화 명령어 컴포넌트

# /대기열초기화 - 대기열을 초기화합니다.
@commands.command(name="대기열초기화", description="대기열을 초기화합니다.")
async def clear_queue(ctx):
    """
    대기열을 초기화하는 명령어.
    """
    ctx.bot.music_queue.clear()
    embed = discord.Embed(
        title="대기열 초기화됨",
        description="대기열이 초기화되었습니다.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

# 슬래시 명령어 정의
async def clear_queue_slash(interaction: discord.Interaction):
    """
    대기열을 초기화하는 명령어.
    """
    interaction.client.music_queue.clear()
    embed = discord.Embed(
        title="대기열 초기화됨",
        description="대기열이 초기화되었습니다.",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)
