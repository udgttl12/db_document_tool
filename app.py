"""
DB 명세서 & ERD 자동화 플랫폼 - Streamlit UI
"""
import streamlit as st
import sys
from pathlib import Path
import logging

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.connectors import ProfileLoader, DBConnector
from src.introspect import SchemaInspector, CommentGenerator
from src.generators import (
    MermaidERDGenerator,
    ExcelGenerator,
    MarkdownGenerator,
    HTMLGenerator,
    PDFGenerator
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 페이지 설정
st.set_page_config(
    page_title="DB 명세서 & ERD 자동화",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'profiles' not in st.session_state:
    st.session_state.profiles = []
if 'selected_profile' not in st.session_state:
    st.session_state.selected_profile = None
if 'schema_data' not in st.session_state:
    st.session_state.schema_data = None
if 'erd_content' not in st.session_state:
    st.session_state.erd_content = None


def load_profiles():
    """DB 프로필 로드"""
    try:
        loader = ProfileLoader("config/db_profiles.json")
        config = loader.load()
        st.session_state.profiles = config.get('profiles', [])
        st.session_state.options = config.get('options', {})
        return True
    except Exception as e:
        st.error(f"프로필 로드 실패: {str(e)}")
        return False


def analyze_schema(profile, schema_name):
    """스키마 분석"""
    try:
        with st.spinner("스키마 분석 중..."):
            # DB 연결
            connector = DBConnector(profile['url'])
            if not connector.connect():
                st.error("DB 연결 실패")
                return None

            inspector = connector.get_inspector()

            # 스키마 분석
            options = st.session_state.get('options', {})
            schema_inspector = SchemaInspector(
                inspector,
                include_pattern=options.get('defaultInclude', '.*'),
                exclude_pattern=options.get('defaultExclude', '')
            )

            schema_data = schema_inspector.analyze_schema(schema_name)

            # 자동 코멘트 생성
            comment_gen = CommentGenerator()
            for table_name, table_info in schema_data['tables'].items():
                table_info['columns'] = comment_gen.generate_for_table(table_info['columns'])

            # 연결 종료
            connector.disconnect()

            return schema_data

    except Exception as e:
        st.error(f"스키마 분석 실패: {str(e)}")
        logger.exception(e)
        return None


def generate_erd(schema_data):
    """ERD 생성"""
    try:
        options = st.session_state.get('options', {})
        domain_prefixes = options.get('domainPrefixes', [])

        erd_gen = MermaidERDGenerator(domain_prefixes)
        erd_content = erd_gen.generate(schema_data)

        return erd_content

    except Exception as e:
        st.error(f"ERD 생성 실패: {str(e)}")
        logger.exception(e)
        return None


def main():
    """메인 함수"""
    st.title("📊 DB 명세서 & ERD 자동화 플랫폼")
    st.markdown("---")

    # 사이드바: DB 프로필 선택
    with st.sidebar:
        st.header("⚙️ 설정")

        if st.button("🔄 프로필 새로고침"):
            load_profiles()

        if not st.session_state.profiles:
            if load_profiles():
                st.success("프로필 로드 완료")
            else:
                st.warning("프로필을 로드할 수 없습니다.")
                return

        # 프로필 선택
        profile_options = {p['label']: p for p in st.session_state.profiles}
        selected_label = st.selectbox(
            "DB 프로필 선택",
            options=list(profile_options.keys())
        )

        if selected_label:
            selected_profile = profile_options[selected_label]
            st.session_state.selected_profile = selected_profile

            st.info(f"**Engine:** {selected_profile['engine']}")
            st.info(f"**Tags:** {', '.join(selected_profile.get('tags', []))}")

            # 스키마 선택
            schemas = selected_profile.get('schemas', [])
            selected_schema = st.selectbox("스키마 선택", schemas)

            # 분석 버튼
            if st.button("🔍 스키마 분석", type="primary"):
                schema_data = analyze_schema(selected_profile, selected_schema)
                if schema_data:
                    st.session_state.schema_data = schema_data
                    st.success(f"✅ {schema_data.get('table_count', 0)}개 테이블 분석 완료")

                    # ERD 생성
                    erd_content = generate_erd(schema_data)
                    if erd_content:
                        st.session_state.erd_content = erd_content

    # 메인 영역
    if st.session_state.schema_data:
        schema_data = st.session_state.schema_data

        # 탭 구성
        tab1, tab2, tab3, tab4 = st.tabs(["📋 테이블 목록", "🗺️ ERD", "🔍 테이블 상세", "📥 문서 내보내기"])

        with tab1:
            st.header("테이블 목록")
            tables = schema_data.get('tables', {})

            table_list = []
            for table_name, table_data in sorted(tables.items()):
                table_list.append({
                    '테이블명': table_name,
                    '설명': table_data.get('comment', ''),
                    '컬럼 수': len(table_data.get('columns', []))
                })

            st.dataframe(table_list, use_container_width=True)

        with tab2:
            st.header("ERD (Mermaid)")
            if st.session_state.erd_content:
                st.code(st.session_state.erd_content, language='mermaid')

                # Mermaid 렌더링 (외부 뷰어 사용 권장)
                st.info("💡 ERD를 보려면 위 코드를 복사하여 [Mermaid Live Editor](https://mermaid.live)에 붙여넣으세요.")
            else:
                st.warning("ERD를 생성할 수 없습니다.")

        with tab3:
            st.header("테이블 상세")

            # 테이블 검색
            search = st.text_input("🔍 테이블 검색", "")

            tables = schema_data.get('tables', {})
            filtered_tables = {
                name: data for name, data in tables.items()
                if search.lower() in name.lower()
            }

            for table_name, table_data in sorted(filtered_tables.items()):
                with st.expander(f"**{table_name}** - {table_data.get('comment', '')}"):
                    st.subheader("컬럼")

                    columns = table_data.get('columns', [])
                    primary_keys = table_data.get('primary_keys', [])

                    col_list = []
                    for col in columns:
                        col_list.append({
                            '컬럼명': f"🔑 {col['name']}" if col['name'] in primary_keys else col['name'],
                            '타입': col['type'],
                            'Nullable': 'Y' if col.get('nullable', True) else 'N',
                            '설명': col.get('comment', '')
                        })

                    st.dataframe(col_list, use_container_width=True)

                    # FK 정보
                    fks = table_data.get('foreign_keys', [])
                    if fks:
                        st.subheader("Foreign Keys")
                        fk_list = []
                        for fk in fks:
                            fk_list.append({
                                'FK명': fk.get('name', ''),
                                '컬럼': ', '.join(fk.get('constrained_columns', [])),
                                '참조 테이블': fk.get('referred_table', ''),
                                '참조 컬럼': ', '.join(fk.get('referred_columns', []))
                            })
                        st.dataframe(fk_list, use_container_width=True)

        with tab4:
            st.header("문서 내보내기")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Excel")
                if st.button("📊 Excel 생성"):
                    with st.spinner("Excel 생성 중..."):
                        try:
                            excel_gen = ExcelGenerator()
                            output_path = "output/schema.xlsx"
                            excel_gen.generate(schema_data, output_path)
                            st.success(f"✅ Excel 생성 완료: {output_path}")

                            with open(output_path, 'rb') as f:
                                st.download_button(
                                    "📥 Excel 다운로드",
                                    f,
                                    file_name="schema.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                        except Exception as e:
                            st.error(f"Excel 생성 실패: {str(e)}")

                st.subheader("Markdown")
                if st.button("📝 Markdown 생성"):
                    with st.spinner("Markdown 생성 중..."):
                        try:
                            md_gen = MarkdownGenerator()
                            output_path = "output/schema.md"
                            md_gen.generate(schema_data, st.session_state.erd_content, output_path)
                            st.success(f"✅ Markdown 생성 완료: {output_path}")

                            with open(output_path, 'r', encoding='utf-8') as f:
                                st.download_button(
                                    "📥 Markdown 다운로드",
                                    f.read(),
                                    file_name="schema.md",
                                    mime="text/markdown"
                                )
                        except Exception as e:
                            st.error(f"Markdown 생성 실패: {str(e)}")

            with col2:
                st.subheader("HTML")
                if st.button("🌐 HTML 생성"):
                    with st.spinner("HTML 생성 중..."):
                        try:
                            html_gen = HTMLGenerator()
                            output_path = "output/schema.html"
                            html_gen.generate(schema_data, st.session_state.erd_content, output_path)
                            st.success(f"✅ HTML 생성 완료: {output_path}")

                            with open(output_path, 'r', encoding='utf-8') as f:
                                st.download_button(
                                    "📥 HTML 다운로드",
                                    f.read(),
                                    file_name="schema.html",
                                    mime="text/html"
                                )
                        except Exception as e:
                            st.error(f"HTML 생성 실패: {str(e)}")

                st.subheader("PDF")
                if st.button("📄 PDF 생성"):
                    with st.spinner("PDF 생성 중..."):
                        try:
                            pdf_gen = PDFGenerator()
                            if not pdf_gen.is_available():
                                st.warning("⚠️ WeasyPrint가 설치되지 않아 PDF 생성이 불가능합니다.")
                            else:
                                html_gen = HTMLGenerator()
                                output_path = "output/schema.pdf"
                                pdf_gen.generate(schema_data, html_gen, st.session_state.erd_content, output_path)
                                st.success(f"✅ PDF 생성 완료: {output_path}")

                                with open(output_path, 'rb') as f:
                                    st.download_button(
                                        "📥 PDF 다운로드",
                                        f,
                                        file_name="schema.pdf",
                                        mime="application/pdf"
                                    )
                        except Exception as e:
                            st.error(f"PDF 생성 실패: {str(e)}")

    else:
        st.info("👈 왼쪽 사이드바에서 DB 프로필을 선택하고 스키마를 분석해주세요.")


if __name__ == "__main__":
    main()
