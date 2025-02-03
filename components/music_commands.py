import discord
from discord.ext import commands
import asyncio
import time
import random
import sys
import os
from discord.ui import Modal, TextInput, View, Button

# 상위 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ffmpeg_options
from components.play_commands import YTDLSource, play_next_song

# /다음곡 - 대기열의 다음 곡 재생하기
@commands.command(name="다음곡", description="대기열의 다음 곡을 재생합니다.")
async def skip_to_next(ctx):
    # 수정된 부분: voice_client 가져오기
    voice_client = ctx.guild.voice_client

    if not voice_client:
        embed = discord.Embed(
            title="오류",
            description="봇이 음성 채널에 연결되어 있지 않습니다.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    if not ctx.bot.music_queue and not ctx.bot.auto_play_enabled:
        embed = discord.Embed(
            title="알림",
            description="현재 곡이 마지막 곡입니다.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        return

    if voice_client.is_playing():
        voice_client.stop()
        voice_client.cleanup()

    await play_next_song(voice_client, ctx.bot)

    embed = discord.Embed(
        title="다음 곡 재생 중",
        description=f"[{ctx.bot.current_track.title}]({ctx.bot.current_track.data.get('webpage_url', 'https://www.youtube.com')})",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# 슬래시 명령어 정의
async def skip_to_next_slash(interaction: discord.Interaction):
    # 수정된 부분: voice_client 가져오기
    voice_client = interaction.guild.voice_client

    if not voice_client:
        embed = discord.Embed(
            title="오류",
            description="봇이 음성 채널에 연결되어 있지 않습니다.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if not interaction.client.music_queue and not interaction.client.auto_play_enabled:
        embed = discord.Embed(
            title="알림",
            description="현재 곡이 마지막 곡입니다.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if voice_client.is_playing():
        voice_client.stop()
        voice_client.cleanup()

    await play_next_song(voice_client, interaction.client)

    embed = discord.Embed(
        title="다음 곡 재생 중",
        description=f"[{interaction.client.current_track.title}]({interaction.client.current_track.data.get('webpage_url', 'https://www.youtube.com')})",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

# /셔플 - 대기열에 있는 노래들을 무작위로 섞습니다.
@commands.command(name="셔플", description="대기열에 있는 노래들을 무작위로 섞습니다.")
async def shuffle_queue(ctx):
    if not ctx.bot.music_queue:
        embed = discord.Embed(
            title="대기열",
            description="대기열이 비어 있습니다.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        return

    # 대기열을 무작위로 섞습니다.
    random.shuffle(ctx.bot.music_queue)

    # 대기열 목록을 만듭니다.
    queue_list = []
    for i, track in enumerate(ctx.bot.music_queue, 1):
        queue_list.append(f"{i}. [{track.title}]({track.data.get('webpage_url', 'https://www.youtube.com')})")

    embed = discord.Embed(
        title="🎵 셔플된 대기열",
        description="\n".join(queue_list),
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"총 {len(ctx.bot.music_queue)}곡")
    await ctx.send(embed=embed)

# 슬래시 명령어 정의
async def shuffle_queue_slash(interaction: discord.Interaction):
    if not interaction.client.music_queue:
        embed = discord.Embed(
            title="대기열",
            description="대기열이 비어 있습니다.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
        return

    # 대기열을 무작위로 섞습니다.
    random.shuffle(interaction.client.music_queue)

    # 대기열 목록을 만듭니다.
    queue_list = []
    for i, track in enumerate(interaction.client.music_queue, 1):
        queue_list.append(f"{i}. [{track.title}]({track.data.get('webpage_url', 'https://www.youtube.com')})")

    embed = discord.Embed(
        title="🎵 셔플된 대기열",
        description="\n".join(queue_list),
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"총 {len(interaction.client.music_queue)}곡")
    await interaction.response.send_message(embed=embed)

# /삭제 - 대기열에서 특정 곡을 삭제합니다.
@commands.command(name="삭제", description="대기열에서 특정 곡을 삭제합니다.")
async def remove_from_queue(ctx, 삭제할곡순서: int):
    if 삭제할곡순서 < 1 or 삭제할곡순서 > len(ctx.bot.music_queue):
        await ctx.send("유효한 곡 순서를 입력해주세요.")
        return

    removed_track = ctx.bot.music_queue[삭제할곡순서 - 1]
    del ctx.bot.music_queue[삭제할곡순서 - 1]

    embed = discord.Embed(
        title="곡 삭제됨",
        description=f"대기열에서 {삭제할곡순서}번 [{removed_track.title}]({removed_track.data.get('webpage_url', 'https://www.youtube.com')})이(가) 삭제되었습니다.",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

# 슬래시 명령어 정의
async def remove_from_queue_slash(interaction: discord.Interaction, 삭제할곡순서: int):
    if 삭제할곡순서 < 1 or 삭제할곡순서 > len(interaction.client.music_queue):
        await interaction.response.send_message("유효한 곡 순서를 입력해주세요.", ephemeral=True)
        return

    removed_track = interaction.client.music_queue[삭제할곡순서 - 1]
    del interaction.client.music_queue[삭제할곡순서 - 1]

    embed = discord.Embed(
        title="곡 삭제됨",
        description=f"대기열에서 {삭제할곡순서}번 [{removed_track.title}]({removed_track.data.get('webpage_url', 'https://www.youtube.com')})이(가) 삭제되었습니다.",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)

# /반복 - 대기열 반복, 현재 곡 반복, 반복 없음 상태를 순환합니다.
@commands.command(name="반복", description="대기열 반복, 현재 곡 반복, 반복 없음 상태를 순환합니다.")
async def toggle_repeat(ctx):
    # 반복 모드를 순환합니다.
    if ctx.bot.repeat_mode == "none":
        ctx.bot.repeat_mode = "queue"
        await ctx.send("🔂 대기열이 반복됩니다.")
    elif ctx.bot.repeat_mode == "queue":
        ctx.bot.repeat_mode = "current"
        await ctx.send("🔁 현재 곡이 반복됩니다.")
    elif ctx.bot.repeat_mode == "current":
        ctx.bot.repeat_mode = "none"
        await ctx.send("⏹️ 반복이 해제되었습니다.")

# 슬래시 명령어 정의
async def toggle_repeat_slash(interaction: discord.Interaction):
    # 반복 모드를 순환합니다.
    if interaction.client.repeat_mode == "none":
        interaction.client.repeat_mode = "queue"
        await interaction.response.send_message("🔂 대기열이 반복됩니다.")
    elif interaction.client.repeat_mode == "queue":
        interaction.client.repeat_mode = "current"
        await interaction.response.send_message("🔁 현재 곡이 반복됩니다.")
    elif interaction.client.repeat_mode == "current":
        interaction.client.repeat_mode = "none"
        await interaction.response.send_message("⏹️ 반복이 해제되었습니다.")

# # /추천노래 명령어 수정
# @commands.command(name="추천노래", description="추천 노래를 재생합니다.")  # 명령어 이름 변경
# async def play_recommended(ctx):
#     try:
#         voice_client = ctx.guild.voice_client

#         if not voice_client:
#             embed = discord.Embed(
#                 title="오류",
#                 description="봇이 음성 채널에 연결되어 있지 않습니다.",
#                 color=discord.Color.red()
#             )
#             await ctx.send(embed=embed)
#             return

#         # 이전 재생 중인 음악 정리
#         if voice_client.is_playing():
#             voice_client.stop()
#         voice_client.cleanup()

#         # 현재 곡의 장르를 기반으로 추천 노래를 검색합니다.
#         if ctx.bot.current_track:
#             genre = ctx.bot.current_track.data.get('genre', '')
#             recommended_query = f"{ctx.bot.current_track.title} {genre} 비슷한 노래"
#         else:
#             recommended_query = "추천 노래"

#         max_attempts = 5
#         attempts = 0

#         while attempts < max_attempts:
#             recommended_track = await YTDLSource.from_query(recommended_query, loop=ctx.bot.loop, stream=True)
            
#             if recommended_track.title != ctx.bot.current_track.title:
#                 ctx.bot.current_track = recommended_track
#                 break

#             attempts += 1

#         if attempts == max_attempts:
#             recommended_track = await YTDLSource.from_query("추천 노래", loop=ctx.bot.loop, stream=True)
#             ctx.bot.current_track = recommended_track

#         ctx.bot.current_track_start_time = time.time()

#         if voice_client.is_connected():
#             audio = await discord.FFmpegOpusAudio.from_probe(recommended_track.url, **ffmpeg_options)
#             voice_client.play(audio, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client, ctx.bot), ctx.bot.loop))
#             embed = discord.Embed(
#                 title="추천 노래 재생 중",
#                 description=f"[{recommended_track.title}]({recommended_track.data.get('webpage_url', 'https://www.youtube.com')})",
#                 color=discord.Color.green()
#             )
#             await ctx.send(embed=embed)
#         else:
#             await ctx.send("봇이 음성 채널에 연결되어 있지 않습니다.")
#     except Exception as e:
#         print(f"추천 노래 재생 중 오류 발생: {e}")
#         embed = discord.Embed(
#             title="오류 발생",
#             description=f"추천 노래를 재생하는 중 오류가 발생했습니다: {e}",
#             color=discord.Color.red()
#         )
#         await ctx.send(embed=embed)

# # 슬래시 명령어 수정
# async def play_recommended_slash(interaction: discord.Interaction):
#     # 응답 지연 처리 추가
#     await interaction.response.defer(thinking=True)
    
#     # 현재 음성 채널에 연결된 봇의 음성 클라이언트를 가져옵니다.
#     voice_client = interaction.guild.voice_client  # 수정된 부분

#     if not voice_client:  # 수정된 부분
#         embed = discord.Embed(
#             title="오류",
#             description="봇이 음성 채널에 연결되어 있지 않습니다.",
#             color=discord.Color.red()
#         )
#         await interaction.followup.send(embed=embed, ephemeral=True)
#         return

#     try:
#         # 현재 곡의 장르를 기반으로 추천 노래를 검색합니다.
#         if interaction.client.current_track:
#             genre = interaction.client.current_track.data.get('genre', '')
#             recommended_query = f"{interaction.client.current_track.title} {genre} 비슷한 노래"
#         else:
#             recommended_query = "추천 노래"

#         max_attempts = 5
#         attempts = 0

#         while attempts < max_attempts:
#             recommended_track = await YTDLSource.from_query(recommended_query, loop=interaction.client.loop, stream=True)
            
#             if recommended_track.title != interaction.client.current_track.title:
#                 interaction.client.current_track = recommended_track
#                 break

#             attempts += 1

#         if attempts == max_attempts:
#             recommended_track = await YTDLSource.from_query("추천 노래", loop=interaction.client.loop, stream=True)
#             interaction.client.current_track = recommended_track

#         interaction.client.current_track_start_time = time.time()

#         if voice_client.is_playing():
#             voice_client.stop()
#         await asyncio.sleep(1)
#         if voice_client.is_connected():
#             voice_client.cleanup()
#             voice_client.play(
#                 recommended_track.source,
#                 after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(voice_client, interaction.client), interaction.client.loop)
#             )
#         else:
#             print("봇이 음성 채널에 연결되어 있지 않습니다.")
#         embed = discord.Embed(
#             title="추천 노래 재생 중",
#             description=f"[{recommended_track.title}]({recommended_track.data.get('webpage_url', 'https://www.youtube.com')})",
#             color=discord.Color.green()
#         )
#         await interaction.followup.send(embed=embed)  # response.send_message 대신 followup.send 사용
#     except Exception as e:
#         embed = discord.Embed(
#             title="오류 발생",
#             description=f"추천 노래를 재생하는 중 오류가 발생했습니다: {e}",
#             color=discord.Color.red()
#         )
#         await interaction.followup.send(embed=embed, ephemeral=True)

# /정지 - 현재 음악 정지하기 및 봇 퇴장하기
@commands.command(name="정지", description="현재 재생 중인 음악을 멈추고 봇을 퇴장시킵니다.")
async def stop(ctx):
    voice_client = ctx.guild.voice_client

    if voice_client:
        try:
            # 응답 즉시 전송
            embed = discord.Embed(
                title="정지",
                description="음악을 멈추고 봇이 퇴장합니다...",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            
            # 정리 작업 수행
            if voice_client.is_playing():
                voice_client.stop()
            if hasattr(voice_client, 'cleanup'):
                voice_client.cleanup()
            await voice_client.disconnect()
            
        except Exception as e:
            print(f"음성 연결 종료 중 오류 발생: {e}")
            embed = discord.Embed(
                title="오류",
                description="음성 연결을 종료하는 중 오류가 발생했습니다.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="알림",
            description="봇이 음성 채널에 연결되어 있지 않습니다.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

# 슬래시 명령어 정의
async def stop_slash(interaction: discord.Interaction):
    # 응답 지연 처리 추가
    await interaction.response.defer()
    
    voice_client = interaction.guild.voice_client

    if voice_client:
        try:
            # 먼저 메시지 전송
            embed = discord.Embed(
                title="정지",
                description="음악을 멈추고 봇이 퇴장합니다...",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
            
            # 정리 작업 수행
            if voice_client.is_playing():
                voice_client.stop()
            if hasattr(voice_client, 'cleanup'):
                voice_client.cleanup()
            await voice_client.disconnect()
            
        except Exception as e:
            print(f"음성 연결 종료 중 오류 발생: {e}")
            embed = discord.Embed(
                title="오류",
                description="음성 연결을 종료하는 중 오류가 발생했습니다.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
    else:
        embed = discord.Embed(
            title="알림",
            description="봇이 음성 채널에 연결되어 있지 않습니다.",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

# setup 함수 정의
async def setup(bot):
    print("Setting up music commands...")
    
    # 기본 명령어 등록
    basic_commands = [
        skip_to_next,
        shuffle_queue,
        remove_from_queue,
        toggle_repeat,
        stop
    ]
    
    for command in basic_commands:
        bot.add_command(command)
    
    # 슬래시 명령어 등록 - 각각 개별적으로 등록
    @bot.tree.command(name="다음곡", description="대기열의 다음 곡을 재생합니다.")
    async def next_song(interaction: discord.Interaction):
        await skip_to_next_slash(interaction)

    @bot.tree.command(name="셔플", description="대기열에 있는 노래들을 무작위로 섞습니다.")
    async def shuffle(interaction: discord.Interaction):
        await shuffle_queue_slash(interaction)

    @bot.tree.command(name="삭제", description="대기열에서 특정 곡을 삭제합니다.")
    async def remove(interaction: discord.Interaction, 삭제할곡순서: int):
        await remove_from_queue_slash(interaction, 삭제할곡순서)

    @bot.tree.command(name="반복", description="대기열 반복, 현재 곡 반복, 반복 없음 상태를 순환합니다.")
    async def repeat(interaction: discord.Interaction):
        await toggle_repeat_slash(interaction)

    @bot.tree.command(name="정지", description="현재 재생 중인 음악을 정지합니다.")
    async def stop_cmd(interaction: discord.Interaction):
        await stop_slash(interaction)

    print("Music commands setup completed!")
