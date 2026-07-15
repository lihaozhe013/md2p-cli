import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Convert Markdown to PDF with custom styles")
    parser.add_argument("file", nargs="?", help="Path to the Markdown file")
    parser.add_argument("--name", "-n", dest="name", help="Path to the Markdown file")
    parser.add_argument("--output", "-o", help="Output PDF path (default: same as input with .pdf)")
    args = parser.parse_args()

    # 检查系统是否安装了 md-to-pdf
    if not shutil.which("md-to-pdf"):
        print("Error: md-to-pdf not found. Install it with: npm i -g md-to-pdf", file=sys.stderr)
        sys.exit(1)

    project_root = Path(__file__).resolve().parent
    md_path = args.name or args.file
    if not md_path:
        parser.print_usage()
        print("Error: a Markdown file is required", file=sys.stderr)
        sys.exit(1)
    md_file = Path(md_path).resolve()

    if not md_file.exists():
        print(f"Error: file not found: {md_file}", file=sys.stderr)
        sys.exit(1)

    output = args.output or str(md_file.with_suffix(".pdf"))

    # Puppeteer PDF 选项 —— 启用页脚页码，关闭默认页眉（日期）
    pdf_options = {
        "format": "A4",
        "margin": "20mm",
        "printBackground": True,
        "displayHeaderFooter": True,
        "headerTemplate": "<span></span>",
        "footerTemplate": (
            '<div style="font-size: 10px; text-align: center; width: 100%;">'
            'Page <span class="pageNumber"></span> of <span class="totalPages"></span>'
            '</div>'
        ),
    }

    # MathJax 配置 —— 识别 $...$ 和 $$...$$ 作为 LaTeX 行内/块级公式
    mathjax_config = (
        'MathJax = { tex: { '
        'inlineMath: [["$", "$"], ["\\\\(", "\\\\)" ]], '
        'displayMath: [["$$", "$$"], ["\\\\[", "\\\\]"]] '
        '} };'
    )

    # 写入临时配置文件传递给 md-to-pdf（script 参数仅支持通过 config-file 传入）
    config_data = {
        "stylesheet": [str(project_root / "github-markdown.css")],
        "body_class": ["markdown-body"],
        "pdf_options": pdf_options,
        "script": [
            {"content": mathjax_config},
            {"url": "js/tex-chtml.js"},
        ],
    }

    config_file = project_root / ".md-to-pdf.json"
    config_file.write_text(json.dumps(config_data, indent=2))

    # 预处理：在 $$...$$ 块级公式内，将 `\\`（LaTeX 换行）自动变为 `\\\\`
    # 避免 Marked（markdown 解析器）把 `\\` 当作断行处理，破坏 matrix 等多行公式
    def escape_latex_newlines(content):
        result = []
        in_block = False
        for line in content.splitlines(keepends=True):
            stripped = line.rstrip("\n\r")
            if stripped.strip() == "$$":
                in_block = not in_block
            if in_block and stripped.endswith("\\\\"):
                line = stripped[:-2] + "\\\\\\\\\n"
            result.append(line)
        return "".join(result)

    md_content = md_file.read_text(encoding="utf-8")
    md_content = escape_latex_newlines(md_content)

    # 通过 stdin 管道传入处理后的内容（因为 CLI 不支持 `--script` 参数）
    cmd = [
        "md-to-pdf",
        "--basedir", str(project_root),
        "--config-file", str(config_file),
    ]

    result = subprocess.run(cmd, input=md_content.encode("utf-8"), capture_output=True)
    if result.returncode != 0:
        print(result.stderr.decode("utf-8", errors="replace"), file=sys.stderr)
        sys.exit(result.returncode)
    if result.stdout:
        Path(output).write_bytes(result.stdout)


if __name__ == "__main__":
    main()
