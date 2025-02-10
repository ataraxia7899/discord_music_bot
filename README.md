# 🎵 Discord 음악 봇

## 🖥️ 프로젝트 소개

이 프로젝트는 Python과 Discord.py를 사용하여 개발된 **음악 재생 Discord 봇**입니다.  
YouTube에서 음악을 검색하고 스트리밍하며, 음성 채널에서 고품질의 음악을 제공합니다.  
간단한 명령어를 통해 음악 재생, 정지, 대기열 관리, 셔플 및 반복 재생 등의 기능을 사용할 수 있습니다.

---

## 사용 방법

1. 음성 채널에 입장합니다.
2. `!재생` 또는 `/재생` 명령어로 음악을 재생합니다.
3. 다양한 명령어로 음악을 컨트롤합니다.

---

## 📌 주요 기능

### 1. 음악 재생 기능

- `/재생` 또는 `!재생`: YouTube URL 또는 검색어로 음악 재생
- 플레이리스트 지원: YouTube 플레이리스트 URL로 여러 곡 한 번에 추가
- 자동 재연결: 네트워크 문제 발생 시 자동으로 재연결 시도

### 2. 대기열 관리

- `/대기열` 또는 `!대기열`: 현재 대기열 확인
- `/이동` 또는 `!이동`: 대기열에서 곡 순서 변경
- `/삭제` 또는 `!삭제`: 대기열에서 특정 곡 제거
- `/대기열초기화` 또는 `!대기열초기화`: 대기열 전체 초기화
- `/셔플` 또는 `!셔플`: 대기열 곡 순서 무작위 변경

### 3. 재생 제어

- `/현재곡` 또는 `!현재곡`: 현재 재생 중인 곡 정보 표시
- `/다음곡` 또는 `!다음곡`: 다음 곡으로 넘어가기
- `/정지` 또는 `!정지`: 재생 중지 및 봇 퇴장
- `/반복` 또는 `!반복`: 반복 모드 설정 (대기열 반복/현재곡 반복/반복없음)

### 4. 시스템 기능

- 자동 퇴장: 음성 채널에 사용자가 없을 경우 자동 퇴장
- 캐시 시스템: 자주 재생되는 곡의 정보를 캐시하여 빠른 재생 지원
- 오류 복구: 재생 중 오류 발생 시 자동으로 다음 곡으로 넘어감

---

## 성능 최적화

- 스트리밍 최적화: 효율적인 버퍼 관리로 끊김 현상 최소화
- 동시 처리: 비동기 처리를 통한 빠른 응답 시간
- 메모리 관리: 캐시 크기 제한 및 자동 정리

---

## 신규 추가 기능

1. 재생 품질 개선

   - 오디오 품질 자동 조절
   - 네트워크 상태에 따른 버퍼 크기 최적화

2. 안정성 강화

   - 재생 오류 자동 복구
   - 네트워크 재연결 메커니즘 개선

3. 사용자 경험 개선

   - 더 자세한 곡 정보 표시
   - 진행 상태 표시 기능 추가

4. 대기열 관리 강화

   - 플레이리스트 지연 로딩
   - 대기열 상태 실시간 업데이트

5. 로스트아크 라는 게임 api를 사용한 알림시스템

   - 한 컨텐츠에서 원하는 보상이 나오는 날에 알림
   - 공식 api를 이용해 게임 정보를 조회해 캐시로 저장 후 압축
   - 오래된 캐시는 삭제하도록 작성됨

---

## 🛠️ 기술 스택

- **Python**: 봇의 주요 로직 구현.
- **Discord.py**: Discord API와의 상호작용을 위한 라이브러리.
- **yt-dlp**: YouTube 동영상 정보 추출 및 오디오 스트리밍.
- **FFmpeg**: 오디오 처리를 위한 필수 도구.

## 📂 디렉토리 구조

📦 프로젝트 루트<br>
├── bot.py # 봇의 메인 코드<br>
├── secret.py # 디스코드 봇 토큰 저장 파일<br>
└── README.md # 프로젝트 설명 파일

---

## 🚀 실행 방법

### 1️⃣ 필수 도구 설치

1. `Python 3.8` 이상 설치.
2. `FFmpeg` 설치 후 시스템 PATH에 추가.

### 2️⃣ 프로젝트 클론

```
git clone <저장소 URL>
cd <프로젝트 폴더>
```

### 3️⃣ 필요한 패키지 설치

```
pip install -r requirements.txt
```

### 4️⃣ 봇 토큰 설정

1. 주석으로 표시된 코드들을 수정한 뒤 `secret.py` 파일에 Discord 봇 토큰을 넣고 실행
2. 혹은 환경변수를 다음과 같이 설정한 뒤 실행행

```
#!/bin/bash

# 환경 변수 설정
export DISCORD_BOT_TOKEN='your_discord_bot_token'
export LOSTARK_API_KEY='your_lostark_api_key'

# 봇 실행
python3 bot.py
```

### 5️⃣ 봇 실행

```
python bot.py
```

---

## 📧 문의 및 기여

- 문제가 발생하거나 새로운 기능 추가를 제안하고 싶다면 이슈를 생성해주세요.
- Pull Request를 통해 기여할 수 있습니다.

## 📢 주의사항

1. 이 프로젝트는 학습 목적으로 제작되었으며, YouTube의 이용 약관을 준수해야 합니다.
2. 상업적 또는 공공 배포 목적으로 사용하지 마십시오.
3. FFmpeg와 yt-dlp가 올바르게 설치되어 있어야 정상적으로 작동합니다.

## 문제점 기록

1. 현재 /다음곡 명령어를 사용시 오류 채팅이 출력되지만 해당 명령어는 정상 작동되는 것을 확인
