import json
import shutil
import subprocess
import sys
from pathlib import Path

from postprocess import postprocess
from preprocess import preprocess


class ConvertResult:
    def __init__(self, success: bool, output_path: str | None = None, error: str | None = None):
        self.success = success
        self.output_path = output_path
        self.error = error


def escape_latex_newlines(content: str) -> str:
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


def get_project_root() -> Path:
    return Path(__file__).resolve().parent


def ensure_config(project_root: Path) -> Path:
    config_file = project_root / ".md-to-pdf.json"
    if not config_file.exists():
        example = project_root / ".md-to-pdf.json.example"
        if not example.exists():
            raise FileNotFoundError(f"{example} not found")
        config = json.loads(example.read_text(encoding="utf-8"))
        config["stylesheet"] = [str(project_root / s) for s in config["stylesheet"]]
        for script in config.get("script", []):
            if "url" in script:
                script["path"] = str((project_root / script["url"]).resolve())
                del script["url"]
        config_file.write_text(
            json.dumps(config, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return config_file


def set_config_stylesheet(config_file: Path, css_path: str | Path) -> None:
    config = json.loads(config_file.read_text(encoding="utf-8"))
    config["stylesheet"] = [str(css_path)]
    config_file.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def check_md_to_pdf() -> bool:
    return shutil.which("md-to-pdf") is not None


def convert_file(
    md_file: Path,
    project_root: Path,
    config_file: Path,
    output: str | None = None,
) -> ConvertResult:
    md_content = md_file.read_text(encoding="utf-8")
    md_content = preprocess(md_content)
    md_file.write_text(md_content, encoding="utf-8")
    md_content = escape_latex_newlines(md_content)

    output_path = output or str(md_file.with_suffix(".pdf"))

    cmd = [
        str(shutil.which("md-to-pdf") or "md-to-pdf"),
        "--basedir", str(project_root),
        "--config-file", str(config_file),
    ]

    use_shell = sys.platform == "win32" and cmd[0].lower().endswith((".cmd", ".bat"))
    if use_shell:
        cmd = subprocess.list2cmdline(cmd)
    result = subprocess.run(cmd, input=md_content.encode("utf-8"), capture_output=True, shell=use_shell)
    if result.returncode != 0:
        return ConvertResult(
            success=False,
            error=result.stderr.decode("utf-8", errors="replace"),
        )
    if result.stdout:
        Path(output_path).write_bytes(result.stdout)
        postprocess(output_path, md_file.stem)
        return ConvertResult(success=True, output_path=output_path)

    return ConvertResult(success=False, error="No output from md-to-pdf")
