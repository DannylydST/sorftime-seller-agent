#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Candidate ASIN Verification — batch `product_detail` reality-check for the review pipeline.

Hardened v3.6.1 — the three pitfalls this avoids:
  1. In-process `call_tool_json` (NOT `subprocess.run(["python3", ...])` — on Windows the
     `python3` in a subprocess resolves to the Microsoft Store stub, not real Python).
  2. Auto-unwraps the `{"doc": <field descriptions>, "data": <real values>}` envelope —
     reading title/price from the top-level dict returns the doc text, not values.
  3. Key-tolerant field extraction (snake_case + PascalCase fallbacks).

Also: per-ASIN retry with backoff + stagger between calls (batch concurrency blows the API).

Usage:
  python3 scripts/verify_candidates.py --input asins.txt --out verify_raw.json
  python3 scripts/verify_candidates.py --input asins.json --out verify_raw.json
  # asins.txt  = one ASIN per line (blank/comment lines ignored)
  # asins.json = a list of strings, or a list of {"asin": ...} dicts
  # --brief    = also print a compact per-ASIN summary table
"""
import argparse
import json
import sys
import time
from pathlib import Path

# Windows GBK console cannot print emoji. Force UTF-8.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.mcp_client import call_tool_json


def load_asins(path: str):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = None
    if isinstance(data, list):
        asins = []
        for item in data:
            if isinstance(item, str):
                asins.append(item.strip())
            elif isinstance(item, dict):
                a = item.get("asin") or item.get("ASIN") or item.get("product_id")
                if a:
                    asins.append(str(a).strip())
        return [a for a in asins if a]
    # plain text: one ASIN per line
    asins = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    return asins


def fetch(asin: str, retries: int = 3):
    """In-process product_detail fetch with retry + backoff. Returns the unwrapped data."""
    for attempt in range(1, retries + 1):
        try:
            r = call_tool_json("product_detail", {"amz_site": "US", "asin": asin})
            if isinstance(r, dict) and r.get("_error"):
                raise RuntimeError(r["_error"])
            # unwrap {"doc":..., "data":...} envelope — `data` holds the real values
            if isinstance(r, dict) and "data" in r:
                return r["data"]
            return r
        except Exception as e:
            if attempt < retries:
                time.sleep(8 * attempt)  # backoff
            else:
                return {"_error": str(e)[:200]}


def g(d, *keys, default=""):
    """Key-tolerant field lookup."""
    if not isinstance(d, dict):
        return default
    for k in keys:
        if k in d and d[k] not in (None, "", []):
            return d[k]
    return default


def brief(asin: str, d: dict) -> str:
    """Compact one-ASIN summary (mirrors the round workflow's review fields)."""
    if not isinstance(d, dict):
        return f"{asin}: RAW {str(d)[:150]}"
    if d.get("_error"):
        return f"{asin}: ERROR {d['_error']}"
    title = str(g(d, "title", "Title", "product_title"))[:70]
    price = g(d, "price", "Price", "current_price")
    sales = g(d, "monthly_sales_volume", "month_sales_volume", "ListingSalesVolumeOfMonth")
    rating = g(d, "star_rating", "rating", "Ratings")
    reviews = g(d, "review_count", "review_number", "ReviewsCount")
    fba = g(d, "fba_fee", "FBAFee", "estimated_fba_fee")
    wgt = g(d, "weight_g", "weight", "Weight")
    pkg = g(d, "package_size_cm", "package_dimension")
    online = g(d, "online_date", "listing_date", "FirstAvailableDate")
    var = g(d, "variation_count", "variations")
    cat = g(d, "top_category", "category", "Category")
    sub = g(d, "subcategory", "sub_category", "Subcategory")
    lines = [f"ASIN {asin} | {title}",
             f"  price={price} sales={sales} {rating}*/{reviews}评 FBA={fba} wgt_g={wgt} online={online} var={var}"]
    if cat:
        lines.append(f"  cat={cat} | sub={sub}")
    if pkg:
        lines.append(f"  package_cm={pkg}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Batch product_detail ASIN verification")
    parser.add_argument("--input", required=True, help="asins.txt (one per line) or asins.json")
    parser.add_argument("--out", default="verify_raw.json", help="Output JSON (merges if exists)")
    parser.add_argument("--stagger", type=float, default=2.0, help="Seconds between calls (anti rate-limit)")
    parser.add_argument("--retries", type=int, default=3, help="Per-ASIN retries")
    parser.add_argument("--brief", action="store_true", help="Also print compact summary")
    parser.add_argument("--site", default="US", help="Marketplace site (default US)")
    args = parser.parse_args()

    asins = load_asins(args.input)
    if not asins:
        print("No ASINs found in input.")
        sys.exit(1)
    print(f"> Verifying {len(asins)} ASINs (site {args.site})...")

    results = {}
    for i, asin in enumerate(asins, 1):
        results[asin] = fetch(asin, args.retries)
        if args.stagger and i < len(asins):
            time.sleep(args.stagger)  # 错峰 — batch concurrency blows the API
        print(f"[{i}/{len(asins)}] {asin} done", flush=True)

    # Merge into existing output (multi-batch support)
    out = Path(args.out)
    merged = {}
    if out.exists():
        try:
            merged = json.loads(out.read_text(encoding="utf-8"))
        except Exception:
            merged = {}
    merged.update(results)
    out.write_text(json.dumps(merged, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"saved {out} (total {len(merged)} ASINs)")

    if args.brief:
        print("\n" + "=" * 90)
        for asin in asins:
            print(brief(asin, results.get(asin) or {}))
            print("=" * 90)
    return 0


if __name__ == "__main__":
    sys.exit(main())
