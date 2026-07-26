"""
Schema 存储管理
- 从 Sorftime MCP 服务端拉取的 tools/list 结果持久化
- 版本化管理（按时间戳），支持回滚
- 为 bridge、matrix、fixtures 提供统一数据接口
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from .env_config import load_env
from .platform_utils import get_cache_dir

load_env()

# 存储根目录
SCHEMA_DIR = get_cache_dir() / "schema-store"
LATEST_FILE = SCHEMA_DIR / "latest.json"


def _ensure_dir():
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)


def _version_path() -> Path:
    """生成带时间戳的版本文件路径"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return SCHEMA_DIR / f"schema-{timestamp}.json"


def save(tools: list[dict]) -> Path:
    """
    保存从服务端拉取的工具 Schema 列表
    同时更新 latest.json 和带时间戳的版本文件
    """
    _ensure_dir()
    payload = {
        "saved_at": datetime.now().isoformat(),
        "tool_count": len(tools),
        "tools": tools,
    }

    # 写版本文件
    vpath = _version_path()
    with open(vpath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # 更新 latest.json（软链接/复制）
    with open(LATEST_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return vpath


def load_latest() -> list[dict]:
    """加载最近一次同步的 Schema"""
    if not LATEST_FILE.exists():
        return []
    with open(LATEST_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("tools", [])


def load_version(timestamp: str) -> list[dict]:
    """加载指定时间戳版本的 Schema"""
    vpath = SCHEMA_DIR / f"schema-{timestamp}.json"
    if not vpath.exists():
        raise FileNotFoundError(f"Schema 版本不存在: {vpath}")
    with open(vpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("tools", [])


def list_versions() -> list[str]:
    """列出所有可用的版本时间戳（从新到旧）"""
    _ensure_dir()
    versions = []
    for f in SCHEMA_DIR.glob("schema-*.json"):
        # 提取时间戳部分
        stamp = f.stem.replace("schema-", "")
        versions.append(stamp)
    return sorted(versions, reverse=True)


def rollback_to(timestamp: str) -> Path:
    """
    回滚到指定版本：将指定版本复制为 latest
    """
    vpath = SCHEMA_DIR / f"schema-{timestamp}.json"
    if not vpath.exists():
        raise FileNotFoundError(f"Schema 版本不存在: {vpath}")

    # 备份当前 latest
    if LATEST_FILE.exists():
        backup = SCHEMA_DIR / f"latest-backup-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy2(LATEST_FILE, backup)

    shutil.copy2(vpath, LATEST_FILE)
    return LATEST_FILE


def get_tool_schema(tool_name: str) -> dict | None:
    """获取指定工具的 Schema"""
    for tool in load_latest():
        if tool.get("name") == tool_name:
            return tool
    return None


def get_tool_names() -> set[str]:
    """获取当前已知所有工具名"""
    return {t.get("name", "") for t in load_latest() if t.get("name")}
