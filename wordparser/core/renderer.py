"""LibreOffice 渲染器

提供 .doc → .docx 转换和页面渲染为图片功能。
LibreOffice 是可选依赖，不可用时相关功能自动跳过。
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentRenderer:
    """LibreOffice 文档渲染器"""

    def __init__(self, libreoffice_path: str | None = None):
        self.lo_path = libreoffice_path or self._detect_libreoffice()

    def is_available(self) -> bool:
        """检测 LibreOffice 是否可用（仅检查文件存在，避免 --version 弹窗）"""
        if not self.lo_path:
            return False
        return Path(self.lo_path).is_file()

    def is_doc(self, path: Path) -> bool:
        """检测是否为 .doc 格式（非 .docx）"""
        return path.suffix.lower() == ".doc"

    def convert_doc_to_docx(self, doc_path: Path, output_dir: Path | None = None) -> Path:
        """将 .doc 转换为 .docx，返回转换后的路径"""
        if not self.is_available():
            raise RuntimeError("LibreOffice 不可用，无法转换 .doc 文件")

        doc_path = Path(doc_path)
        output_dir = output_dir or doc_path.parent

        self._kill_soffice()
        startupinfo, creation_flags = self._windows_hide_flags()

        result = subprocess.run(
            self._build_headless_args(
                convert_to="docx",
                outdir=str(output_dir),
                input_file=str(doc_path),
            ),
            startupinfo=startupinfo,
            creationflags=creation_flags,
            capture_output=True, text=True, timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(f"LibreOffice 转换失败: {result.stderr}")

        output_path = output_dir / doc_path.with_suffix(".docx").name
        if not output_path.exists():
            raise RuntimeError(f"转换输出文件不存在: {output_path}")

        return output_path

    def render_page_to_image(self, docx_path: Path, page_number: int = 0) -> bytes:
        """渲染指定页为 PNG bytes

        流程：LibreOffice docx→PDF → pdf2image PDF→PNG → bytes
        """
        if not self.is_available():
            raise RuntimeError("LibreOffice 不可用")

        import tempfile

        from pdf2image import convert_from_path

        with tempfile.TemporaryDirectory(prefix="wp_lo_render_") as tmpdir:
            self._kill_soffice()
            startupinfo, creation_flags = self._windows_hide_flags()

            subprocess.run(
                self._build_headless_args(
                    convert_to="pdf",
                    outdir=tmpdir,
                    input_file=str(docx_path),
                ),
                startupinfo=startupinfo,
                creationflags=creation_flags,
                capture_output=True, text=True, timeout=120,
            )

            pdf_path = Path(tmpdir) / docx_path.with_suffix(".pdf").name
            if not pdf_path.exists():
                raise RuntimeError(f"PDF 渲染失败: {pdf_path}")

            images = convert_from_path(str(pdf_path), first_page=page_number + 1, last_page=page_number + 1)
            if not images:
                raise RuntimeError(f"页面 {page_number} 渲染为图片失败")

            import io
            buf = io.BytesIO()
            images[0].save(buf, format="PNG")
            return buf.getvalue()

    def _kill_soffice(self) -> None:
        """终止残留的 LibreOffice 进程，防止 GUI 进程复用导致弹窗"""
        if sys.platform != "win32":
            return
        subprocess.run(
            'taskkill /f /im soffice.exe >nul 2>&1',
            shell=True, timeout=10,
        )

    def _build_headless_args(
        self,
        convert_to: str,
        outdir: str,
        input_file: str,
    ) -> list[str]:
        """构建无弹窗 LibreOffice 命令行参数"""
        return [
            self.lo_path,
            "--headless",
            "--norestore",
            "--nolockcheck",
            "--nologo",
            "--nofirststartwizard",
            "--convert-to", convert_to,
            "--outdir", outdir,
            input_file,
        ]

    @staticmethod
    def _windows_hide_flags() -> tuple:
        """返回 Windows 平台隐藏窗口的 startupinfo 和 creationflags"""
        startupinfo = None
        creation_flags = 0
        if hasattr(subprocess, 'STARTUPINFO'):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
        if hasattr(subprocess, 'CREATE_NO_WINDOW'):
            creation_flags = subprocess.CREATE_NO_WINDOW
        return startupinfo, creation_flags

    def _detect_libreoffice(self) -> str | None:
        """自动检测 LibreOffice 路径"""
        path_result = shutil.which("soffice")
        if path_result:
            return path_result

        candidates = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            "/usr/bin/soffice",
            "/usr/local/bin/soffice",
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        ]
        for candidate in candidates:
            if Path(candidate).exists():
                return candidate

        return None
