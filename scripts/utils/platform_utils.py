"""
跨平台工具函数 — 集中处理 venv 路径、Agent 环境检测、缓存目录等可移植性问题

设计原则：
- 所有路径计算都基于当前文件位置动态推导，不硬编码任何绝对路径
- 支持 macOS、Linux、Windows 三大平台
- 支持 Claude Code、OpenClaw、Cowork、Claude.ai Web 等 Agent 环境
- 所有配置项均可通过环境变量覆盖
"""

import os
import platform
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# 技能根目录
# ---------------------------------------------------------------------------

def get_skill_root() -> Path:
    """返回技能根目录（基于当前文件位置动态计算）"""
    return Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# venv 路径（跨平台）
# ---------------------------------------------------------------------------

def get_venv_dir() -> Path:
    """返回 venv 目录"""
    return get_skill_root() / ".venv"


def get_venv_python() -> Path:
    """
    返回当前平台下 venv 的 Python 可执行文件路径。
    Windows: .venv\\Scripts\\python.exe
    Unix:    .venv/bin/python
    """
    venv = get_venv_dir()
    if platform.system() == "Windows":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def get_venv_pip() -> Path:
    """
    返回当前平台下 venv 的 pip 可执行文件路径。
    """
    venv_python = get_venv_python()
    if platform.system() == "Windows":
        return venv_python.parent / "pip.exe"
    return venv_python.parent / "pip"


# ---------------------------------------------------------------------------
# 缓存目录（支持环境变量覆盖）
# ---------------------------------------------------------------------------

def get_cache_dir() -> Path:
    """
    返回缓存目录。优先级：
    1. SORFTIME_CACHE_DIR 环境变量
    2. 平台默认缓存目录
       - Windows: %LOCALAPPDATA%\\sorftime-cache
       - macOS/Linux: ~/.sorftime-cache
    """
    env_dir = os.getenv("SORFTIME_CACHE_DIR", "").strip()
    if env_dir:
        return Path(env_dir)
    if platform.system() == "Windows":
        local_appdata = os.getenv("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        return Path(local_appdata) / "sorftime-cache"
    return Path.home() / ".sorftime-cache"


# ---------------------------------------------------------------------------
# Shell 检测
# ---------------------------------------------------------------------------

def detect_shell_rc() -> Path | None:
    """
    检测用户当前使用的 shell，返回对应的 rc 文件路径。
    用于 install.py 中建议写入环境变量的位置。
    """
    if platform.system() == "Windows":
        # Windows 建议用户手动设置环境变量（PowerShell profile 太复杂）
        return None

    shell = os.getenv("SHELL", "")
    if "zsh" in shell:
        return Path.home() / ".zshrc"
    if "bash" in shell:
        bashrc = Path.home() / ".bashrc"
        if bashrc.exists():
            return bashrc
        return Path.home() / ".bash_profile"
    # 默认 fallback
    return Path.home() / ".profile"


# ---------------------------------------------------------------------------
# Agent 环境检测
# ---------------------------------------------------------------------------

def detect_agent_env() -> str:
    """
    检测当前运行的 Agent 环境。支持：
    - Claude Code (CLAUDE_CODE env)
    - OpenClaw (OPENCLAW_AGENT_ID env)
    - Cowork (COWORK_AGENT_ID env)
    - Claude.ai Web (CLAUDE_WEB_SESSION env)
    - 通用 MCP (MCP_SERVER_NAME env)
    - 通过目录推断
    """
    # 环境变量优先
    if os.environ.get("CLAUDE_CODE"):
        return "claude-code"
    if os.environ.get("OPENCLAW_AGENT_ID"):
        return "openclaw"
    if os.environ.get("COWORK_AGENT_ID"):
        return "cowork"
    if os.environ.get("CLAUDE_WEB_SESSION"):
        return "claude-web"
    if os.environ.get("MCP_SERVER_NAME"):
        return "generic-mcp"

    # 通过目录存在性推断
    home = Path.home()
    found = []
    if (home / ".claude").exists():
        found.append("claude-code")
    if (home / ".openclaw").exists():
        found.append("openclaw")
    if (home / ".cowork").exists():
        found.append("cowork")

    if len(found) == 1:
        return found[0]
    if len(found) > 1:
        return "multiple"
    return "unknown"


def get_agent_config_dir() -> Path | None:
    """
    返回当前 Agent 的配置目录。
    如果检测到多个 Agent，返回第一个存在的。
    """
    env = detect_agent_env()
    home = Path.home()

    if env == "claude-code":
        return home / ".claude"
    if env == "openclaw":
        return home / ".openclaw"
    if env == "cowork":
        return home / ".cowork"

    # 通用 fallback：按优先级返回第一个存在的
    for candidate in [home / ".claude", home / ".openclaw", home / ".cowork"]:
        if candidate.exists():
            return candidate
    return None


# ---------------------------------------------------------------------------
# 文件权限（跨平台）
# ---------------------------------------------------------------------------

def safe_chmod_private(path: Path) -> None:
    """
    安全地设置文件权限为仅所有者可读写。
    在 Windows 上跳过（chmod 600 无效），在 Unix 上执行。
    """
    if platform.system() != "Windows":
        path.chmod(0o600)


# ---------------------------------------------------------------------------
# 临时目录（跨平台）
# ---------------------------------------------------------------------------

def get_temp_dir() -> Path:
    """
    返回跨平台的临时目录。
    - Windows: %TEMP%
    - Unix: /tmp 或 $TMPDIR
    """
    import tempfile
    return Path(tempfile.gettempdir())


# ---------------------------------------------------------------------------
# 可执行文件名称（跨平台）
# ---------------------------------------------------------------------------

def get_python_cmd() -> str:
    """返回当前 Python 可执行文件的绝对路径"""
    return sys.executable


# ---------------------------------------------------------------------------
# 调试输出
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Sorftime Seller Agent Platform Info ===")
    print(f"skill_root:    {get_skill_root()}")
    print(f"venv_dir:      {get_venv_dir()}")
    print(f"venv_python:   {get_venv_python()}")
    print(f"venv_exists:   {get_venv_python().exists()}")
    print(f"venv_pip:      {get_venv_pip()}")
    print(f"cache_dir:     {get_cache_dir()}")
    print(f"agent_env:     {detect_agent_env()}")
    print(f"agent_cfg_dir: {get_agent_config_dir()}")
    print(f"shell_rc:      {detect_shell_rc()}")
    print(f"platform:      {platform.system()} {platform.release()}")
    print(f"python_cmd:    {get_python_cmd()}")
    print(f"temp_dir:      {get_temp_dir()}")
