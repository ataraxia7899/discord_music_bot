import discord
from discord.ext import commands

# /삭제 명령어 컴포넌트

# /삭제 - 대기열에서 특정 곡을 삭제합니다.
@commands.command(name="삭제", description="대기열에서 특정 곡을 삭제합니다.")
async def remove_from_queue(ctx, index: int):
    """
    대기열에서 특정 곡을 삭제하는 명령어.
    """
    if index < 1 or index > len(ctx.bot.music_queue):
        await ctx.send("유효한 인덱스를 입력하세요.")
        return

    removed_track = ctx.bot.music_queue[index - 1]
    del ctx.bot.music_queue[index - 1]

    embed = discord.Embed(
        title="곡 삭제됨",
        description=f"[{removed_track.title}]({removed_track.data.get('webpage_url', 'https://www.youtube.com')})가 대기열에서 삭제되었습니다.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

# 슬래시 명령어 정의
async def remove_from_queue_slash(interaction: discord.Interaction, index: int):
    """
    대기열에서 특정 곡을 삭제하는 명령어.
    """
    if index < 1 or index > len(interaction.client.music_queue):
        await interaction.response.send_message("유효한 인덱스를 입력하세요.", ephemeral=True)
        return

    removed_track = interaction.client.music_queue[index - 1]
    del interaction.client.music_queue[index - 1]

    embed = discord.Embed(
        title="곡 삭제됨",
        description=f"[{removed_track.title}]({removed_track.data.get('webpage_url', 'https://www.youtube.com')})가 대기열에서 삭제되었습니다.",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)
