import discord
from yt_dlp import YoutubeDL, DownloadError
import asyncio
import aiohttp  # aiohttp import 추가
from config import get_ytdl_options, ffmpeg_options
from .audio_cache import AudioCache  # audio_cache에서 AudioCache 가져오기

class YTDLSource:
    _cache = {}
    
    def __init__(self, source, *, data, start_time=0):
        self.source = source
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self._start_time = start_time

    @classmethod
    async def from_query(cls, query, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        ytdl = YoutubeDL(get_ytdl_options())

        try:
            if query in cls._cache:
                data = cls._cache[query]
            else:
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=not stream))
                cls._cache[query] = data

            if 'entries' in data:
                data = data['entries'][0]

            filename = data['url'] if stream else ytdl.prepare_filename(data)
            source = await discord.FFmpegOpusAudio.from_probe(filename, **ffmpeg_options)
            return cls(source, data=data)
            
        except Exception as e:
            raise ValueError(f"동영상을 처리하는 중 오류가 발생했습니다: {e}")

class StreamPlayer:
    """음악 스트리밍을 처리하는 메인 클래스"""
    def __init__(self):
        # 캐시 시스템 초기화 (최대 100개 항목, 1시간 TTL)
        self.cache = AudioCache(max_size=100, ttl=3600)
        self._session = None  # aiohttp 세션
        # 동시 다운로드 제한 (서버 부하 방지)
        self._download_semaphore = asyncio.Semaphore(3)

    async def get_session(self):
        """aiohttp 세션 가져오기 (없으면 생성)"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def prepare_audio(self, url: str, loop=None):
        """
        오디오 URL을 처리하고 재생 가능한 형태로 준비
        
        Args:
            url (str): 유튜브 URL 또는 검색어
            loop: 비동기 이벤트 루프
        
        Returns:
            dict: 오디오 정보를 포함한 데이터
        """
        loop = loop or asyncio.get_event_loop()
        
        async with self._download_semaphore:  # 동시 다운로드 제한
            # 캐시된 데이터 확인
            cached_data = await self.cache.get(url)
            if cached_data:
                return cached_data

            # 새로운 데이터 추출
            ytdl = YoutubeDL({
                'format': 'bestaudio/best',
                'noplaylist': True,
                'nocheckcertificate': True,
                'ignoreerrors': True,
                'quiet': True,
                'extract_flat': True,
                'skip_download': True
            })

            try:
                # 비동기로 데이터 추출
                data = await loop.run_in_executor(
                    None, 
                    lambda: ytdl.extract_info(url, download=False)
                )
                # 캐시에 저장
                await self.cache.set(url, data)
                return data
            except Exception as e:
                print(f"Audio preparation error: {e}")
                raise

    async def cleanup(self):
        """리소스 정리"""
        if self._session and not self._session.closed:
            await self._session.close()
