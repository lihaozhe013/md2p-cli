from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from converter import check_md_to_pdf

from .converter_thread import ConverterThread
from .widgets.drop_area import DropArea
from .widgets.options_panel import OptionsPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._thread: ConverterThread | None = None
        self._setup_ui()
        self._apply_style()
        self._check_dependencies()

    def _setup_ui(self):
        self.setWindowTitle("md-to-pdf GUI")
        self.setMinimumSize(600, 550)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        self._drop_area = DropArea()
        self._drop_area.file_selected.connect(self._on_file_selected)
        layout.addWidget(self._drop_area)

        self._options_panel = OptionsPanel()
        layout.addWidget(self._options_panel)

        self._convert_btn = QPushButton("开始转换")
        self._convert_btn.setMinimumHeight(40)
        self._convert_btn.setCursor(Qt.PointingHandCursor)
        self._convert_btn.clicked.connect(self._on_convert)
        self._convert_btn.setEnabled(False)
        layout.addWidget(self._convert_btn)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setVisible(False)
        self._progress_bar.setFixedHeight(6)
        layout.addWidget(self._progress_bar)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(120)
        self._log.setPlaceholderText("日志信息...")
        layout.addWidget(self._log)

        self._status_label = QLabel("就绪")
        self._status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._status_label)

    def _apply_style(self):
        p = self.palette()
        accent = p.color(QPalette.Highlight).name()
        accent_text = p.color(QPalette.HighlightedText).name()
        base = p.color(QPalette.Base).name()
        text_color = p.color(QPalette.Text).name()
        window = p.color(QPalette.Window).name()

        self._convert_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent};
                color: {accent_text};
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {QColor(accent).darker(110).name()};
            }}
            QPushButton:disabled {{
                background-color: {QColor(accent).lighter(140).name()};
                color: {QColor(accent_text).lighter(150).name()};
            }}
        """)

        self._log.setStyleSheet(f"""
            QTextEdit {{
                background-color: {base};
                color: {text_color};
                border: 1px solid {p.color(QPalette.Mid).name()};
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
            }}
        """)

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {window};
            }}
        """)

    def _check_dependencies(self):
        if not check_md_to_pdf():
            self._log.append("⚠ md-to-pdf 未安装！请运行: npm i -g md-to-pdf")

    def _on_file_selected(self, path: str):
        self._convert_btn.setEnabled(True)
        stem = Path(path).stem
        self._options_panel.set_output_filename(stem + ".pdf")
        self._log.append(f"已选择: {path}")

    def _on_convert(self):
        md_path = self._drop_area.file_path
        if not md_path:
            return

        css_path = self._options_panel.css_path
        if not css_path:
            self._log.append("错误: 未找到 CSS 文件")
            return

        md_file = Path(md_path)
        output_dir = self._options_panel.output_dir
        filename = self._options_panel.output_filename or f"{md_file.stem}.pdf"
        output_path = str(Path(output_dir) / filename) if output_dir else str(md_file.with_suffix(".pdf"))

        self._set_ui_busy(True)
        self._log.append(f"开始转换: {md_file.name}")

        self._thread = ConverterThread(
            md_path=md_path,
            css_path=css_path,
            output_path=output_path,
            page_size=self._options_panel.page_size,
            margin=self._options_panel.margin,
            show_footer=self._options_panel.show_footer,
        )
        self._thread.started.connect(lambda name: self._log.append(f"正在处理: {name}"))
        self._thread.progress.connect(lambda msg: self._log.append(msg))
        self._thread.finished.connect(self._on_conversion_done)
        self._thread.start()

    def _on_conversion_done(self, result):
        self._set_ui_busy(False)
        if result.success:
            self._status_label.setText("✓ 转换成功")
            self._log.append(f"✓ 成功: {result.output_path}")
        else:
            self._status_label.setText("✗ 转换失败")
            self._log.append(f"✗ 失败: {result.error}")
        self._thread = None

    def _set_ui_busy(self, busy: bool):
        self._convert_btn.setEnabled(not busy)
        self._convert_btn.setText("转换中..." if busy else "开始转换")
        self._progress_bar.setVisible(busy)
        self._drop_area.setAcceptDrops(not busy)
