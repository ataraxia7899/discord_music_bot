import discord
from discord.ext import commands
import random

# /셔플 명령어 컴포넌트

# /셔플 - 대기열에 있는 노래들을 무작위로 섞습니다.
@commands.command(name="셔플", description="대기열에 있는 노래들을 무작위로 섞습니다.")
async def shuffle_queue(ctx):
    """
    대기열을 셔플하는 명령어.
    """
    if not ctx.bot.music_queue:
        await ctx.send("대기열이 비어 있습니다.")
        return

    # 대기열 셔플
    random.shuffle(ctx.bot.music_queue)

    # 셔플된 대기열 출력
    shuffled_list = "\n".join([f"{i + 1}. {track.title}" for i, track in enumerate(ctx.bot.music_queue)])
    await ctx.send(f"🎶 대기열이 셔플되었습니다:\n{shuffled_list}")

# 슬래시 명령어 정의
async def shuffle_queue_slash(interaction: discord.Interaction):
    """
    대기열을 셔플하는 명령어.
    """
    if not interaction.client.music_queue:
        await interaction.response.send_message("대기열이 비어 있습니다.", ephemeral=True)
        return

    # 대기열 셔플
    random.shuffle(interaction.client.music_queue)

    # 셔플된 대기열 출력
    shuffled_list = "\n".join([f"{i + 1}. {track.title}" for i, track in enumerate(interaction.client.music_queue)])
    await interaction.response.send_message(f"🎶 대기열이 셔플되었습니다:\n{shuffled_list}")
