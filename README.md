# 📊 DB 명세서 & ERD 자동화 플랫폼

> 여러 데이터베이스의 스키마 정보를 자동으로 읽어 **테이블 명세서**와 **ERD**를 시각적으로 생성하는 멀티-DB 지원 도구

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red)](https://streamlit.io/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-green)](https://www.sqlalchemy.org/)

---

## 🎯 주요 기능

- ✅ **멀티 DB 프로필 관리** - JSON 기반으로 여러 DB 환경 등록 및 선택
- ✅ **자동 스키마 분석** - SQLAlchemy Inspector로 테이블/컬럼/PK/FK/인덱스 자동 수집
- ✅ **Mermaid ERD 생성** - FK 관계 기반 ER Diagram 자동 생성
- ✅ **자동 코멘트 생성** - 컬럼명 규칙 기반 한글 주석 자동 생성
- ✅ **4가지 포맷 문서화** - Excel, Markdown, HTML, PDF 형식 지원
- ✅ **스냅샷 & Diff** - 스키마 버전 관리 및 환경 간 비교
- ✅ **도메인 분할** - 접두사 기반 도메인별 ERD 생성
- ✅ **Streamlit UI** - 직관적인 웹 인터페이스

---

## 📂 프로젝트 구조

```
db_document_tool/
├─ config/
│  └─ db_profiles.json          # DB 프로필 설정
├─ src/
│  ├─ connectors/               # DB 연결 모듈
│  │  ├─ db_connector.py
│  │  └─ profile_loader.py
│  ├─ introspect/               # 스키마 분석 엔진
│  │  ├─ schema_inspector.py
│  │  └─ comment_generator.py
│  ├─ generators/               # 문서 생성기
│  │  ├─ mermaid_generator.py
│  │  ├─ excel_generator.py
│  │  ├─ markdown_generator.py
│  │  ├─ html_generator.py
│  │  └─ pdf_generator.py
│  ├─ ui/                       # Streamlit UI
│  └─ snapshot_manager.py       # 스냅샷 & Diff
├─ templates/
│  └─ schema_template.html      # HTML 템플릿
├─ output/                      # 생성된 문서 출력
├─ snapshots/                   # 스냅샷 저장
├─ app.py                       # Streamlit 메인
├─ requirements.txt             # 패키지 의존성
└─ README.md
```

---

## 🚀 설치 및 실행

### 1️⃣ 필수 요구사항

- Python 3.8 이상
- MySQL, PostgreSQL, Oracle 등 지원 (드라이버 별도 설치)

### 2️⃣ 패키지 설치

```bash
# 가상환경 생성 (권장)
python -m venv venv

# 가상환경 활성화
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 3️⃣ DB 프로필 설정

`config/db_profiles.json` 파일을 편집하여 DB 연결 정보를 설정합니다.

```json
{
  "profiles": [
    {
      "id": "academy-dev",
      "label": "Academy DEV",
      "engine": "mysql",
      "url": "mysql+pymysql://user:password@localhost:3306",
      "schemas": ["academy", "billing"],
      "tags": ["dev", "academy"]
    }
  ],
  "options": {
    "defaultInclude": ".*",
    "defaultExclude": "_history$|_backup$",
    "domainPrefixes": ["user_", "course_", "billing_"],
    "fetchComments": true,
    "timeoutSeconds": 60
  }
}
```

### 4️⃣ 애플리케이션 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

---

## 📖 사용 방법

### 1. DB 프로필 선택

- 사이드바에서 등록된 DB 프로필을 선택합니다.
- 분석할 스키마를 선택합니다.

### 2. 스키마 분석

- **"🔍 스키마 분석"** 버튼을 클릭하여 테이블 메타데이터를 수집합니다.
- 자동으로 ERD가 생성됩니다.

### 3. 문서 생성

**📋 테이블 목록** 탭에서 전체 테이블 개요를 확인합니다.

**🗺️ ERD** 탭에서 Mermaid ERD 코드를 확인하고, [Mermaid Live Editor](https://mermaid.live)에서 시각화합니다.

**🔍 테이블 상세** 탭에서 각 테이블의 컬럼, FK, 인덱스 정보를 확인합니다.

**📥 문서 내보내기** 탭에서:
- Excel 명세서 생성 및 다운로드
- Markdown 문서 생성 및 다운로드
- HTML 문서 생성 및 다운로드
- PDF 문서 생성 및 다운로드 (WeasyPrint 필요)

### 4. 스냅샷 관리

- 현재 스키마를 스냅샷으로 저장하여 버전 관리
- 두 스냅샷을 비교하여 Diff 리포트 생성

---

## 🛠️ 기술 스택

| 구성 | 기술 | 용도 |
|------|------|------|
| DB 연결 | SQLAlchemy | 다중 DB 지원 |
| 프레임워크 | Streamlit | 웹 UI |
| 템플릿 | Jinja2 | HTML 생성 |
| Excel | Pandas + Openpyxl | 스타일 지정 |
| PDF | WeasyPrint | HTML → PDF |
| ERD | Mermaid | 시각화 |
| 설정 관리 | JSON | 프로필 |
| 버전 관리 | JSON | 스냅샷 |

---

## 📝 자동 코멘트 규칙

컬럼명 패턴에 따라 자동으로 한글 코멘트를 생성합니다:

| 패턴 | 코멘트 예시 |
|------|------------|
| `*_id` | ID |
| `*_yn` | 여부 |
| `*_at` | 시간 |
| `*_date` | 날짜 |
| `*_cnt` | 개수 |
| `created_at` | 생성일시 |
| `updated_at` | 수정일시 |

---

## 🔒 보안 권장사항

- **Read-Only 계정 사용** - DB 연결 시 읽기 전용 계정 권장
- **비밀번호 관리** - `.env` 파일이나 환경 변수 사용
- **접근 제한** - 프로덕션 환경에서는 VPN/방화벽 설정

---

## 🎯 향후 계획

| 버전 | 기능 |
|------|------|
| v1.0 | ✅ 멀티 DB 문서화, ERD, Export |
| v1.1 | 🔄 스냅샷 + Diff (현재 완료) |
| v1.2 | 🔜 Cytoscape 인터랙티브 ERD |
| v1.3 | 🔜 Oracle/PostgreSQL/MSSQL 확장 |
| v2.0 | 🔜 FastAPI + Vue 확장 |

---

## 🐛 문제 해결

### WeasyPrint PDF 생성 오류

WeasyPrint는 GTK+ 라이브러리가 필요합니다:

**Windows:**
```bash
# GTK+ 설치 후
pip install weasyprint
```

**Mac:**
```bash
brew install cairo pango gdk-pixbuf libffi
pip install weasyprint
```

**Linux:**
```bash
sudo apt-get install libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
pip install weasyprint
```

### MySQL 연결 오류

PyMySQL 또는 mysqlclient 필요:

```bash
pip install pymysql
# 또는
pip install mysqlclient
```

---

## 📄 라이선스

MIT License

---

## 🤝 기여

이슈 제기 및 Pull Request 환영합니다!

---

## 📧 문의

프로젝트 관련 문의사항은 GitHub Issues를 이용해주세요.

---

**Made with ❤️ by DB Document Tool Team**
