import discord
from discord.ext import commands, tasks
import aiohttp
import datetime
import pytz
from discord import app_commands
# from secret import YOUR_LOSTARK_API_KEY  테스트용 secret 파일안에 key를 넣고 실행 코드
import asyncio
from typing import Dict, List, Optional
import json
import os

class AdventureIsland(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.subscribers: Dict[int, set] = {}  # {guild_id: {user_ids}}
        self.calendar_data: Dict[str, List] = {}  # {date: [island_data]}
        self.last_update = None
        self.cache_file = 'adventure_island_cache.json'
        self.max_cache_size = 1024 * 1024  # 1MB 제한
        
        # 캐시 크기 관리 추가
        self.cleanup_old_data()
        self.update_calendar.start()

    def cleanup_old_data(self):
        """오래된 캐시 데이터를 정리합니다."""
        try:
            if os.path.exists(self.cache_file):
                if os.path.getsize(self.cache_file) > self.max_cache_size:
                    # 한 달 이상 지난 데이터 삭제
                    current_date = datetime.datetime.now()
                    one_month_ago = (current_date - datetime.timedelta(days=31)).strftime('%Y-%m-%d')
                    
                    # 오래된 데이터 필터링
                    self.calendar_data = {
                        date: data 
                        for date, data in self.calendar_data.items() 
                        if date >= one_month_ago
                    }
                    
                    # 캐시 저장
                    self.save_cache()
                    print(f"캐시 정리 완료: {os.path.getsize(self.cache_file)} bytes")
        except Exception as e:
            print(f"캐시 정리 중 오류 발생: {e}")

    def load_cache(self):
        """캐시된 데이터를 로드합니다."""
        try:
            if os.path.exists('adventure_island_cache.json'):
                with open('adventure_island_cache.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.subscribers = {int(k): set(map(int, v)) for k, v in data.get('subscribers', {}).items()}
                    self.calendar_data = data.get('calendar_data', {})
                    self.last_update = data.get('last_update')
        except Exception as e:
            print(f"캐시 로드 중 오류 발생: {e}")

    def save_cache(self):
        """현재 데이터를 캐시에 저장합니다."""
        try:
            cache_data = {
                'subscribers': {str(k): list(map(str, v)) for k, v in self.subscribers.items()},
                'calendar_data': self.calendar_data,
                'last_update': self.last_update
            }
            with open('adventure_island_cache.json', 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"캐시 저장 중 오류 발생: {e}")

    @app_commands.command(name="골드섬알림", description="골드섬 알림을 켜거나 끕니다")
    async def toggle_notification(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        user_id = interaction.user.id

        if guild_id not in self.subscribers:
            self.subscribers[guild_id] = set()

        if user_id in self.subscribers[guild_id]:
            self.subscribers[guild_id].remove(user_id)
            await interaction.response.send_message("골드섬 알림이 꺼졌습니다.", ephemeral=True)
        else:
            self.subscribers[guild_id].add(user_id)
            await interaction.response.send_message("골드섬 알림이 켜졌습니다.", ephemeral=True)
        
        self.save_cache()

    @app_commands.command(name="골드섬알림상태", description="현재 골드섬 알림 상태를 확인합니다")
    async def check_notification_status(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        user_id = interaction.user.id
        
        is_subscribed = (
            guild_id in self.subscribers and 
            user_id in self.subscribers[guild_id]
        )
        
        status = "켜짐 ✅" if is_subscribed else "꺼짐 ❌"
        await interaction.response.send_message(
            f"현재 골드섬 알림 상태: {status}", 
            ephemeral=True
        )

    @app_commands.command(name="다음골드섬", description="다음 골드섬 정보를 확인합니다")
    async def next_gold_island(self, interaction: discord.Interaction):
        await interaction.response.defer()

        kr_tz = pytz.timezone('Asia/Seoul')
        now = datetime.datetime.now(kr_tz)
        today = now.strftime('%Y-%m-%d')
        
        next_gold_island = None
        next_date = None

        # 현재 날짜부터 순차적으로 검색
        for date, islands in sorted(self.calendar_data.items()):
            if date < today:
                continue
                
            for island in islands:
                if self._has_gold_reward(island):
                    next_gold_island = island
                    next_date = date
                    break
            if next_gold_island:
                break

        if next_gold_island:
            days_until = (datetime.datetime.strptime(next_date, '%Y-%m-%d') - now).days
            time_str = "오전" if self._is_morning(next_gold_island) else "오후"
            
            embed = discord.Embed(
                title="🏝️ 다음 골드 모험섬 정보",
                description=f"다음 골드 보상 모험섬까지 **{days_until}일** 남았습니다!",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="모험섬 정보",
                value=f"📅 날짜: {next_date}\n⏰ 시간대: {time_str}\n🏝️ 섬: {next_gold_island['ContentsName']}\n💰 보상: {self._get_rewards(next_gold_island)}",
                inline=False
            )
        else:
            next_update = self._get_next_update_date()
            embed = discord.Embed(
                title="🏝️ 골드 모험섬 정보",
                description=f"현재 조회된 기간 내에 골드 보상이 있는 모험섬이 없습니다.\n다음 데이터 업데이트: {next_update}",
                color=discord.Color.red()
            )

        await interaction.followup.send(embed=embed)

    def _has_gold_reward(self, island_data: dict) -> bool:
        """섬이 골드 보상을 포함하는지 확인합니다."""
        rewards = island_data.get('Rewards', [])
        return any('골드' in reward.get('Name', '') for reward in rewards)

    def _is_morning(self, island_data: dict) -> bool:
        """섬이 오전 출현인지 확인합니다."""
        start_time = island_data.get('StartTimes', [''])[0]
        if start_time:
            hour = int(start_time.split(':')[0])
            return hour < 12
        return False

    def _get_rewards(self, island_data: dict) -> str:
        """보상 정보를 문자열로 반환합니다."""
        rewards = island_data.get('Rewards', [])
        return ', '.join(reward.get('Name', '') for reward in rewards)

    def _get_next_update_date(self) -> str:
        """다음 데이터 업데이트 날짜를 반환합니다."""
        kr_tz = pytz.timezone('Asia/Seoul')
        now = datetime.datetime.now(kr_tz)
        next_update = now + datetime.timedelta(days=7)
        return next_update.strftime('%Y-%m-%d')

    @tasks.loop(hours=24)
    async def update_calendar(self):
        """캘린더 데이터를 업데이트합니다."""
        try:
            headers = {
                'accept': 'application/json',
                'authorization': f'bearer {os.getenv("YOUR_LOSTARK_API_KEY")}'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://developer-lostark.game.onstove.com/gamecontents/calendar',
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 데이터 정리 및 저장
                        new_calendar_data = {}
                        for event in data:
                            if event.get('CategoryName') == '모험 섬':
                                date = event.get('StartTimes', [''])[0].split('T')[0]
                                if date not in new_calendar_data:
                                    new_calendar_data[date] = []
                                new_calendar_data[date].append(event)
                        
                        self.calendar_data = new_calendar_data
                        self.last_update = datetime.datetime.now().isoformat()
                        
                        # 캐시 저장
                        self.save_cache()
                        
                        # 골드섬 알림 처리
                        await self._process_notifications()
                    else:
                        print(f"API 요청 실패: {response.status}")
        except Exception as e:
            print(f"캘린더 업데이트 중 오류 발생: {e}")

    async def _process_notifications(self):
        """골드섬 알림을 처리합니다."""
        kr_tz = pytz.timezone('Asia/Seoul')
        now = datetime.datetime.now(kr_tz)
        today = now.strftime('%Y-%m-%d')
        
        if today in self.calendar_data:
            gold_islands = [
                island for island in self.calendar_data[today]
                if self._has_gold_reward(island)
            ]
            
            if gold_islands:
                for guild_id, subscribers in self.subscribers.items():
                    for user_id in subscribers:
                        try:
                            user = await self.bot.fetch_user(user_id)
                            for island in gold_islands:
                                time_str = "오전" if self._is_morning(island) else "오후"
                                await user.send(
                                    f"🏝️ **오늘의 골드 모험섬 알림**\n"
                                    f"```\n"
                                    f"시간대: {time_str}\n"
                                    f"섬: {island['ContentsName']}\n"
                                    f"보상: {self._get_rewards(island)}\n"
                                    f"```"
                                )
                        except Exception as e:
                            print(f"DM 발송 실패 (유저 ID: {user_id}): {e}")

    @update_calendar.before_loop
    async def before_update_calendar(self):
        """봇이 준비될 때까지 대기합니다."""
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(AdventureIsland(bot))
