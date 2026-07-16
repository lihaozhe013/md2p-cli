import json
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from converter import (
    ConvertResult,
    convert_file,
    ensure_config,
    get_project_root,
    set_config_stylesheet,
)


class ConverterThread(QThread):
    started = Signal(str)
    progress = Signal(str)
    finished = Signal(ConvertResult)

    def __init__(self, md_path: str, css_path: str, output_path: str,
                 page_size: str, margin: str, show_footer: bool, parent=None):
        super().__init__(parent)
        self.md_path = md_path
        self.css_path = css_path
        self.output_path = output_path
        self.page_size = page_size
        self.margin = margin
        self.show_footer = show_footer

    def run(self):
        md_file = Path(self.md_path).resolve()
        project_root = get_project_root()
        config_file = ensure_config(project_root)

        self.started.emit(md_file.name)

        set_config_stylesheet(config_file, self.css_path)

        config = json.loads(config_file.read_text(encoding="utf-8"))
        config["pdf_options"]["format"] = self.page_size
        config["pdf_options"]["margin"] = self.margin
        config["pdf_options"]["displayHeaderFooter"] = self.show_footer
        config_file.write_text(
            json.dumps(config, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        self.progress.emit("预处理中...")
        result = convert_file(md_file, project_root, config_file, self.output_path)

        if result.success:
            self.progress.emit(f"转换成功 → {result.output_path}")
        else:
            self.progress.emit(f"转换失败: {result.error}")

        self.finished.emit(result)
