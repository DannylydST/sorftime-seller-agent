"""
Sorftime Seller Agent 版本号管理
单一事实来源，所有脚本从这里读取版本信息
"""

__version__ = "3.0.0"
__updated__ = "2026-04-22"


def get_version() -> str:
    return __version__


def get_version_info() -> dict:
    return {"version": __version__, "updated": __updated__}
