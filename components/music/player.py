import discord
from yt_dlp import YoutubeDL, DownloadError
import asyncio
from config import get_ytdl_options, ffmpeg_options

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
