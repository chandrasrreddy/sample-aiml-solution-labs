# UC-14: Multi-Region Pricing Comparison — Claude Sonnet 4.6

> **Use Case:** "Compare Claude Sonnet 4.6 pricing across us-east-1, eu-west-1, and ap-northeast-1. Show Standard Global vs Standard Regional for each."

---

## 1. Pricing Source

All prices sourced from local Bedrock pricing cache files (`~/bedrock_pricing.json`, `~/bedrock_pricing_3p.json`). No training data used.

---

## 2. Multi-Region Pricing Comparison

### Standard Global (Cross-Region) — per 1M tokens

| Price Component | us-east-1 | eu-west-1 | ap-northeast-1 |
|:----------------|:---------:|:---------:|:--------------:|
| Input            | $3.00     | $3.00     | $3.00          |
| Output           | $15.00    | $15.00    | $15.00         |
| Cache Read       | $0.30     | $0.30     | $0.30          |
| Cache Write      | $3.75     | $3.75     | $3.75          |

### Standard Regional (In-Region) — per 1M tokens

| Price Component | us-east-1 | eu-west-1 | ap-northeast-1 |
|:----------------|:---------:|:---------:|:--------------:|
| Input            | $3.30     | $3.30     | $3.30          |
| Output           | $16.50    | $16.50    | $16.50         |
| Cache Read       | $0.33     | $0.33     | $0.33          |
| Cache Write      | $4.125    | $4.125    | $4.125         |

---

## 3. Global vs Regional Price Differential

| Price Component | Standard Global | Standard Regional | Regional Premium |
|:----------------|:--------------:|:-----------------:|:----------------:|
| Input            | $3.00          | $3.30             | +10.0%           |
| Output           | $15.00         | $16.50            | +10.0%           |
| Cache Read       | $0.30          | $0.33             | +10.0%           |
| Cache Write      | $3.75          | $4.125            | +10.0%           |

---

## 4. Variant Availability by Region

| Region | Standard Global | Standard Regional | Batch Global | Batch Regional |
|:-------|:---------------:|:-----------------:|:------------:|:--------------:|
| us-east-1      | ✅ | ✅ | ✅ | ✅ |
| eu-west-1      | ✅ | ✅ | ✅ | ✅ |
| ap-northeast-1 | ✅ | ✅ | ✅ | ✅ |

All three regions have identical variant availability for Claude Sonnet 4.6. Prompt caching (cache read + cache write) is supported in both Standard Global and Standard Regional across all regions.

---

## 5. Key Observations

1. **Uniform Global pricing**: Standard Global prices are identical across all three regions ($3.00/$15.00 input/output per 1M tokens). This is expected — Global (cross-region) pricing is region-agnostic by design.

2. **Uniform Regional pricing**: Standard Regional prices are also identical across all three regions ($3.30/$16.50 input/output per 1M tokens). The 10% premium over Global applies uniformly.

3. **10% Regional premium**: Standard Regional is consistently 10% more expensive than Standard Global across all price components (input, output, cache read, cache write).

4. **Caching supported everywhere**: Prompt caching is available in all regions for both Global and Regional variants, with cache read at 10% of input price and cache write at 125% of input price.

5. **No Priority or Flex tiers**: Claude Sonnet 4.6 does not offer Priority or Flex tiers in any of these regions — only Standard and Batch are available.

---

## 6. Recommendation

For Claude Sonnet 4.6, **Standard Global is the most cost-effective on-demand option** regardless of region. The 10% savings over Regional applies to all token types. Use Regional only if data residency requirements mandate in-region inference.
