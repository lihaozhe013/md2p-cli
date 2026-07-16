.PHONY: gui cli help install

default: gui

help:
	@echo "Usage:"
	@echo "  make gui      启动 PySide6 图形界面"
	@echo "  make cli      查看 CLI 帮助"
	@echo "  make install  安装/同步依赖"
	@echo "  make build-win  打包 Windows 单文件 exe"

gui:
	uv run python gui_main.py

cli:
	uv run python main.py --help

install:
	uv sync

build-win:
	uv run python scripts/build_win.py
