# UC-19 QA Verification Result

## Use Case
> "I'm building a customer service agent on Claude Sonnet 4.6 in us-east-1. It's production, customer-facing. Which tier and variant should I use?"

## Verification Method
Applied the tier advisor decision framework from `bedrock-tier-guidance.md` and verified tier discovery against the pricing cache using `extract_bedrock_model_prices(results, all_tiers=True)`.

This is a **tier advisor use case** — no cost calculations are required. Verification focuses on:
1. Correct tier discovery from cache
2. Correct application of the decision framework
3. Accurate pricing data in the recommendation
4. Appropriate alternatives and trade-offs

---

## Tier Discovery
| Check | Response | Cache Data | Status |
|-------|:--------:|:----------:|:------:|
| Tiers found | Standard Global, Standard Regional, Batch Global, Batch Regional | Standard Global, Standard Regional, Batch Global, Batch Regional | ✅ PASS |
| Flex available? | Not found | Not in cache | ✅ PASS |
| Priority available? | Not found | Not in cache | ✅ PASS |

## Pricing Accuracy
| Tier + Variant | Field | Response | Cache Value | Status |
|----------------|-------|:--------:|:-----------:|:------:|
| Standard Global | Input | $3.00/M | $3.00/M | ✅ PASS |
| Standard Global | Output | $15.00/M | $15.00/M | ✅ PASS |
| Standard Global | Cache Read | $0.30/M | $0.30/M | ✅ PASS |
| Standard Global | Cache Write | $3.75/M | $3.75/M | ✅ PASS |
| Standard Regional | Input | $3.30/M | $3.30/M | ✅ PASS |
| Standard Regional | Output | $16.50/M | $16.50/M | ✅ PASS |
| Standard Regional | Cache Read | $0.33/M | $0.33/M | ✅ PASS |
| Standard Regional | Cache Write | $4.125/M | $4.125/M | ✅ PASS |
| Batch Global | Input | $1.50/M | $1.50/M | ✅ PASS |
| Batch Global | Output | $7.50/M | $7.50/M | ✅ PASS |
| Batch Global | Cache Read | — (none) | null | ✅ PASS |
| Batch Global | Cache Write | — (none) | null | ✅ PASS |
| Batch Regional | Input | $1.65/M | $1.65/M | ✅ PASS |
| Batch Regional | Output | $8.25/M | $8.25/M | ✅ PASS |
| Batch Regional | Cache Read | — (none) | null | ✅ PASS |
| Batch Regional | Cache Write | — (none) | null | ✅ PASS |

## Decision Framework Application
| Rule | User Context | Expected Recommendation | Response Recommendation | Status |
|------|-------------|------------------------|------------------------|:------:|
| Production + customer-facing → Standard | "production, customer-facing" | Standard | Standard | ✅ PASS |
| No data residency stated → Global | No residency requirement mentioned | Global | Global | ✅ PASS |
| Caching available → recommend enabling | Standard Global has cache_read=$0.30 | Recommend caching | Recommended caching | ✅ PASS |
| Don't recommend Flex for production | Production workload | Exclude Flex | Excluded Flex (not available, but also noted as unsuitable) | ✅ PASS |
| Don't recommend Batch for real-time | Customer-facing, real-time | Exclude Batch as primary | Listed as alternative only | ✅ PASS |
| Show alternatives with trade-offs | Tier advisor requirement | Show Batch, Regional options | Showed all 3 alternatives with trade-offs | ✅ PASS |

## Guidance Compliance
| Guidance Rule | Compliance | Status |
|---------------|-----------|:------:|
| Always discover available tiers from cache before recommending | Used `all_tiers=True` to discover | ✅ PASS |
| Default to Standard Global when user hasn't expressed variant preference | Recommended Standard Global | ✅ PASS |
| Prefer tiers with prompt caching support | Highlighted caching as biggest cost lever | ✅ PASS |
| Show price difference between recommended and alternatives | Showed 50% savings for Batch, ~10% premium for Regional | ✅ PASS |
| Don't recommend Flex for production workloads | Did not recommend Flex | ✅ PASS |
| Don't hardcode tier names — discover from cache | Discovered from cache, noted Flex/Priority absence | ✅ PASS |

---

## Overall Verdict
| Section | Result |
|---------|:------:|
| Tier Discovery | ✅ PASS |
| Pricing Accuracy (16 fields) | ✅ PASS |
| Decision Framework (6 rules) | ✅ PASS |
| Guidance Compliance (6 rules) | ✅ PASS |

### Summary
**28 of 28 checks pass.** The recommendation correctly identifies Standard Global as the appropriate tier for a production, customer-facing customer service agent. All pricing data matches the cache. The decision framework was applied correctly: Standard for production SLA, Global for cost savings without data residency constraints, and prompt caching highlighted as the primary cost optimization. Alternatives (Batch, Regional) are presented with accurate trade-offs. No Flex or Priority tiers were incorrectly recommended.
