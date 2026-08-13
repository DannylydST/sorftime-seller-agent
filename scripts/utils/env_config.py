"""
Key 持久化工具：将 SORFTIME_MCP_KEY 保存到用户级配置目录（非技能目录内）。

解决 OpenClaw spawn 新 shell 时环境变量丢失的问题，同时避免分发技能包时泄露 key——
key 独立于技能实例存在，技能目录可安全打包/删除。
"""

import os
import sys
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parent.parent.parent

_KEY_NAME = "SORFTIME_MCP_KEY"

sys.path.insert(0, str(_SKILL_ROOT / "scripts"))
from utils.platform_utils import safe_chmod_private


def _get_env_file() -> Path:
    """Key 文件路径：用户级 ~/.sorftime/env（Windows: %USERPROFILE%\\.sorftime\\env）。

    不落盘在技能目录内——技能包可安全分发，key 独立存在。
    支持 SORFTIME_ENV_FILE 环境变量覆盖（高级用法）。
    """
    override = os.getenv("SORFTIME_ENV_FILE", "").strip()
    if override:
        return Path(override)
    if sys.platform == "win32":
        base = Path(os.getenv("USERPROFILE", str(Path.home())))
    else:
        base = Path.home()
    return base / ".sorftime" / "env"


_ENV_FILE = _get_env_file()


def load_env():
    """将 .env 文件内容加载到 os.environ（如果存在）"""
    if not _ENV_FILE.exists():
        return
    try:
        content = _ENV_FILE.read_text(encoding="utf-8")
    except Exception:
        return
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def save_key(key: str) -> Path:
    """保存 SORFTIME_MCP_KEY 到用户级配置目录（~/.sorftime/env）"""
    _ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    _ENV_FILE.write_text(f'{_KEY_NAME}="{key}"\n', encoding="utf-8")
    safe_chmod_private(_ENV_FILE)
    return _ENV_FILE


def has_key() -> bool:
    """检查环境变量或 .env 中是否有可用的 Key"""
    return bool(get_key())


def get_key() -> str:
    """获取当前可用的 Key（优先环境变量，fallback 到 .env）"""
    # 优先环境变量
    env_key = os.getenv(_KEY_NAME, "").strip()
    if env_key:
        return env_key
    # fallback 到 .env
    if not _ENV_FILE.exists():
        return ""
    try:
        content = _ENV_FILE.read_text(encoding="utf-8")
    except Exception:
        return ""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith(f"{_KEY_NAME}="):
            value = line[len(f"{_KEY_NAME}="):].strip().strip('"').strip("'")
            return value
    return ""
