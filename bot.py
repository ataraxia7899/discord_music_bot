import discord
from discord.ext import commands
import os
from config import settings
import asyncio
import logging
from music_components import get_music_manager, get_queue_manager, MusicPlayer

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=settings.default_prefix, intents=intents, help_command=None)

    async def on_message(self, message):
        """메시지 이벤트를 처리하지 않음으로써 접두사 명령어 비활성화"""
        pass

        
    async def setup_hook(self):
        """봇 시작시 초기 설정을 담당"""
        logger.info("Starting bot setup...")
        
        # 컴포넌트 초기화
        self.music_manager = get_music_manager(self)
        self.audio_player = MusicPlayer(self)
        self.queue_manager = get_queue_manager(self)
        
        # 컴포넌트 로딩
        for filename in os.listdir("./music_components"):
            if filename.endswith(".py") and not filename.startswith("__"):
                try:
                    await self.load_extension(f"music_components.{filename[:-3]}")
                    logger.info(f"Loaded extension: {filename}")
                except Exception as e:
                    logger.error(f"Failed to load extension {filename}: {e}")
        
        # 음성 채널 상태 체크를 위한 이벤트 리스너 추가
        self.add_listener(self.on_voice_state_update)
        self.add_listener(self.on_voice_state_update_bot)
        
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
            
            if channel_members == 0:
                # 잠시 대기 후 다시 확인
                await asyncio.sleep(10)
                
                # 대기 후 다시 확인
                channel_members = len([m for m in voice_client.channel.members if not m.bot])
                if channel_members == 0:
                    if voice_client.is_playing():
                        voice_client.stop()
                    await voice_client.disconnect()
                    
                    # 메시지 전송 및 상태 초기화
                    text_channel = member.guild.text_channels[0]
                    await text_channel.send("👋 음성 채널에 아무도 없어서 나갔습니다.")
                    state = self.music_manager.get_server_state(guild_id)
                    await state.clear_queue()

    async def on_voice_state_update_bot(self, member, before, after):
        """봇의 음성 상태 변경을 모니터링"""
        if member.id == self.user.id:
            logger.info(f"봇 음성 상태 변경: {before.channel} -> {after.channel}")
            if after.channel is None:
                logger.info("봇이 음성 채널에서 나감")
            else:
                logger.info(f"봇이 음성 채널에 입장: {after.channel.name}")

def main():
    """봇을 실행하는 메인 함수"""
    bot = MusicBot()
    
    @bot.event
    async def on_ready():
        logger.info(f'Bot is ready: {bot.user.name} (ID: {bot.user.id})')
        try:
            await bot.tree.sync()
            logger.info("Global commands synchronized successfully")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    bot.run(settings.bot_token)

if __name__ == "__main__":
    main()
