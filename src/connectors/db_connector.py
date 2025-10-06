"""
DB 연결 관리자
SQLAlchemy를 사용하여 여러 DB에 연결
"""
from typing import Optional
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine, Inspector
import logging

logger = logging.getLogger(__name__)


class DBConnector:
    """DB 연결을 관리하는 클래스"""

    def __init__(self, connection_url: str, timeout: int = 60):
        """
        Args:
            connection_url: SQLAlchemy 연결 문자열
            timeout: 연결 타임아웃 (초)
        """
        self.connection_url = connection_url
        self.timeout = timeout
        self.engine: Optional[Engine] = None
        self.inspector: Optional[Inspector] = None

    def connect(self) -> bool:
        """
        DB에 연결

        Returns:
            연결 성공 여부
        """
        try:
            # SQLAlchemy 엔진 생성
            self.engine = create_engine(
                self.connection_url,
                connect_args={'connect_timeout': self.timeout},
                pool_pre_ping=True,  # 연결 유효성 체크
                echo=False
            )

            # 연결 테스트
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")

            # Inspector 생성
            self.inspector = inspect(self.engine)

            logger.info(f"DB 연결 성공: {self._mask_url(self.connection_url)}")
            return True

        except Exception as e:
            logger.error(f"DB 연결 실패: {str(e)}")
            return False

    def disconnect(self):
        """DB 연결 종료"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.inspector = None
            logger.info("DB 연결 종료")

    def get_inspector(self) -> Optional[Inspector]:
        """
        SQLAlchemy Inspector 반환

        Returns:
            Inspector 객체 또는 None
        """
        return self.inspector

    def get_engine(self) -> Optional[Engine]:
        """
        SQLAlchemy Engine 반환

        Returns:
            Engine 객체 또는 None
        """
        return self.engine

    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self.engine is not None and self.inspector is not None

    @staticmethod
    def _mask_url(url: str) -> str:
        """
        비밀번호를 마스킹한 URL 반환

        Args:
            url: 연결 문자열

        Returns:
            마스킹된 URL
        """
        if '://' in url and '@' in url:
            parts = url.split('://')
            if len(parts) == 2:
                protocol = parts[0]
                rest = parts[1]
                if '@' in rest:
                    creds, host = rest.split('@', 1)
                    if ':' in creds:
                        user = creds.split(':')[0]
                        return f"{protocol}://{user}:****@{host}"
        return url

    def __enter__(self):
        """Context manager 진입"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.disconnect()
