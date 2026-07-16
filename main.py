import argparse
import sys
from pathlib import Path

from converter import (
    check_md_to_pdf,
    convert_file,
    ensure_config,
    get_project_root,
)


def main():
    parser = argparse.ArgumentParser(description="Convert Markdown to PDF with custom styles")
    parser.add_argument("file", nargs="?", help="Path to the Markdown file or directory")
    parser.add_argument("--name", "-n", dest="name", help="Path to the Markdown file")
    parser.add_argument("--output", "-o", help="Output PDF path (default: same as input with .pdf)")
    parser.add_argument("--recursive", "-r", action="store_true",
                        help="Recursively convert all .md files in the given directory")
    args = parser.parse_args()

    if not check_md_to_pdf():
        print("Error: md-to-pdf not found. Install it with: npm i -g md-to-pdf", file=sys.stderr)
        sys.exit(1)

    project_root = get_project_root()
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
            result = convert_file(md_file, project_root, config_file)
            if result.success:
                print(f"  -> {result.output_path}")
            else:
                print(f"  ERROR: {result.error}", file=sys.stderr)
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
        result = convert_file(md_file, project_root, config_file, output)
        if result.success:
            print(f"Converted: {md_file} -> {result.output_path}")
        else:
            print(f"Error: {result.error}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
