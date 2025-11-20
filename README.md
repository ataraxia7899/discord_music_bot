# 🎵 Discord 음악 봇

## 🖥️ 프로젝트 소개

이 프로젝트는 Python과 Discord.py를 사용하여 개발된 **음악 재생 Discord 봇**입니다.  
YouTube에서 음악을 검색하고 스트리밍하며, 음성 채널에서 고품질의 음악을 제공합니다.  

## 📂 프로젝트 구조

```
discord_music_bot/
├── music_components/          # 음악 관련 컴포넌트
│   ├── __init__.py
│   ├── music_core.py         # 음악 재생 상태 및 핵심 로직 (ServerMusicState)
│   ├── music_player.py       # 명령어 처리 및 재생 제어 (MusicPlayer)
│   └── queue_manager.py      # 대기열 관리 및 조작 (QueueManager)
├── bot.py                    # 봇 실행 및 초기화
├── config.py                 # 통합 설정 관리 (Settings Singleton)
└── requirements.txt          # 의존성 패키지 목록
```

## 🔄 최근 업데이트 내용

### 1. 슬래시 커맨드 전면 도입
- 모든 명령어는 슬래시 커맨드(`/`) 사용
- `CommandNotFound` 오류 원천 차단

### 2. 플레이리스트 지원 강화
- **백그라운드 로딩**: 첫 곡은 즉시 재생하고 나머지는 백그라운드에서 추가
- **오류 자동 건너뛰기**: 연령 제한이나 삭제된 영상은 자동으로 건너뛰고 알림
- 대규모 플레이리스트도 끊김 없이 처리

### 3. 성능 최적화
- **재생 시작 속도 개선**: FFmpeg 및 yt-dlp 옵션 튜닝으로 지연 시간 최소화
- **안정적인 스트리밍**: 버퍼 사이즈 최적화로 끊김 현상 감소

### 4. 멀티 서버 지원
- 서버별 독립적인 대기열 및 재생 상태 관리 완벽 지원

## 📌 주요 기능

### 1. 음악 재생
- `/재생 [검색어/URL]`: YouTube URL 또는 검색어로 음악 재생 (플레이리스트 지원)
- 고품질 오디오 스트리밍 (96-128kbps Opus)

### 2. 대기열 관리
- `/대기열`: 현재 대기열 확인
- `/삭제 [번호]`: 대기열에서 특정 곡 제거
- `/셔플`: 대기열 무작위 섞기

### 3. 재생 제어
- `/다음곡`: 현재 곡을 건너뛰고 다음 곡 재생
- `/정지`: 재생 중지 및 봇 퇴장
- `/반복`: 반복 모드 전환 (없음 ➡️ 한곡 ➡️ 전체)

## 🛠️ 기술 스택

- Python 3.8+
- discord.py 2.3.2+
- yt-dlp 2023.11.16+
- FFmpeg
- asyncio

## 🚀 설치 및 실행

1. 필수 요구사항 설치
```bash
pip install -r requirements.txt
```

2. FFmpeg 설치 (택 1)
- Windows:
  ```bash
  winget install ffmpeg
  ```
  > 💡 winget이 설치되어 있지 않다면: Windows 스토어에서 "앱 설치 관리자" 설치
- Linux: `sudo apt install ffmpeg`
- macOS: `brew install ffmpeg`

3. 환경 변수 설정
```bash
# .env 파일 생성 (필수)
DISCORD_BOT_TOKEN=your_token_here
```

4. 봇 실행
```bash
python bot.py
```

## ⚠️ 알려진 문제점

1. ~~채팅방 문제: 다른 채널에서 사용해도 메인 채널에 메시지 출력~~ (수정됨)
2. ~~플레이리스트 로딩 속도 저하~~ (백그라운드 로딩으로 해결)
3. ~~반복 모드 버그~~ (수정됨)
4. ~~FFmpeg 경로 문제~~ (winget 설치로 해결됨)

## 🔧 추가 예정 기능

1. 플레이리스트 저장/불러오기

## 📢 주의사항

- YouTube 이용약관을 준수하여 사용해주세요
- 상업적 사용은 금지됩니다
- 이슈나 기능 제안은 GitHub 이슈를 통해 해주세요
