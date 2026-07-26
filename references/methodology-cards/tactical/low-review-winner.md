# Low Rating Replacement Opportunity

> Category: Tactical Strategy | Seller Stage: Beginner+ | Platform: Amazon/Walmart

## Core Logic
High sales + low rating = validated demand + subpar product experience → You build a better version and intercept the traffic directly.

## Methodology

**Key Distinction: Full-Ranking vs Hard-Threshold Filtering**

Traditional methods (including many competitor tools) use hard thresholds for product discovery:
```
minRating <= 4.2  AND  monthlySales >= 1000  AND  reviewCount >= 50
```
A product with 980 monthly sales and a 4.3 rating gets filtered out — it's only 20 units and 0.1 points shy of the threshold, yet it's a great target with a rating slightly below category average but stable demand.

Sorftime's **Replacement Opportunity Index ⭐** uses full-ranking:
```
Replacement Opportunity Index = Monthly Sales x (5 - Rating) x Review Count Modifier
```
Every product participates in the ranking — a product with 980 monthly sales simply "scores 98 on the sales dimension," and a 4.3 rating yields (5-4.3)=0.7 on the "rating gap" dimension. The composite score can still rank high. **No hard threshold, only composite score.**

Comparison with Sorftime's `hot-low-rating` preset:
- `hot-low-rating`: hard thresholds `maxRating<=4.2, minUnits>=1000` — the result set is a discrete "pass/fail"
- Replacement Opportunity Index: full-ranking; products below 1000 units just score slightly lower and can still make the list

**Why these products are valuable**: Customers have already voted with their wallets (high sales), but reviews repeatedly complain about a specific flaw (low rating). You build an improved version — standing on the shoulders of giants.

## Trigger Phrases
- "Are there products that sell well but have terrible reviews?"
- "Find me improvement opportunities"
- "What problems do negative reviews focus on?"
- "Which category is easiest to enter?"

## Execution Steps

### Conversation Mode (agent-x)
```
Step 1: ProductSearch --category <categoryID> --sort-by replacement_index --limit 100
        → Sort by Replacement Opportunity Index descending, full ranking
        → Obtain a candidate list of "high sales / low rating" products

Step 2: ProductReviewsQuery --asins ASIN1,ASIN2,...ASIN10 --sort-by recency --limit 20
        → Deep-read the latest negative reviews for each candidate ASIN
        → Extract negative review keywords (quality/packaging/functionality/after-sales...)

Step 3: analyst.py --asins ASIN1,ASIN2 --detail
        → Confirm margin headroom — if the existing margin is already razor-thin, an improved version is pointless
```

## Interpretation Notes
1. Top products: high sales, rating significantly below category average (typically 0.5+ lower than category mean)
2. **Grey Zone Gems**: Products with 800-1200 monthly sales and 4.0-4.3 ratings — competitor hard-threshold tools miss these, but they are often the best improvement targets: "good product concept, flawed execution"
3. Red flags: If negative reviews concentrate on "insufficient features" rather than "quality defects," it means demand is upgrading rather than the product being flawed — improvement costs are higher

## Risk Notes
- ⭐ The Replacement Opportunity Index **does not include patent risk detection**! A patent search is mandatory before proceeding
- Low ratings may stem from a ruined brand reputation — not something an improved product can fix
- Not all low ratings are improvable: some pain points (size, material) are dictated by the cost structure and may be beyond your reach

## Combo Strategy
This Strategy → Brand Gap Entry (assess the category's brand landscape) → Keyword Scatter (find traffic entry points) → Hidden Profit Index (validate profit) → Launch
