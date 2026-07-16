from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QFont, QPalette
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)


class DropArea(QFrame):
    file_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._file_path: str | None = None
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(120)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self._icon_label = QLabel("📄")
        self._icon_label.setAlignment(Qt.AlignCenter)
        icon_font = QFont()
        icon_font.setPointSize(32)
        self._icon_label.setFont(icon_font)

        self._hint_label = QLabel("拖拽 Markdown 文件到此处\n或点击下方按钮选择")
        self._hint_label.setAlignment(Qt.AlignCenter)

        self._file_label = QLabel("")
        self._file_label.setAlignment(Qt.AlignCenter)
        self._file_label.setWordWrap(True)
        self._file_label.setVisible(False)
        file_font = QFont()
        file_font.setBold(True)
        self._file_label.setFont(file_font)

        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignCenter)
        self._select_btn = QPushButton("选择文件")
        self._select_btn.clicked.connect(self._on_select)
        self._clear_btn = QPushButton("清除")
        self._clear_btn.clicked.connect(self._on_clear)
        self._clear_btn.setVisible(False)
        btn_layout.addWidget(self._select_btn)
        btn_layout.addWidget(self._clear_btn)

        layout.addWidget(self._icon_label)
        layout.addWidget(self._hint_label)
        layout.addWidget(self._file_label)
        layout.addLayout(btn_layout)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def _apply_style(self):
        p = self.palette()
        bg = p.color(QPalette.Window).name()
        border_color = p.color(QPalette.Mid).name()
        hover_bg = QColor(p.color(QPalette.Window))
        hover_bg = QColor(
            min(hover_bg.red() + 15, 255),
            min(hover_bg.green() + 15, 255),
            min(hover_bg.blue() + 15, 255),
        )
        accent = p.color(QPalette.Highlight).name()

        self.setStyleSheet(f"""
            DropArea {{
                background-color: {bg};
                border: 2px dashed {border_color};
                border-radius: 12px;
                padding: 16px;
            }}
            DropArea:hover {{
                border-color: {border_color};
                background-color: {hover_bg.name()};
            }}
            DropArea[drag_over="true"] {{
                border-color: {accent};
                background-color: {accent}22;
            }}
            QPushButton {{
                padding: 8px 20px;
                border-radius: 6px;
                font-size: 13px;
            }}
        """)
        self._select_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent};
                color: {p.color(QPalette.HighlightedText).name()};
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {QColor(accent).darker(110).name()};
            }}
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1 and urls[0].toLocalFile().endswith(".md"):
                event.acceptProposedAction()
                self.setProperty("drag_over", True)
                self.style().unpolish(self)
                self.style().polish(self)

    def dragLeaveEvent(self, event):
        self.setProperty("drag_over", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        self.setProperty("drag_over", False)
        self.style().unpolish(self)
        self.style().polish(self)
        urls = event.mimeData().urls()
        if urls:
            self._set_file(urls[0].toLocalFile())
            event.acceptProposedAction()

    def _on_select(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 Markdown 文件", "", "Markdown (*.md);;All Files (*)"
        )
        if file_path:
            self._set_file(file_path)

    def _on_clear(self):
        self._file_path = None
        self._file_label.setVisible(False)
        self._hint_label.setVisible(True)
        self._icon_label.setVisible(True)
        self._clear_btn.setVisible(False)

    def _set_file(self, path: str):
        self._file_path = path
        name = Path(path).name
        self._file_label.setText(f"已选择: {name}")
        self._file_label.setVisible(True)
        self._hint_label.setVisible(False)
        self._icon_label.setVisible(False)
        self._clear_btn.setVisible(True)
        self.file_selected.emit(path)

    @property
    def file_path(self) -> str | None:
        return self._file_path
