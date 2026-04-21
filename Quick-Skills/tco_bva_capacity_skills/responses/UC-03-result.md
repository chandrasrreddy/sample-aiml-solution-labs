# UC-03 QA Verification Result

## Use Case
> "Price an agent that reviews legal contracts. Claude Opus 4.6 in eu-west-1. 50K sessions/month, 1 question per session (upload doc, get analysis). No tools — pure document analysis. Large RAG: 20 chunks of 500 tokens each. System prompt is 3,000 tokens. Output is long — 1,000 tokens per response. Include capacity check and business value — lawyers spend 45 min per contract review, AI reduces to 10 min, cost is $250/hr."

## Verification Method
Applied pricing_spec_v1.2.md formulas (§2, §3, §6, §8) to the response's stated assumptions. Special attention to N=0 caching special case (§3.2).

---

## Token Profile

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| cacheable_base | 3,000 | T_sys + T_tools = 3,000 + 0 = 3,000 | ✅ |
| rag_tokens | 10,000 | N_rag × T_rag_chunk = 20 × 500 = 10,000 | ✅ |
| base_prompt | 13,100 | cacheable_base + T_user + rag_tokens = 3,000 + 100 + 10,000 = 13,100 | ✅ |
| delta | 600 | T_call + T_result = 100 + 500 = 600 | ✅ |
| turns | 1 | N_invoke + 1 = 0 + 1 = 1 | ✅ |
| total_input_per_question | 13,100 | Σ(i=0 to 0)[base_prompt + i × delta] = 13,100 | ✅ |
| output_per_question | 1,000 | T_answer + N_invoke × T_call = 1,000 + 0 × 100 = 1,000 | ✅ |

**Closed-form verification:**
```
total_input = turns × base_prompt + delta × N × turns / 2
            = 1 × 13,100 + 600 × 0 × 1 / 2
            = 13,100 ✅
```

---

## Cache Splits (N=0 Special Case — §3.2)

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| **Q1 cache_write** | 13,100 | base_prompt = 13,100 (§3.2: N=0 → cw = base_prompt) | ✅ |
| **Q1 cache_read** | 0 | 0 (§3.2: N=0 → cr = 0) | ✅ |
| **Q1 regular** | 0 | 0 (§3.2: N=0 → reg = 0) | ✅ |
| Q1 sum | 13,100 | 13,100 + 0 + 0 = 13,100 = total_input_per_question ✅ | ✅ |
| **Q2 cache_write** | 10,100 | T_user + rag_tokens = 100 + 10,000 = 10,100 (§3.2) | ✅ |
| **Q2 cache_read** | 3,000 | cacheable_base = 3,000 (§3.2) | ✅ |
| **Q2 regular** | 0 | 0 (§3.2) | ✅ |
| Q2 sum | 13,100 | 10,100 + 3,000 + 0 = 13,100 = total_input_per_question ✅ | ✅ |

**Note:** Q2 values are computed by the function but not used because n_subsequent = 0 (only 1 question per session).

### Per-Session Totals (§3.4)

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| n_subsequent | 0 | Q_s - 1 = 1 - 1 = 0 | ✅ |
| session_cw | 13,100 | q1_cw + 0 × q2_cw = 13,100 + 0 = 13,100 | ✅ |
| session_cr | 0 | q1_cr + 0 × q2_cr = 0 + 0 = 0 | ✅ |
| session_reg | 0 | q1_reg + 0 × q2_reg = 0 + 0 = 0 | ✅ |
| **Sum identity** | 13,100 | 13,100 + 0 + 0 = 13,100 = 1 × 13,100 ✅ | ✅ |

---

## Monthly Token Volumes

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| monthly_cache_write | 655,000,000 | 50,000 × 13,100 = 655,000,000 | ✅ |
| monthly_cache_read | 0 | 50,000 × 0 = 0 | ✅ |
| monthly_regular_input | 0 | 50,000 × 0 = 0 | ✅ |
| monthly_output | 50,000,000 | 50,000 × 1,000 = 50,000,000 | ✅ |

---

## Model Cost

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| cache_write_cost | $4,093.75 | 655,000,000 / 1M × $6.25 = $4,093.75 | ✅ |
| cache_read_cost | $0.00 | 0 / 1M × $0.50 = $0.00 | ✅ |
| regular_input_cost | $0.00 | 0 / 1M × $5.00 = $0.00 | ✅ |
| output_cost | $1,250.00 | 50,000,000 / 1M × $25.00 = $1,250.00 | ✅ |
| **total_with_cache** | **$5,343.75** | $4,093.75 + $0.00 + $0.00 + $1,250.00 = **$5,343.75** | ✅ |
| no_cache_input | $3,275.00 | 50,000 × 13,100 / 1M × $5.00 = $3,275.00 | ✅ |
| no_cache_output | $1,250.00 | 50,000 × 1,000 / 1M × $25.00 = $1,250.00 | ✅ |
| **total_no_cache** | **$4,525.00** | $3,275.00 + $1,250.00 = **$4,525.00** | ✅ |
| savings_monthly | -$818.75 | $4,525.00 - $5,343.75 = -$818.75 | ✅ |
| savings_pct | -18.1% | -$818.75 / $4,525.00 × 100 = -18.09% | ✅ |

**Key insight verified:** Caching is more expensive because cache_write price ($6.25/M) > input price ($5.00/M), and with N=0 + 1 Q/session, ALL input tokens are cache-written with zero cache reads. The response correctly recommends using no-cache pricing.

---

## AgentCore Cost

Not applicable — pure document analysis, no AgentCore requested. ✅

---

## Capacity Check (§6)

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| active_min/month | 15,840 | 12 × 60 × 22 = 15,840 | ✅ |
| avg Q/min | 3.16 | 50,000 / 15,840 = 3.1566 | ✅ |
| avg RPM | 3.16 | 3.1566 × 1 = 3.16 | ✅ |
| peak RPM | 9.47 | 3.16 × 3.0 = 9.47 | ✅ |
| base_context | 13,100 | 100 + 3,000 + 0 + 10,000 = 13,100 | ✅ |
| avg_input/turn | 13,100 | 13,100 + (600/2) × 0 = 13,100 | ✅ |
| avg_output/turn | 1,000 | (0 × 100 + 1,000) / 1 = 1,000 | ✅ |
| avg TPM | 57,134 | 3.16 × (13,100 + 1,000 × 5) = 57,134 | ✅ |
| peak TPM | 171,402 | 57,134 × 3.0 = 171,402 | ✅ |
| max_tokens overhead | 3,096 | max(0, 4,096 - 1,000) = 3,096 | ✅ |
| effective peak TPM | 200,720 | 171,402 + (9.47 × 3,096) = 200,721 | ✅ (rounding) |
| RPM fits | True | 9.47 ≤ 10,000 → True | ✅ |
| TPM fits | True | 200,720 ≤ 3,000,000 → True | ✅ |
| RPM utilization | 0.1% | (9.47 / 10,000) × 100 = 0.09% | ✅ |
| TPM utilization | 6.7% | (200,720 / 3,000,000) × 100 = 6.69% | ✅ |

---

## Business Value (§8)

### Dimension 1 — Time Savings (Moderate Tier: E=0.65, F=0.60)

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| time_saved | 35 min | 45 - 10 = 35 | ✅ |
| effective_sessions | 32,500 | 50,000 × 0.65 = 32,500 | ✅ |
| time_saved_hrs | 18,958.33 | 32,500 × 35 / 60 = 18,958.33 | ✅ |
| productive_hrs | 11,375 | 18,958.33 × 0.60 = 11,375 | ✅ |
| Dim 1a (productivity) | $5,687,500/mo | 11,375 × $500 = $5,687,500 | ✅ |
| Dim 1b (cost savings) | $2,843,750/mo | 11,375 × $250 = $2,843,750 | ✅ |

### All Tiers Verification

| Tier | E | F | Productive Hrs | 1a Monthly | 1b Monthly | Status |
|------|:-:|:-:|---------------:|-----------:|-----------:|:------:|
| Conservative | 0.50 | 0.50 | 7,292 | $3,645,833 | $1,822,917 | ✅ |
| Moderate | 0.65 | 0.60 | 11,375 | $5,687,500 | $2,843,750 | ✅ |
| Optimistic | 0.80 | 0.70 | 16,333 | $8,166,667 | $4,083,333 | ✅ |

**Conservative check:** 50,000 × 0.50 = 25,000 × 35/60 = 14,583.33 × 0.50 = 7,291.67 hrs → $3,645,833 ✅
**Optimistic check:** 50,000 × 0.80 = 40,000 × 35/60 = 23,333.33 × 0.70 = 16,333.33 hrs → $8,166,667 ✅

### ROI Summary (§8.5)

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| grand_total_annual | $68,250,000 | $5,687,500 × 12 = $68,250,000 | ✅ |
| agent_cost_annual | $54,300 | $4,525 × 12 = $54,300 | ✅ |
| net_value | $68,195,700 | $68,250,000 - $54,300 = $68,195,700 | ✅ |
| ROI % | 125,590% | ($68,195,700 / $54,300) × 100 = 125,590% | ✅ |
| payback_days | < 1 day | ($54,300 / $68,250,000) × 365 = 0.29 days | ✅ |

---

## N=0 Special Case Verification Points

| Check | Expected | Actual | Status |
|-------|----------|--------|:------:|
| turns = 1 | 1 | 1 | ✅ |
| total_input = base_prompt | 13,100 | 13,100 | ✅ |
| Q1: cw = base_prompt | 13,100 | 13,100 | ✅ |
| Q1: cr = 0 | 0 | 0 | ✅ |
| Q1: reg = 0 | 0 | 0 | ✅ |
| No Q2 (n_subsequent = 0) | 0 subsequent Qs | 0 | ✅ |
| Session totals = Q1 totals | cw=13,100, cr=0, reg=0 | cw=13,100, cr=0, reg=0 | ✅ |
| Cache more expensive than no-cache | Yes (cw_price > input_price) | -18.1% savings | ✅ |
| Response recommends no-cache | Yes | Yes | ✅ |

---

## Overall Verdict

| Section | Result |
|---------|:------:|
| Token Profile | ✅ PASS |
| Cache Splits (N=0) | ✅ PASS |
| Monthly Tokens | ✅ PASS |
| Model Cost (with cache) | ✅ PASS |
| Model Cost (no cache) | ✅ PASS |
| Caching Savings | ✅ PASS |
| AgentCore | ✅ N/A (correct) |
| Capacity Check | ✅ PASS |
| Business Value | ✅ PASS |
| N=0 Special Case | ✅ PASS |

### Summary

**37 of 37 fields pass.** All token counts, cache splits, cost calculations, capacity metrics, and business value figures match the spec formulas exactly. The N=0 special case is correctly handled — single turn, single question per session, with the correct observation that caching is counterproductive when cache_write price exceeds input price and there are no cache reads.
