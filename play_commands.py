from yt_dlp import YoutubeDL

_ytdl = YoutubeDL({
    'socket_timeout': 30,          # 소켓 타임아웃 증가
    'retries': 10,                # 재시도 횟수 증가
    'fragment_retries': 10,       # 조각 다운로드 재시도 증가
    'http_chunk_size': 1024*1024, # 청크 크기 조정
}) 