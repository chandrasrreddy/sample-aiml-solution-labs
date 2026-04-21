# UC-20 QA Verification Result

## Use Case
> "I'm prototyping an agent and want the cheapest option. What tier should I use for Qwen3 235B in us-east-1?"

## Verification Method
Applied tier advisor logic from `bedrock-tier-guidance.md` and verified pricing data from `extract_bedrock_model_prices()` against the response's stated values.

---

## Model Discovery
| Field | Response | Cache Query Result | Status |
|-------|:--------:|:------------------:|:------:|
| Model name | Qwen3 235B A22B 2507 | Qwen3 235B A22B 2507 | ✅ PASS |
| Provider | Alibaba (Qwen) | Alibaba (Qwen) | ✅ PASS |
| Region | us-east-1 | us-east-1 | ✅ PASS |
| Variant availability | Regional only | Regional only (no Global results) | ✅ PASS |

## Tier Availability
| Field | Response | Cache Query Result | Status |
|-------|:--------:|:------------------:|:------:|
| Flex available | Yes | Yes (Flex Regional found) | ✅ PASS |
| Standard available | Yes | Yes (Standard Regional found) | ✅ PASS |
| Batch available | Yes | Yes (Batch Regional found) | ✅ PASS |
| Priority available | Yes | Yes (Priority Regional found) | ✅ PASS |
| Provisioned available | No | No (not in results) | ✅ PASS |

## Pricing Verification (per 1M tokens)
| Tier | Price Type | Response | Cache Value | Status |
|------|-----------|:--------:|:-----------:|:------:|
| Flex | Input | $0.11 | $0.11 (= $0.00011/1K × 1000) | ✅ PASS |
| Flex | Output | $0.44 | $0.44 (= $0.00044/1K × 1000) | ✅ PASS |
| Flex | Cache Read | None | None | ✅ PASS |
| Flex | Cache Write | None | None | ✅ PASS |
| Batch | Input | $0.11 | $0.11 (= $0.00011/1K × 1000) | ✅ PASS |
| Batch | Output | $0.44 | $0.44 (= $0.00044/1K × 1000) | ✅ PASS |
| Batch | Cache Read | None | None | ✅ PASS |
| Batch | Cache Write | None | None | ✅ PASS |
| Standard | Input | $0.22 | $0.22 (= $0.00022/1K × 1000) | ✅ PASS |
| Standard | Output | $0.88 | $0.88 (= $0.00088/1K × 1000) | ✅ PASS |
| Standard | Cache Read | None | None | ✅ PASS |
| Standard | Cache Write | None | None | ✅ PASS |
| Priority | Input | $0.385 | $0.385 (= $0.000385/1K × 1000) | ✅ PASS |
| Priority | Output | $1.54 | $1.54 (= $0.00154/1K × 1000) | ✅ PASS |
| Priority | Cache Read | None | None | ✅ PASS |
| Priority | Cache Write | None | None | ✅ PASS |

## Tier Advisor Logic
| Field | Response | Spec/Guidance Check | Status |
|-------|:--------:|:-------------------:|:------:|
| User intent: "prototyping" | Mapped to dev/test | Guidance: "dev/test" → Flex if available | ✅ PASS |
| User intent: "cheapest" | Flex recommended | Flex = $0.11/$0.44 (cheapest on-demand real-time) | ✅ PASS |
| Flex vs Batch pricing | Tied at $0.11/$0.44 | Confirmed identical from cache | ✅ PASS |
| Flex preferred over Batch | Yes (real-time for prototyping) | Guidance: Batch is async (24h window), not suitable for interactive prototyping | ✅ PASS |
| Standard = 2× Flex | Stated as 2× | $0.22/$0.11 = 2.0×, $0.88/$0.44 = 2.0× | ✅ PASS |
| Priority = ~3.5× Flex | Stated as 3.5× | $0.385/$0.11 = 3.5×, $1.54/$0.44 = 3.5× | ✅ PASS |
| No caching on any tier | Correctly noted | All cache_read/cache_write = None across all tiers | ✅ PASS |
| Regional-only model | Correctly noted | No Global variant found in cache | ✅ PASS |
| Flex not for production warning | Included | Guidance: "Don't recommend Flex for production workloads — no SLA" | ✅ PASS |
| Upgrade path provided | Flex → Standard → Priority | Matches guidance decision framework | ✅ PASS |

---

## Overall Verdict
| Section | Result |
|---------|:------:|
| Model Discovery | ✅ PASS (4/4) |
| Tier Availability | ✅ PASS (5/5) |
| Pricing Verification | ✅ PASS (16/16) |
| Tier Advisor Logic | ✅ PASS (10/10) |

### Summary
**35 of 35 fields pass.** All pricing data matches the cache exactly. Tier recommendation correctly applies the dev/test → Flex guidance. Flex and Batch are correctly identified as tied for cheapest, with Flex preferred for interactive prototyping. All trade-offs and warnings are properly documented. No prompt caching is available for this model on any tier, which is correctly noted.
