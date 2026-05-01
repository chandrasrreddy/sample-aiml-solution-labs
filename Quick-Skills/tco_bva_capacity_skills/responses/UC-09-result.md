# UC-09 QA Verification Result

## Use Case
> "Price an agent that helps real estate agents with property valuations. Claude Sonnet 4.6 in us-east-1. 150K sessions/month, 5 questions per session. 7 tools (MLS search, comparable sales, tax records, neighborhood stats, mortgage calculator, market trends, property history). RAG: 12 chunks of property data. Business value: valuations take 40 min manually, 12 min with AI, agent cost $75/hr."

## Verification Method
Applied pricing_spec_v1.2.md formulas to the response's stated assumptions. All intermediate values independently computed and compared.

---

## Token Profile

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| rag_tokens | 3,600 | 12 × 300 = 3,600 | ✅ |
| cacheable_base | 5,000 | 1,000 + 4,000 = 5,000 | ✅ |
| base_prompt | 8,700 | 5,000 + 100 + 3,600 = 8,700 | ✅ |
| delta | 600 | 100 + 500 = 600 | ✅ |
| turns | 8 | 7 + 1 = 8 | ✅ |
| total_input_per_question | 86,400 | 8 × 8,700 + 600 × 7 × 8/2 = 86,400 | ✅ |
| total_output_per_question | 800 | 100 + 7 × 100 = 800 | ✅ |

## Model Cost

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| questions_per_month | 750,000 | 150,000 × 5 = 750,000 | ✅ |
| monthly_input_tokens | 64,800,000,000 | 86,400 × 750,000 = 64,800,000,000 | ✅ |
| monthly_output_tokens | 600,000,000 | 800 × 750,000 = 600,000,000 | ✅ |
| no_cache_input_cost | $194,400.00 | 64,800 × $3.00 = $194,400.00 | ✅ |
| no_cache_output_cost | $9,000.00 | 600 × $15.00 = $9,000.00 | ✅ |
| no_cache_total | $203,400.00 | $194,400 + $9,000 = $203,400.00 | ✅ |
| total_model_cost (with cache) | $51,131.25 | $23,343.75 + $17,437.50 + $1,350.00 + $9,000.00 = $51,131.25 | ✅ |
| savings_monthly | $152,268.75 | $203,400.00 − $51,131.25 = $152,268.75 | ✅ |
| savings_pct | 74.9% | $152,268.75 / $203,400.00 × 100 = 74.86% | ✅ |
| per_session | $0.3409 | $51,131.25 / 150,000 = $0.3409 | ✅ |
| per_question | $0.0682 | $51,131.25 / 750,000 = $0.0682 | ✅ |

## Cache Splits

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| Q1 cache_write | 12,300 | 8,700 + (7−1) × 600 = 12,300 | ✅ |
| Q1 cache_read | 73,500 | Σ(k=1→7)[8,700 + (k−1)×600] = 73,500 | ✅ |
| Q1 regular | 600 | delta = 600 | ✅ |
| Q1 sum | 86,400 | 12,300 + 73,500 + 600 = 86,400 ✓ | ✅ |
| Q2 cache_write | 7,300 | (100 + 3,600) + (7−1) × 600 = 7,300 | ✅ |
| Q2 cache_read | 78,500 | 5,000 + Σ(k=1→7)[8,700 + (k−1)×600] = 78,500 | ✅ |
| Q2 regular | 600 | delta = 600 | ✅ |
| Q2 sum | 86,400 | 7,300 + 78,500 + 600 = 86,400 ✓ | ✅ |
| Session cache_write | 41,500 | 12,300 + 4 × 7,300 = 41,500 | ✅ |
| Session cache_read | 387,500 | 73,500 + 4 × 78,500 = 387,500 | ✅ |
| Session regular | 3,000 | 600 + 4 × 600 = 3,000 | ✅ |
| Session sum identity | 432,000 | 41,500 + 387,500 + 3,000 = 432,000 = 5 × 86,400 ✓ | ✅ |
| Monthly cache_write | 6,225,000,000 | 150,000 × 41,500 = 6,225,000,000 | ✅ |
| Monthly cache_read | 58,125,000,000 | 150,000 × 387,500 = 58,125,000,000 | ✅ |
| Monthly regular | 450,000,000 | 150,000 × 3,000 = 450,000,000 | ✅ |

## Cache Costs

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| cache_write_cost | $23,343.75 | 6,225 × $3.75 = $23,343.75 | ✅ |
| cache_read_cost | $17,437.50 | 58,125 × $0.30 = $17,437.50 | ✅ |
| regular_input_cost | $1,350.00 | 450 × $3.00 = $1,350.00 | ✅ |
| output_cost | $9,000.00 | 600 × $15.00 = $9,000.00 | ✅ |

## AgentCore Cost
*Not applicable — AgentCore not requested.*

## Capacity Check

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| active_minutes | 15,840 | 12 × 60 × 22 = 15,840 | ✅ |
| avg_questions/min | 47.35 | 750,000 / 15,840 = 47.35 | ✅ |
| avg_rpm | 378.8 | 47.35 × 8 = 378.8 | ✅ |
| peak_rpm | 1,136 | 378.8 × 3.0 = 1,136 | ✅ |
| avg_input_per_turn | 10,800 | 8,700 + (600/2) × 7 = 10,800 | ✅ |
| avg_output_per_turn | 100 | (7 × 100 + 100) / 8 = 100 | ✅ |
| avg_tpm | 4,280,303 | 378.8 × (10,800 + 100 × 5) = 4,280,303 | ✅ |
| peak_tpm | 12,840,909 | 4,280,303 × 3.0 = 12,840,909 | ✅ |
| max_tokens_overhead | 3,996 | max(0, 4,096 − 100) = 3,996 | ✅ |
| effective_peak_tpm | 17,381,818 | 12,840,909 + (1,136 × 3,996) = 17,381,818 | ✅ |
| rpm_utilization | 11% | 1,136 / 10,000 = 11.4% | ✅ |
| tpm_utilization | 290% | 17,381,818 / 6,000,000 = 289.7% | ✅ |
| rpm_fits | True | 1,136 ≤ 10,000 | ✅ |
| tpm_fits | False | 17,381,818 > 6,000,000 | ✅ |
| fits | False | TPM bottleneck | ✅ |

## Business Value

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| time_saved | 28 min | 40 − 12 = 28 | ✅ |
| Conservative productive_hrs | 17,500 | 150,000 × 0.50 × 28/60 × 0.50 = 17,500 | ✅ |
| Conservative productivity/mo | $5,250,000 | 17,500 × $300 = $5,250,000 | ✅ |
| Conservative cost_savings/mo | $1,312,500 | 17,500 × $75 = $1,312,500 | ✅ |
| Moderate productive_hrs | 27,300 | 150,000 × 0.65 × 28/60 × 0.60 = 27,300 | ✅ |
| Moderate productivity/mo | $8,190,000 | 27,300 × $300 = $8,190,000 | ✅ |
| Moderate cost_savings/mo | $2,047,500 | 27,300 × $75 = $2,047,500 | ✅ |
| Optimistic productive_hrs | 39,200 | 150,000 × 0.80 × 28/60 × 0.70 = 39,200 | ✅ |
| Optimistic productivity/mo | $11,760,000 | 39,200 × $300 = $11,760,000 | ✅ |
| Optimistic cost_savings/mo | $2,940,000 | 39,200 × $75 = $2,940,000 | ✅ |
| grand_total_annual | $98,280,000 | $8,190,000 × 12 = $98,280,000 | ✅ |
| agent_cost_annual | $613,575 | $51,131.25 × 12 = $613,575 | ✅ |
| net_value | $97,666,425 | $98,280,000 − $613,575 = $97,666,425 | ✅ |
| roi_pct | 15,918% | ($97,666,425 / $613,575) × 100 = 15,918% | ✅ |
| payback_days | ~2.3 | ($613,575 / $98,280,000) × 365 = 2.3 | ✅ |

---

## Overall Verdict

| Section | Result |
|---------|:------:|
| Token Profile | ✅ PASS (7/7) |
| Model Cost | ✅ PASS (11/11) |
| Cache Splits | ✅ PASS (15/15) |
| Cache Costs | ✅ PASS (4/4) |
| AgentCore | N/A (not requested) |
| Capacity Check | ✅ PASS (15/15) |
| Business Value | ✅ PASS (15/15) |

### Summary
**67 of 67 fields pass.** All token counts, cache splits, cost calculations, capacity metrics, and business value figures match spec v1.2 formulas exactly. No discrepancies found.
