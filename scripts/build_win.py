"""Build a single-file Windows executable for the GUI."""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = REPO_ROOT / "dist"

DATA_FILES = [
    "github-markdown.css",
    "rose.css",
    ".md-to-pdf.json.example",
    "js/tex-chtml.js",
]


def main():
    add_data = []
    for f in DATA_FILES:
        src = str(REPO_ROOT / f)
        dst = str((REPO_ROOT / f).parent.relative_to(REPO_ROOT)) or "."
        add_data.append(f"{src}:{dst}")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "md-to-pdf-gui",
        "--distpath", str(DIST_DIR),
        "--specpath", str(DIST_DIR),
        "--workpath", str(DIST_DIR / "build"),
        *[f"--add-data={d}" for d in add_data],
        "--hidden-import", "pypdf.constants",
        str(REPO_ROOT / "gui_main.py"),
    ]

    subprocess.run(cmd, check=True, cwd=REPO_ROOT)
    print(f"\nDone! Executable at: {DIST_DIR / 'md-to-pdf-gui.exe'}")


if __name__ == "__main__":
    main()
