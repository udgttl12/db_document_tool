"""
DB 프로필 설정 파일 로더
JSON 파일에서 여러 DB 프로필을 읽어와 관리
"""
import json
from typing import Dict, List, Optional
from pathlib import Path


class ProfileLoader:
    """DB 프로필 설정을 관리하는 클래스"""

    def __init__(self, config_path: str = "config/db_profiles.json"):
        """
        Args:
            config_path: JSON 설정 파일 경로
        """
        self.config_path = Path(config_path)
        self.profiles = []
        self.options = {}

    def load(self) -> Dict:
        """
        JSON 파일에서 DB 프로필 로드

        Returns:
            프로필과 옵션이 포함된 딕셔너리
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        self.profiles = config.get('profiles', [])
        self.options = config.get('options', {})

        return {
            'profiles': self.profiles,
            'options': self.options
        }

    def get_profile(self, profile_id: str) -> Optional[Dict]:
        """
        특정 ID의 프로필 반환

        Args:
            profile_id: 프로필 ID

        Returns:
            프로필 딕셔너리 또는 None
        """
        for profile in self.profiles:
            if profile.get('id') == profile_id:
                return profile
        return None

    def get_profiles_by_tag(self, tag: str) -> List[Dict]:
        """
        특정 태그를 가진 프로필들 반환

        Args:
            tag: 검색할 태그

        Returns:
            프로필 리스트
        """
        return [
            profile for profile in self.profiles
            if tag in profile.get('tags', [])
        ]

    def list_all_profiles(self) -> List[Dict]:
        """모든 프로필 리스트 반환"""
        return self.profiles

    def get_options(self) -> Dict:
        """설정 옵션 반환"""
        return self.options
