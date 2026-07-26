#!/usr/bin/env python3
"""
Intent Router + Seller Stage Detection
Extracts from natural language: platform, marketplace, analysis mode, seller stage, key entities
Bilingual: supports both English and Chinese input
"""

import argparse
import json
import re
import sys

PLATFORM_MAP = {
    "amazon": ["amazon", "amz", "亚马逊"],
    "tiktok": ["tiktok", "tiktok shop", "tt", "抖音电商"],
    "shopee": ["shopee", "虾皮"],
    "temu": ["temu", "特姆"],
    "walmart": ["walmart", "沃尔玛", "wm"],
}

MODE_MAP = {
    "blueocean": [
        # English
        "blue ocean", "opportunity", "potential", "discover", "find product",
        "product discovery", "sourcing", "hidden profit", "hidden gem",
        # Chinese
        "蓝海", "机会", "潜力", "选品", "找产品", "隐赚",
    ],
    "competitor": [
        # English
        "competitor", "asin", "rival", "deep dive", "analyze this product",
        "this asin", "competitor analysis", "competitor research",
        # Chinese
        "竞品", "对手", "拆解", "分析这个产品", "这个 asin", "竞品分析",
    ],
    "keyword": [
        # English
        "keyword", "traffic keyword", "seo", "search term", "cpc", "bid",
        "keyword research", "keyword optimization", "long tail",
        # Chinese
        "关键词", "流量词", "搜索词", "竞价",
    ],
    "market": [
        # English
        "market", "category", "industry", "niche", "segment", "market analysis",
        "category analysis", "market research",
        # Chinese
        "市场", "类目", "行业", "赛道",
    ],
    "monitor": [
        # English
        "monitor", "daily report", "alert", "track", "watch",
        # Chinese
        "监控", "日报", "预警", "跟踪",
    ],
    "profit": [
        # English
        "profit", "margin", "break even", "fba fee", "logistics cost",
        "profitability", "roi", "calculate", "cost analysis",
        # Chinese
        "利润", "算账", "毛利率", "fba费用", "物流成本", "盈亏",
    ],
}

SITE_HINTS = {
    "US": ["us", "usa", "united states", "america", "美国", "美站", "amazon.com"],
    "UK": ["uk", "united kingdom", "britain", "英国", "英站", "amazon.co.uk"],
    "DE": ["de", "germany", "德国", "德站", "amazon.de"],
    "JP": ["jp", "japan", "日本", "日站", "amazon.co.jp"],
    "CA": ["ca", "canada", "加拿大", "加站", "amazon.ca"],
    "FR": ["fr", "france", "法国", "法站", "amazon.fr"],
    "IT": ["it", "italy", "意大利", "意站", "amazon.it"],
    "ES": ["es", "spain", "西班牙", "西站", "amazon.es"],
    "AU": ["au", "australia", "澳大利亚", "澳站", "amazon.com.au"],
    "IN": ["in", "india", "印度", "印站", "amazon.in"],
    "MX": ["mx", "mexico", "墨西哥", "墨站", "amazon.com.mx"],
    "BR": ["br", "brazil", "巴西", "巴站", "amazon.com.br"],
}

STAGE_SIGNALS = {
    "newbie": [
        # English
        "beginner", "newbie", "first time", "no experience", "just started",
        "getting started", "new to", "learning", "starter",
        # Chinese
        "新手", "刚入门", "第一次", "没经验", "小白", "从零开始", "初学者", "刚做",
    ],
    "grower": [
        # English
        "growing", "scaling", "monthly sales", "expand", "team", "acos",
        "ad optimization", "growth", "intermediate",
        # Chinese
        "做了半年", "月销", "扩品类", "团队", "广告优化", "成长期", "上升期",
    ],
    "pro": [
        # English
        "brand", "multi-store", "erp", "api", "batch", "automation",
        "supply chain", "enterprise", "mature", "advanced", "professional",
        # Chinese
        "品牌", "多店铺", "批量", "自动化", "供应链", "成熟", "大公司",
    ],
}

CATEGORY_EXPLICIT_SIGNALS = [
    # English
    "category", "industry", "niche", "segment", "vertical",
    "i want to sell", "specifically in", "only in", "limited to",
    "focused on", "specialized in",
    # Chinese
    "类目", "行业", "赛道", "大类", "细分类目",
    "我要做", "专门做", "只做", "限定在", "限制在",
]

RISKY_CATEGORY_KEYWORDS = {
    # English category names + Chinese
    "food": ["food", "grocery", "食品", "零食"],
    "beverage": ["beverage", "drink", "饮料", "饮品"],
    "supplement": ["supplement", "vitamin", "保健品", "补剂"],
    "cosmetics": ["cosmetics", "makeup", "skincare", "化妆品", "护肤品"],
    "medical": ["medical", "healthcare", "医疗器械", "医疗"],
    "electronics": ["electronics", "electronic", "电子", "电器"],
    "clothing": ["clothing", "apparel", "服装", "衣服"],
    "shoes": ["shoes", "footwear", "鞋", "鞋类"],
}


def detect_platform(text: str) -> str:
    t = text.lower()
    for platform, hints in PLATFORM_MAP.items():
        for h in hints:
            if h in t:
                return platform
    return "amazon"  # default


def detect_mode(text: str) -> str:
    t = text.lower()
    scores = {}
    for mode, hints in MODE_MAP.items():
        scores[mode] = sum(1 for h in hints if h in t)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "blueocean"


def detect_site(text: str, platform: str) -> str:
    t = text.lower()
    for site, hints in SITE_HINTS.items():
        for h in hints:
            if h in t:
                return site
    defaults = {"amazon": "US", "tiktok": "US", "shopee": "TW", "temu": "US", "walmart": "US"}
    return defaults.get(platform, "US")


def detect_stage(text: str) -> str:
    t = text.lower()
    scores = {}
    for stage, hints in STAGE_SIGNALS.items():
        scores[stage] = sum(1 for h in hints if h in t)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "grower"


def detect_explicit_category(text: str) -> dict:
    """Detect if user explicitly specified a category, and whether they requested high-risk ones"""
    t = text.lower()
    is_explicit = any(sig in t for sig in CATEGORY_EXPLICIT_SIGNALS)

    requested_risky = []
    for category, keywords in RISKY_CATEGORY_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            requested_risky.append(category)

    return {
        "explicit_category": is_explicit or bool(requested_risky),
        "requested_risky_categories": requested_risky,
    }


def extract_asin(text: str) -> list:
    """Extract ASIN / productId"""
    pattern = r"\b[Bb][0-9A-Za-z]{9}\b"
    return re.findall(pattern, text)


def extract_keywords(text: str) -> list:
    """Extract quoted or structured keywords"""
    # Chinese quotes
    quotes = re.findall(r'[「""""]([^""""]+)[""""」]', text)
    if quotes:
        return quotes
    # English quotes
    eq = re.findall(r'"([^"]+)"', text)
    if eq:
        return eq
    return []


def route(text: str) -> dict:
    platform = detect_platform(text)
    mode = detect_mode(text)
    site = detect_site(text, platform)
    stage = detect_stage(text)
    asins = extract_asin(text)
    keywords = extract_keywords(text)
    cat_info = detect_explicit_category(text)

    # Recommend tool combinations based on mode and stage
    if platform == "walmart":
        recommendations = {
            "blueocean": {
                "newbie": ["walmart_keyword_search_results", "walmart_keyword_extends"],
                "grower": ["walmart_keyword_search_results", "walmart_keyword_extends"],
                "pro": ["walmart_keyword_search_results", "walmart_keyword_extends"],
            },
            "competitor": {
                "newbie": ["walmart_product_detail_by_product_id", "walmart_product_traffic_terms"],
                "grower": ["walmart_product_detail_by_product_id", "walmart_product_traffic_terms", "walmart_product_trend_by_product_id"],
                "pro": ["walmart_product_detail_by_product_id", "walmart_product_traffic_terms", "walmart_product_trend_by_product_id"],
            },
            "keyword": {
                "newbie": ["walmart_keyword_detail", "walmart_keyword_search_results"],
                "grower": ["walmart_keyword_detail", "walmart_keyword_extends", "walmart_keyword_search_results"],
                "pro": ["walmart_keyword_extends", "walmart_keyword_search_results", "walmart_keyword_detail"],
            },
            "market": {
                "newbie": ["walmart_category_report_by_node_id"],
                "grower": ["walmart_category_report_by_node_id", "walmart_keyword_search_results"],
                "pro": ["walmart_category_report_by_node_id", "walmart_keyword_search_results"],
            },
            "monitor": {
                "grower": ["walmart_product_detail_by_product_id"],
                "pro": ["walmart_product_detail_by_product_id", "walmart_category_report_by_node_id"],
            },
            "profit": {
                "newbie": ["walmart_product_detail_by_product_id"],
                "grower": ["walmart_product_detail_by_product_id", "walmart_keyword_detail"],
                "pro": ["walmart_product_detail_by_product_id", "walmart_keyword_detail"],
            },
        }
    else:
        recommendations = {
            "blueocean": {
                "newbie": ["potential_product", "category_report", "product_search"],
                "grower": ["category_report", "product_search", "potential_product"],
                "pro": ["product_search", "potential_product", "category_report"],
            },
            "competitor": {
                "newbie": ["product_detail", "product_reviews"],
                "grower": ["product_detail", "product_reviews", "product_traffic_terms", "competitor_product_keywords"],
                "pro": ["product_detail", "product_traffic_terms", "competitor_product_keywords", "product_variations"],
            },
            "keyword": {
                "newbie": ["keyword_detail", "keyword_search_results"],
                "grower": ["keyword_detail", "keyword_extends", "keyword_search_results"],
                "pro": ["keyword_extends", "competitor_product_keywords", "keyword_detail"],
            },
            "market": {
                "newbie": ["category_name_search", "category_report"],
                "grower": ["category_report", "product_search", "category_search_from_top_node"],
                "pro": ["category_report", "product_search", "similar_product_feature"],
            },
            "monitor": {
                "grower": ["product_detail", "keyword_detail"],
                "pro": ["product_detail", "keyword_detail", "category_report"],
            },
            "profit": {
                "newbie": ["product_detail"],
                "grower": ["product_detail", "keyword_detail"],
                "pro": ["product_detail", "keyword_detail"],
            },
        }

    tools = recommendations.get(mode, {}).get(stage, ["product_search"])

    # Prioritize hidden profit index if explicitly mentioned
    if any(h in text.lower() for h in ["hidden profit", "potential_product", "potential index", "隐赚", "potential"]):
        if "potential_product" not in tools:
            tools.insert(0, "potential_product")

    missing = []
    if mode in ("blueocean", "market", "keyword") and not keywords and not asins:
        missing.append("Please provide a keyword or category name for accurate analysis")
    if mode == "competitor":
        if platform == "walmart" and not asins:
            missing.append("Please provide the Walmart ProductId to analyze")
        elif platform != "walmart" and not asins:
            missing.append("Please provide the ASIN to analyze")

    return {
        "platform": platform,
        "site": site,
        "mode": mode,
        "seller_stage": stage,
        "asins": asins,
        "keywords": keywords,
        "recommended_tools": tools,
        "missing_info": missing,
        "original_text": text,
        "explicit_category": cat_info["explicit_category"],
        "requested_risky_categories": cat_info["requested_risky_categories"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True, help="User input text")
    args = parser.parse_args()
    result = route(args.text)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
