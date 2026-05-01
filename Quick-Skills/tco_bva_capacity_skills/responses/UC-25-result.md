# UC-25 QA Verification Result

## Use Case
> "I have 10 million questions per month. How much will this cost on Bedrock?"

## Verification Method
Applied pricing_spec_v1.2.md formulas to the response's stated assumptions. This is a "volume without context" vague use case — verified that assumptions follow the handling rules (Claude Sonnet 4.6, us-east-1, 5 Q/session → 2M sessions, 3 tools, standard token profile).

---

## Assumption Validation
| Field | Response | Expected (per vague UC rules) | Status |
|-------|:--------:|:-----------------------------:|:------:|
| Model | Claude Sonnet 4.6 | Claude Sonnet 4.6 | ✅ PASS |
| Region | us-east-1 | us-east-1 | ✅ PASS |
| Sessions/month | 2,000,000 | 10M ÷ 5 = 2,000,000 | ✅ PASS |
| Questions/session | 5 | 5 (standard default) | ✅ PASS |
| Questions/month | 10,000,000 | 2M × 5 = 10,000,000 | ✅ PASS |
| Tools invoked | 3 | 3 (moderate default) | ✅ PASS |
| Turns/question | 4 | 3 + 1 = 4 | ✅ PASS |

## Token Profile
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| Cacheable base | 5,000 | 1,000 + 4,000 = 5,000 | ✅ PASS |
| RAG tokens | 3,000 | 10 × 300 = 3,000 | ✅ PASS |
| Base prompt | 8,100 | 5,000 + 100 + 3,000 = 8,100 | ✅ PASS |
| Delta | 600 | 100 + 500 = 600 | ✅ PASS |
| Total input/question | 36,000 | 8,100 + 8,700 + 9,300 + 9,900 = 36,000 | ✅ PASS |
| Output/question | 400 | 100 + 3 × 100 = 400 | ✅ PASS |

**Closed-form verification:** turns × base_prompt + delta × N_invoke × turns / 2 = 4 × 8,100 + 600 × 3 × 4 / 2 = 32,400 + 3,600 = 36,000 ✓

## Model Pricing
| Field | Response | Cache Value | Status |
|-------|:--------:|:-----------:|:------:|
| Input price | $3.00/M | $3.00/M (Standard Global) | ✅ PASS |
| Output price | $15.00/M | $15.00/M (Standard Global) | ✅ PASS |
| Cache read price | $0.30/M | $0.30/M | ✅ PASS |
| Cache write price | $3.75/M | $3.75/M | ✅ PASS |

## Cache Splits
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| Q1 cache_write | 9,300 | base_prompt + (N-1) × delta = 8,100 + 2 × 600 = 9,300 | ✅ PASS |
| Q1 cache_read | 26,100 | Σ(k=1→3)[8,100 + (k-1)×600] = 8,100 + 8,700 + 9,300 = 26,100 | ✅ PASS |
| Q1 regular | 600 | delta = 600 | ✅ PASS |
| Q1 sum | 36,000 | 9,300 + 26,100 + 600 = 36,000 ✓ | ✅ PASS |
| Q2 cache_write | 4,300 | (T_user + rag) + (N-1) × delta = 3,100 + 2 × 600 = 4,300 | ✅ PASS |
| Q2 cache_read | 31,100 | cacheable_base + Σ(k=1→3)[8,100 + (k-1)×600] = 5,000 + 26,100 = 31,100 | ✅ PASS |
| Q2 regular | 600 | delta = 600 | ✅ PASS |
| Q2 sum | 36,000 | 4,300 + 31,100 + 600 = 36,000 ✓ | ✅ PASS |
| Session cache_write | 26,500 | 9,300 + 4 × 4,300 = 26,500 | ✅ PASS |
| Session cache_read | 150,500 | 26,100 + 4 × 31,100 = 150,500 | ✅ PASS |
| Session regular | 3,000 | 600 + 4 × 600 = 3,000 | ✅ PASS |
| Session sum | 180,000 | 26,500 + 150,500 + 3,000 = 180,000 = 5 × 36,000 ✓ | ✅ PASS |

## Monthly Tokens
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| Monthly cache_write | 53,000,000,000 | 2,000,000 × 26,500 = 53,000,000,000 | ✅ PASS |
| Monthly cache_read | 301,000,000,000 | 2,000,000 × 150,500 = 301,000,000,000 | ✅ PASS |
| Monthly regular | 6,000,000,000 | 2,000,000 × 3,000 = 6,000,000,000 | ✅ PASS |
| Monthly output | 4,000,000,000 | 2,000,000 × 2,000 = 4,000,000,000 | ✅ PASS |

## Model Cost
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| Cache write cost | $198,750.00 | 53,000 × $3.75 = $198,750.00 | ✅ PASS |
| Cache read cost | $90,300.00 | 301,000 × $0.30 = $90,300.00 | ✅ PASS |
| Regular input cost | $18,000.00 | 6,000 × $3.00 = $18,000.00 | ✅ PASS |
| Output cost | $60,000.00 | 4,000 × $15.00 = $60,000.00 | ✅ PASS |
| **Total with cache** | **$367,050.00** | $198,750 + $90,300 + $18,000 + $60,000 = **$367,050.00** | ✅ PASS |
| No-cache input | $1,080,000.00 | 360,000 × $3.00 = $1,080,000.00 | ✅ PASS |
| No-cache output | $60,000.00 | 4,000 × $15.00 = $60,000.00 | ✅ PASS |
| **No-cache total** | **$1,140,000.00** | $1,080,000 + $60,000 = **$1,140,000.00** | ✅ PASS |
| Savings monthly | $772,950.00 | $1,140,000 - $367,050 = $772,950.00 | ✅ PASS |
| Savings % | 67.8% | $772,950 / $1,140,000 × 100 = 67.80% | ✅ PASS |
| Annual total | $4,404,600.00 | $367,050 × 12 = $4,404,600.00 | ✅ PASS |
| Per question | $0.0367 | $367,050 / 10,000,000 = $0.03671 | ✅ PASS |
| Per session | $0.1835 | $367,050 / 2,000,000 = $0.18353 | ✅ PASS |

## Capacity Check
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| Active min/month | 15,840 | 12 × 60 × 22 = 15,840 | ✅ PASS |
| Avg Q/min | 631.31 | 10,000,000 / 15,840 = 631.31 | ✅ PASS |
| Avg RPM | 2,525.25 | 631.31 × 4 = 2,525.25 | ✅ PASS |
| Peak RPM | 7,575.76 | 2,525.25 × 3.0 = 7,575.76 | ✅ PASS |
| RPM limit | 10,000 | From query_quotas() | ✅ PASS |
| RPM fits | ✅ Yes | 7,575.76 ≤ 10,000 | ✅ PASS |
| RPM utilization | 75.8% | 7,575.76 / 10,000 = 75.76% | ✅ PASS |
| Base context | 8,100 | 100 + 1,000 + 4,000 + 3,000 = 8,100 | ✅ PASS |
| Avg input/turn | 9,000 | 8,100 + (600/2) × 3 = 9,000 | ✅ PASS |
| Avg output/turn | 100 | (3 × 100 + 100) / 4 = 100 | ✅ PASS |
| Output burndown | 5× | Claude Sonnet 4.6 = 5× | ✅ PASS |
| Avg TPM | 23,989,899 | 2,525.25 × (9,000 + 100 × 5) = 23,989,899 | ✅ PASS |
| Peak TPM | 71,969,697 | 23,989,899 × 3.0 = 71,969,697 | ✅ PASS |
| max_tokens overhead | 3,996 | 4,096 - 100 = 3,996 | ✅ PASS |
| Effective peak TPM | 102,242,424 | 71,969,697 + (7,575.76 × 3,996) = 102,242,424 | ✅ PASS |
| TPM limit | 6,000,000 | From query_quotas() | ✅ PASS |
| TPM fits | ❌ No | 102,242,424 > 6,000,000 | ✅ PASS |
| TPM utilization | 1,704% | 102,242,424 / 6,000,000 = 1,704% | ✅ PASS |
| Overall fits | ❌ No | RPM ✅ AND TPM ❌ = ❌ | ✅ PASS |

---

## Overall Verdict
| Section | Result |
|---------|:------:|
| Assumption Validation | ✅ PASS (7/7) |
| Token Profile | ✅ PASS (6/6) |
| Model Pricing | ✅ PASS (4/4) |
| Cache Splits | ✅ PASS (12/12) |
| Monthly Tokens | ✅ PASS (4/4) |
| Model Cost | ✅ PASS (13/13) |
| Capacity Check | ✅ PASS (20/20) |

### Summary
**66 of 66 fields pass.** All token calculations, cache splits, cost figures, and capacity metrics match the spec formulas exactly. The vague use case assumptions correctly follow the handling rules: Claude Sonnet 4.6, us-east-1, 2M sessions derived from 10M questions ÷ 5 Q/session, 3 tools (moderate default), standard token profile. The capacity check correctly identifies TPM as the bottleneck at 1,704% utilization with the 5× output burndown rate. No AgentCore or business value sections are included (not requested and no agent context provided), which is appropriate for this pricing-only vague prompt.
