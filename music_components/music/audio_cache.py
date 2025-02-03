from typing import Dict, Optional
from datetime import datetime, timedelta
import json
import os

class AudioCache:
    """
    음악 정보 캐싱을 위한 클래스
    
    Attributes:
        _cache (Dict): 캐시 저장소
        _max_size (int): 최대 캐시 항목 수
        _ttl (int): 캐시 유효 시간(초)
    """
    
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        """
        Args:
            max_size: 최대 캐시 크기 (기본값: 100)
            ttl: 캐시 유효 시간(초) (기본값: 1시간)
        """
        self._cache: Dict[str, dict] = {}
        self._max_size = max_size
        self._ttl = ttl
        self._cache_file = "audio_cache.json"
        self._load_cache()  # 캐시 파일 로드
    
    def _load_cache(self):
        """디스크에서 캐시 로드"""
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    saved_cache = json.load(f)
                    # timestamp를 datetime으로 변환
                    for key, value in saved_cache.items():
                        value['timestamp'] = datetime.fromisoformat(value['timestamp'])
                        self._cache[key] = value
        except Exception as e:
            print(f"캐시 로드 실패: {e}")
    
    def _save_cache(self):
        """캐시를 디스크에 저장"""
        try:
            save_data = {}
            for key, value in self._cache.items():
                save_data[key] = {
                    'info': value['info'],
                    'timestamp': value['timestamp'].isoformat()
                }
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"캐시 저장 실패: {e}")

    async def get(self, key: str) -> Optional[dict]:
        """
        캐시된 데이터 조회
        
        Args:
            key: 캐시 키
            
        Returns:
            Optional[dict]: 캐시된 데이터 또는 None
        """
        if key in self._cache:
            data = self._cache[key]
            # TTL 체크
            if datetime.now() - data['timestamp'] < timedelta(seconds=self._ttl):
                return data['info']
            # TTL 만료된 경우 삭제
            del self._cache[key]
        return None
        
    async def set(self, key: str, value: dict):
        """
        데이터를 캐시에 저장
        
        Args:
            key: 캐시 키
            value: 저장할 데이터
        """
        # 캐시 크기 제한 체크
        if len(self._cache) >= self._max_size:
            # 가장 오래된 항목 제거
            oldest = min(self._cache.items(), key=lambda x: x[1]['timestamp'])
            del self._cache[oldest[0]]
            
        # 새로운 데이터 저장
        self._cache[key] = {
            'info': value,
            'timestamp': datetime.now()
        }
        self._save_cache()  # 캐시 변경시 자동 저장
