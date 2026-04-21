# UC-04 QA Verification Result

## Use Case
> Cost estimate for a product recommendation chatbot for an online retailer. Nova Pro in us-east-1. 2M sessions/month, 4 questions per session. 3 tools (product search, inventory check, cart add). RAG with 8 chunks of product catalog data. Calculate business value — the retailer has $5B annual revenue and expects 3% sales increase from better CX. Also check if this fits in Standard tier.

## Verification Method
Applied pricing_spec_v1.2.md formulas to the response's stated assumptions. All values independently recomputed from first principles.

---

## Independent Recomputation

### Input Parameters
- P_in = $0.80/M, P_out = $3.20/M, P_cr = $0.20/M, P_cw = $0.00/M
- S = 2,000,000, Q_s = 4, N = 3
- T_sys = 1,000, T_tools = 4,000, T_user = 100
- N_rag = 8, T_rag_chunk = 300
- T_call = 100, T_result = 500, T_answer = 100

### §2.1 Base Context
```
rag_tokens = 8 × 300 = 2,400
cacheable_base = 1,000 + 4,000 = 5,000
base_prompt = 5,000 + 100 + 2,400 = 7,500
```

### §2.2–2.3 Tool Delta & Turns
```
delta = 100 + 500 = 600
turns = 3 + 1 = 4
```

### §2.4 Input Tokens Per Question
```
Turn 0: 7,500
Turn 1: 7,500 + 600 = 8,100
Turn 2: 7,500 + 1,200 = 8,700
Turn 3: 7,500 + 1,800 = 9,300
total_input_per_question = 7,500 + 8,100 + 8,700 + 9,300 = 33,600

Closed-form: 4 × 7,500 + 600 × 3 × 4 / 2 = 30,000 + 3,600 = 33,600 ✓
```

### §2.5 Output Tokens Per Question
```
total_output_per_question = 100 + 3 × 100 = 400
```

### §2.6 Monthly Totals
```
questions_per_month = 2,000,000 × 4 = 8,000,000
monthly_input_tokens = 33,600 × 8,000,000 = 268,800,000,000
monthly_output_tokens = 400 × 8,000,000 = 3,200,000,000
```

### §2.7 No-Cache Cost
```
no_cache_input = (268,800,000,000 / 1,000,000) × 0.80 = 268,800 × 0.80 = $215,040.00
no_cache_output = (3,200,000,000 / 1,000,000) × 3.20 = 3,200 × 3.20 = $10,240.00
no_cache_total = $215,040.00 + $10,240.00 = $225,280.00
```

---

## Cache Splits (§3.3)

### Q1 (N=3 ≥ 1)
```
q1_cache_write = base_prompt + (N-1) × delta = 7,500 + 2 × 600 = 8,700
q1_cache_read = Σ(k=1 to 3) [base_prompt + (k-1) × delta]
             = (7,500 + 0) + (7,500 + 600) + (7,500 + 1,200)
             = 7,500 + 8,100 + 8,700 = 24,300
q1_regular = delta = 600

Verification: 8,700 + 24,300 + 600 = 33,600 = total_input_per_question ✓
```

### Q2+ (N=3 ≥ 1)
```
q2_cache_write = (T_user + rag_tokens) + (N-1) × delta = (100 + 2,400) + 2 × 600 = 2,500 + 1,200 = 3,700
q2_cache_read = cacheable_base + Σ(k=1 to 3) [base_prompt + (k-1) × delta]
             = 5,000 + 24,300 = 29,300
q2_regular = delta = 600

Verification: 3,700 + 29,300 + 600 = 33,600 = total_input_per_question ✓
```

### Per Session (§3.4)
```
n_subsequent = 4 - 1 = 3

session_cw = 8,700 + 3 × 3,700 = 8,700 + 11,100 = 19,800
session_cr = 24,300 + 3 × 29,300 = 24,300 + 87,900 = 112,200
session_reg = 600 + 3 × 600 = 600 + 1,800 = 2,400

Session identity: 19,800 + 112,200 + 2,400 = 134,400 = 4 × 33,600 ✓
```

### Monthly Tokens
```
monthly_cw = 2,000,000 × 19,800 = 39,600,000,000
monthly_cr = 2,000,000 × 112,200 = 224,400,000,000
monthly_reg = 2,000,000 × 2,400 = 4,800,000,000
monthly_out = 2,000,000 × (4 × 400) = 2,000,000 × 1,600 = 3,200,000,000
```

### Cache Costs (§3.5)
```
cache_write_cost = (39,600,000,000 / 1,000,000) × 0.00 = $0.00
cache_read_cost = (224,400,000,000 / 1,000,000) × 0.20 = 224,400 × 0.20 = $44,880.00
regular_input_cost = (4,800,000,000 / 1,000,000) × 0.80 = 4,800 × 0.80 = $3,840.00
output_cost = (3,200,000,000 / 1,000,000) × 3.20 = 3,200 × 3.20 = $10,240.00

total_model_cost = $0.00 + $44,880.00 + $3,840.00 + $10,240.00 = $58,960.00
```

### Savings (§3.6)
```
savings_monthly = $225,280.00 - $58,960.00 = $166,320.00
savings_pct = $166,320.00 / $225,280.00 × 100 = 73.83% ≈ 73.8%
```

---

## Model Cost

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| cacheable_base | 5,000 | 5,000 | ✅ |
| base_prompt | 7,500 | 7,500 | ✅ |
| delta | 600 | 600 | ✅ |
| turns | 4 | 4 | ✅ |
| total_input_per_question | 33,600 | 33,600 | ✅ |
| total_output_per_question | 400 | 400 | ✅ |
| questions_per_month | 8,000,000 | 8,000,000 | ✅ |
| no_cache_input_cost | $215,040.00 | $215,040.00 | ✅ |
| no_cache_output_cost | $10,240.00 | $10,240.00 | ✅ |
| no_cache_total | $225,280.00 | $225,280.00 | ✅ |
| cache_write_cost | $0.00 | $0.00 | ✅ |
| cache_read_cost | $44,880.00 | $44,880.00 | ✅ |
| regular_input_cost | $3,840.00 | $3,840.00 | ✅ |
| output_cost | $10,240.00 | $10,240.00 | ✅ |
| total_model_cost | $58,960.00 | $58,960.00 | ✅ |
| savings_monthly | $166,320.00 | $166,320.00 | ✅ |
| savings_pct | 73.8% | 73.8% | ✅ |
| annual_cost | $707,520.00 | $707,520.00 | ✅ |
| per_session | $0.0295 | $0.0295 | ✅ |
| per_question | $0.0074 | $0.0074 | ✅ |

## Cache Splits

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| q1_cache_write | 8,700 | 8,700 | ✅ |
| q1_cache_read | 24,300 | 24,300 | ✅ |
| q1_regular | 600 | 600 | ✅ |
| q1_sum | 33,600 | 33,600 | ✅ |
| q2_cache_write | 3,700 | 3,700 | ✅ |
| q2_cache_read | 29,300 | 29,300 | ✅ |
| q2_regular | 600 | 600 | ✅ |
| q2_sum | 33,600 | 33,600 | ✅ |
| session_cw | 19,800 | 19,800 | ✅ |
| session_cr | 112,200 | 112,200 | ✅ |
| session_reg | 2,400 | 2,400 | ✅ |
| session_identity | 134,400 | 134,400 (= 4 × 33,600) | ✅ |
| monthly_cw | 39,600,000,000 | 39,600,000,000 | ✅ |
| monthly_cr | 224,400,000,000 | 224,400,000,000 | ✅ |
| monthly_reg | 4,800,000,000 | 4,800,000,000 | ✅ |
| monthly_out | 3,200,000,000 | 3,200,000,000 | ✅ |

## Capacity Check

### Independent Recomputation (§6)
```
active_minutes_per_month = 12 × 60 × 22 = 15,840
avg_questions_per_min = 8,000,000 / 15,840 = 505.05
avg_rpm = 505.05 × 4 = 2,020.20
peak_rpm = 2,020.20 × 3.0 = 6,060.61

base_context = 100 + 1,000 + 4,000 + 2,400 = 7,500
delta = 600
avg_input_per_turn = 7,500 + (600/2) × 3 = 7,500 + 900 = 8,400
avg_output_per_turn = (3 × 100 + 100) / 4 = 400 / 4 = 100

avg_tpm = 2,020.20 × (8,400 + 100 × 1) = 2,020.20 × 8,500 = 17,171,717
peak_tpm = 17,171,717 × 3.0 = 51,515,152

max_tokens_overhead = max(0, 4,096 - 100) = 3,996
effective_peak_tpm = 51,515,152 + (6,060.61 × 3,996) = 51,515,152 + 24,218,198 = 75,733,350

rpm_fits = 6,060.61 ≤ 250 → False
tpm_fits = 75,733,350 ≤ 1,000,000 → False
fits = False
```

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| active_minutes_per_month | 15,840 | 15,840 | ✅ |
| avg_questions_per_min | 505.05 | 505.05 | ✅ |
| avg_rpm | 2,020.2 | 2,020.20 | ✅ |
| peak_rpm | 6,060.6 | 6,060.61 | ✅ |
| avg_input_per_turn | 8,400 | 8,400 | ✅ |
| avg_output_per_turn | 100 | 100 | ✅ |
| avg_tpm | 17,171,717 | 17,171,717 | ✅ |
| peak_tpm | 51,515,152 | 51,515,152 | ✅ |
| max_tokens_overhead | 3,996 | 3,996 | ✅ |
| effective_peak_tpm | 75,733,333 | 75,733,350 | ✅ (rounding) |
| rpm_fits | False | False | ✅ |
| tpm_fits | False | False | ✅ |
| fits | False | False | ✅ |
| rpm_utilization | 2,424% | 2,424.2% | ✅ |
| tpm_utilization | 7,573% | 7,573.3% | ✅ |

## Business Value

### Independent Recomputation (§8)

#### Dimension 1a — Productivity (Moderate)
```
time_saved = 20 - 10 = 10 min
effective_sessions = 2,000,000 × 0.65 = 1,300,000
time_saved_hrs = 1,300,000 × 10 / 60 = 216,666.67
productive_hrs = 216,666.67 × 0.60 = 130,000
productivity_monthly = 130,000 × $300 = $39,000,000
productivity_annual = $39,000,000 × 12 = $468,000,000
```

#### Dimension 1b — Cost Savings (Moderate)
```
cost_savings_monthly = 130,000 × $75 = $9,750,000
cost_savings_annual = $9,750,000 × 12 = $117,000,000
```

#### Dimension 3 — Sales Increase
```
dim3_annual = $5,000,000,000 × 3.0% = $150,000,000
```

#### Summary
```
grand_total = $468,000,000 + $150,000,000 = $618,000,000
agent_cost_annual = $58,960 × 12 = $707,520
net_value = $618,000,000 - $707,520 = $617,292,480
roi_pct = ($617,292,480 / $707,520) × 100 = 87,247%
payback_days = ($707,520 / $618,000,000) × 365 = 0.42 days
```

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| time_saved_min | 10 | 10 | ✅ |
| effective_sessions (Moderate) | 1,300,000 | 1,300,000 | ✅ |
| productive_hrs (Moderate) | 130,000 | 130,000 | ✅ |
| productivity_monthly (Moderate) | $39,000,000 | $39,000,000 | ✅ |
| productivity_annual (Moderate) | $468,000,000 | $468,000,000 | ✅ |
| cost_savings_monthly (Moderate) | $9,750,000 | $9,750,000 | ✅ |
| dim3_annual | $150,000,000 | $150,000,000 | ✅ |
| grand_total_annual | $618,000,000 | $618,000,000 | ✅ |
| agent_cost_annual | $707,520 | $707,520 | ✅ |
| net_value | $617,292,480 | $617,292,480 | ✅ |
| roi_pct | 87,247% | 87,247% | ✅ |
| payback_days | < 1 day | 0.42 days | ✅ |
| Conservative productive_hrs | 83,333 | 83,333 | ✅ |
| Conservative productivity/mo | $25,000,000 | $25,000,000 | ✅ |
| Optimistic productive_hrs | 186,667 | 186,667 | ✅ |
| Optimistic productivity/mo | $56,000,000 | $56,000,000 | ✅ |

---

## Overall Verdict

| Section | Result |
|---------|:------:|
| Token Profile | ✅ PASS |
| Cache Splits (Q1) | ✅ PASS |
| Cache Splits (Q2+) | ✅ PASS |
| Session Identity | ✅ PASS |
| Monthly Tokens | ✅ PASS |
| No-Cache Baseline | ✅ PASS |
| Cached Cost | ✅ PASS |
| Savings | ✅ PASS |
| Capacity Check | ✅ PASS |
| Business Value (Dim 1) | ✅ PASS |
| Business Value (Dim 3) | ✅ PASS |
| Business Value (Summary) | ✅ PASS |

### Summary
**55 of 55 fields pass.** All token counts, cache splits, cost calculations, capacity checks, and business value computations match the spec within 0.1% tolerance. The session identity (session_cw + session_cr + session_reg = Q_s × total_input_per_question) holds exactly. Nova Pro's free cache writes ($0.00/M) are correctly handled, yielding 73.8% caching savings. The workload does NOT fit in Standard tier — both RPM (2,424%) and TPM (7,573%) massively exceed quotas.
