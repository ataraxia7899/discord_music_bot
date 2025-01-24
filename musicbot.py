import discord  # 디스코드 API 모듈
from discord.ext import commands  # 확장 모듈
from discord import app_commands  # 슬래시 명령어 모듈
import asyncio  # 비동기 처리 모듈
import re  # URL 검증 및 정리를 위한 정규식 모듈
from urllib.parse import urlparse, parse_qs  # URL 파싱을 위한 모듈
from collections import deque  # 대기열 및 이전 곡 관리를 위한 deque 사용
import os
import time  # 시간 추적을 위한 모듈 추가
from secret import token  # 디스코드 봇 토큰 가져오기

# 클라우드에서 환경변수로 토큰을 지정해서 사용하기 위한 코드
# import os
# token = os.getenv("DISCORD_BOT_TOKEN")

# 디스코드 봇 객체 생성
intents = discord.Intents.default()
intents.message_content = True  # 메시지 읽기 권한 활성화
bot = commands.Bot(command_prefix="!", intents=intents)

# 대기열 및 현재 재생 중인 곡 관리
bot.music_queue = deque()  # 대기열 저장소
bot.current_track = None  # 현재 재생 중인 곡 정보
bot.current_track_start_time = None  # 현재 곡 시작 시간 (초 단위)
bot.auto_play_enabled = False  # 자동재생 기능 상태
bot.repeat_mode = "none"  # 반복 모드 상태 (none, current, queue)

# 봇 준비 이벤트 처리 및 슬래시 명령어 동기화
@bot.event
async def on_ready():
    """
    봇이 준비되었을 때 호출되는 이벤트 핸들러.
    """
    print(f'봇이 로그인되었습니다: {bot.user}')
    
    try:
        synced = await bot.tree.sync()  # 슬래시 명령어 동기화 시도
        print(f"동기화된 슬래시 명령어: {len(synced)}개")  
        
        commands = [command.name for command in bot.tree.get_commands()]
        print(f"등록된 슬래시 명령어 목록: {commands}")
    
    except Exception as e:
        print(f"명령어 동기화 중 오류 발생: {e}")

# 컴포넌트 명령어 불러오기
from components.play import play_slash
from components.skip import skip_to_next_slash
from components.stop import stop_slash
from components.now_playing import now_playing_slash
from components.shuffle import shuffle_queue_slash
from components.toggle_repeat import toggle_repeat_slash
from components.remove_from_queue import remove_from_queue_slash
from components.move_in_queue import move_in_queue_slash
from components.clear_queue import clear_queue_slash

# 슬래시 명령어 등록
@bot.tree.command(name="재생", description="유튜브 URL 또는 검색어를 통해 음악을 재생합니다.")
async def play_command(interaction: discord.Interaction, query: str):
    await play_slash(interaction, query)

@bot.tree.command(name="다음곡", description="대기열의 다음 곡을 재생합니다.")
async def skip_to_next_command(interaction: discord.Interaction):
    await skip_to_next_slash(interaction)

@bot.tree.command(name="정지", description="현재 재생 중인 음악을 멈추고 봇을 퇴장시킵니다.")
async def stop_command(interaction: discord.Interaction):
    await stop_slash(interaction)

@bot.tree.command(name="현재곡", description="현재 재생 중인 곡의 정보를 표시합니다.")
async def now_playing_command(interaction: discord.Interaction):
    await now_playing_slash(interaction)

@bot.tree.command(name="셔플", description="대기열에 있는 노래들을 무작위로 섞습니다.")
async def shuffle_queue_command(interaction: discord.Interaction):
    await shuffle_queue_slash(interaction)

@bot.tree.command(name="반복", description="현재 곡 반복, 대기열 반복, 반복 없음 상태를 순환합니다.")
async def toggle_repeat_command(interaction: discord.Interaction):
    await toggle_repeat_slash(interaction)

@bot.tree.command(name="삭제", description="대기열에서 특정 곡을 삭제합니다.")
async def remove_from_queue_command(interaction: discord.Interaction, index: int):
    await remove_from_queue_slash(interaction, index)

@bot.tree.command(name="이동", description="대기열에서 특정 곡을 이동합니다.")
async def move_in_queue_command(interaction: discord.Interaction, from_index: int, to_index: int):
    await move_in_queue_slash(interaction, from_index, to_index)

@bot.tree.command(name="대기열초기화", description="대기열을 초기화합니다.")
async def clear_queue_command(interaction: discord.Interaction):
    await clear_queue_slash(interaction)

# 유튜브 URL 검증 함수 정의 (다양한 형식 지원)
def is_valid_youtube_url(url):
    """
    유튜브 URL이 유효한지 확인하는 함수.
    다양한 유튜브 URL 형식을 지원합니다.
    """
    youtube_regex = (
        r"^(https?:\/\/)?"  # http 또는 https 프로토콜 (선택적)
        r"(www\.)?"  # www. (선택적)
        r"(youtube\.com|youtu\.be)\/"  # youtube.com 또는 youtu.be
        r"((watch\?v=|embed\/|shorts\/|v\/|playlist\?list=)?([a-zA-Z0-9_-]+))"  # 다양한 형식의 경로
        r"(\?[a-zA-Z0-9_=&-]*)?$"  # 추가적인 쿼리 매개변수 (선택적)
    )
    return re.match(youtube_regex, url) is not None

# 유튜브 URL 정리 함수 정의 (추가 매개변수 제거)
def clean_youtube_url(url):
    """
    유튜브 URL에서 불필요한 매개변수를 제거하고 순수한 동영상 또는 플레이리스트 ID를 추출합니다.
    """
    parsed_url = urlparse(url)

    # youtu.be 형식 (공유 URL)
    if "youtu.be" in parsed_url.netloc:
        video_id = parsed_url.path.lstrip("/")  # 동영상 ID 추출
        return f"https://www.youtube.com/watch?v={video_id}"

    # youtube.com 형식 (긴 URL)
    elif "youtube.com" in parsed_url.netloc:
        query_params = parse_qs(parsed_url.query)  # 쿼리 매개변수 파싱

        # 플레이리스트 URL 처리
        if "list" in query_params:
            playlist_id = query_params.get("list", [None])[0]  # "list" 매개변수에서 플레이리스트 ID 추출
            if "v" in query_params:  # 동영상 ID와 함께 제공된 경우
                video_id = query_params.get("v", [None])[0]
                return f"https://www.youtube.com/watch?v={video_id}&list={playlist_id}"
            return f"https://www.youtube.com/playlist?list={playlist_id}"

        # 단일 동영상 URL 처리
        elif "v" in query_params:
            video_id = query_params.get("v", [None])[0]
            return f"https://www.youtube.com/watch?v={video_id}"

        # shorts URL 처리
        elif "shorts" in parsed_url.path:
            video_id = parsed_url.path.split("/")[2]
            return f"https://www.youtube.com/watch?v={video_id}"

        # index 매개변수 제거
        if "index" in query_params:
            del query_params["index"]
            cleaned_query = "&".join([f"{key}={value[0]}" for key, value in query_params.items()])
            return f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{cleaned_query}"

    raise ValueError("유효한 YouTube URL이 아닙니다.")

# 음성 채널의 상태를 모니터링하여, 유저가 모두 떠났을 때 봇이 자동으로 음성 채널에서 나가도록 함함
@bot.event
async def on_voice_state_update(member, before, after):
    """
    음성 채널의 상태가 변경될 때 호출되는 이벤트.
    """
    # 봇이 음성 채널에 연결되어 있는지 확인
    voice_client = discord.utils.get(bot.voice_clients, guild=member.guild)
    if not voice_client:
        return

    # 봇이 연결된 음성 채널에 남아 있는 멤버 확인
    if before.channel == voice_client.channel and after.channel != voice_client.channel:
        # 해당 음성 채널에 남아 있는 멤버 수 확인
        remaining_members = [
            m for m in voice_client.channel.members if not m.bot
        ]  # 봇을 제외한 멤버만 계산

        if len(remaining_members) == 0:
            # 멤버가 아무도 남아 있지 않으면 음성 채널 떠남
            await voice_client.disconnect()
            print("음성 채널에 유저가 없어 봇이 나갔습니다.")

# 토큰으로 봇 실행 시작
bot.run(token)