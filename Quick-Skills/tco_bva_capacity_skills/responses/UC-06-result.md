# UC-06 QA Verification Result

## Use Case
> Price a research agent for a hedge fund. Claude Opus 4.6 in us-east-1. 100K sessions/month, 8 questions per session. 10 tools (market data API, SEC filings search, earnings transcript search, sentiment analyzer, portfolio analyzer, risk calculator, news aggregator, peer comparison, valuation model, trade simulator). Heavy RAG: 15 chunks of 400 tokens. Output 500 tokens. Business value: analysts spend 30 min per research query, AI reduces to 8 min, analyst cost $150/hr, revenue per hour $500.

## Verification Method
Applied pricing_spec_v1.2.md formulas to the response's stated assumptions. All calculations independently reproduced using Python.

---

## Token Profile
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| rag_tokens | 6,000 | 15 × 400 = 6,000 | ✅ |
| cacheable_base | 5,000 | 1,000 + 4,000 = 5,000 | ✅ |
| base_prompt | 11,100 | 5,000 + 100 + 6,000 = 11,100 | ✅ |
| delta | 600 | 100 + 500 = 600 | ✅ |
| turns | 11 | 10 + 1 = 11 | ✅ |
| total_input/question | 155,100 | 11 × 11,100 + 600 × 10 × 11/2 = 155,100 | ✅ |
| total_output/question | 1,500 | 500 + 10 × 100 = 1,500 | ✅ |

## Cache Splits
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| q1_cache_write | 16,500 | 11,100 + 9 × 600 = 16,500 | ✅ |
| q1_cache_read | 138,000 | Σ(k=1..10)[11,100 + (k-1)×600] = 138,000 | ✅ |
| q1_regular | 600 | 600 (last turn delta) | ✅ |
| q1_sum | 155,100 | 16,500 + 138,000 + 600 = 155,100 ✓ | ✅ |
| q2_cache_write | 11,500 | 6,100 + 9 × 600 = 11,500 | ✅ |
| q2_cache_read | 143,000 | 5,000 + Σ(k=1..10)[11,100 + (k-1)×600] = 143,000 | ✅ |
| q2_regular | 600 | 600 (last turn delta) | ✅ |
| q2_sum | 155,100 | 11,500 + 143,000 + 600 = 155,100 ✓ | ✅ |
| session_cw | 97,000 | 16,500 + 7 × 11,500 = 97,000 | ✅ |
| session_cr | 1,139,000 | 138,000 + 7 × 143,000 = 1,139,000 | ✅ |
| session_reg | 4,800 | 600 + 7 × 600 = 4,800 | ✅ |
| session_sum | 1,240,800 | 8 × 155,100 = 1,240,800 ✓ | ✅ |

## Model Cost
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| monthly_cache_write_tokens | 9,700,000,000 | 100,000 × 97,000 = 9,700,000,000 | ✅ |
| monthly_cache_read_tokens | 113,900,000,000 | 100,000 × 1,139,000 = 113,900,000,000 | ✅ |
| monthly_regular_input_tokens | 480,000,000 | 100,000 × 4,800 = 480,000,000 | ✅ |
| monthly_output_tokens | 1,200,000,000 | 100,000 × 12,000 = 1,200,000,000 | ✅ |
| cache_write_cost | $60,625.00 | 9,700 × $6.25 = $60,625.00 | ✅ |
| cache_read_cost | $56,950.00 | 113,900 × $0.50 = $56,950.00 | ✅ |
| regular_input_cost | $2,400.00 | 480 × $5.00 = $2,400.00 | ✅ |
| output_cost | $30,000.00 | 1,200 × $25.00 = $30,000.00 | ✅ |
| **total_model_cost** | **$149,975.00** | **$60,625 + $56,950 + $2,400 + $30,000 = $149,975.00** | ✅ |
| no_cache_input_cost | $620,400.00 | 124,080 × $5.00 = $620,400.00 | ✅ |
| no_cache_output_cost | $30,000.00 | 1,200 × $25.00 = $30,000.00 | ✅ |
| no_cache_total | $650,400.00 | $620,400 + $30,000 = $650,400.00 | ✅ |
| savings_monthly | $500,425.00 | $650,400 − $149,975 = $500,425.00 | ✅ |
| savings_pct | 76.9% | $500,425 / $650,400 × 100 = 76.9% | ✅ |
| total_annual | $1,799,700.00 | $149,975 × 12 = $1,799,700.00 | ✅ |
| per_session | $1.4998 | $149,975 / 100,000 = $1.4998 | ✅ |
| per_question | $0.1875 | $149,975 / 800,000 = $0.1875 | ✅ |

## Capacity Check
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| active_minutes/month | 15,840 | 12 × 60 × 22 = 15,840 | ✅ |
| avg_questions/min | 50.51 | 800,000 / 15,840 = 50.51 | ✅ |
| avg_rpm | 555.6 | 50.51 × 11 = 555.6 | ✅ |
| peak_rpm | 1,667 | 555.6 × 3.0 = 1,667 | ✅ |
| base_context | 11,100 | 100 + 1,000 + 4,000 + 6,000 = 11,100 | ✅ |
| avg_input/turn | 14,100 | 11,100 + (600/2) × 10 = 14,100 | ✅ |
| avg_output/turn | 136 | (10 × 100 + 500) / 11 = 136 | ✅ |
| avg_tpm | 8,211,111 | 555.6 × (14,100 + 136 × 5) = 8,211,111 | ✅ |
| peak_tpm | 24,633,333 | 8,211,111 × 3.0 = 24,633,333 | ✅ |
| max_tokens_overhead | 3,960 | 4,096 − 136 = 3,960 | ✅ |
| effective_peak_tpm | 31,233,333 | 24,633,333 + (1,667 × 3,960) = 31,233,333 | ✅ |
| rpm_fits | ✅ True | 1,667 ≤ 10,000 | ✅ |
| tpm_fits | ❌ False | 31,233,333 > 3,000,000 | ✅ |
| rpm_utilization | 17% | 1,667 / 10,000 × 100 = 17% | ✅ |
| tpm_utilization | 1,041% | 31,233,333 / 3,000,000 × 100 = 1,041% | ✅ |

## Business Value
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| time_saved | 22 min | 30 − 8 = 22 | ✅ |
| effective_sessions (Mod) | 65,000 | 100,000 × 0.65 = 65,000 | ✅ |
| time_saved_hrs (Mod) | 23,833 | 65,000 × 22 / 60 = 23,833 | ✅ |
| productive_hrs (Mod) | 14,300 | 23,833 × 0.60 = 14,300 | ✅ |
| productivity_monthly (Mod) | $7,150,000 | 14,300 × $500 = $7,150,000 | ✅ |
| cost_savings_monthly (Mod) | $2,145,000 | 14,300 × $150 = $2,145,000 | ✅ |
| productive_hrs (Con) | 9,167 | 50,000 × 22/60 × 0.50 = 9,167 | ✅ |
| productivity_monthly (Con) | $4,583,333 | 9,167 × $500 = $4,583,333 | ✅ |
| productive_hrs (Opt) | 20,533 | 80,000 × 22/60 × 0.70 = 20,533 | ✅ |
| productivity_monthly (Opt) | $10,266,667 | 20,533 × $500 = $10,266,667 | ✅ |
| grand_total_annual | $85,800,000 | $7,150,000 × 12 = $85,800,000 | ✅ |
| agent_cost_annual | $1,799,700 | $149,975 × 12 = $1,799,700 | ✅ |
| net_value | $84,000,300 | $85,800,000 − $1,799,700 = $84,000,300 | ✅ |
| roi_pct | 4,667% | ($84,000,300 / $1,799,700) × 100 = 4,667% | ✅ |
| payback_days | ~8 days | ($1,799,700 / $85,800,000) × 365 = 7.7 days | ✅ |

---

## Overall Verdict
| Section | Result |
|---------|:------:|
| Token Profile | ✅ PASS (7/7) |
| Cache Splits | ✅ PASS (12/12) |
| Model Cost | ✅ PASS (17/17) |
| AgentCore Cost | N/A (not requested) |
| Capacity Check | ✅ PASS (14/14) |
| Business Value | ✅ PASS (14/14) |

### Summary
**64 of 64 fields pass.** All token counts, cache splits, cost calculations, capacity metrics, and business value figures match the spec exactly. No discrepancies found.

Key observations for this heavy workload:
- 10 tools → 11 turns/question creates massive token compounding (155,100 input tokens/question)
- Prompt caching saves 76.9% ($500K/mo) — critical for Opus-class pricing
- TPM is severely over quota (1,041% utilization) — requires quota increase + optimization
- Despite $150K/mo model cost, ROI is 4,667% due to high analyst cost ($150/hr) and revenue ($500/hr)
