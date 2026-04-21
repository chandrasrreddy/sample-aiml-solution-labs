# UC-10 QA Verification Result

## Use Case
> "Cost estimate for a student advising chatbot at a large university. Nova Lite in us-east-1. 400K sessions/month, 4 questions per session. 2 tools (course catalog search, degree audit). Light RAG: 3 chunks. Small system prompt: 500 tokens. Business value: advising sessions take 20 min, AI reduces to 5 min, advisor cost $40/hr."

## Verification Method
Applied pricing_spec_v1.2.md formulas to the response's stated assumptions.

---

## Token Profile
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| cacheable_base | 4,500 | 500 + 4,000 = 4,500 | ✅ |
| rag_tokens | 900 | 3 × 300 = 900 | ✅ |
| base_prompt | 5,500 | 4,500 + 100 + 900 = 5,500 | ✅ |
| delta | 600 | 100 + 500 = 600 | ✅ |
| turns | 3 | 2 + 1 = 3 | ✅ |
| total_input/question | 18,300 | 3 × 5,500 + 600 × 2 × 3/2 = 16,500 + 1,800 = 18,300 | ✅ |
| total_output/question | 300 | 100 + 2 × 100 = 300 | ✅ |

## Cache Splits
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| Q1 cache_write | 6,100 | 5,500 + (2-1) × 600 = 6,100 | ✅ |
| Q1 cache_read | 11,600 | Σ(k=1..2)[5,500 + (k-1)×600] = 5,500 + 6,100 = 11,600 | ✅ |
| Q1 regular | 600 | delta = 600 | ✅ |
| Q1 sum | 18,300 | 6,100 + 11,600 + 600 = 18,300 ✓ | ✅ |
| Q2 cache_write | 1,600 | (100 + 900) + (2-1) × 600 = 1,600 | ✅ |
| Q2 cache_read | 16,100 | 4,500 + Σ(k=1..2)[5,500 + (k-1)×600] = 4,500 + 11,600 = 16,100 | ✅ |
| Q2 regular | 600 | delta = 600 | ✅ |
| Q2 sum | 18,300 | 1,600 + 16,100 + 600 = 18,300 ✓ | ✅ |
| session_cw | 10,900 | 6,100 + 3 × 1,600 = 10,900 | ✅ |
| session_cr | 59,900 | 11,600 + 3 × 16,100 = 59,900 | ✅ |
| session_reg | 2,400 | 600 + 3 × 600 = 2,400 | ✅ |
| session_sum | 73,200 | 10,900 + 59,900 + 2,400 = 73,200 = 4 × 18,300 ✓ | ✅ |

## Monthly Tokens
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| cache_write | 4,360,000,000 | 400,000 × 10,900 = 4,360,000,000 | ✅ |
| cache_read | 23,960,000,000 | 400,000 × 59,900 = 23,960,000,000 | ✅ |
| regular_input | 960,000,000 | 400,000 × 2,400 = 960,000,000 | ✅ |
| output | 480,000,000 | 400,000 × 1,200 = 480,000,000 | ✅ |

## Model Cost
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| cache_write_cost | $0.00 | 4,360M / 1M × $0.00 = $0.00 | ✅ |
| cache_read_cost | $1,797.00 | 23,960M / 1M × $0.075 = $1,797.00 | ✅ |
| regular_input_cost | $288.00 | 960M / 1M × $0.30 = $288.00 | ✅ |
| output_cost | $1,200.00 | 480M / 1M × $2.50 = $1,200.00 | ✅ |
| **total_with_cache** | **$3,285.00** | $0.00 + $1,797.00 + $288.00 + $1,200.00 = **$3,285.00** | ✅ |
| no_cache_input | $8,784.00 | 29,280M / 1M × $0.30 = $8,784.00 | ✅ |
| no_cache_output | $1,200.00 | 480M / 1M × $2.50 = $1,200.00 | ✅ |
| **no_cache_total** | **$9,984.00** | $8,784.00 + $1,200.00 = **$9,984.00** | ✅ |
| savings_monthly | $6,699.00 | $9,984.00 - $3,285.00 = $6,699.00 | ✅ |
| savings_pct | 67.1% | $6,699.00 / $9,984.00 × 100 = 67.1% | ✅ |

## AgentCore Cost
Not applicable — not requested.

## Capacity Check
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| active_minutes | 15,840 | 12 × 60 × 22 = 15,840 | ✅ |
| avg_questions/min | 101.01 | 1,600,000 / 15,840 = 101.01 | ✅ |
| avg_rpm | 303.03 | 101.01 × 3 = 303.03 | ✅ |
| peak_rpm | 909.09 | 303.03 × 3.0 = 909.09 | ✅ |
| base_context | 5,500 | 100 + 500 + 4,000 + 900 = 5,500 | ✅ |
| avg_input/turn | 6,100 | 5,500 + (600/2) × 2 = 6,100 | ✅ |
| avg_output/turn | 100 | (2 × 100 + 100) / 3 = 100 | ✅ |
| avg_tpm | 1,878,788 | 303.03 × (6,100 + 100 × 1) = 1,878,788 | ✅ |
| peak_tpm | 5,636,364 | 1,878,788 × 3.0 = 5,636,364 | ✅ |
| max_tokens_overhead | 3,996 | max(0, 4,096 - 100) = 3,996 | ✅ |
| effective_peak_tpm | 9,269,091 | 5,636,364 + (909.09 × 3,996) = 9,269,091 | ✅ |
| rpm_fits | True | 909.09 ≤ 2,000 → True | ✅ |
| tpm_fits | False | 9,269,091 > 8,000,000 → False | ✅ |
| rpm_utilization | 45.5% | (909.09 / 2,000) × 100 = 45.5% | ✅ |
| tpm_utilization | 115.9% | (9,269,091 / 8,000,000) × 100 = 115.9% | ✅ |

## Business Value
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| time_saved | 15 min | 20 - 5 = 15 | ✅ |
| **Conservative** | | | |
| effective_sessions | 200,000 | 400,000 × 0.50 = 200,000 | ✅ |
| time_saved_hrs | 50,000 | 200,000 × 15 / 60 = 50,000 | ✅ |
| productive_hrs | 25,000 | 50,000 × 0.50 = 25,000 | ✅ |
| productivity_monthly | $7,500,000 | 25,000 × $300 = $7,500,000 | ✅ |
| cost_savings_monthly | $1,000,000 | 25,000 × $40 = $1,000,000 | ✅ |
| **Moderate** | | | |
| effective_sessions | 260,000 | 400,000 × 0.65 = 260,000 | ✅ |
| time_saved_hrs | 65,000 | 260,000 × 15 / 60 = 65,000 | ✅ |
| productive_hrs | 39,000 | 65,000 × 0.60 = 39,000 | ✅ |
| productivity_monthly | $11,700,000 | 39,000 × $300 = $11,700,000 | ✅ |
| cost_savings_monthly | $1,560,000 | 39,000 × $40 = $1,560,000 | ✅ |
| **Optimistic** | | | |
| effective_sessions | 320,000 | 400,000 × 0.80 = 320,000 | ✅ |
| time_saved_hrs | 80,000 | 320,000 × 15 / 60 = 80,000 | ✅ |
| productive_hrs | 56,000 | 80,000 × 0.70 = 56,000 | ✅ |
| productivity_monthly | $16,800,000 | 56,000 × $300 = $16,800,000 | ✅ |
| cost_savings_monthly | $2,240,000 | 56,000 × $40 = $2,240,000 | ✅ |
| **ROI Summary** | | | |
| agent_cost_annual | $39,420 | $3,285 × 12 = $39,420 | ✅ |
| grand_total_annual | $140,400,000 | $11,700,000 × 12 = $140,400,000 | ✅ |
| net_value | $140,360,580 | $140,400,000 - $39,420 = $140,360,580 | ✅ |
| roi_pct | 356,064% | ($140,360,580 / $39,420) × 100 = 356,064% | ✅ |
| payback_days | < 1 day | ($39,420 / $140,400,000) × 365 = 0.1 days | ✅ |

---

## Overall Verdict
| Section | Result |
|---------|:------:|
| Token Profile | ✅ PASS |
| Cache Splits | ✅ PASS |
| Monthly Tokens | ✅ PASS |
| Model Cost | ✅ PASS |
| AgentCore | N/A (not requested) |
| Capacity Check | ✅ PASS |
| Business Value | ✅ PASS |

### Summary
**46 of 46 fields pass.** All token counts, cache splits, cost calculations, capacity metrics, and business value figures match spec formulas exactly. Nova Lite's free cache writes ($0.00) are correctly handled. The output_burndown_rate=1 (not Claude's 5×) is correctly applied. The capacity check correctly identifies that reducing max_tokens from 4,096 to ~300 would resolve the marginal TPM overage.
