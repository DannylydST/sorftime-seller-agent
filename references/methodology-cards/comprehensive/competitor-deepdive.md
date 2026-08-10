# Competitor Deep Dive

> Type: Tactical | Seller Stage: Growing / Professional | Platform: Amazon / Walmart

## Core Logic

Competitor analysis is not about listing "who is selling." It is about quantifying threat levels for each competitor -- a high-volume seller with poor ratings is less threatening than a mid-volume seller with strong ratings and comprehensive keyword coverage.

## Methodology Principles

The traditional mistake in competitor analysis is "single-metric absolutism": ranking opponents solely by monthly sales, benchmarking solely by price, judging quality solely by rating. The consequences of this hard-threshold mindset:

- Low-price, high-volume sellers are over-emphasized (their actual margins are thin; they pose no long-term threat).
- High-rating, mid-volume "quietly profitable" players are overlooked.
- Emerging threats (those with rapid review velocity) go undetected early.

Sorftime's Competitive Threat Index is a textbook application of full-ranking:

```
Threat Index = α x Monthly Sales (normalized) + β x Keyword Overlap Rate + γ x Rating Gap Score
             + δ x Review Velocity + ε x Price Band Overlap + ζ x Variant Coverage
             + η x Estimated Ad Penetration + θ x Brand Moat Score

Where α + β + γ + δ + ε + ζ + η + θ = 1, dynamically adjusted by the seller's product positioning.
```

- The Threat Index is a continuous 0-100 value. All competitors are ranked and visible.
- There is no hard threshold like "don't analyze competitors with monthly sales below 500." A competitor with 200 monthly sales but 80% keyword overlap (highly homogeneous) may have a higher Threat Index than a differentiated competitor with 1000 monthly sales.
- Weights are adjustable: a "blockbuster" strategy increases α (sales weight); a differentiation strategy increases β (keyword overlap weight).

## Trigger Scenarios

- "Analyze this ASIN's competitors"
- "Who is competing for my traffic?"
- "Identify the 5 most threatening competitors"
- "What weaknesses does this competitor have that I can exploit?"

## Conversational Execution (agent-x / MCP Channel)

### Step 1: Full Pull --> Competitor Teardown
```bash
python3 scripts/analyst.py --mode competitor --platform amazon --site US --asin "B0XXXXXXXX"
```
`analyst.py --mode competitor` pulls the target ASIN's detail, traffic keywords, and
competitor keyword overlap in a single call. No hard threshold -- even competitors with
extremely low monthly sales are visible in the ranking.

### Step 2: Deep Dive into Top Competitors
```bash
# analyst.py --mode competitor already returns, per ASIN:
#   product_detail  (price / sales / rating / FBA / seller)
#   product_traffic_terms  (traffic-driving keywords + exposure position)
#   competitor_product_keywords  (keyword overlap)
# For reviews, call the MCP tool directly (capped at 100, no pagination):
python3 scripts/sorftime_bridge.py --one-shot product_reviews '{"amz_site":"US","asin":"B0YYYYYYYY","review_type":"Both"}'
```

Layer-by-layer deep dive:
- **Traffic terms**: View the competitor's core traffic-driving keywords and their traffic structure (head terms vs. long-tail vs. brand-term-only).
- **Keyword overlap**: See which keywords the competitor ranks for, and calculate overlap with your own product.
- **Reviews (max 100)**: `product_reviews` is capped at 100 reviews with no `page` parameter -- use `review_type` (`Both`/`Positive`/`Negative`) to sample different sentiment buckets for negative-review vulnerability analysis.

### Step 3: Cross-Validation
- Use ProductRequest to confirm the competitor's FBA fees and pricing strategy; estimate their margin structure.
- If a competitor has broad keyword coverage but a consistently declining rating (negative review trend), they are a "paper tiger" -- high short-term sales but unsustainable.
- ❌ Common mistake: Only analyzing the top 3 competitors. After ranking by Threat Index, positions 7-8 in the top 10 are often the "best attack targets" -- they have volume but clear, exploitable weaknesses.

## Interpretation Framework

1. **High-threat competitor common traits**: High keyword overlap + small rating gap (< 0.3) = for every keyword you hold, they are also in the top 10. These are your most direct traffic competitors. High-volume competitors with low keyword overlap operate in a "different lane" and pose no direct threat.

2. **"Grey Zone" competitors ⭐** (threats invisible to hard-threshold systems):
   - Monthly sales 300, rating 4.6, 70% keyword overlap with you -- the "small but mighty" seller. In hard-threshold systems sorted by sales volume, they might sit beyond position 30 and go unnoticed, but in Sorftime's Threat Index they rank top 10.
   - Rapid review velocity from new products (50+ reviews/month average) -- current sales are not high but momentum is strong; these are "future threats."

3. **Attack opportunities** (competitor negative-review analysis):
   - High-threat competitors with negative review rate > 15% --> Attack vector: quality disputes.
   - Competitor negative reviews concentrated on "size doesn't match" or "missing accessories" --> If your product has an edge in these areas, feature it directly in your listing and A+ content.
   - Competitor differentiated keyword density is low --> You can avoid head-to-head competition via long-tail keywords.

## Risk Notes

- Competitor data is inherently about "visible competition." FBA inventory levels, off-platform advertising, and brand influence are not covered by the 8 dimensions.
- The Threat Index is a ranking recommendation tool, not an automated decision engine. Weight settings require manual verification, especially Estimated Ad Penetration (inferred from ad share on SERP; subject to sampling error).
- Review sentiment analysis is based on limited pages (1-3 pages). For high-volume competitors, the distribution of the most recent reviews may deviate from the overall pattern.

## Workflow Chain

This Card --> Keyword Strategy Optimization (use keyword overlap results to build attack/evasion strategies) --> Blue Ocean Opportunity Discovery (enter through sub-niches where competitors have weak coverage)

Typical flow: Identify top 5 competitors by Threat Index --> Analyze their traffic-driving keyword structure --> Discover a keyword cluster where all competitors have weak coverage --> Validate that cluster's market space via the Blue Ocean card.
