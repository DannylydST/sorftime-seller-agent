"""
Formatting utilities: format MCP-returned data into seller-friendly Markdown summaries
"""

import json
from typing import Any, Dict, List, Optional


def _safe_get(item: dict, keys: list, default="") -> Any:
    for k in keys:
        if k in item:
            return item[k]
    return default


def fmt_competitor_brief(asin: str, detail: Any, reviews: Any, traffic: Any) -> str:
    """Generate competitor analysis brief"""
    lines = [f"# Competitor Analysis Report: {asin}", ""]

    # Product details
    if isinstance(detail, dict):
        title = _safe_get(detail, ["title", "Product Name"])
        price = _safe_get(detail, ["price", "Current Price"])
        sales = _safe_get(detail, ["monthly_sales_volume", "month_sales_volume", "Sales Volume"])
        rating = _safe_get(detail, ["star_rating", "Star Rating"])
        review_count = _safe_get(detail, ["review_count", "Review Count"])
        brand = _safe_get(detail, ["brand", "Brand Name"])
        category = _safe_get(detail, ["category", "Category"])

        lines.append("## Product Details")
        if title:
            lines.append(f"- **Title**: {title}")
        if brand:
            lines.append(f"- **Brand**: {brand}")
        if category:
            lines.append(f"- **Category**: {category}")
        if price:
            lines.append(f"- **Price**: {price}")
        if sales:
            lines.append(f"- **Monthly Sales**: {sales}")
        if rating:
            lines.append(f"- **Rating**: {rating}")
        if review_count:
            lines.append(f"- **Reviews**: {review_count}")
        lines.append("")
    else:
        lines.append("## Product Details")
        lines.append("> No detail data available")
        lines.append("")

    # Review summary
    if isinstance(reviews, dict):
        review_summary = _safe_get(reviews, ["summary", "review_summary"])
        if review_summary:
            lines.append("## Review Summary")
            lines.append(str(review_summary))
            lines.append("")
    elif isinstance(reviews, list) and reviews:
        lines.append(f"## Review Samples ({len(reviews)} items)")
        for r in reviews[:3]:
            content = _safe_get(r, ["content", "Review Content"])[:60]
            stars = _safe_get(r, ["stars", "star_rating", "Star Rating"])
            lines.append(f"- {'⭐' * int(stars) if stars and str(stars).isdigit() else ''} {content}...")
        lines.append("")

    # Traffic keyword summary
    if isinstance(traffic, list) and traffic:
        lines.append("## Traffic Keywords Top 10")
        lines.append("| Keyword | Rank | Search Volume |")
        lines.append("|---------|------|---------------|")
        for t in traffic[:10]:
            if isinstance(t, dict):
                kw = _safe_get(t, ["keyword", "Keyword"])
                rank = _safe_get(t, ["rank", "Rank"])
                vol = _safe_get(t, ["search_volume", "Search Volume"])
                lines.append(f"| {kw} | {rank} | {vol} |")
        lines.append("")
    elif isinstance(traffic, dict):
        lines.append("## Traffic Keywords")
        text = json.dumps(traffic, ensure_ascii=False, indent=2)
        if len(text) > 600:
            text = text[:600] + "\n... (truncated)"
        lines.append(f"```json\n{text}\n```")
        lines.append("")

    return "\n".join(lines)
