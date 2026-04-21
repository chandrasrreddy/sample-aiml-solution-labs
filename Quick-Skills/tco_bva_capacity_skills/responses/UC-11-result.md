# UC-11 QA Verification Result

## Use Case
> "Compare the pricing for Claude Sonnet 4.6, Nova Pro, and Llama 4 Maverick in us-east-1. Show all available tiers and variants for each. Which is cheapest for a standard on-demand workload?"

## Verification Method
This is a pricing-only comparison (no calculations). Verified that all prices in the response file match the values returned by `extract_bedrock_model_prices()` from the local cache files.

---

## Claude Sonnet 4.6

| Tier + Variant | Field | Response | Cache Query | Status |
|----------------|-------|:--------:|:-----------:|:------:|
| Standard Global | Input | $3.00 | $3.00 | ✅ |
| Standard Global | Output | $15.00 | $15.00 | ✅ |
| Standard Global | Cache Read | $0.30 | $0.30 | ✅ |
| Standard Global | Cache Write | $3.75 | $3.75 | ✅ |
| Standard Regional | Input | $3.30 | $3.30 | ✅ |
| Standard Regional | Output | $16.50 | $16.50 | ✅ |
| Standard Regional | Cache Read | $0.33 | $0.33 | ✅ |
| Standard Regional | Cache Write | $4.125 | $4.125 | ✅ |
| Batch Global | Input | $1.50 | $1.50 | ✅ |
| Batch Global | Output | $7.50 | $7.50 | ✅ |
| Batch Regional | Input | $1.65 | $1.65 | ✅ |
| Batch Regional | Output | $8.25 | $8.25 | ✅ |

## Nova Pro

| Tier + Variant | Field | Response | Cache Query | Status |
|----------------|-------|:--------:|:-----------:|:------:|
| Standard Global | Input | $1.25 | $1.25 | ✅ |
| Standard Global | Output | $10.00 | $10.00 | ✅ |
| Standard Regional | Input | $1.375 | $1.375 | ✅ |
| Standard Regional | Output | $4.00 | $4.00 | ✅ |
| Standard Regional | Cache Read | $0.20 | $0.20 | ✅ |
| Flex Global | Input | $0.625 | $0.625 | ✅ |
| Flex Global | Output | $5.00 | $5.00 | ✅ |
| Flex Regional | Input | $0.40 | $0.40 | ✅ |
| Flex Regional | Output | $1.60 | $1.60 | ✅ |
| Flex Regional | Cache Read | $0.20 | $0.20 | ✅ |
| Priority Global | Input | $2.1875 | $2.1875 | ✅ |
| Priority Global | Output | $17.50 | $17.50 | ✅ |
| Priority Regional | Input | $2.40625 | $2.40625 | ✅ |
| Priority Regional | Output | $19.25 | $19.25 | ✅ |
| Priority Regional | Cache Read | $0.20 | $0.20 | ✅ |
| Batch Global | Input | $0.625 | $0.625 | ✅ |
| Batch Global | Output | $5.00 | $5.00 | ✅ |
| Batch Regional | Input | $0.40 | $0.40 | ✅ |
| Batch Regional | Output | $5.50 | $5.50 | ✅ |
| Custom Model Regional | Input | $0.80 | $0.80 | ✅ |
| Custom Model Regional | Output | $3.20 | $3.20 | ✅ |

## Llama 4 Maverick 17B

| Tier + Variant | Field | Response | Cache Query | Status |
|----------------|-------|:--------:|:-----------:|:------:|
| Standard Regional | Input | $0.24 | $0.24 | ✅ |
| Standard Regional | Output | $0.97 | $0.97 | ✅ |
| Batch Regional | Input | $0.12 | $0.12 | ✅ |
| Batch Regional | Output | $0.485 | $0.485 | ✅ |

## Recommendation Verification

| Check | Status |
|-------|:------:|
| Cheapest standard on-demand identified as Llama 4 Maverick | ✅ |
| Maverick Standard Regional ($0.24/$0.97) < Nova Pro Standard Global ($1.25/$10.00) | ✅ |
| Maverick Standard Regional ($0.24/$0.97) < Claude Standard Global ($3.00/$15.00) | ✅ |
| All tiers shown for each model | ✅ |
| All variants shown for each model | ✅ |
| No prices from training data (all from cache) | ✅ |

---

## Overall Verdict

| Section | Result |
|---------|:------:|
| Claude Sonnet 4.6 Prices | ✅ PASS (12/12) |
| Nova Pro Prices | ✅ PASS (21/21) |
| Llama 4 Maverick Prices | ✅ PASS (4/4) |
| Recommendation | ✅ PASS |

### Summary
37 of 37 price fields match cache. Recommendation correctly identifies Llama 4 Maverick as cheapest for standard on-demand. All tiers and variants present in cache are shown. No calculations required — pricing-only comparison verified against cache files.

**Result: ✅ PASS**
