import discord
from discord.ext import commands
import os
from config import BOT_TOKEN, DEFAULT_PREFIX
from core import music_bot

class MusicBot(commands.Bot):
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
        print("Starting bot setup...")
        
        # 컴포넌트 로딩
        for filename in os.listdir("./components"):
            if filename.endswith(".py") and not filename.startswith("__"):
                try:
                    await self.load_extension(f"components.{filename[:-3]}")
                    print(f"Loaded extension: {filename}")
                except Exception as e:
                    print(f"Failed to load extension {filename}: {e}")
        
        # 전역 명령어 등록 (sync 제거)
        print("Registering global commands...")

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
