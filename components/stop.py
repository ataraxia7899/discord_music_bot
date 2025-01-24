import discord
from discord.ext import commands

# /정지 명령어 컴포넌트

# /정지 - 현재 음악 정지하기 및 봇 퇴장하기
@commands.command(name="정지", description="현재 재생 중인 음악을 멈추고 봇을 퇴장시킵니다.")
async def stop(ctx):
    """
    현재 재생 중인 음악을 멈추고 봇을 퇴장시킵니다.
    """
    voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)

    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        voice_client.stop()
        await voice_client.disconnect()
        embed = discord.Embed(
            title="정지",
            description="음악을 멈추고 봇이 퇴장했습니다.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="오류",
            description="봇이 음성 채널에 있지 않거나 재생 중인 음악이 없습니다.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# 슬래시 명령어 정의
async def stop_slash(interaction: discord.Interaction):
    """
    현재 재생 중인 음악을 멈추고 봇을 퇴장시킵니다.
    """
    voice_client = discord.utils.get(interaction.client.voice_clients, guild=interaction.guild)

    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        voice_client.stop()
        await voice_client.disconnect()
        embed = discord.Embed(
            title="정지",
            description="음악을 멈추고 봇이 퇴장했습니다.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(
            title="오류",
            description="봇이 음성 채널에 있지 않거나 재생 중인 음악이 없습니다.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
