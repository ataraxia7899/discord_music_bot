import discord
from discord.ext import commands
import os
from config import BOT_TOKEN, DEFAULT_PREFIX
from core import music_bot
import asyncio

"""
디스코드 봇의 메인 클래스와 실행 로직
봇의 초기화, 이벤트 핸들링, 명령어 등록을 담당합니다.
"""

class MusicBot(commands.Bot):
    """
    음악 봇의 주요 클래스
    
    Attributes:
        music_core: 음악 관련 핵심 기능 인스턴스
        music_queue: 재생 대기열
        current_track: 현재 재생 중인 트랙
        repeat_mode: 반복 재생 모드
    """
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=DEFAULT_PREFIX, intents=intents)
        self.music_core = music_bot
        self.music_queue = music_bot.music_queue
        self.current_track = music_bot.current_track
        self.current_track_start_time = music_bot.current_track_start_time
        self.repeat_mode = music_bot.repeat_mode
        self.auto_play_enabled = music_bot.auto_play_enabled
        
    async def setup_hook(self):
        """
        봇 시작시 초기 설정을 담당
        - 컴포넌트 로드
        - 이벤트 리스너 등록
        - 전역 명령어 등록
        """
        print("Starting bot setup...")
        
        # 컴포넌트 로딩 (수정된 부분)
        for filename in os.listdir("./music_components"):
            if filename.endswith(".py") and not filename.startswith("__"):
                try:
                    await self.load_extension(f"music_components.{filename[:-3]}")
                    print(f"Loaded extension: {filename}")
                except Exception as e:
                    print(f"Failed to load extension {filename}: {e}")
        
        # 전역 명령어 등록 (sync 제거)
        print("Registering global commands...")
        
        # 음성 채널 상태 체크를 위한 이벤트 리스너 추가
        self.add_listener(self.on_voice_state_update)
        
    async def on_voice_state_update(self, member, before, after):
        """음성 채널 상태가 변경될 때 호출되는 이벤트 핸들러"""
        if member.id == self.user.id:  # 봇 자신의 상태 변경은 무시
            return
            
        voice_client = member.guild.voice_client
        if voice_client and voice_client.channel:
            # 봇이 음성 채널에 연결되어 있는 경우
            
            # 봇이 있는 채널의 멤버 수 계산 (봇 제외)
            channel_members = len([m for m in voice_client.channel.members if not m.bot])
            
            if channel_members == 0:  # 봇을 제외하고 아무도 없는 경우
                # 잠시 대기 후 다시 확인 (즉시 나가는 것 방지)
                await asyncio.sleep(10)
                
                # 대기 후 다시 확인
                channel_members = len([m for m in voice_client.channel.members if not m.bot])
                if channel_members == 0:
                    if voice_client.is_playing():
                        voice_client.stop()
                    await voice_client.disconnect()
                    
                    # 알림 메시지 전송
                    text_channel = member.guild.text_channels[0]  # 첫 번째 텍스트 채널에 알림
                    await text_channel.send("👋 음성 채널에 아무도 없어서 나갔습니다.")

def main():
    bot = MusicBot()
    
    @bot.event
    async def on_ready():
        print(f'{bot.user} 봇이 실행되었습니다.')
        print(f'Logged in as: {bot.user.name}')
        print(f'Bot ID: {bot.user.id}')
        print('------')
        
        # 봇이 시작될 때 한 번만 명령어 동기화
        try:
            await bot.tree.sync()
            print("Global commands synchronized successfully")
        except Exception as e:
            print(f"Failed to sync commands: {e}")
    
    bot.run(BOT_TOKEN)

if __name__ == "__main__":
    main()
