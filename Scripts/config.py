from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path(__file__).resolve().parent / "app_settings.ini"

DEFAULT_CONFIG = {
    "ui": {
        "title": "Рекомендательная система фильмов",
        "theme": "dark",
        "font_family": "Segoe UI",
        "font_size": "11",
        "window_width": "1200",
        "window_height": "760",
    },
    "paths": {
        "data_dir": str(ROOT_DIR / "Data"),
        "graphics_dir": str(ROOT_DIR / "Graphics"),
        "output_dir": str(ROOT_DIR / "Output"),
        "notes_dir": str(ROOT_DIR / "Notes"),
    },
}


def load_config() -> ConfigParser:
    parser = ConfigParser()
    parser.read_dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        parser.read(CONFIG_PATH, encoding="utf-8")
    else:
        save_config(parser)
    return parser


def save_config(config: ConfigParser) -> None:
    with CONFIG_PATH.open("w", encoding="utf-8") as cfg:
        config.write(cfg)
