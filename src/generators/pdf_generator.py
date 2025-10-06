"""
PDF 문서 생성기
WeasyPrint를 사용하여 HTML을 PDF로 변환
"""
from typing import Dict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PDFGenerator:
    """PDF 문서 생성 클래스"""

    def __init__(self):
        """초기화"""
        try:
            from weasyprint import HTML
            self.HTML = HTML
            self.available = True
        except ImportError:
            logger.warning("WeasyPrint not available. PDF generation will be disabled.")
            self.available = False

    def generate_from_html(self, html_content: str, output_path: str) -> bool:
        """
        HTML 문자열을 PDF로 변환

        Args:
            html_content: HTML 문자열
            output_path: 출력 PDF 경로

        Returns:
            성공 여부
        """
        if not self.available:
            logger.error("WeasyPrint is not installed. Cannot generate PDF.")
            return False

        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # HTML을 PDF로 변환
            html_doc = self.HTML(string=html_content)
            html_doc.write_pdf(output_path)

            logger.info(f"PDF generated: {output_path}")
            return True

        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            return False

    def generate_from_html_file(self, html_path: str, output_path: str) -> bool:
        """
        HTML 파일을 PDF로 변환

        Args:
            html_path: HTML 파일 경로
            output_path: 출력 PDF 경로

        Returns:
            성공 여부
        """
        if not self.available:
            logger.error("WeasyPrint is not installed. Cannot generate PDF.")
            return False

        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # HTML 파일을 PDF로 변환
            html_doc = self.HTML(filename=html_path)
            html_doc.write_pdf(output_path)

            logger.info(f"PDF generated from {html_path}: {output_path}")
            return True

        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            return False

    def generate(self, schema_data: Dict, html_generator, erd_content: str = '', output_path: str = None) -> bool:
        """
        스키마 메타데이터를 PDF로 생성 (HTML Generator 사용)

        Args:
            schema_data: 스키마 메타데이터
            html_generator: HTMLGenerator 인스턴스
            erd_content: Mermaid ERD 문자열 (선택)
            output_path: 출력 파일 경로

        Returns:
            성공 여부
        """
        if not self.available:
            logger.error("WeasyPrint is not installed. Cannot generate PDF.")
            return False

        try:
            # HTML 생성
            html_content = html_generator.generate(schema_data, erd_content=erd_content)

            # PDF 변환
            return self.generate_from_html(html_content, output_path)

        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            return False

    def is_available(self) -> bool:
        """
        PDF 생성 가능 여부 확인

        Returns:
            사용 가능 여부
        """
        return self.available


# PDF 대체 옵션: 외부 도구 사용
class AlternativePDFGenerator:
    """
    대체 PDF 생성기 (wkhtmltopdf 등 외부 도구 사용)
    """

    @staticmethod
    def generate_with_wkhtmltopdf(html_path: str, output_path: str) -> bool:
        """
        wkhtmltopdf를 사용하여 PDF 생성

        Args:
            html_path: HTML 파일 경로
            output_path: 출력 PDF 경로

        Returns:
            성공 여부
        """
        import subprocess
        import shutil

        # wkhtmltopdf 확인
        if not shutil.which('wkhtmltopdf'):
            logger.error("wkhtmltopdf not found in PATH")
            return False

        try:
            cmd = [
                'wkhtmltopdf',
                '--enable-local-file-access',
                html_path,
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"PDF generated with wkhtmltopdf: {output_path}")
                return True
            else:
                logger.error(f"wkhtmltopdf error: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"PDF generation with wkhtmltopdf failed: {str(e)}")
            return False
