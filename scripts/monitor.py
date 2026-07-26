#!/usr/bin/env python3
"""
Monitoring Engine — Maintain watchlist, generate change summaries and alerts
Not just display current data, but detect anomalies and flag risks through historical snapshot comparison
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.cache import get, set
from utils.mcp_client import call_tool_json
from utils.platform_utils import get_cache_dir

_CACHE = get_cache_dir()
WATCHLIST = _CACHE / "watchlist.json"
SNAPSHOT_DIR = _CACHE / "snapshots"


def load_watchlist() -> dict:
    if WATCHLIST.exists():
        return json.loads(WATCHLIST.read_text(encoding="utf-8"))
    return {"asins": [], "keywords": [], "categories": []}


def save_watchlist(data: dict):
    WATCHLIST.parent.mkdir(parents=True, exist_ok=True)
    WATCHLIST.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_item(item_type: str, value: str, platform: str = "amazon", site: str = "US"):
    wl = load_watchlist()
    entry = {"value": value, "platform": platform, "site": site}
    arr = wl.setdefault(item_type + "s", [])
    if entry not in arr:
        arr.append(entry)
    save_watchlist(wl)
    print(f"Added {item_type}: {value} ({platform.upper()} {site})")


def _snapshot_path(tool_name: str, params: dict) -> Path:
    params_hash = hashlib.md5(json.dumps(params, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    return SNAPSHOT_DIR / f"{tool_name}_{params_hash}.json"


def load_snapshot(tool_name: str, params: dict) -> dict | None:
    sp = _snapshot_path(tool_name, params)
    if sp.exists():
        return json.loads(sp.read_text(encoding="utf-8"))
    return None


def save_snapshot(tool_name: str, params: dict, data: dict):
    sp = _snapshot_path(tool_name, params)
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "params": params,
        "data": data,
    }
    sp.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")


def _to_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _unwrap(d: dict) -> dict:
    """product_detail and similar tools return {"doc":..., "data":{...}} envelope — extract inner data"""
    if isinstance(d, dict) and "doc" in d and isinstance(d.get("data"), dict):
        return d["data"]
    return d


def compare_product(current: dict, previous: dict | None) -> list:
    """Compare ASIN details, return alert list"""
    alerts = []
    if not previous:
        return alerts

    prev_data = _unwrap(previous.get("data", {}))

    price = _to_float(current.get("price"))
    prev_price = _to_float(prev_data.get("price"))
    if price is not None and prev_price is not None and prev_price > 0:
        change_pct = (price - prev_price) / prev_price * 100
        if abs(change_pct) >= 10:
            direction = "Up" if change_pct > 0 else "Down"
            alerts.append(f"- **Price Change \U0001f525**: ${prev_price:.2f} -> ${price:.2f} ({direction} {abs(change_pct):.1f}%)")
        elif abs(change_pct) >= 5:
            direction = "Up" if change_pct > 0 else "Down"
            alerts.append(f"- Price Change: ${prev_price:.2f} -> ${price:.2f} ({direction} {abs(change_pct):.1f}%)")

    reviews = _to_float(current.get("review_count", current.get("ratings_count")))
    prev_reviews = _to_float(prev_data.get("review_count", prev_data.get("ratings_count")))
    if reviews is not None and prev_reviews is not None:
        growth = reviews - prev_reviews
        if growth >= 100:
            alerts.append(f"- **Review Surge ⚠️**: {int(prev_reviews)} -> {int(reviews)} (+{int(growth)})")
        elif growth > 5:
            alerts.append(f"- Reviews increased: {int(prev_reviews)} -> {int(reviews)} (+{int(growth)})")
        elif growth < 0:
            alerts.append(f"- Reviews decreased: {int(prev_reviews)} -> {int(reviews)} ({int(growth)})")

    rating = _to_float(current.get("star_rating", current.get("rating")))
    prev_rating = _to_float(prev_data.get("star_rating", prev_data.get("rating")))
    if rating is not None and prev_rating is not None:
        diff = rating - prev_rating
        if abs(diff) > 0.1:
            direction = "Rise" if diff > 0 else "Decline"
            alerts.append(f"- **Rating {direction} ⚠️**: {prev_rating:.2f} -> {rating:.2f} ({direction} {abs(diff):.2f})")

    sales = _to_float(current.get("monthly_sales_volume", current.get("month_sales_volume")))
    prev_sales = _to_float(prev_data.get("monthly_sales_volume", prev_data.get("month_sales_volume")))
    if sales is not None and prev_sales is not None and prev_sales > 0:
        change_pct = (sales - prev_sales) / prev_sales * 100
        if abs(change_pct) >= 20:
            direction = "Up" if change_pct > 0 else "Down"
            alerts.append(f"- Monthly Sales Significant Change: {int(prev_sales)} -> {int(sales)} ({direction} {abs(change_pct):.1f}%)")

    return alerts


def compare_keyword(current: dict, previous: dict | None) -> list:
    """Compare keyword details, return alert list"""
    alerts = []
    if not previous:
        return alerts

    prev_data = _unwrap(previous.get("data", {}))

    vol = _to_float(current.get("monthly_search_volume", current.get("search_volume")))
    prev_vol = _to_float(prev_data.get("monthly_search_volume", prev_data.get("search_volume")))
    if vol is not None and prev_vol is not None and prev_vol > 0:
        change_pct = (vol - prev_vol) / prev_vol * 100
        if abs(change_pct) >= 15:
            direction = "Up" if change_pct > 0 else "Down"
            alerts.append(f"- **Search Volume Significant Change \U0001f4c8**: {int(prev_vol)} -> {int(vol)} ({direction} {abs(change_pct):.1f}%)")

    cpc = _to_float(current.get("recommended_cpc_bid", current.get("cpc")))
    prev_cpc = _to_float(prev_data.get("recommended_cpc_bid", prev_data.get("cpc")))
    if cpc is not None and prev_cpc is not None and prev_cpc > 0:
        change_pct = (cpc - prev_cpc) / prev_cpc * 100
        if abs(change_pct) >= 15:
            direction = "Up" if change_pct > 0 else "Down"
            alerts.append(f"- **CPC Significant Change \U0001f4b0**: ${prev_cpc:.2f} -> ${cpc:.2f} ({direction} {abs(change_pct):.1f}%)")

    return alerts


def daily_report(alert_only: bool = False):
    wl = load_watchlist()
    if not alert_only:
        print("# Sorftime Daily Monitoring Report")
        print()

    any_alert = False

    for entry in wl.get("asins", []):
        val = entry["value"]
        site = entry.get("site", "US")
        params = {"amz_site": site, "asin": val}
        prev = load_snapshot("product_detail", params)

        try:
            data = _unwrap(call_tool_json("product_detail", params))
            alerts = compare_product(data, prev)
            save_snapshot("product_detail", params, data)

            if not alerts:
                with (_CACHE / "monitor.log").open("a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat(timespec='seconds')} {val} "
                            f"price={data.get('price', 'N/A')} sales={data.get('monthly_sales_volume', 'N/A')} "
                            f"rating={data.get('star_rating', 'N/A')} reviews={data.get('review_count', 'N/A')} No significant change\n")

            if alert_only and not alerts:
                continue

            any_alert = True
            print(f"## ASIN: {val}")
            print(f"- Price: {data.get('price', 'N/A')}")
            print(f"- Monthly Sales: {data.get('monthly_sales_volume', data.get('month_sales_volume', 'N/A'))}")
            print(f"- Rating: {data.get('star_rating', data.get('rating', 'N/A'))}")
            print(f"- Review Count: {data.get('review_count', 'N/A')}")
            if alerts:
                print()
                for a in alerts:
                    print(a)
            elif not alert_only:
                print("- Status: No significant change")
            print()
        except Exception as e:
            if not alert_only:
                print(f"## ASIN: {val}")
                print(f"- Fetch failed: {e}")
                print()

    for entry in wl.get("keywords", []):
        val = entry["value"]
        site = entry.get("site", "US")
        params = {"keyword_support_site": site, "keyword": val}
        prev = load_snapshot("keyword_detail", params)

        try:
            data = _unwrap(call_tool_json("keyword_detail", params))
            alerts = compare_keyword(data, prev)
            save_snapshot("keyword_detail", params, data)

            if alert_only and not alerts:
                continue

            any_alert = True
            print(f"## Keyword: {val}")
            print(f"- Monthly Search Volume: {data.get('monthly_search_volume', data.get('search_volume', 'N/A'))}")
            print(f"- CPC: {data.get('recommended_cpc_bid', data.get('cpc', 'N/A'))}")
            if alerts:
                print()
                for a in alerts:
                    print(a)
            elif not alert_only:
                print("- Status: No significant change")
            print()
        except Exception as e:
            if not alert_only:
                print(f"## Keyword: {val}")
                print(f"- Fetch failed: {e}")
                print()

    if alert_only and not any_alert:
        print("No monitored items triggering alerts.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="daily", choices=["daily", "add", "alert"])
    parser.add_argument("--type", default="", choices=["asin", "keyword", "category"])
    parser.add_argument("--value", default="")
    parser.add_argument("--platform", default="amazon")
    parser.add_argument("--site", default="US")
    args = parser.parse_args()

    if args.mode == "add":
        if not args.type or not args.value:
            print("Error: --type and --value are required for add mode", file=sys.stderr)
            sys.exit(1)
        add_item(args.type, args.value, args.platform, args.site)
    elif args.mode == "alert":
        daily_report(alert_only=True)
    else:
        daily_report(alert_only=False)


if __name__ == "__main__":
    main()
