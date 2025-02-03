import discord
from discord.ext import commands, tasks
import aiohttp
import datetime
import pytz
from discord import app_commands
from secret import YOUR_LOSTARK_API_KEY

class AdventureIsland(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.notified_today = False
        # 서버별 구독자 관리를 위한 딕셔너리
        # { guild_id: set(user_ids) }
        self.guild_subscribers = {}
        self.check_adventure_islands.start()

    @app_commands.command(
        name="골드섬알림등록", 
        description="특정 유저를 골드섬 DM 알림 대상자로 등록합니다"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def register_subscriber(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member
    ):
        guild_id = interaction.guild_id
        if guild_id not in self.guild_subscribers:
            self.guild_subscribers[guild_id] = set()
        
        self.guild_subscribers[guild_id].add(user.id)
        await interaction.response.send_message(
            f"{user.mention}님을 골드섬 알림 대상자로 등록했습니다.", 
            ephemeral=True
        )

    @app_commands.command(
        name="골드섬알림제거", 
        description="특정 유저를 골드섬 DM 알림 대상자에서 제거합니다"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_subscriber(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member
    ):
        guild_id = interaction.guild_id
        if guild_id in self.guild_subscribers:
            self.guild_subscribers[guild_id].discard(user.id)
            await interaction.response.send_message(
                f"{user.mention}님을 골드섬 알림 대상자에서 제거했습니다.", 
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "이 서버에는 알림 대상자가 없습니다.", 
                ephemeral=True
            )

    @app_commands.command(
        name="골드섬알림목록", 
        description="현재 서버의 골드섬 알림 대상자 목록을 표시합니다"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def list_subscribers(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if guild_id not in self.guild_subscribers or not self.guild_subscribers[guild_id]:
            await interaction.response.send_message(
                "현재 등록된 알림 대상자가 없습니다.", 
                ephemeral=True
            )
            return

        subscribers = []
        for user_id in self.guild_subscribers[guild_id]:
            user = interaction.guild.get_member(user_id)
            if user:
                subscribers.append(f"• {user.name} ({user.mention})")

        subscriber_list = "\n".join(subscribers)
        await interaction.response.send_message(
            f"**골드섬 알림 대상자 목록**\n{subscriber_list}", 
            ephemeral=True
        )

    async def fetch_adventure_islands(self):
        headers = {
            'accept': 'application/json',
            'authorization': f'bearer {YOUR_LOSTARK_API_KEY}'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get('https://developer-lostark.game.onstove.com/gamecontents/calendar', headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                return None

    @tasks.loop(hours=24)
    async def check_adventure_islands(self):
        # 한국 시간대로 설정
        kr_tz = pytz.timezone('Asia/Seoul')
        now = datetime.datetime.now(kr_tz)
        
        if self.notified_today:
            if now.hour == 0 and now.minute < 5:
                self.notified_today = False
            return

        data = await self.fetch_adventure_islands()
        if not data:
            return

        gold_islands = []
        for event in data:
            if event.get('ContentsType') == '모험 섬':
                rewards = event.get('Rewards', [])
                if any('골드' in reward.get('Name', '') for reward in rewards):
                    gold_islands.append(event.get('ContentsName', '알 수 없는 섬'))

        if gold_islands and not self.notified_today:
            dm_message = (
                f"🏝️ **오늘의 골드 모험섬 알림**\n"
                f"다음 섬에서 골드 보상을 획득할 수 있습니다:\n"
                f"```\n" + "\n".join(gold_islands) + "```"
            )
            
            # 각 서버의 구독자들에게 DM 발송
            for guild_id, subscribers in self.guild_subscribers.items():
                for user_id in subscribers:
                    try:
                        user = await self.bot.fetch_user(user_id)
                        await user.send(dm_message)
                    except Exception as e:
                        print(f"Error sending DM to user {user_id}: {e}")

            self.notified_today = True

    @check_adventure_islands.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(AdventureIsland(bot))
