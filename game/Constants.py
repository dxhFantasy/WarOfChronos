from pathlib import Path
import json
import sys


def _find_config_path() -> Path:
    """优先使用 exe 同目录的 Constants.json，开发时使用本文件同目录。"""
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / "Constants.json")
    candidates.append(Path(__file__).resolve().with_name("Constants.json"))
    for path in candidates:
        if path.is_file():
            return path
    checked = "\n".join(str(path) for path in candidates)
    raise FileNotFoundError(f"找不到 Constants.json，已查找：\n{checked}")


_CONFIG_PATH = _find_config_path()
with _CONFIG_PATH.open("r", encoding="utf-8-sig") as _const_file:
    _config: dict[str, object] = json.load(_const_file)


DEBUG: bool = bool(_config.get("debug", _config.get("DEBUG", False)))
