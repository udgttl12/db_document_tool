"""
스냅샷 & Diff 관리자
스키마 버전 관리 및 환경 간 비교
"""
import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SnapshotManager:
    """스키마 스냅샷 관리 클래스"""

    def __init__(self, snapshot_dir: str = "snapshots"):
        """
        Args:
            snapshot_dir: 스냅샷 저장 디렉터리
        """
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, schema_data: Dict, profile_id: str, schema_name: str, description: str = "") -> str:
        """
        스키마 스냅샷 저장

        Args:
            schema_data: 스키마 메타데이터
            profile_id: DB 프로필 ID
            schema_name: 스키마 이름
            description: 스냅샷 설명

        Returns:
            스냅샷 파일명
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{profile_id}_{schema_name}_{timestamp}.json"
        filepath = self.snapshot_dir / filename

        snapshot = {
            "metadata": {
                "profile_id": profile_id,
                "schema_name": schema_name,
                "timestamp": timestamp,
                "datetime": datetime.now().isoformat(),
                "description": description,
                "table_count": schema_data.get('table_count', 0)
            },
            "schema_data": schema_data
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)

        logger.info(f"Snapshot saved: {filename}")
        return filename

    def load_snapshot(self, filename: str) -> Optional[Dict]:
        """
        스냅샷 로드

        Args:
            filename: 스냅샷 파일명

        Returns:
            스냅샷 데이터
        """
        filepath = self.snapshot_dir / filename

        if not filepath.exists():
            logger.error(f"Snapshot not found: {filename}")
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load snapshot: {str(e)}")
            return None

    def list_snapshots(self, profile_id: Optional[str] = None, schema_name: Optional[str] = None) -> List[Dict]:
        """
        스냅샷 목록 조회

        Args:
            profile_id: 필터링할 프로필 ID
            schema_name: 필터링할 스키마 이름

        Returns:
            스냅샷 메타데이터 리스트
        """
        snapshots = []

        for filepath in self.snapshot_dir.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    snapshot = json.load(f)
                    metadata = snapshot.get('metadata', {})

                    # 필터링
                    if profile_id and metadata.get('profile_id') != profile_id:
                        continue
                    if schema_name and metadata.get('schema_name') != schema_name:
                        continue

                    metadata['filename'] = filepath.name
                    snapshots.append(metadata)

            except Exception as e:
                logger.warning(f"Failed to read snapshot {filepath.name}: {str(e)}")

        # 시간 역순 정렬
        snapshots.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return snapshots

    def compare_snapshots(self, snapshot1_file: str, snapshot2_file: str) -> Dict:
        """
        두 스냅샷 비교

        Args:
            snapshot1_file: 첫 번째 스냅샷 파일명
            snapshot2_file: 두 번째 스냅샷 파일명

        Returns:
            비교 결과 딕셔너리
        """
        snap1 = self.load_snapshot(snapshot1_file)
        snap2 = self.load_snapshot(snapshot2_file)

        if not snap1 or not snap2:
            return {"error": "Failed to load snapshots"}

        schema1 = snap1.get('schema_data', {})
        schema2 = snap2.get('schema_data', {})

        diff_result = self._compare_schemas(schema1, schema2)

        return {
            "snapshot1": snap1.get('metadata', {}),
            "snapshot2": snap2.get('metadata', {}),
            "diff": diff_result
        }

    def _compare_schemas(self, schema1: Dict, schema2: Dict) -> Dict:
        """
        스키마 비교 (내부 메서드)

        Args:
            schema1: 첫 번째 스키마
            schema2: 두 번째 스키마

        Returns:
            차이점 딕셔너리
        """
        tables1 = set(schema1.get('tables', {}).keys())
        tables2 = set(schema2.get('tables', {}).keys())

        added_tables = list(tables2 - tables1)
        removed_tables = list(tables1 - tables2)
        common_tables = list(tables1 & tables2)

        modified_tables = []

        # 공통 테이블 비교
        for table_name in common_tables:
            table1_data = schema1['tables'][table_name]
            table2_data = schema2['tables'][table_name]

            table_diff = self._compare_tables(table1_data, table2_data)

            if table_diff['has_changes']:
                modified_tables.append({
                    'table_name': table_name,
                    'changes': table_diff
                })

        return {
            "added_tables": added_tables,
            "removed_tables": removed_tables,
            "modified_tables": modified_tables,
            "summary": {
                "added": len(added_tables),
                "removed": len(removed_tables),
                "modified": len(modified_tables)
            }
        }

    def _compare_tables(self, table1: Dict, table2: Dict) -> Dict:
        """
        테이블 비교 (내부 메서드)

        Args:
            table1: 첫 번째 테이블
            table2: 두 번째 테이블

        Returns:
            차이점 딕셔너리
        """
        columns1 = {col['name']: col for col in table1.get('columns', [])}
        columns2 = {col['name']: col for col in table2.get('columns', [])}

        added_columns = list(set(columns2.keys()) - set(columns1.keys()))
        removed_columns = list(set(columns1.keys()) - set(columns2.keys()))

        modified_columns = []
        for col_name in set(columns1.keys()) & set(columns2.keys()):
            col1 = columns1[col_name]
            col2 = columns2[col_name]

            changes = []
            if col1.get('type') != col2.get('type'):
                changes.append(f"Type: {col1.get('type')} → {col2.get('type')}")
            if col1.get('nullable') != col2.get('nullable'):
                changes.append(f"Nullable: {col1.get('nullable')} → {col2.get('nullable')}")
            if col1.get('comment') != col2.get('comment'):
                changes.append(f"Comment: {col1.get('comment')} → {col2.get('comment')}")

            if changes:
                modified_columns.append({
                    'column_name': col_name,
                    'changes': changes
                })

        # FK 비교
        fks1 = set(fk.get('name', '') for fk in table1.get('foreign_keys', []))
        fks2 = set(fk.get('name', '') for fk in table2.get('foreign_keys', []))

        added_fks = list(fks2 - fks1)
        removed_fks = list(fks1 - fks2)

        has_changes = bool(added_columns or removed_columns or modified_columns or added_fks or removed_fks)

        return {
            "has_changes": has_changes,
            "added_columns": added_columns,
            "removed_columns": removed_columns,
            "modified_columns": modified_columns,
            "added_foreign_keys": added_fks,
            "removed_foreign_keys": removed_fks
        }

    def generate_diff_report(self, diff_result: Dict, output_path: Optional[str] = None) -> str:
        """
        Diff 리포트 생성 (Markdown)

        Args:
            diff_result: 비교 결과
            output_path: 출력 파일 경로 (선택)

        Returns:
            Markdown 문자열
        """
        lines = []

        snap1 = diff_result.get('snapshot1', {})
        snap2 = diff_result.get('snapshot2', {})
        diff = diff_result.get('diff', {})

        lines.append("# 스키마 비교 리포트")
        lines.append("")
        lines.append("## 스냅샷 정보")
        lines.append("")
        lines.append(f"### Snapshot 1")
        lines.append(f"- **프로필**: {snap1.get('profile_id')}")
        lines.append(f"- **스키마**: {snap1.get('schema_name')}")
        lines.append(f"- **생성일시**: {snap1.get('datetime')}")
        lines.append("")
        lines.append(f"### Snapshot 2")
        lines.append(f"- **프로필**: {snap2.get('profile_id')}")
        lines.append(f"- **스키마**: {snap2.get('schema_name')}")
        lines.append(f"- **생성일시**: {snap2.get('datetime')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        summary = diff.get('summary', {})
        lines.append("## 요약")
        lines.append("")
        lines.append(f"- **추가된 테이블**: {summary.get('added', 0)}")
        lines.append(f"- **제거된 테이블**: {summary.get('removed', 0)}")
        lines.append(f"- **변경된 테이블**: {summary.get('modified', 0)}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 추가된 테이블
        added = diff.get('added_tables', [])
        if added:
            lines.append("## ✅ 추가된 테이블")
            lines.append("")
            for table in added:
                lines.append(f"- `{table}`")
            lines.append("")

        # 제거된 테이블
        removed = diff.get('removed_tables', [])
        if removed:
            lines.append("## ❌ 제거된 테이블")
            lines.append("")
            for table in removed:
                lines.append(f"- `{table}`")
            lines.append("")

        # 변경된 테이블
        modified = diff.get('modified_tables', [])
        if modified:
            lines.append("## 🔄 변경된 테이블")
            lines.append("")
            for item in modified:
                table_name = item['table_name']
                changes = item['changes']

                lines.append(f"### `{table_name}`")
                lines.append("")

                if changes.get('added_columns'):
                    lines.append("**추가된 컬럼:**")
                    for col in changes['added_columns']:
                        lines.append(f"- {col}")
                    lines.append("")

                if changes.get('removed_columns'):
                    lines.append("**제거된 컬럼:**")
                    for col in changes['removed_columns']:
                        lines.append(f"- {col}")
                    lines.append("")

                if changes.get('modified_columns'):
                    lines.append("**변경된 컬럼:**")
                    for col_change in changes['modified_columns']:
                        lines.append(f"- **{col_change['column_name']}**")
                        for change in col_change['changes']:
                            lines.append(f"  - {change}")
                    lines.append("")

        report = "\n".join(lines)

        # 파일로 저장
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)

        return report

    def delete_snapshot(self, filename: str) -> bool:
        """
        스냅샷 삭제

        Args:
            filename: 삭제할 파일명

        Returns:
            삭제 성공 여부
        """
        filepath = self.snapshot_dir / filename

        if not filepath.exists():
            return False

        try:
            filepath.unlink()
            logger.info(f"Snapshot deleted: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete snapshot: {str(e)}")
            return False
