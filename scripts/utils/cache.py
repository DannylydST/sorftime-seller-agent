"""
Sorftime 数据缓存层
SQLite 本地缓存，减少重复调用，节省 token 和时间
"""

import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from platform_utils import get_cache_dir

CACHE_DIR = get_cache_dir()
CACHE_DB = CACHE_DIR / "cache.db"


def _ensure_db():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CACHE_DB))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cache (
            tool_name TEXT NOT NULL,
            params_hash TEXT NOT NULL,
            result TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            ttl INTEGER NOT NULL,
            PRIMARY KEY (tool_name, params_hash)
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON cache(created_at)")
    conn.commit()
    conn.close()


def _hash_params(params: dict) -> str:
    return hashlib.sha256(json.dumps(params, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:32]


def get(tool_name: str, params: dict, default_ttl: int = 21600) -> dict | None:
    """
    从缓存读取结果。ttl 单位秒，默认 6 小时。
    类目数据建议 24h，产品数据 6h，关键词数据 12h。
    """
    _ensure_db()
    conn = sqlite3.connect(str(CACHE_DB))
    h = _hash_params(params)
    row = conn.execute(
        "SELECT result, created_at, ttl FROM cache WHERE tool_name = ? AND params_hash = ?",
        (tool_name, h),
    ).fetchone()
    conn.close()

    if not row:
        return None

    result, created_at, ttl = row
    if time.time() - created_at > ttl:
        return None

    try:
        return json.loads(result)
    except Exception:
        return None


def set(tool_name: str, params: dict, result: dict, ttl: int = 21600):
    """写入缓存"""
    _ensure_db()
    conn = sqlite3.connect(str(CACHE_DB))
    h = _hash_params(params)
    conn.execute(
        "INSERT OR REPLACE INTO cache (tool_name, params_hash, result, created_at, ttl) VALUES (?, ?, ?, ?, ?)",
        (tool_name, h, json.dumps(result, ensure_ascii=False), int(time.time()), ttl),
    )
    conn.commit()
    conn.close()


def clear_expired():
    """清理过期缓存"""
    _ensure_db()
    conn = sqlite3.connect(str(CACHE_DB))
    now = int(time.time())
    conn.execute("DELETE FROM cache WHERE created_at + ttl < ?", (now,))
    conn.commit()
    conn.close()


# 预设 TTL 策略
TTL_PRESETS = {
    "category_report": 86400,
    "category_name_search": 86400,
    "category_search_from_top_node": 86400,
    "tiktok_category_report": 86400,
    "product_search": 21600,
    "product_detail": 21600,
    "product_reviews": 43200,
    "product_variations": 43200,
    "product_traffic_terms": 43200,
    "keyword_detail": 43200,
    "keyword_search_results": 43200,
    "keyword_extends": 43200,
    "potential_product": 21600,
    "similar_product_feature": 43200,
    "competitor_product_keywords": 43200,
    "ali1688_similar_product": 86400,
    "tiktok_product_detail": 21600,
    "get_time": 60,
    # Walmart
    "walmart_keyword_detail": 43200,
    "walmart_keyword_extends": 43200,
    "walmart_keyword_search_results": 21600,
    "walmart_keyword_list": 43200,
    "walmart_product_detail_by_product_id": 21600,
    "walmart_product_trend_by_product_id": 43200,
    "walmart_product_traffic_terms": 43200,
    "walmart_product_variations_by_product_id": 43200,
    "walmart_category_report_by_node_id": 86400,
}
