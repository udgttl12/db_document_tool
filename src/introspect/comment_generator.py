"""
자동 코멘트 생성기
컬럼명 규칙을 기반으로 한글 코멘트 자동 생성
"""
import re
from typing import Dict, List


class CommentGenerator:
    """컬럼명 규칙 기반 자동 코멘트 생성"""

    # 기본 패턴 규칙
    DEFAULT_PATTERNS = {
        r'_id$': 'ID',
        r'_yn$': '여부',
        r'_at$': '시간',
        r'_date$': '날짜',
        r'_time$': '시간',
        r'_cnt$': '개수',
        r'_count$': '개수',
        r'^is_': '여부',
        r'^has_': '보유여부',
        r'_flag$': '플래그',
        r'_status$': '상태',
        r'_type$': '유형',
        r'_code$': '코드',
        r'_name$': '명',
        r'_desc$': '설명',
        r'_url$': 'URL',
        r'_path$': '경로',
        r'_email$': '이메일',
        r'_phone$': '전화번호',
        r'_addr$': '주소',
        r'_address$': '주소',
        r'created_at$': '생성일시',
        r'updated_at$': '수정일시',
        r'deleted_at$': '삭제일시',
        r'^created_by$': '생성자',
        r'^updated_by$': '수정자',
        r'^deleted_by$': '삭제자'
    }

    # 컬럼명 단어 사전 (영문 -> 한글)
    WORD_DICT = {
        'user': '사용자',
        'course': '강좌',
        'class': '클래스',
        'teacher': '강사',
        'student': '학생',
        'billing': '청구',
        'payment': '결제',
        'order': '주문',
        'product': '상품',
        'category': '카테고리',
        'price': '가격',
        'amount': '금액',
        'total': '합계',
        'start': '시작',
        'end': '종료',
        'begin': '시작',
        'finish': '종료',
        'active': '활성',
        'enabled': '활성화',
        'disabled': '비활성화',
        'content': '내용',
        'title': '제목',
        'description': '설명',
        'memo': '메모',
        'note': '비고',
        'comment': '코멘트',
        'message': '메시지',
        'image': '이미지',
        'file': '파일',
        'password': '비밀번호',
        'token': '토큰',
        'session': '세션',
        'level': '레벨',
        'grade': '등급',
        'point': '포인트',
        'score': '점수'
    }

    def __init__(self, custom_patterns: Dict[str, str] = None, custom_words: Dict[str, str] = None):
        """
        Args:
            custom_patterns: 사용자 정의 패턴 규칙
            custom_words: 사용자 정의 단어 사전
        """
        self.patterns = {**self.DEFAULT_PATTERNS, **(custom_patterns or {})}
        self.words = {**self.WORD_DICT, **(custom_words or {})}

    def generate(self, column_name: str, existing_comment: str = '') -> str:
        """
        컬럼명으로부터 코멘트 자동 생성

        Args:
            column_name: 컬럼 이름
            existing_comment: 기존 코멘트 (있으면 그대로 사용)

        Returns:
            생성된 코멘트
        """
        # 기존 코멘트가 있으면 그대로 사용
        if existing_comment and existing_comment.strip():
            return existing_comment

        # 패턴 매칭
        for pattern, suffix in self.patterns.items():
            if re.search(pattern, column_name):
                base_name = self._extract_base_name(column_name, pattern)
                translated = self._translate_words(base_name)
                return f"{translated} {suffix}".strip()

        # 패턴 매칭 실패 시 단어 번역만 시도
        translated = self._translate_words(column_name)
        return translated if translated != column_name else ''

    def _extract_base_name(self, column_name: str, pattern: str) -> str:
        """
        패턴을 제거한 기본 이름 추출

        Args:
            column_name: 컬럼 이름
            pattern: 제거할 패턴

        Returns:
            기본 이름
        """
        return re.sub(pattern, '', column_name)

    def _translate_words(self, text: str) -> str:
        """
        언더스코어로 분리된 단어를 한글로 번역

        Args:
            text: 번역할 텍스트

        Returns:
            번역된 텍스트
        """
        words = text.split('_')
        translated = []

        for word in words:
            if word:
                translated.append(self.words.get(word.lower(), word))

        return ' '.join(translated)

    def generate_for_table(self, columns: List[Dict]) -> List[Dict]:
        """
        테이블의 모든 컬럼에 대해 코멘트 생성

        Args:
            columns: 컬럼 리스트

        Returns:
            코멘트가 추가된 컬럼 리스트
        """
        for column in columns:
            if 'comment' not in column or not column['comment']:
                column['comment'] = self.generate(column['name'])

        return columns

    def add_custom_pattern(self, pattern: str, suffix: str):
        """사용자 정의 패턴 추가"""
        self.patterns[pattern] = suffix

    def add_custom_word(self, eng: str, kor: str):
        """사용자 정의 단어 추가"""
        self.words[eng.lower()] = kor
