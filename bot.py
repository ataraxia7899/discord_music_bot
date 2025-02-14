import discord
from discord.ext import commands
import os
from config import BOT_TOKEN, DEFAULT_PREFIX, global_config, GuildState
import asyncio
from music_components.play_commands import YTDLSource
from collections import deque

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
        self.music_states = {}  # 서버별 상태 관리
        self.music_queue = deque()  # 기본 대기열 추가
        self.current_track = None   # 현재 트랙 추가
        self.repeat_mode = "none"   # 반복 모드 추가
        
    async def setup_hook(self):
        """
        봇 시작시 초기 설정을 담당
        - 컴포넌트 로드
        - 이벤트 리스너 등록
        - 전역 명령어 등록
        """
        print("Starting bot setup...")
        
        # 컴포넌트 로딩
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
            
        guild_id = member.guild.id
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
                    global_config.clear_guild_state(guild_id)
                    
                    # 알림 메시지 전송
                    text_channel = member.guild.text_channels[0]  # 첫 번째 텍스트 채널에 알림
                    await text_channel.send("👋 음성 채널에 아무도 없어서 나갔습니다.")

    async def get_guild_state(self, guild_id: int) -> GuildState:
        """서버별 상태를 가져오거나 생성"""
        if guild_id not in self.music_states:
            self.music_states[guild_id] = GuildState()
        return self.music_states[guild_id]

    @commands.command(name='재생')
    async def play(self, ctx, *, query: str):
        guild_state = await self.get_guild_state(ctx.guild.id)
        
        # 트랙 추가
        track = await self.get_track(query)
        guild_state.music_queue.append(track)  # GuildState의 music_queue 사용
        
        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    async def play_next(self, ctx):
        guild_state = await global_config.get_guild_state(ctx.guild.id)
        
        if not guild_state.music_queue:
            return
        
        track = guild_state.music_queue.popleft()
        # 재생 로직...

    @commands.command(name='큐')
    async def queue(self, ctx):
        guild_state = await global_config.get_guild_state(ctx.guild.id)
        
        if not guild_state.music_queue:
            await ctx.send("재생 대기열이 비어있습니다.")
            return
        
        # 큐 표시 로직...

    @commands.command(name='나가기')
    async def leave(self, ctx):
        guild_state = await global_config.get_guild_state(ctx.guild.id)
        guild_state.music_queue.clear()
        guild_state.current_track = None
        await ctx.voice_client.disconnect()

    @play.error
    async def play_error(self, ctx, error):
        if isinstance(error, AttributeError):
            await ctx.send("음악 재생 중 오류가 발생했습니다. 봇의 상태를 초기화합니다.")
            await global_config.clear_guild_state(ctx.guild.id)

    async def get_track(self, query: str):
        return await YTDLSource.from_query(query, loop=self.loop)

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
