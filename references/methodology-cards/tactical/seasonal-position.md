# Peak Season Positioning

> Category: Tactical Strategy | Seller Stage: Growing+ | Platform: Amazon/Walmart

## Core Logic
Prepare inventory and position 2-3 months ahead of a seasonal demand surge, leveraging "first-mover advantage" to capture search rankings. — If you only start thinking about it when peak season arrives, the logistics window is already closed and ad costs have already doubled.

## Methodology

**Key Distinction: Full-Ranking vs Hard-Threshold Filtering**

Traditional seasonal product selection tools use fixed-rule judgments:
```
peak/offpeak_ratio >= 3.0  AND  "current month is 2 months before peak"  AND  categoryTrend is rising
```
A product with a peak/offpeak ratio of 2.8x but an exceptionally steep trend acceleration curve gets filtered — "ratio not met." In reality, 2.8x may simply be because the previous off-peak baseline was slightly higher than estimated, while the "trend acceleration" is actually greater, meaning this year's peak could far outpace last year's.

Sorftime's **Seasonal Boom Index ⭐** uses full-ranking:
```
Boom Index = Peak/Valley Ratio Score (40%) x Trend Acceleration (40%) x Actionable Window (20%)
```
No hard threshold on the peak/valley ratio — 2.8x simply means "93 points on the amplitude dimension," only 7 points shy of 3.0x's 100 points. If this product's trend acceleration (the change in growth slope this year vs last year) far exceeds that of 3.0x products, its composite Boom Index ranking can completely surpass traditionally "high ratio" products.

**Why look at trend acceleration (not just peak/offpeak ratio)**:
- A product with last year's peak/offpeak = 4.0 may already be fading this year
- A product with last year's peak/offpeak = 2.5 but trend acceleration +60% (search volume surging YoY) may be this year's new hotspot
- Acceleration leads by 2-3 months — exactly the signal window for your pre-positioning

## Trigger Phrases
- "When should I start stocking up on seasonal products?"
- "What opportunities are there for next peak season?"
- "What seasonal styles should I start preparing now?"
- "Which products have the strongest peak season breakout potential?"

## Execution Steps

### Conversation Mode (agent-x)
```
Step 1: CategoryTrend --category <categoryID> --period 12m
        → View 12-month trend curve
        → Identify peak months (clear spikes) and the current stage

Step 2: ProductSearch --category <categoryID> --sort-by seasonal_boom_index --limit 100
        → Sort by Seasonal Boom Index descending, full ranking
        → No peak/offpeak ratio limits — composite score only

Step 3: Confirm current time window
        Calculate: peak_month - current_month
        If within 2-3 months → Act immediately
        If within 4-6 months → Plan but no rush
        If already at peak eve → Recommend skipping (too late)

Step 4: Google Trends cross-validation
        agent-reach search "Google Trends <keyword> 2025 2026"
        → Confirm search trends align with Sorftime data

Step 5: analyst.py --asins <Top candidate ASINs> --detail
        → Confirm inventory depth, supply chain lead times
```

## Interpretation Notes
1. Top product common traits: moderately high peak/offpeak ratio (not necessarily the highest) + trend acceleration significantly ahead + 2-3 month window
2. **Grey Zone Opportunities**: Products with a peak/offpeak ratio of 2.0-2.8x — traditional tools consider them "not seasonal enough," but if the acceleration metric is strong (+50%+), it indicates the category's seasonality is **intensifying**, giving high certainty for early positioning
3. Red flags: High peak/offpeak ratio (5x+) but negative trend acceleration — the category is declining, and this year's peak may underperform last year's

## Risk Notes
- ⭐ The Boom Index **does not include** supply chain feasibility — discovering an opportunity with a 60-day window is useless if your supply chain lead time is 90 days
- The biggest risk in seasonal products is inventory overhang: if the peak doesn't materialize or you enter too late, inventory becomes a liability
- Recommendation for first-time seasonal category entry: small-batch trial + reserve 30% of ad budget specifically for peak season ramp-up; don't burn money chasing rankings during the off-season
- Some seasonal products concentrate search traffic within a 60-day window around peak season, with almost zero traffic the rest of the year — make sure you're calculating "peak-season ROI" not "full-year ROI"

## Combo Strategy
This Strategy → Keyword Scatter (use peak-season keywords to find unmonopolized traffic) → Low Rating Replacement (find and improve products that drew negative reviews last peak season) → Lightweight Product Profit Optimization (lightweight seasonal products have lower logistics costs and more flexibility)
