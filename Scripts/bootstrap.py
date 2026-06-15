from __future__ import annotations

from pathlib import Path

from Library.file_utils import ensure_directories
from Scripts.config import ROOT_DIR, load_config


def bootstrap_environment() -> dict[str, Path]:
    config = load_config()
    data_dir = Path(config["paths"]["data_dir"])
    graphics_dir = Path(config["paths"]["graphics_dir"])
    output_dir = Path(config["paths"]["output_dir"])
    notes_dir = Path(config["paths"]["notes_dir"])

    ensure_directories([data_dir, graphics_dir, output_dir, notes_dir, ROOT_DIR / "Scripts"])
    return {
        "data": data_dir,
        "graphics": graphics_dir,
        "output": output_dir,
        "notes": notes_dir,
    }
