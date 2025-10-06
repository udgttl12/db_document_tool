# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

DB 명세서 & ERD 자동화 플랫폼 - 여러 데이터베이스의 스키마를 자동으로 분석하여 테이블 명세서와 ERD를 생성하는 Streamlit 웹 애플리케이션입니다.

## 개발 환경 설정 (Windows)

### 필수 요구사항
- Python 3.8 이상
- MySQL/PostgreSQL/Oracle 드라이버 (사용하는 DB에 따라)

### 초기 설정
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 애플리케이션 실행
```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

## 핵심 아키텍처

### 데이터 흐름

```
DB 프로필(JSON) → DBConnector → SchemaInspector → 메타데이터
                                                      ↓
스냅샷 저장 ← SnapshotManager    Generators → 문서 생성 (Excel/MD/HTML/PDF)
                                   ↓
                              MermaidERDGenerator → ERD
```

### 계층 구조

1. **연결 계층 (src/connectors/)**
   - `ProfileLoader`: `config/db_profiles.json`에서 DB 연결 정보 로드
   - `DBConnector`: SQLAlchemy Engine 및 Inspector 생성/관리
   - Inspector는 읽기 전용으로 스키마 메타데이터만 수집

2. **분석 계층 (src/introspect/)**
   - `SchemaInspector`: SQLAlchemy Inspector를 사용하여 테이블/컬럼/PK/FK/인덱스 추출
   - `CommentGenerator`: 컬럼명 패턴 기반 자동 한글 코멘트 생성 (예: `*_id` → "ID", `*_yn` → "여부")
   - 정규식 필터링으로 테이블 include/exclude 가능

3. **생성 계층 (src/generators/)**
   - `MermaidERDGenerator`: FK 관계 기반 Mermaid ER Diagram 생성
   - `ExcelGenerator`: Pandas + Openpyxl로 스타일 지정된 Excel 생성
   - `MarkdownGenerator`: Jinja2 없이 순수 문자열로 MD 생성
   - `HTMLGenerator`: Jinja2 템플릿(`templates/schema_template.html`) 사용
   - `PDFGenerator`: WeasyPrint로 HTML → PDF 변환 (선택적)

4. **스냅샷 관리 (src/snapshot_manager.py)**
   - 스키마 메타데이터를 JSON으로 저장하여 버전 관리
   - 두 스냅샷 간 Diff 비교 (추가/제거/변경된 테이블/컬럼)

5. **UI 계층 (app.py)**
   - Streamlit 세션 상태로 프로필/스키마 데이터/ERD 관리
   - 탭 구조: 테이블 목록 / ERD / 테이블 상세 / 문서 내보내기

## DB 프로필 설정

`config/db_profiles.json` 구조:

```json
{
  "profiles": [
    {
      "id": "unique-id",
      "label": "표시명",
      "engine": "mysql|postgresql|oracle",
      "url": "SQLAlchemy 연결 URL",
      "schemas": ["schema1", "schema2"],
      "tags": ["dev", "prod"]
    }
  ],
  "options": {
    "defaultInclude": "정규식 패턴",
    "defaultExclude": "정규식 패턴",
    "domainPrefixes": ["user_", "course_"],
    "fetchComments": true,
    "timeoutSeconds": 60
  }
}
```

- `url` 형식: `{dialect}+{driver}://{user}:{password}@{host}:{port}/{database}`
- 예: `mysql+pymysql://user:pass@localhost:3306`

## 도메인 분할 기능

`domainPrefixes` 옵션으로 테이블 접두사 기반 ERD 분리:
- `["user_", "course_", "billing_"]` 설정 시
- `user_` 접두사 테이블들만 포함한 별도 ERD 생성
- 접두사에 속하지 않는 테이블은 "others" 도메인에 포함

## 중요 개발 규칙

### 코멘트 자동 생성 규칙 확장
`src/introspect/comment_generator.py`의 `DEFAULT_PATTERNS` 및 `WORD_DICT`를 수정하여 추가:
```python
DEFAULT_PATTERNS = {
    r'_id$': 'ID',
    r'_yn$': '여부',
    # 새 패턴 추가
}

WORD_DICT = {
    'user': '사용자',
    # 새 단어 추가
}
```

### 새 DB 엔진 지원 추가
1. 해당 드라이버 설치 (예: `psycopg2-binary` for PostgreSQL)
2. `requirements.txt`에 추가
3. `config/db_profiles.json`에서 `engine` 및 `url` 형식 확인
4. SQLAlchemy가 지원하는 모든 DB 사용 가능

### 새 문서 포맷 추가
`src/generators/` 하위에 새 Generator 클래스 생성:
- `generate(schema_data: Dict, ...) -> str/bool` 메서드 구현
- `schema_data` 구조: `{"schema": str, "tables": {table_name: table_metadata}}`
- `app.py`의 "문서 내보내기" 탭에 버튼 추가

### PDF 생성 주의사항
- WeasyPrint는 GTK+ 라이브러리 필요 (Windows 설치 복잡)
- `PDFGenerator.is_available()` 체크 후 사용
- 대안: `AlternativePDFGenerator.generate_with_wkhtmltopdf()` (wkhtmltopdf 설치 필요)

## 출력 디렉터리

- `output/`: 생성된 문서 (Excel, MD, HTML, PDF)
- `snapshots/`: 스키마 스냅샷 JSON 파일 (`{profile_id}_{schema}_{timestamp}.json`)

## 보안 고려사항

- DB 연결은 항상 읽기 전용 계정 사용 권장
- `config/db_profiles.json`에 비밀번호 직접 입력 대신 환경 변수 사용 고려
- `DBConnector._mask_url()`: 로그 출력 시 비밀번호 마스킹

## 트러블슈팅

### WeasyPrint 설치 실패 (Windows)
GTK+ 바이너리 설치 필요. 대안: wkhtmltopdf 사용

### MySQL 연결 오류
```bash
pip install pymysql
# 또는
pip install mysqlclient
```

### Mermaid ERD 미리보기
Streamlit에서 직접 렌더링 불가. 코드 복사 후 [Mermaid Live Editor](https://mermaid.live)에서 확인
