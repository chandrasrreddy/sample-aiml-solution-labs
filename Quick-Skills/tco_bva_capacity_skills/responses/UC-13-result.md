# UC-13 QA Verification Result

## Use Case
> "Show me the cost difference with and without prompt caching for Claude Sonnet 4.6 in us-east-1. 1M sessions, 5 questions per session, 10 tools invoked, system prompt 2,000 tokens, tool descriptions 4,000 tokens, 10 RAG chunks of 300 tokens each."

## Verification Method
Applied pricing_spec_v1.2.md formulas to the response's stated assumptions. All intermediate values independently computed and compared.

---

## Token Profile

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| rag_tokens | 3,000 | 10 × 300 = 3,000 | ✅ |
| cacheable_base | 6,000 | 2,000 + 4,000 = 6,000 | ✅ |
| base_prompt | 9,100 | 6,000 + 100 + 3,000 = 9,100 | ✅ |
| delta | 600 | 100 + 500 = 600 | ✅ |
| turns | 11 | 10 + 1 = 11 | ✅ |
| total_input_per_question | 133,100 | 11 × 9,100 + 600 × 10 × 11/2 = 133,100 | ✅ |
| total_output_per_question | 1,100 | 100 + 10 × 100 = 1,100 | ✅ |

## Monthly Volumes

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| questions_per_month | 5,000,000 | 1,000,000 × 5 = 5,000,000 | ✅ |
| monthly_input_tokens | 665,500,000,000 | 133,100 × 5,000,000 = 665,500,000,000 | ✅ |
| monthly_output_tokens | 5,500,000,000 | 1,100 × 5,000,000 = 5,500,000,000 | ✅ |

## Cache Splits

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| q1_cache_write | 14,500 | 9,100 + (10−1)×600 = 14,500 | ✅ |
| q1_cache_read | 118,000 | Σ(k=1..10)[9,100+(k−1)×600] = 118,000 | ✅ |
| q1_regular | 600 | delta = 600 | ✅ |
| q1_sum | 133,100 | 14,500+118,000+600 = 133,100 | ✅ |
| q2_cache_write | 8,500 | (100+3,000)+(10−1)×600 = 8,500 | ✅ |
| q2_cache_read | 124,000 | 6,000+Σ(k=1..10)[9,100+(k−1)×600] = 124,000 | ✅ |
| q2_regular | 600 | delta = 600 | ✅ |
| q2_sum | 133,100 | 8,500+124,000+600 = 133,100 | ✅ |
| session_cw | 48,500 | 14,500+4×8,500 = 48,500 | ✅ |
| session_cr | 614,000 | 118,000+4×124,000 = 614,000 | ✅ |
| session_reg | 3,000 | 600+4×600 = 3,000 | ✅ |
| session_sum | 665,500 | 48,500+614,000+3,000 = 665,500 = 5×133,100 | ✅ |

## Monthly Token Totals

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| monthly_cache_write | 48,500,000,000 | 1,000,000 × 48,500 = 48,500,000,000 | ✅ |
| monthly_cache_read | 614,000,000,000 | 1,000,000 × 614,000 = 614,000,000,000 | ✅ |
| monthly_regular_input | 3,000,000,000 | 1,000,000 × 3,000 = 3,000,000,000 | ✅ |
| monthly_output | 5,500,000,000 | 1,000,000 × 5,500 = 5,500,000,000 | ✅ |

## Model Cost (With Cache)

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| cache_write_cost | $181,875.00 | 48,500M × $3.75/M = $181,875.00 | ✅ |
| cache_read_cost | $184,200.00 | 614,000M × $0.30/M = $184,200.00 | ✅ |
| regular_input_cost | $9,000.00 | 3,000M × $3.00/M = $9,000.00 | ✅ |
| output_cost | $82,500.00 | 5,500M × $15.00/M = $82,500.00 | ✅ |
| total_monthly | $457,575.00 | $181,875+$184,200+$9,000+$82,500 = $457,575.00 | ✅ |
| total_annual | $5,490,900.00 | $457,575 × 12 = $5,490,900.00 | ✅ |

## Model Cost (No Cache — Baseline)

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| input_cost | $1,996,500.00 | 665,500M × $3.00/M = $1,996,500.00 | ✅ |
| output_cost | $82,500.00 | 5,500M × $15.00/M = $82,500.00 | ✅ |
| total_monthly | $2,079,000.00 | $1,996,500+$82,500 = $2,079,000.00 | ✅ |
| total_annual | $24,948,000.00 | $2,079,000 × 12 = $24,948,000.00 | ✅ |

## Savings

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| savings_monthly | $1,621,425.00 | $2,079,000−$457,575 = $1,621,425.00 | ✅ |
| savings_annual | $19,457,100.00 | $1,621,425 × 12 = $19,457,100.00 | ✅ |
| savings_pct | 78.0% | $1,621,425/$2,079,000 × 100 = 78.0% | ✅ |

## Per-Unit Costs

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| per_session | $0.4576 | $457,575/1,000,000 = $0.4576 | ✅ |
| per_question | $0.0915 | $457,575/5,000,000 = $0.0915 | ✅ |

---

## Overall Verdict

| Section | Result |
|---------|:------:|
| Token Profile | ✅ PASS (7/7) |
| Monthly Volumes | ✅ PASS (3/3) |
| Cache Splits | ✅ PASS (12/12) |
| Model Cost (With Cache) | ✅ PASS (6/6) |
| Model Cost (No Cache) | ✅ PASS (4/4) |
| Savings | ✅ PASS (3/3) |
| Per-Unit Costs | ✅ PASS (2/2) |

### Summary
**37 of 37 fields pass.** All token counts, cache splits, cost calculations, and savings percentages match the spec exactly. The session-aware caching model identity (session_cw + session_cr + session_reg = Q_s × total_input_per_question) holds. No AgentCore, capacity, or business value sections were required for this pricing-only use case.
