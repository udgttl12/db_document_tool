"""
Mermaid ERD 생성기
스키마 메타데이터를 Mermaid ER Diagram으로 변환
"""
from typing import Dict, List, Set, Optional
import re


class MermaidERDGenerator:
    """Mermaid ERD 생성 클래스"""

    def __init__(self, domain_prefixes: List[str] = None):
        """
        Args:
            domain_prefixes: 도메인 분할을 위한 접두사 리스트
        """
        self.domain_prefixes = domain_prefixes or []

    def generate(self, schema_data: Dict, domain_filter: Optional[str] = None) -> str:
        """
        전체 스키마에 대한 ERD 생성

        Args:
            schema_data: 스키마 메타데이터
            domain_filter: 특정 도메인 필터 (접두사)

        Returns:
            Mermaid ERD 문자열
        """
        tables = schema_data.get('tables', {})

        # 도메인 필터 적용
        if domain_filter:
            tables = {
                name: data for name, data in tables.items()
                if name.startswith(domain_filter)
            }

        if not tables:
            return "erDiagram\n  %% No tables found"

        erd_lines = ["erDiagram"]

        # 테이블 정의
        for table_name, table_data in tables.items():
            table_def = self._generate_table(table_name, table_data)
            erd_lines.append(table_def)

        # 관계 정의
        relationships = self._generate_relationships(tables)
        erd_lines.extend(relationships)

        return "\n".join(erd_lines)

    def _generate_table(self, table_name: str, table_data: Dict) -> str:
        """
        단일 테이블 정의 생성

        Args:
            table_name: 테이블 이름
            table_data: 테이블 메타데이터

        Returns:
            Mermaid 테이블 정의 문자열
        """
        lines = [f"  {table_name} {{"]

        columns = table_data.get('columns', [])
        primary_keys = table_data.get('primary_keys', [])

        for column in columns:
            col_name = column['name']
            col_type = self._simplify_type(column['type'])

            # PK 표시
            pk_mark = " PK" if col_name in primary_keys else ""

            # 코멘트 추가
            comment = column.get('comment', '')
            comment_text = f' "{comment}"' if comment else ''

            lines.append(f"    {col_type} {col_name}{pk_mark}{comment_text}")

        lines.append("  }")

        return "\n".join(lines)

    def _simplify_type(self, type_str: str) -> str:
        """
        데이터 타입 단순화

        Args:
            type_str: 원본 타입 문자열

        Returns:
            단순화된 타입
        """
        type_str = type_str.upper()

        # 괄호 제거
        type_str = re.sub(r'\(.*?\)', '', type_str).strip()

        # 타입 매핑
        type_map = {
            'INTEGER': 'INT',
            'BIGINT': 'BIGINT',
            'SMALLINT': 'INT',
            'TINYINT': 'INT',
            'VARCHAR': 'VARCHAR',
            'CHAR': 'CHAR',
            'TEXT': 'TEXT',
            'DATETIME': 'DATETIME',
            'TIMESTAMP': 'TIMESTAMP',
            'DATE': 'DATE',
            'TIME': 'TIME',
            'DECIMAL': 'DECIMAL',
            'FLOAT': 'FLOAT',
            'DOUBLE': 'DOUBLE',
            'BOOLEAN': 'BOOLEAN',
            'BOOL': 'BOOLEAN',
            'JSON': 'JSON'
        }

        for full_type, simple_type in type_map.items():
            if full_type in type_str:
                return simple_type

        return 'VARCHAR'

    def _generate_relationships(self, tables: Dict) -> List[str]:
        """
        FK 관계 생성

        Args:
            tables: 테이블 메타데이터

        Returns:
            관계 정의 문자열 리스트
        """
        relationships = []
        processed = set()

        for table_name, table_data in tables.items():
            foreign_keys = table_data.get('foreign_keys', [])

            for fk in foreign_keys:
                referred_table = fk.get('referred_table')

                # 참조 테이블이 현재 스키마에 있는지 확인
                if referred_table not in tables:
                    continue

                # 중복 관계 방지
                rel_key = f"{referred_table}_{table_name}"
                if rel_key in processed:
                    continue
                processed.add(rel_key)

                # 관계 타입 결정 (일대다)
                constrained_cols = fk.get('constrained_columns', [])
                referred_cols = fk.get('referred_columns', [])

                if constrained_cols and referred_cols:
                    col_label = f"{constrained_cols[0]}"
                else:
                    col_label = "FK"

                # Mermaid 관계 표현: Parent ||--o{ Child : "label"
                relationships.append(
                    f'  {referred_table} ||--o{{ {table_name} : "{col_label}"'
                )

        return relationships

    def generate_by_domains(self, schema_data: Dict) -> Dict[str, str]:
        """
        도메인별로 분리된 ERD 생성

        Args:
            schema_data: 스키마 메타데이터

        Returns:
            도메인명: ERD 문자열 딕셔너리
        """
        domain_erds = {}

        if not self.domain_prefixes:
            # 도메인 분할이 없으면 전체 ERD 반환
            domain_erds['all'] = self.generate(schema_data)
            return domain_erds

        # 각 도메인별 ERD 생성
        for prefix in self.domain_prefixes:
            domain_name = prefix.rstrip('_')
            erd = self.generate(schema_data, domain_filter=prefix)
            if "No tables found" not in erd:
                domain_erds[domain_name] = erd

        # 도메인에 속하지 않는 테이블들
        all_tables = schema_data.get('tables', {})
        unassigned_tables = {
            name: data for name, data in all_tables.items()
            if not any(name.startswith(prefix) for prefix in self.domain_prefixes)
        }

        if unassigned_tables:
            unassigned_schema = {
                'schema': schema_data.get('schema'),
                'tables': unassigned_tables
            }
            domain_erds['others'] = self.generate(unassigned_schema)

        return domain_erds

    def save_to_file(self, erd_content: str, output_path: str):
        """
        ERD를 파일로 저장

        Args:
            erd_content: ERD 내용
            output_path: 출력 파일 경로
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(erd_content)
