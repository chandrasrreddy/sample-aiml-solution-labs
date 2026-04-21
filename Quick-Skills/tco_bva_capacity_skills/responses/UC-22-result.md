# UC-22 QA Verification Result

## Use Case
> "I need to build a customer support agent in us-east-1. 500K sessions per month, 5 questions per session, 3 tools. How much will it cost?"

## Verification Method
Applied pricing_spec_v1.2.md formulas to the response's stated assumptions. All values independently recomputed from first principles.

---

## Independent Recomputation

### Input Parameters
- P_in = $3.00/M, P_out = $15.00/M, P_cr = $0.30/M, P_cw = $3.75/M
- S = 500,000, Q_s = 5, N = 3
- T_sys = 1,000, T_tools = 4,000, T_user = 100
- N_rag = 10, T_rag_chunk = 300
- T_call = 100, T_result = 500, T_answer = 100

### §2.1 Base Context
```
rag_tokens = 10 × 300 = 3,000
cacheable_base = 1,000 + 4,000 = 5,000
base_prompt = 5,000 + 100 + 3,000 = 8,100
```

### §2.2–2.3 Tool Delta & Turns
```
delta = 100 + 500 = 600
turns = 3 + 1 = 4
```

### §2.4 Input Tokens Per Question
```
Turn 0: 8,100
Turn 1: 8,100 + 600 = 8,700
Turn 2: 8,100 + 1,200 = 9,300
Turn 3: 8,100 + 1,800 = 9,900
total_input_per_question = 8,100 + 8,700 + 9,300 + 9,900 = 36,000

Closed-form: 4 × 8,100 + 600 × 3 × 4 / 2 = 32,400 + 3,600 = 36,000 ✓
```

### §2.5 Output Tokens Per Question
```
total_output_per_question = 100 + 3 × 100 = 400
```

### §2.6 Monthly Totals
```
questions_per_month = 500,000 × 5 = 2,500,000
monthly_input_tokens = 36,000 × 2,500,000 = 90,000,000,000
monthly_output_tokens = 400 × 2,500,000 = 1,000,000,000
```

### §2.7 No-Cache Cost
```
no_cache_input = (90,000,000,000 / 1,000,000) × 3.00 = 90,000 × 3.00 = $270,000.00
no_cache_output = (1,000,000,000 / 1,000,000) × 15.00 = 1,000 × 15.00 = $15,000.00
no_cache_total = $270,000.00 + $15,000.00 = $285,000.00
```

---

## Cache Splits (§3.3)

### Q1 (N=3 ≥ 1)
```
q1_cache_write = base_prompt + (N-1) × delta = 8,100 + 2 × 600 = 9,300
q1_cache_read = Σ(k=1 to 3) [base_prompt + (k-1) × delta]
             = (8,100 + 0) + (8,100 + 600) + (8,100 + 1,200)
             = 8,100 + 8,700 + 9,300 = 26,100
q1_regular = delta = 600

Verification: 9,300 + 26,100 + 600 = 36,000 = total_input_per_question ✓
```

### Q2+ (N=3 ≥ 1)
```
q2_cache_write = (T_user + rag_tokens) + (N-1) × delta = (100 + 3,000) + 2 × 600 = 3,100 + 1,200 = 4,300
q2_cache_read = cacheable_base + Σ(k=1 to 3) [base_prompt + (k-1) × delta]
             = 5,000 + 26,100 = 31,100
q2_regular = delta = 600

Verification: 4,300 + 31,100 + 600 = 36,000 = total_input_per_question ✓
```

### Per Session (§3.4)
```
n_subsequent = 5 - 1 = 4

session_cw = 9,300 + 4 × 4,300 = 9,300 + 17,200 = 26,500
session_cr = 26,100 + 4 × 31,100 = 26,100 + 124,400 = 150,500
session_reg = 600 + 4 × 600 = 600 + 2,400 = 3,000

Session identity: 26,500 + 150,500 + 3,000 = 180,000 = 5 × 36,000 ✓
```

### Monthly Tokens
```
monthly_cw = 500,000 × 26,500 = 13,250,000,000
monthly_cr = 500,000 × 150,500 = 75,250,000,000
monthly_reg = 500,000 × 3,000 = 1,500,000,000
monthly_out = 500,000 × (5 × 400) = 500,000 × 2,000 = 1,000,000,000
```

### Cache Costs (§3.5)
```
cache_write_cost = (13,250,000,000 / 1,000,000) × 3.75 = 13,250 × 3.75 = $49,687.50
cache_read_cost = (75,250,000,000 / 1,000,000) × 0.30 = 75,250 × 0.30 = $22,575.00
regular_input_cost = (1,500,000,000 / 1,000,000) × 3.00 = 1,500 × 3.00 = $4,500.00
output_cost = (1,000,000,000 / 1,000,000) × 15.00 = 1,000 × 15.00 = $15,000.00

total_model_cost = $49,687.50 + $22,575.00 + $4,500.00 + $15,000.00 = $91,762.50
```

### Savings (§3.6)
```
savings_monthly = $285,000.00 - $91,762.50 = $193,237.50
savings_pct = $193,237.50 / $285,000.00 × 100 = 67.80%
```

---

## Model Cost

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| cacheable_base | 5,000 | 5,000 | ✅ |
| base_prompt | 8,100 | 8,100 | ✅ |
| delta | 600 | 600 | ✅ |
| turns | 4 | 4 | ✅ |
| total_input_per_question | 36,000 | 36,000 | ✅ |
| total_output_per_question | 400 | 400 | ✅ |
| questions_per_month | 2,500,000 | 2,500,000 | ✅ |
| no_cache_input_cost | $270,000.00 | $270,000.00 | ✅ |
| no_cache_output_cost | $15,000.00 | $15,000.00 | ✅ |
| no_cache_total | $285,000.00 | $285,000.00 | ✅ |
| cache_write_cost | $49,687.50 | $49,687.50 | ✅ |
| cache_read_cost | $22,575.00 | $22,575.00 | ✅ |
| regular_input_cost | $4,500.00 | $4,500.00 | ✅ |
| output_cost | $15,000.00 | $15,000.00 | ✅ |
| total_model_cost | $91,762.50 | $91,762.50 | ✅ |
| savings_monthly | $193,237.50 | $193,237.50 | ✅ |
| savings_pct | 67.8% | 67.8% | ✅ |
| annual_cost | $1,101,150.00 | $1,101,150.00 | ✅ |
| per_session | $0.1835 | $91,762.50 / 500,000 = $0.1835 | ✅ |
| per_question | $0.0367 | $91,762.50 / 2,500,000 = $0.0367 | ✅ |

## Cache Splits

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| q1_cache_write | 9,300 | 9,300 | ✅ |
| q1_cache_read | 26,100 | 26,100 | ✅ |
| q1_regular | 600 | 600 | ✅ |
| q1_sum | 36,000 | 36,000 | ✅ |
| q2_cache_write | 4,300 | 4,300 | ✅ |
| q2_cache_read | 31,100 | 31,100 | ✅ |
| q2_regular | 600 | 600 | ✅ |
| q2_sum | 36,000 | 36,000 | ✅ |
| session_cw | 26,500 | 26,500 | ✅ |
| session_cr | 150,500 | 150,500 | ✅ |
| session_reg | 3,000 | 3,000 | ✅ |
| session_identity | 180,000 | 180,000 (= 5 × 36,000) | ✅ |
| monthly_cw | 13,250,000,000 | 13,250,000,000 | ✅ |
| monthly_cr | 75,250,000,000 | 75,250,000,000 | ✅ |
| monthly_reg | 1,500,000,000 | 1,500,000,000 | ✅ |
| monthly_out | 1,000,000,000 | 1,000,000,000 | ✅ |

## Capacity Check

### Independent Recomputation (§6)
```
active_minutes_per_month = 12 × 60 × 22 = 15,840
avg_questions_per_min = 2,500,000 / 15,840 = 157.83
avg_rpm = 157.83 × 4 = 631.31
peak_rpm = 631.31 × 3.0 = 1,893.94

base_context = 100 + 1,000 + 4,000 + 3,000 = 8,100
delta = 600
avg_input_per_turn = 8,100 + (600/2) × 3 = 8,100 + 900 = 9,000
avg_output_per_turn = (3 × 100 + 100) / 4 = 400 / 4 = 100

avg_tpm = 631.31 × (9,000 + 100 × 5) = 631.31 × 9,500 = 5,997,475
peak_tpm = 5,997,475 × 3.0 = 17,992,424

max_tokens_overhead = max(0, 4,096 - 100) = 3,996
effective_peak_tpm = 17,992,424 + (1,893.94 × 3,996) = 17,992,424 + 7,568,184 = 25,560,608

rpm_fits = 1,893.94 ≤ 10,000 → True
tpm_fits = 25,560,608 > 6,000,000 → False
fits = False
```

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| active_minutes_per_month | 15,840 | 15,840 | ✅ |
| avg_questions_per_min | 157.83 | 157.83 | ✅ |
| avg_rpm | 631.31 | 631.31 | ✅ |
| peak_rpm | 1,893.94 | 1,893.94 | ✅ |
| base_context | 8,100 | 8,100 | ✅ |
| avg_input_per_turn | 9,000 | 9,000 | ✅ |
| avg_output_per_turn | 100 | 100 | ✅ |
| avg_tpm | 5,997,475 | 5,997,475 | ✅ |
| peak_tpm | 17,992,424 | 17,992,424 | ✅ |
| max_tokens_overhead | 3,996 | 3,996 | ✅ |
| effective_peak_tpm | 25,560,606 | 25,560,608 | ✅ (rounding) |
| rpm_fits | True | True | ✅ |
| tpm_fits | False | False | ✅ |
| fits | False | False | ✅ |
| rpm_utilization | 18.9% | 18.9% | ✅ |
| tpm_utilization | 426.0% | 426.0% | ✅ |

---

## Overall Verdict

| Section | Result |
|---------|:------:|
| Assumptions (vague handling) | ✅ PASS — Model defaulted to Claude Sonnet 4.6, standard token profile applied |
| Token Profile | ✅ PASS |
| Cache Splits (Q1) | ✅ PASS |
| Cache Splits (Q2+) | ✅ PASS |
| Session Identity | ✅ PASS |
| Monthly Tokens | ✅ PASS |
| No-Cache Baseline | ✅ PASS |
| Cached Cost | ✅ PASS |
| Savings | ✅ PASS |
| Capacity Check | ✅ PASS |

### Summary
**52 of 52 fields pass.** All token counts, cache splits, cost calculations, and capacity checks match the spec within 0.1% tolerance. The session identity (session_cw + session_cr + session_reg = Q_s × total_input_per_question) holds exactly. Vague use case handling correctly applied: model defaulted to Claude Sonnet 4.6, region was specified (us-east-1), and standard token profile used for all unspecified parameters. Prompt caching yields 67.8% savings. The workload does NOT fit in Standard tier — TPM utilization is 426% due to the 5× Claude output burndown rate.

**Verdict: ✅ PASS**
