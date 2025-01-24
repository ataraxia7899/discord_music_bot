import discord
from discord.ext import commands

# /이동 명령어 컴포넌트

# /이동 - 대기열에서 특정 곡을 이동합니다.
@commands.command(name="이동", description="대기열에서 특정 곡을 이동합니다.")
async def move_in_queue(ctx, from_index: int, to_index: int):
    """
    대기열에서 특정 곡을 이동하는 명령어.
    """
    if from_index < 1 or from_index > len(ctx.bot.music_queue) or to_index < 1 or to_index > len(ctx.bot.music_queue):
        await ctx.send("유효한 인덱스를 입력하세요.")
        return

    track = ctx.bot.music_queue[from_index - 1]
    del ctx.bot.music_queue[from_index - 1]
    ctx.bot.music_queue.insert(to_index - 1, track)

    embed = discord.Embed(
        title="곡 이동됨",
        description=f"[{track.title}]({track.data.get('webpage_url', 'https://www.youtube.com')})가 대기열에서 이동되었습니다.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

# 슬래시 명령어 정의
async def move_in_queue_slash(interaction: discord.Interaction, from_index: int, to_index: int):
    """
    대기열에서 특정 곡을 이동하는 명령어.
    """
    if from_index < 1 or from_index > len(interaction.client.music_queue) or to_index < 1 or to_index > len(interaction.client.music_queue):
        await interaction.response.send_message("유효한 인덱스를 입력하세요.", ephemeral=True)
        return

    track = interaction.client.music_queue[from_index - 1]
    del interaction.client.music_queue[from_index - 1]
    interaction.client.music_queue.insert(to_index - 1, track)

    embed = discord.Embed(
        title="곡 이동됨",
        description=f"[{track.title}]({track.data.get('webpage_url', 'https://www.youtube.com')})가 대기열에서 이동되었습니다.",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)
