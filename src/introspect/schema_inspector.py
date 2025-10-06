"""
스키마 분석 엔진
SQLAlchemy Inspector를 사용하여 DB 스키마 메타데이터 수집
"""
from typing import Dict, List, Optional
from sqlalchemy.engine import Inspector
import logging
import re

logger = logging.getLogger(__name__)


class SchemaInspector:
    """DB 스키마를 분석하여 메타데이터를 추출하는 클래스"""

    def __init__(self, inspector: Inspector, include_pattern: str = ".*", exclude_pattern: str = ""):
        """
        Args:
            inspector: SQLAlchemy Inspector 객체
            include_pattern: 포함할 테이블 정규식 패턴
            exclude_pattern: 제외할 테이블 정규식 패턴
        """
        self.inspector = inspector
        self.include_pattern = re.compile(include_pattern) if include_pattern else None
        self.exclude_pattern = re.compile(exclude_pattern) if exclude_pattern else None

    def get_schemas(self) -> List[str]:
        """
        사용 가능한 스키마 목록 반환

        Returns:
            스키마 이름 리스트
        """
        try:
            return self.inspector.get_schema_names()
        except Exception as e:
            logger.error(f"스키마 목록 조회 실패: {str(e)}")
            return []

    def get_tables(self, schema: Optional[str] = None) -> List[str]:
        """
        특정 스키마의 테이블 목록 반환 (필터 적용)

        Args:
            schema: 스키마 이름

        Returns:
            테이블 이름 리스트
        """
        try:
            tables = self.inspector.get_table_names(schema=schema)
            return self._filter_tables(tables)
        except Exception as e:
            logger.error(f"테이블 목록 조회 실패: {str(e)}")
            return []

    def _filter_tables(self, tables: List[str]) -> List[str]:
        """
        테이블 필터링

        Args:
            tables: 전체 테이블 리스트

        Returns:
            필터링된 테이블 리스트
        """
        filtered = tables

        if self.include_pattern:
            filtered = [t for t in filtered if self.include_pattern.match(t)]

        if self.exclude_pattern:
            filtered = [t for t in filtered if not self.exclude_pattern.match(t)]

        return filtered

    def get_table_metadata(self, table_name: str, schema: Optional[str] = None) -> Dict:
        """
        테이블의 상세 메타데이터 반환

        Args:
            table_name: 테이블 이름
            schema: 스키마 이름

        Returns:
            메타데이터 딕셔너리
        """
        try:
            columns = self._get_columns(table_name, schema)
            primary_keys = self._get_primary_keys(table_name, schema)
            foreign_keys = self._get_foreign_keys(table_name, schema)
            indexes = self._get_indexes(table_name, schema)
            table_comment = self._get_table_comment(table_name, schema)

            return {
                'name': table_name,
                'schema': schema,
                'comment': table_comment,
                'columns': columns,
                'primary_keys': primary_keys,
                'foreign_keys': foreign_keys,
                'indexes': indexes
            }
        except Exception as e:
            logger.error(f"테이블 메타데이터 조회 실패 ({table_name}): {str(e)}")
            return {}

    def _get_columns(self, table_name: str, schema: Optional[str]) -> List[Dict]:
        """컬럼 정보 조회"""
        columns = self.inspector.get_columns(table_name, schema=schema)
        return [
            {
                'name': col['name'],
                'type': str(col['type']),
                'nullable': col.get('nullable', True),
                'default': col.get('default'),
                'comment': col.get('comment', ''),
                'autoincrement': col.get('autoincrement', False)
            }
            for col in columns
        ]

    def _get_primary_keys(self, table_name: str, schema: Optional[str]) -> List[str]:
        """Primary Key 조회"""
        try:
            pk = self.inspector.get_pk_constraint(table_name, schema=schema)
            return pk.get('constrained_columns', [])
        except:
            return []

    def _get_foreign_keys(self, table_name: str, schema: Optional[str]) -> List[Dict]:
        """Foreign Key 조회"""
        try:
            fks = self.inspector.get_foreign_keys(table_name, schema=schema)
            return [
                {
                    'name': fk.get('name'),
                    'constrained_columns': fk.get('constrained_columns', []),
                    'referred_table': fk.get('referred_table'),
                    'referred_columns': fk.get('referred_columns', []),
                    'referred_schema': fk.get('referred_schema')
                }
                for fk in fks
            ]
        except:
            return []

    def _get_indexes(self, table_name: str, schema: Optional[str]) -> List[Dict]:
        """인덱스 조회"""
        try:
            indexes = self.inspector.get_indexes(table_name, schema=schema)
            return [
                {
                    'name': idx.get('name'),
                    'columns': idx.get('column_names', []),
                    'unique': idx.get('unique', False)
                }
                for idx in indexes
            ]
        except:
            return []

    def _get_table_comment(self, table_name: str, schema: Optional[str]) -> str:
        """테이블 코멘트 조회"""
        try:
            comment = self.inspector.get_table_comment(table_name, schema=schema)
            return comment.get('text', '') if comment else ''
        except:
            return ''

    def analyze_schema(self, schema: Optional[str] = None) -> Dict:
        """
        전체 스키마 분석

        Args:
            schema: 스키마 이름

        Returns:
            스키마 전체 메타데이터
        """
        tables = self.get_tables(schema)
        table_metadata = {}

        logger.info(f"스키마 분석 시작: {schema or 'default'}, 테이블 수: {len(tables)}")

        for table in tables:
            metadata = self.get_table_metadata(table, schema)
            if metadata:
                table_metadata[table] = metadata

        logger.info(f"스키마 분석 완료: {len(table_metadata)}개 테이블 처리")

        return {
            'schema': schema,
            'tables': table_metadata,
            'table_count': len(table_metadata)
        }
