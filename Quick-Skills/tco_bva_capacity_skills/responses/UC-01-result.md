# UC-01 QA Verification Result

## Use Case
> "Estimate the full cost for an IT helpdesk agent using Claude Sonnet 4.6 in us-east-1. 500K sessions/month, 3 questions per session, 5 tool calls per question (ticket lookup, KB search, status update, escalation check, resolution log). Include AgentCore Runtime, Gateway, and Memory. Then check capacity and calculate business value — currently each ticket takes 15 min manually, with AI it takes 4 min. Human cost is $65/hr."

## Verification Method
Applied pricing_spec_v1.2.md formulas independently in Python to the response's stated assumptions. All intermediate values computed from scratch and compared against the response file.

---

## Token Profile

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| cacheable_base | 5,000 | 1,000 + 4,000 = 5,000 | ✅ |
| rag_tokens | 3,000 | 10 × 300 = 3,000 | ✅ |
| base_prompt | 8,100 | 5,000 + 100 + 3,000 = 8,100 | ✅ |
| delta | 600 | 100 + 500 = 600 | ✅ |
| turns | 6 | 5 + 1 = 6 | ✅ |
| total_input_per_question | 57,600 | 6 × 8,100 + 600 × 5 × 6/2 = 57,600 | ✅ |
| total_output_per_question | 600 | 100 + 5 × 100 = 600 | ✅ |
| questions_per_month | 1,500,000 | 500,000 × 3 = 1,500,000 | ✅ |

## Cache Splits

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| q1_cache_write | 10,500 | 8,100 + 4 × 600 = 10,500 | ✅ |
| q1_cache_read | 46,500 | 8,100 + 8,700 + 9,300 + 9,900 + 10,500 = 46,500 | ✅ |
| q1_regular | 600 | delta = 600 | ✅ |
| q1_sum | 57,600 | 10,500 + 46,500 + 600 = 57,600 ✓ | ✅ |
| q2_cache_write | 5,500 | 3,100 + 4 × 600 = 5,500 | ✅ |
| q2_cache_read | 51,500 | 5,000 + 46,500 = 51,500 | ✅ |
| q2_regular | 600 | delta = 600 | ✅ |
| q2_sum | 57,600 | 5,500 + 51,500 + 600 = 57,600 ✓ | ✅ |
| session_cw | 21,500 | 10,500 + 2 × 5,500 = 21,500 | ✅ |
| session_cr | 149,500 | 46,500 + 2 × 51,500 = 149,500 | ✅ |
| session_reg | 1,800 | 600 + 2 × 600 = 1,800 | ✅ |
| session_sum | 172,800 | 3 × 57,600 = 172,800 ✓ | ✅ |

## Model Cost

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| monthly_cache_write | 10,750,000,000 | 500,000 × 21,500 = 10,750,000,000 | ✅ |
| monthly_cache_read | 74,750,000,000 | 500,000 × 149,500 = 74,750,000,000 | ✅ |
| monthly_regular | 900,000,000 | 500,000 × 1,800 = 900,000,000 | ✅ |
| monthly_output | 900,000,000 | 500,000 × 1,800 = 900,000,000 | ✅ |
| cache_write_cost | $40,312.50 | 10,750 × $3.75 = $40,312.50 | ✅ |
| cache_read_cost | $22,425.00 | 74,750 × $0.30 = $22,425.00 | ✅ |
| regular_input_cost | $2,700.00 | 900 × $3.00 = $2,700.00 | ✅ |
| output_cost | $13,500.00 | 900 × $15.00 = $13,500.00 | ✅ |
| total_model_cost | $78,937.50 | $40,312.50 + $22,425.00 + $2,700.00 + $13,500.00 = $78,937.50 | ✅ |
| no_cache_input | $259,200.00 | 86,400 × $3.00 = $259,200.00 | ✅ |
| no_cache_output | $13,500.00 | 900 × $15.00 = $13,500.00 | ✅ |
| no_cache_total | $272,700.00 | $259,200.00 + $13,500.00 = $272,700.00 | ✅ |
| savings_monthly | $193,762.50 | $272,700.00 - $78,937.50 = $193,762.50 | ✅ |
| savings_pct | 71.1% | $193,762.50 / $272,700.00 × 100 = 71.05% | ✅ |

## AgentCore Cost

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| sessions_per_month | 500,000 | 1,500,000 / 3 = 500,000 | ✅ |
| time_per_question_s | 24.0 | (1+5) × 4.0 = 24.0 | ✅ |
| active_cpu_per_question_s | 7.2 | 24.0 × 0.30 = 7.2 | ✅ |
| active_cpu_per_session_s | 21.6 | 7.2 × 3 = 21.6 | ✅ |
| idle_gaps_s | 60 | (3-1) × 30 = 60 | ✅ |
| session_duration_s | 132.0 | (24.0 × 3) + 60 = 132.0 | ✅ |
| runtime_cpu_cost | $537.00 | 21.6 × 2 × (0.0895/3600) × 500,000 = $537.00 | ✅ |
| runtime_mem_cost | $693.00 | 132.0 × 4 × (0.00945/3600) × 500,000 = $693.00 | ✅ |
| runtime_total | $1,230.00 | $537.00 + $693.00 = $1,230.00 | ✅ |
| gateway_invocations | $45.00 | 6 × 1,500,000 × $0.000005 = $45.00 | ✅ |
| gateway_search | $37.50 | 1,500,000 × $0.000025 = $37.50 | ✅ |
| gateway_indexing | $0.001 | 5 × $0.0002 = $0.001 | ✅ |
| gateway_total | $82.50 | $45.00 + $37.50 + $0.001 = $82.50 | ✅ |
| stm_cost | $750.00 | 2 × 1,500,000 × $0.00025 = $750.00 | ✅ |
| ltm_storage_cost | $1,125.00 | 3 × 500,000 × $0.00075 = $1,125.00 | ✅ |
| ltm_retrieval_cost | $750.00 | 1 × 1,500,000 × $0.0005 = $750.00 | ✅ |
| memory_total | $2,625.00 | $750.00 + $1,125.00 + $750.00 = $2,625.00 | ✅ |
| agentcore_total | $3,937.50 | $1,230.00 + $82.50 + $2,625.00 = $3,937.50 | ✅ |

## Combined Total

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| total_monthly | $82,875.00 | $78,937.50 + $3,937.50 = $82,875.00 | ✅ |
| total_annual | $994,500.00 | $82,875.00 × 12 = $994,500.00 | ✅ |
| per_session | $0.166 | $82,875.00 / 500,000 = $0.1658 | ✅ |
| per_question | $0.055 | $82,875.00 / 1,500,000 = $0.0553 | ✅ |

## Capacity Check

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| active_minutes_per_month | 15,840 | 12 × 60 × 22 = 15,840 | ✅ |
| avg_questions_per_min | 94.70 | 1,500,000 / 15,840 = 94.70 | ✅ |
| avg_rpm | 568.18 | 94.70 × 6 = 568.18 | ✅ |
| peak_rpm | 1,704.55 | 568.18 × 3.0 = 1,704.55 | ✅ |
| base_context | 8,100 | 100 + 1,000 + 4,000 + 3,000 = 8,100 | ✅ |
| avg_input_per_turn | 9,600 | 8,100 + (600/2) × 5 = 9,600 | ✅ |
| avg_output_per_turn | 100 | (5 × 100 + 100) / 6 = 100 | ✅ |
| avg_tpm | 5,738,636 | 568.18 × (9,600 + 100 × 5) = 5,738,636 | ✅ |
| peak_tpm | 17,215,909 | 5,738,636 × 3.0 = 17,215,909 | ✅ |
| max_tokens_overhead | 3,996 | max(0, 4,096 - 100) = 3,996 | ✅ |
| effective_peak_tpm | 24,027,273 | 17,215,909 + (1,704.55 × 3,996) = 24,027,273 | ✅ |
| rpm_fits | True | 1,704.55 ≤ 10,000 → True | ✅ |
| tpm_fits | False | 24,027,273 > 6,000,000 → False | ✅ |
| rpm_utilization | 17.0% | 1,704.55 / 10,000 × 100 = 17.0% | ✅ |
| tpm_utilization | 400.5% | 24,027,273 / 6,000,000 × 100 = 400.5% | ✅ |

## Business Value

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| time_saved_min | 11 | 15 - 4 = 11 | ✅ |
| effective_sessions (Moderate) | 325,000 | 500,000 × 0.65 = 325,000 | ✅ |
| time_saved_hrs | 59,583 | 325,000 × 11 / 60 = 59,583.33 | ✅ |
| productive_hrs | 35,750 | 59,583.33 × 0.60 = 35,750 | ✅ |
| productivity_monthly (Moderate) | $10,725,000 | 35,750 × $300 = $10,725,000 | ✅ |
| cost_savings_monthly (Moderate) | $2,323,750 | 35,750 × $65 = $2,323,750 | ✅ |
| agent_cost_annual | $994,500 | $82,875 × 12 = $994,500 | ✅ |
| grand_total_annual | $128,700,000 | $10,725,000 × 12 = $128,700,000 | ✅ |
| net_value | $127,705,500 | $128,700,000 - $994,500 = $127,705,500 | ✅ |
| roi_pct | 12,841% | ($127,705,500 / $994,500) × 100 = 12,841% | ✅ |
| payback_days | 2.8 | ($994,500 / $128,700,000) × 365 = 2.82 | ✅ |

### Conservative Tier

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| productive_hrs | 22,917 | 500,000 × 0.50 × 11/60 × 0.50 = 22,917 | ✅ |
| productivity_monthly | $6,875,000 | 22,917 × $300 = $6,875,000 | ✅ |
| cost_savings_monthly | $1,489,583 | 22,917 × $65 = $1,489,583 | ✅ |

### Optimistic Tier

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| productive_hrs | 51,333 | 500,000 × 0.80 × 11/60 × 0.70 = 51,333 | ✅ |
| productivity_monthly | $15,400,000 | 51,333 × $300 = $15,400,000 | ✅ |
| cost_savings_monthly | $3,336,667 | 51,333 × $65 = $3,336,667 | ✅ |

---

## Overall Verdict

| Section | Result |
|---------|:------:|
| Token Profile | ✅ PASS (8/8) |
| Cache Splits | ✅ PASS (12/12) |
| Model Cost | ✅ PASS (14/14) |
| AgentCore Cost | ✅ PASS (17/17) |
| Combined Total | ✅ PASS (4/4) |
| Capacity Check | ✅ PASS (16/16) |
| Business Value | ✅ PASS (17/17) |

### Summary
**88 of 88 fields pass.** All intermediate values match within 0.1% tolerance. Token counts, cache splits, cost calculations, AgentCore components, capacity planning, and business value all independently verified against pricing_spec_v1.2.md formulas.

**Verdict: ✅ PASS**
