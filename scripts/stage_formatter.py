#!/usr/bin/env python3
"""
Output Formatter — formats analysis results by seller stage
Principle: prepend/preface/summarize, never modify the original data tables
"""

import argparse
import re
import sys


TERM_GLOSSARY = {
    "Monopoly": "A few brands dominate most sales; newcomers face steep barriers.",
    "Monopoly Coefficient": "Top 3 brands' combined market share. Higher = more dominated by incumbents.",
    "CPC": "Cost Per Click — how much you pay per ad click. Higher CPC = more expensive advertising.",
    "FBA": "Fulfillment by Amazon — Amazon handles storage, packing, and shipping for you.",
    "FBM": "Fulfillment by Merchant — you handle storage and shipping yourself.",
    "Hidden Profit Index": "Sorftime's proprietary blue-ocean score. Higher = more untapped potential products in the search results.",
    "Return Rate": "Percentage of orders returned. High return rates seriously erode profit margins.",
    "Break-Even": "Break-even daily sales: minimum units you need to sell per day to cover costs.",
    "ASIN": "Amazon Standard Identification Number — Amazon's unique product identifier.",
    "Node ID": "Amazon category node's unique identifier for browsing and search.",
}


def extract_mentioned_terms(text: str) -> list:
    """Extract terms that appear in the text"""
    mentioned = []
    for term, definition in TERM_GLOSSARY.items():
        if re.search(re.escape(term), text, re.IGNORECASE):
            mentioned.append((term, definition))
    # Deduplicate, preserve order
    seen = set()
    result = []
    for t, d in mentioned:
        if t.lower() not in seen:
            seen.add(t.lower())
            result.append((t, d))
    return result


def fmt_beginner(text: str) -> str:
    lines = [text.rstrip()]
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Quick Start Guide")
    lines.append("")

    terms = extract_mentioned_terms(text)
    if terms:
        lines.append("### Glossary")
        lines.append("")
        for term, definition in terms:
            lines.append(f"- **{term}**: {definition}")
        lines.append("")

    lines.append("### Next Steps")
    lines.append("")
    if re.search(r"monopol|dominant", text, re.IGNORECASE):
        lines.append("- This category has high competition. Consider testing a more specific long-tail keyword, or find a differentiation angle.")
    if re.search(r"return rate|thin margin|low margin", text, re.IGNORECASE):
        lines.append("- Margins look thin or return risk is high. Start with a small test batch — don't commit to large inventory.")
    if re.search(r"opportunity|blue ocean|potential", text, re.IGNORECASE):
        lines.append("- Opportunity signal detected! Validate quickly: check 3-5 competitor listings to confirm there's room for improvement.")
    if len(lines) == 7:  # None of the above conditions matched
        lines.append("- Save this analysis. Next: compare 2-3 competitors, run a profit calculation, or set up price monitoring.")

    return "\n".join(lines)


def fmt_growing(text: str) -> str:
    bullets = []
    if re.search(r"monopol", text, re.IGNORECASE) and "40%" in text:
        bullets.append("- **Competition Risk**: Top brand concentration is high. Evaluate your differentiation feasibility before entering.")
    if re.search(r"Amazon Basics|self.operated|1P", text, re.IGNORECASE):
        bullets.append("- **Amazon Squeeze**: Amazon Basics/1P appears in top results — their low pricing may compress your margin.")
    if re.search(r"low.review.*high.*sales|reviews?\s*<\s*100", text, re.IGNORECASE):
        bullets.append("- **Opportunity Window**: Low-review, high-sales products found — potential to capture ranking quickly.")
    if re.search(r"price war|below\s*\$10|race to the bottom", text, re.IGNORECASE):
        bullets.append("- **Price War Zone**: Low-price red ocean detected. Consider avoiding or going premium/differentiated.")
    if re.search(r"margin", text, re.IGNORECASE):
        m = re.search(r"(?:gross\s+)?margin[::\s]*([\d.]+%)", text, re.IGNORECASE)
        if m:
            margin = float(m.group(1).replace("%", ""))
            if margin >= 30:
                bullets.append(f"- **Healthy Profit**: Gross margin {m.group(1)} — sufficient room for ad spend.")
            elif margin < 15:
                bullets.append(f"- **Tight Margin**: Gross margin {m.group(1)} — control costs and returns strictly.")
    if not bullets:
        bullets.append("- Data looks stable. Continue monitoring rankings and price changes.")

    header = ["## Key Takeaways", ""] + bullets + ["", "---", ""]
    return "\n".join(header) + text


def fmt_pro(text: str) -> str:
    # Executive summary: extract the most critical data points
    summary_lines = ["## Executive Summary", ""]

    if re.search(r"margin", text, re.IGNORECASE):
        m = re.search(r"(?:gross\s+)?margin\*?\*?[::\s]*([\d.]+%)", text, re.IGNORECASE)
        if m:
            summary_lines.append(f"- Gross Margin: {m.group(1)}")
    if re.search(r"break.even", text, re.IGNORECASE):
        m = re.search(r"break.even\*?\*?[::\s]*([^\n]+)", text, re.IGNORECASE)
        if m:
            summary_lines.append(f"- Break-Even: {m.group(1).strip()}")
    if re.search(r"monopol", text, re.IGNORECASE):
        summary_lines.append("- Competition: High brand concentration — differentiate or avoid.")
    if re.search(r"opportunity|blue ocean", text, re.IGNORECASE):
        summary_lines.append("- Opportunity: Actionable entry window exists — validate quickly.")
    if len(summary_lines) == 2:
        summary_lines.append("- Data summarized. See table below for details.")

    summary_lines.append("")
    summary_lines.append("---")
    summary_lines.append("")

    # Strip explanatory prose meant for beginners/growers
    cleaned = text
    cleaned = re.sub(r"Filter: reviews < \d+.*?barrier\.\n+", "", cleaned)
    cleaned = re.sub(r"## Quick Start Guide[\s\S]*", "", cleaned)

    footer = ["", "---", "", "## Scale Recommendations", "", "- If results are validated, connect Sorftime API for bulk export of similar product data.", "- Use `monitor.py` for automated tracking of prices, reviews, and ranking changes.", ""]

    return "\n".join(summary_lines) + cleaned + "\n".join(footer)


def format_by_stage(stage: str, text: str) -> str:
    stage = stage.lower().strip()
    if stage == "beginner" or stage == "newbie":
        return fmt_beginner(text)
    elif stage == "growing" or stage == "grower":
        return fmt_growing(text)
    elif stage == "professional" or stage == "pro":
        return fmt_pro(text)
    else:
        return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, choices=["beginner", "growing", "professional", "newbie", "grower", "pro"])
    parser.add_argument("--input", default="-", help="Input file path, defaults to stdin")
    args = parser.parse_args()

    if args.input == "-":
        text = sys.stdin.read()
    else:
        with open(args.input, "r", encoding="utf-8") as f:
            text = f.read()

    result = format_by_stage(args.stage, text)
    print(result)


if __name__ == "__main__":
    main()
