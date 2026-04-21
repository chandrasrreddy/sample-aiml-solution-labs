# UC-12 QA Verification Result

## Use Case
> "I have a content moderation pipeline that processes 10M documents per month. Each document is 1 question, no tools, 500 input tokens, 50 output tokens. Compare the cost of running this on Claude Haiku 4.5 in Batch mode vs Standard mode in us-west-2."

## Verification Method
Applied pricing_spec_v1.2.md formulas (§2, §3) to the response's stated assumptions. Verified both Standard and Batch tier calculations independently. Special attention to N=0 caching special case (§3.2) and Batch tier pricing (no caching support).

---

## Token Profile

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| cacheable_base | 0 | T_sys + T_tools = 0 + 0 = 0 | ✅ |
| rag_tokens | 0 | N_rag × T_rag_chunk = 0 × 300 = 0 | ✅ |
| base_prompt | 500 | cacheable_base + T_user + rag_tokens = 0 + 500 + 0 = 500 | ✅ |
| delta | 600 | T_call + T_result = 100 + 500 = 600 | ✅ |
| turns | 1 | N_invoke + 1 = 0 + 1 = 1 | ✅ |
| total_input_per_question | 500 | Σ(i=0 to 0)[base_prompt + i × delta] = 500 | ✅ |
| output_per_question | 50 | T_answer + N_invoke × T_call = 50 + 0 × 100 = 50 | ✅ |

**Closed-form verification:**
```
total_input = turns × base_prompt + delta × N × turns / 2
            = 1 × 500 + 600 × 0 × 1 / 2
            = 500 ✅
```

---

## Cache Splits — Standard Mode (N=0 Special Case — §3.2)

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| **Q1 cache_write** | 500 | base_prompt = 500 (§3.2: N=0 → cw = base_prompt) | ✅ |
| **Q1 cache_read** | 0 | 0 (§3.2: N=0 → cr = 0) | ✅ |
| **Q1 regular** | 0 | 0 (§3.2: N=0 → reg = 0) | ✅ |
| Q1 sum | 500 | 500 + 0 + 0 = 500 = total_input_per_question ✅ | ✅ |

### Per-Session Totals (§3.4)

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| n_subsequent | 0 | Q_s - 1 = 1 - 1 = 0 | ✅ |
| session_cw | 500 | q1_cw + 0 × q2_cw = 500 | ✅ |
| session_cr | 0 | q1_cr + 0 × q2_cr = 0 | ✅ |
| session_reg | 0 | q1_reg + 0 × q2_reg = 0 | ✅ |
| **Sum identity** | 500 | 500 + 0 + 0 = 500 = 1 × 500 ✅ | ✅ |

---

## Monthly Token Volumes

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| monthly_input | 5,000,000,000 | 10,000,000 × 500 = 5,000,000,000 | ✅ |
| monthly_output | 500,000,000 | 10,000,000 × 50 = 500,000,000 | ✅ |

---

## Standard Mode — Model Cost

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| cache_write_cost | $6,250.00 | 5,000,000,000 / 1M × $1.25 = $6,250.00 | ✅ |
| cache_read_cost | $0.00 | 0 / 1M × $0.10 = $0.00 | ✅ |
| regular_input_cost | $0.00 | 0 / 1M × $1.00 = $0.00 | ✅ |
| output_cost | $2,500.00 | 500,000,000 / 1M × $5.00 = $2,500.00 | ✅ |
| **total_with_cache** | **$8,750.00** | $6,250.00 + $0.00 + $0.00 + $2,500.00 = **$8,750.00** | ✅ |
| no_cache_input | $5,000.00 | 5,000,000,000 / 1M × $1.00 = $5,000.00 | ✅ |
| no_cache_output | $2,500.00 | 500,000,000 / 1M × $5.00 = $2,500.00 | ✅ |
| **total_no_cache** | **$7,500.00** | $5,000.00 + $2,500.00 = **$7,500.00** | ✅ |
| savings_monthly | -$1,250.00 | $7,500.00 - $8,750.00 = -$1,250.00 | ✅ |
| savings_pct | -16.7% | -$1,250.00 / $7,500.00 × 100 = -16.67% | ✅ |

**Key insight verified:** Caching is more expensive because cache_write price ($1.25/M) > input price ($1.00/M), and with N=0 + 1 Q/session + cacheable_base=0, ALL input tokens are cache-written with zero cache reads. The response correctly recommends using no-cache pricing ($7,500.00/mo).

---

## Batch Mode — Model Cost

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| batch_input_cost | $2,500.00 | 5,000,000,000 / 1M × $0.50 = $2,500.00 | ✅ |
| batch_output_cost | $1,250.00 | 500,000,000 / 1M × $2.50 = $1,250.00 | ✅ |
| **batch_total** | **$3,750.00** | $2,500.00 + $1,250.00 = **$3,750.00** | ✅ |
| batch_annual | $45,000.00 | $3,750.00 × 12 = $45,000.00 | ✅ |
| per_document | $0.000375 | $3,750.00 / 10,000,000 = $0.000375 | ✅ |

**Batch pricing verified:** Batch prices are exactly 50% of Standard prices (input: $0.50 vs $1.00, output: $2.50 vs $5.00). No caching support in Batch mode (cache_read and cache_write are null in cache data).

---

## Tier Comparison

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| Standard monthly | $7,500.00 | No-cache: $5,000.00 + $2,500.00 = $7,500.00 | ✅ |
| Batch monthly | $3,750.00 | $2,500.00 + $1,250.00 = $3,750.00 | ✅ |
| Monthly savings | $3,750.00 | $7,500.00 - $3,750.00 = $3,750.00 | ✅ |
| Savings % | 50.0% | $3,750.00 / $7,500.00 × 100 = 50.0% | ✅ |
| Annual savings | $45,000.00 | $3,750.00 × 12 = $45,000.00 | ✅ |
| Standard per-doc | $0.00075 | $7,500.00 / 10,000,000 = $0.00075 | ✅ |
| Batch per-doc | $0.000375 | $3,750.00 / 10,000,000 = $0.000375 | ✅ |

---

## Pricing Source Verification

| Field | Response | Cache Data | Status |
|-------|:--------:|:----------:|:------:|
| Standard Input | $1.00/M | "Million Input Tokens Global: 1.0000000000" | ✅ |
| Standard Output | $5.00/M | "Million Response Tokens Global: 5.0000000000" | ✅ |
| Standard Cache Read | $0.10/M | "Million Cache Read Input Tokens Global: 0.1000000000" | ✅ |
| Standard Cache Write | $1.25/M | "Million Cache Write Input Tokens Global: 1.2500000000" | ✅ |
| Batch Input | $0.50/M | "Million Batch Input Tokens Global: 0.5000000000" | ✅ |
| Batch Output | $2.50/M | "Million Batch Response Tokens Global: 2.5000000000" | ✅ |
| Batch Cache Read | N/A | Not present in cache data | ✅ |
| Batch Cache Write | N/A | Not present in cache data | ✅ |

---

## N=0 + 1 Q/Session Special Case Verification

| Check | Expected | Actual | Status |
|-------|----------|--------|:------:|
| turns = 1 | 1 | 1 | ✅ |
| total_input = base_prompt | 500 | 500 | ✅ |
| Q1: cw = base_prompt | 500 | 500 | ✅ |
| Q1: cr = 0 | 0 | 0 | ✅ |
| Q1: reg = 0 | 0 | 0 | ✅ |
| No Q2 (n_subsequent = 0) | 0 subsequent Qs | 0 | ✅ |
| Caching more expensive (Standard) | Yes (cw_price > input_price) | -16.7% savings | ✅ |
| Response recommends no-cache for Standard | Yes | Yes | ✅ |
| Batch has no caching | Yes | cache_read=null, cache_write=null | ✅ |

---

## Overall Verdict

| Section | Result |
|---------|:------:|
| Token Profile | ✅ PASS |
| Cache Splits (N=0) | ✅ PASS |
| Monthly Tokens | ✅ PASS |
| Standard Model Cost (with cache) | ✅ PASS |
| Standard Model Cost (no cache) | ✅ PASS |
| Standard Caching Savings | ✅ PASS |
| Batch Model Cost | ✅ PASS |
| Tier Comparison | ✅ PASS |
| Pricing Sources | ✅ PASS |
| N=0 Special Case | ✅ PASS |
| AgentCore | ✅ N/A (correct) |

### Summary

**30 of 30 fields pass.** All token counts, cache splits, cost calculations, and tier comparison figures match the spec formulas exactly. Key verifications:

1. **Standard no-cache cost ($7,500/mo)** correctly computed — caching is counterproductive with cacheable_base=0 and 1 Q/session.
2. **Batch cost ($3,750/mo)** correctly computed at 50% of Standard rates with no caching support.
3. **50% savings** from Batch vs Standard correctly calculated ($3,750/mo = $45,000/yr savings).
4. **Pricing sourced from cache** — all 6 price points verified against raw cache data entries.
5. **Correct recommendation** to use Batch mode for offline content moderation pipeline.
