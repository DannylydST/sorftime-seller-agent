# Lightweight Product Profit Optimization

> Category: Tactical Strategy | Seller Stage: Beginner+ | Platform: Amazon

## Core Logic
Low FBA fees + decent selling price + light weight = extremely high unit profit efficiency. — The so-called "small and beautiful": the lower the FBA fees, the larger your margin headroom.

## Methodology

**Key Distinction: Full-Ranking vs Hard-Threshold Filtering**

Traditional lightweight product selection logic is a hard-threshold pyramid:
```
weight <= 500g  AND  FBA fee <= $4.00  AND  price >= $15.00
```
A product weighing 510g (slightly exceeding the 500g tier), with $4.10 FBA fee, but priced at $18.99 and selling 1500 units/month gets discarded outright. There is virtually no difference in logistics cost between 510g and 499g, yet traditional rules eliminate the former.

Sorftime's **Profit Efficiency Index ⭐** uses full-ranking:
```
Profit Efficiency = (Profit Margin x Monthly Sales) / FBA Fee
```
Weight and FBA fees are just factors influencing the "profit efficiency" score — not hard cutoffs. A 510g product scores "slightly lower on the weight dimension," but if its profit margin is exceptionally high (70%) with large sales volume, a bigger denominator and bigger numerator produce a composite rank that crushes a batch of 300g products with 20% margins.

**Why the Profit Efficiency Index is better than "absolute profit"**:
- Pure profit: $10/unit x 100 units/month = $1000
- Profit Efficiency: ($10 / $20 selling price) x 100 / $4 FBA ≈ 125
- The efficiency index identifies "low FBA fee + high turnover" potential breakout products, rather than only looking at absolute values

## Trigger Phrases
- "Help me find profitable lightweight products"
- "What small and beautiful products are out there?"
- "Categories with low FBA fees but high profit margins"
- "Small items suitable for beginners to start with"

## Execution Steps

### Conversation Mode (agent-x)
```
Step 1: ProductSearch --category-size small --sort-by profit_efficiency_index --limit 100
        → Sort by Profit Efficiency Index descending, full ranking, no weight/price limits

Step 2: ProductDetail --asins <Top 20 candidates>
        → Get precise weight, FBA fee, selling price, cost structure
        → Confirm actual profit margin (deduct sourcing cost, FBA fee, advertising cost)

Step 3: picker.py --mode lightweight-profit --top-n 30 --detail
        → Output sorted table + estimated ROI projection
        → Auto-tag products that "would be filtered out by traditional methods"

Step 4: Select Top 5 for cross-validation
        analyst.py --mode margin-analysis --asins ASIN1,ASIN2,...
        → Recalculate FBA fees using actual product dimensions and weight
```

## Interpretation Notes
1. Top product common traits: weight 200-500g, FBA fee $3.00-$4.50, selling price $15-$25, profit margin 50%+
2. **Grey Zone Gems**: Products in the 500-600g range — this tier gets filtered by the traditional "500g ceiling" rule, but the FBA fee difference is only $0.50-$1.00, which is easily covered if the product unit price is high. The Profit Efficiency ranking naturally places them in a reasonable position.
3. Red flags: Extremely high profit margin (80%+) but extremely low sales volume (<50/month) — likely a niche with demand too small; the efficiency index score is high but you won't actually make money

## Risk Notes
- ⭐ FBA fees are calculated based on **actual product dimensions and weight**; the estimated fees shown on sourcing pages may be low and must be verified with `ProductDetail`
- Lightweight products are easily copyable by major sellers (low barrier to entry) — check brand registry status
- The Profit Efficiency Index does not factor in return rates — lightweight products with 15%+ return rates may actually produce negative real profit

## Combo Strategy
This Strategy → Low Rating Replacement (find poorly-reviewed lightweight products to improve) → Hidden Profit Index (cross-validate composite potential) → Keyword Scatter (find traffic entry points)
