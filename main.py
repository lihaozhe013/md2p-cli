import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from preprocess import preprocess


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


def convert_file(md_file: Path, project_root: Path, config_file: Path,
                 output: str | None = None) -> None:
    md_content = md_file.read_text(encoding="utf-8")
    md_content = preprocess(md_content)
    md_file.write_text(md_content, encoding="utf-8")
    md_content = escape_latex_newlines(md_content)

    output_path = output or str(md_file.with_suffix(".pdf"))

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
        Path(output_path).write_bytes(result.stdout)


def ensure_config(project_root: Path) -> Path:
    config_file = project_root / ".md-to-pdf.json"
    if not config_file.exists():
        example = project_root / ".md-to-pdf.json.example"
        if not example.exists():
            print(f"Error: {example} not found", file=sys.stderr)
            sys.exit(1)
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
        print(f"Created {config_file} from template")
    return config_file


def main():
    parser = argparse.ArgumentParser(description="Convert Markdown to PDF with custom styles")
    parser.add_argument("file", nargs="?", help="Path to the Markdown file or directory")
    parser.add_argument("--name", "-n", dest="name", help="Path to the Markdown file")
    parser.add_argument("--output", "-o", help="Output PDF path (default: same as input with .pdf)")
    parser.add_argument("--recursive", "-r", action="store_true",
                        help="Recursively convert all .md files in the given directory")
    args = parser.parse_args()

    if not shutil.which("md-to-pdf"):
        print("Error: md-to-pdf not found. Install it with: npm i -g md-to-pdf", file=sys.stderr)
        sys.exit(1)

    project_root = Path(__file__).resolve().parent
    config_file = ensure_config(project_root)

    if args.recursive:
        md_path = args.name or args.file
        if not md_path:
            parser.print_usage()
            print("Error: a directory path is required with -r", file=sys.stderr)
            sys.exit(1)
        root_dir = Path(md_path).resolve()
        if not root_dir.is_dir():
            print(f"Error: not a directory: {root_dir}", file=sys.stderr)
            sys.exit(1)

        md_files = sorted(root_dir.rglob("*.md"))
        if not md_files:
            print(f"No .md files found in {root_dir}")
            return

        for md_file in md_files:
            print(f"Converting {md_file}...")
            convert_file(md_file, project_root, config_file)
            print(f"  -> {md_file.with_suffix('.pdf')}")
    else:
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
        convert_file(md_file, project_root, config_file, output)
        print(f"Converted: {md_file} -> {output}")


if __name__ == "__main__":
    main()
