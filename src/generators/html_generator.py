"""
HTML 문서 생성기
Jinja2 템플릿을 사용하여 스키마 명세서를 HTML로 출력
"""
from typing import Dict
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape


class HTMLGenerator:
    """HTML 문서 생성 클래스"""

    def __init__(self, template_dir: str = "templates"):
        """
        Args:
            template_dir: 템플릿 디렉터리 경로
        """
        self.template_dir = Path(template_dir)

        # Jinja2 환경 설정
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def generate(self, schema_data: Dict, erd_content: str = '', output_path: str = None) -> str:
        """
        스키마 메타데이터를 HTML로 생성

        Args:
            schema_data: 스키마 메타데이터
            erd_content: Mermaid ERD 문자열 (선택)
            output_path: 출력 파일 경로 (선택)

        Returns:
            HTML 문자열
        """
        schema_name = schema_data.get('schema', 'default')
        tables = schema_data.get('tables', {})
        table_count = len(tables)

        # 테이블 리스트 준비
        tables_list = []
        for table_name, table_data in sorted(tables.items()):
            tables_list.append({
                'name': table_name,
                'comment': table_data.get('comment', ''),
                'column_count': len(table_data.get('columns', [])),
                'columns': table_data.get('columns', []),
                'primary_keys': table_data.get('primary_keys', []),
                'foreign_keys': table_data.get('foreign_keys', []),
                'indexes': table_data.get('indexes', [])
            })

        # 템플릿 렌더링
        template = self.env.get_template('schema_template.html')
        html_content = template.render(
            schema_name=schema_name,
            table_count=table_count,
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            erd_content=erd_content,
            tables_list=tables_list
        )

        # 파일로 저장
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

        return html_content

    def generate_simple(self, schema_data: Dict, output_path: str = None) -> str:
        """
        간단한 HTML 생성 (템플릿 없이)

        Args:
            schema_data: 스키마 메타데이터
            output_path: 출력 파일 경로 (선택)

        Returns:
            HTML 문자열
        """
        schema_name = schema_data.get('schema', 'default')
        tables = schema_data.get('tables', {})

        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="ko">',
            '<head>',
            '    <meta charset="UTF-8">',
            f'    <title>DB Schema - {schema_name}</title>',
            '    <style>',
            '        body { font-family: Arial, sans-serif; margin: 20px; }',
            '        table { border-collapse: collapse; width: 100%; margin: 20px 0; }',
            '        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }',
            '        th { background-color: #4CAF50; color: white; }',
            '        .pk { font-weight: bold; color: red; }',
            '    </style>',
            '</head>',
            '<body>',
            f'    <h1>DB Schema: {schema_name}</h1>',
            f'    <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>',
        ]

        # 테이블별 HTML 생성
        for table_name, table_data in sorted(tables.items()):
            html_parts.append(f'    <h2>{table_name}</h2>')

            if table_data.get('comment'):
                html_parts.append(f'    <p><em>{table_data["comment"]}</em></p>')

            html_parts.append('    <table>')
            html_parts.append('        <tr>')
            html_parts.append('            <th>컬럼명</th>')
            html_parts.append('            <th>타입</th>')
            html_parts.append('            <th>Nullable</th>')
            html_parts.append('            <th>설명</th>')
            html_parts.append('        </tr>')

            primary_keys = table_data.get('primary_keys', [])

            for column in table_data.get('columns', []):
                col_name = column['name']
                pk_class = ' class="pk"' if col_name in primary_keys else ''

                html_parts.append('        <tr>')
                html_parts.append(f'            <td{pk_class}>{col_name}</td>')
                html_parts.append(f'            <td>{column["type"]}</td>')
                html_parts.append(f'            <td>{"Y" if column.get("nullable", True) else "N"}</td>')
                html_parts.append(f'            <td>{column.get("comment", "")}</td>')
                html_parts.append('        </tr>')

            html_parts.append('    </table>')

        html_parts.append('</body>')
        html_parts.append('</html>')

        html_content = '\n'.join(html_parts)

        # 파일로 저장
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

        return html_content
