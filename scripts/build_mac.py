"""Build a macOS .app bundle and package it as a .dmg."""
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = REPO_ROOT / "dist"
APP_NAME = "md2p-gui"

DATA_FILES = [
    "css/github-markdown.css",
    "css/rose.css",
    ".md-to-pdf.json.example",
    "js/tex-chtml.js",
    "js/mermaid.min.js",
    "fonts",
]

QUARANTINE_SCRIPT = f"""#!/bin/bash
APP_NAME="{APP_NAME}.app"

if [ ! -d "/Applications/$APP_NAME" ]; then
    echo "Please first drag $APP_NAME to the Applications folder, then run this script again."
    echo ""
    read -p "Press Enter to open /Applications…"
    open /Applications
    exit 1
fi

echo "Removing quarantine attribute from /Applications/$APP_NAME …"
sudo xattr -dr com.apple.quarantine "/Applications/$APP_NAME"

echo ""
echo "Done! You can now open $APP_NAME without Gatekeeper warnings."
exit 0
"""


def build_app() -> Path:
    add_data = []
    for f in DATA_FILES:
        src = str(REPO_ROOT / f)
        dst = str((REPO_ROOT / f).parent.relative_to(REPO_ROOT)) or "."
        add_data.append(f"{src}:{dst}")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",
        "--windowed",
        "--name", APP_NAME,
        "--distpath", str(DIST_DIR),
        "--specpath", str(DIST_DIR),
        "--workpath", str(DIST_DIR / "build"),
        "--osx-bundle-identifier", "com.mdtopdf.gui",
        *[f"--add-data={d}" for d in add_data],
        "--collect-data", "i18n",
        "--hidden-import", "pypdf.constants",
        str(REPO_ROOT / "gui_main.py"),
    ]

    subprocess.run(cmd, check=True, cwd=REPO_ROOT)

    app_path = DIST_DIR / f"{APP_NAME}.app"
    print(f"\nApp bundle built: {app_path}")
    return app_path


def create_dmg(app_path: Path):
    dmg_path = DIST_DIR / f"{APP_NAME}.dmg"
    volume_name = APP_NAME

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        app_dst = tmp / f"{APP_NAME}.app"
        shutil.copytree(app_path, app_dst, symlinks=True)

        apps_link = tmp / "Applications"
        apps_link.symlink_to("/Applications")

        script_path = tmp / "remove_quarantine.command"
        script_path.write_text(QUARANTINE_SCRIPT)
        script_path.chmod(script_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        if dmg_path.exists():
            dmg_path.unlink()

        subprocess.run([
            "hdiutil", "create",
            "-volname", volume_name,
            "-srcfolder", str(tmp),
            "-ov",
            "-format", "UDZO",
            str(dmg_path),
        ], check=True)

    print(f"DMG created: {dmg_path}")


def main():
    app_path = build_app()
    create_dmg(app_path)
    print(f"\nAll done! Distributable: {DIST_DIR / f'{APP_NAME}.dmg'}")


if __name__ == "__main__":
    main()
