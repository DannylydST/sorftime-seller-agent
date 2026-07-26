"""
技能本地 .env 持久化工具
用于跨会话保存 SORFTIME_MCP_KEY，解决 OpenClaw spawn 新 shell 时环境变量丢失的问题
"""

import os
import sys
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _SKILL_ROOT / ".env"

_KEY_NAME = "SORFTIME_MCP_KEY"

sys.path.insert(0, str(_SKILL_ROOT / "scripts"))
from utils.platform_utils import safe_chmod_private


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
    """保存 SORFTIME_MCP_KEY 到技能根目录的 .env 文件"""
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
