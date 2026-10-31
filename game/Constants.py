from pathlib import Path
import json

# 始终相对于本文件定位配置，避免依赖启动目录或 sys.argv[0]。
_CONFIG_PATH = Path(__file__).resolve().with_name("Constants.json")
with _CONFIG_PATH.open("r", encoding="utf-8") as _const_file:
    _config: dict[str, object] = json.load(_const_file)


DEBUG: bool = bool(_config['debug'])
