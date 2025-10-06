"""
Markdown 문서 생성기
스키마 명세서를 Markdown 형식으로 출력
"""
from typing import Dict
from pathlib import Path
from datetime import datetime


class MarkdownGenerator:
    """Markdown 문서 생성 클래스"""

    def __init__(self):
        """초기화"""
        pass

    def generate(self, schema_data: Dict, erd_content: str = '', output_path: str = None) -> str:
        """
        스키마 메타데이터를 Markdown으로 생성

        Args:
            schema_data: 스키마 메타데이터
            erd_content: Mermaid ERD 문자열 (선택)
            output_path: 출력 파일 경로 (선택)

        Returns:
            Markdown 문자열
        """
        schema_name = schema_data.get('schema', 'default')
        tables = schema_data.get('tables', {})
        table_count = schema_data.get('table_count', len(tables))

        md_lines = []

        # 헤더
        md_lines.append(f"# DB 스키마 명세서: {schema_name}")
        md_lines.append("")
        md_lines.append(f"- **생성일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md_lines.append(f"- **스키마**: {schema_name}")
        md_lines.append(f"- **테이블 수**: {table_count}")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

        # 목차
        md_lines.append("## 목차")
        md_lines.append("")
        md_lines.append("1. [ERD](#erd)")
        md_lines.append("2. [테이블 목록](#테이블-목록)")
        md_lines.append("3. [테이블 상세](#테이블-상세)")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

        # ERD 섹션
        if erd_content:
            md_lines.append("## ERD")
            md_lines.append("")
            md_lines.append("```mermaid")
            md_lines.append(erd_content.strip())
            md_lines.append("```")
            md_lines.append("")
            md_lines.append("---")
            md_lines.append("")

        # 테이블 목록
        md_lines.append("## 테이블 목록")
        md_lines.append("")
        md_lines.append("| No | 테이블명 | 설명 | 컬럼 수 |")
        md_lines.append("|----|---------|------|--------|")

        for idx, (table_name, table_data) in enumerate(sorted(tables.items()), 1):
            comment = table_data.get('comment', '')
            column_count = len(table_data.get('columns', []))
            md_lines.append(f"| {idx} | `{table_name}` | {comment} | {column_count} |")

        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

        # 테이블 상세
        md_lines.append("## 테이블 상세")
        md_lines.append("")

        for table_name, table_data in sorted(tables.items()):
            table_md = self._generate_table_section(table_name, table_data)
            md_lines.append(table_md)

        markdown_content = "\n".join(md_lines)

        # 파일로 저장
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

        return markdown_content

    def _generate_table_section(self, table_name: str, table_data: Dict) -> str:
        """
        단일 테이블 섹션 생성

        Args:
            table_name: 테이블 이름
            table_data: 테이블 메타데이터

        Returns:
            Markdown 문자열
        """
        lines = []

        # 테이블 제목
        comment = table_data.get('comment', '')
        lines.append(f"### {table_name}")
        if comment:
            lines.append(f"> {comment}")
        lines.append("")

        # 컬럼 정보
        lines.append("#### 컬럼")
        lines.append("")
        lines.append("| 컬럼명 | 데이터타입 | Nullable | Default | 설명 |")
        lines.append("|--------|-----------|----------|---------|------|")

        columns = table_data.get('columns', [])
        primary_keys = table_data.get('primary_keys', [])

        for column in columns:
            col_name = column['name']
            col_type = column['type']
            nullable = 'Y' if column.get('nullable', True) else 'N'
            default = str(column.get('default', '-'))
            col_comment = column.get('comment', '')

            # PK 표시
            if col_name in primary_keys:
                col_name = f"**{col_name}** 🔑"

            lines.append(f"| {col_name} | `{col_type}` | {nullable} | {default} | {col_comment} |")

        lines.append("")

        # Primary Key
        if primary_keys:
            lines.append("#### Primary Key")
            lines.append("")
            pk_list = ', '.join([f"`{pk}`" for pk in primary_keys])
            lines.append(f"- {pk_list}")
            lines.append("")

        # Foreign Keys
        foreign_keys = table_data.get('foreign_keys', [])
        if foreign_keys:
            lines.append("#### Foreign Keys")
            lines.append("")
            lines.append("| FK명 | 컬럼 | 참조 테이블 | 참조 컬럼 |")
            lines.append("|------|------|------------|----------|")

            for fk in foreign_keys:
                fk_name = fk.get('name', '-')
                constrained = ', '.join(fk.get('constrained_columns', []))
                referred_table = fk.get('referred_table', '-')
                referred_cols = ', '.join(fk.get('referred_columns', []))

                lines.append(f"| {fk_name} | `{constrained}` | `{referred_table}` | `{referred_cols}` |")

            lines.append("")

        # Indexes
        indexes = table_data.get('indexes', [])
        if indexes:
            lines.append("#### Indexes")
            lines.append("")
            lines.append("| 인덱스명 | 컬럼 | Unique |")
            lines.append("|---------|------|--------|")

            for idx in indexes:
                idx_name = idx.get('name', '-')
                idx_cols = ', '.join(idx.get('columns', []))
                is_unique = 'Y' if idx.get('unique', False) else 'N'

                lines.append(f"| {idx_name} | `{idx_cols}` | {is_unique} |")

            lines.append("")

        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def generate_index_only(self, schema_data: Dict) -> str:
        """
        테이블 목록만 포함하는 간단한 Markdown 생성

        Args:
            schema_data: 스키마 메타데이터

        Returns:
            Markdown 문자열
        """
        schema_name = schema_data.get('schema', 'default')
        tables = schema_data.get('tables', {})

        md_lines = [
            f"# {schema_name} - 테이블 목록",
            "",
            "| No | 테이블명 | 설명 |",
            "|----|---------|------|"
        ]

        for idx, (table_name, table_data) in enumerate(sorted(tables.items()), 1):
            comment = table_data.get('comment', '')
            md_lines.append(f"| {idx} | `{table_name}` | {comment} |")

        return "\n".join(md_lines)
