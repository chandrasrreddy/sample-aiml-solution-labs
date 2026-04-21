# UC-08 QA Verification Result

## Use Case
> Estimate costs for a quality control agent in a factory. Claude Sonnet 4.6 in eu-central-1. 300K sessions/month, 2 questions per session. 6 tools (defect image analyzer, production line status, parts inventory, maintenance scheduler, quality report generator, supplier lookup). Include BrowserTool for accessing the factory dashboard. Business value: QC inspections take 10 min manually, 3 min with AI, inspector cost $35/hr.

## Verification Method
Applied pricing_spec_v1.2.md formulas to the response's stated assumptions. All intermediate values independently recomputed.

---

## Input Parameters

| Parameter | Value |
|-----------|-------|
| P_in | $3.00/M |
| P_out | $15.00/M |
| P_cr | $0.30/M |
| P_cw | $3.75/M |
| S (sessions/month) | 300,000 |
| Q_s (questions/session) | 2 |
| T_sys | 1,000 |
| T_tools | 4,000 |
| T_user | 100 |
| N_rag | 10 |
| T_rag_chunk | 300 |
| N_invoke | 6 |
| T_call | 100 |
| T_result | 500 |
| T_answer | 100 |

---

## Token Calculations (Spec §2)

```
rag_tokens = 10 × 300 = 3,000
cacheable_base = 1,000 + 4,000 = 5,000
base_prompt = 5,000 + 100 + 3,000 = 8,100
delta = 100 + 500 = 600
turns = 6 + 1 = 7

total_input_per_question:
  Turn 0: 8,100
  Turn 1: 8,100 + 600 = 8,700
  Turn 2: 8,100 + 1,200 = 9,300
  Turn 3: 8,100 + 1,800 = 9,900
  Turn 4: 8,100 + 2,400 = 10,500
  Turn 5: 8,100 + 3,000 = 11,100
  Turn 6: 8,100 + 3,600 = 11,700
  Sum = 69,300

Closed-form check: 7 × 8,100 + 600 × 6 × 7 / 2 = 56,700 + 12,600 = 69,300 ✓

total_output_per_question = 100 + 6 × 100 = 700
questions_per_month = 300,000 × 2 = 600,000
monthly_input_tokens = 69,300 × 600,000 = 41,580,000,000
monthly_output_tokens = 700 × 600,000 = 420,000,000
```

## Model Cost

### No-Cache Baseline (Spec §2.7)

```
no_cache_input_cost = (41,580,000,000 / 1,000,000) × 3.00 = $124,740.00
no_cache_output_cost = (420,000,000 / 1,000,000) × 15.00 = $6,300.00
no_cache_total = $124,740.00 + $6,300.00 = $131,040.00
```

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| no_cache_input_cost | $124,740.00 | $124,740.00 | ✅ |
| no_cache_output_cost | $6,300.00 | $6,300.00 | ✅ |
| no_cache_total | $131,040.00 | $131,040.00 | ✅ |

---

## Cache Splits (Spec §3.3)

### Q1 (N=6, N≥1 case)

```
q1_cache_write = base_prompt + (N-1) × delta = 8,100 + 5 × 600 = 11,100
q1_cache_read = Σ(k=1 to 6) [base_prompt + (k-1) × delta]
  = (8,100 + 0) + (8,100 + 600) + (8,100 + 1,200) + (8,100 + 1,800) + (8,100 + 2,400) + (8,100 + 3,000)
  = 8,100 + 8,700 + 9,300 + 9,900 + 10,500 + 11,100
  = 57,600
q1_regular = delta = 600

Verification: 11,100 + 57,600 + 600 = 69,300 = total_input_per_question ✓
```

### Q2+ (Spec §3.3)

```
q2_cache_write = (T_user + rag_tokens) + (N-1) × delta = (100 + 3,000) + 5 × 600 = 3,100 + 3,000 = 6,100
q2_cache_read = cacheable_base + Σ(k=1 to 6) [base_prompt + (k-1) × delta]
  = 5,000 + 57,600 = 62,600
q2_regular = delta = 600

Verification: 6,100 + 62,600 + 600 = 69,300 = total_input_per_question ✓
```

### Per-Session (Spec §3.4)

```
n_subsequent = 2 - 1 = 1

session_cw = 11,100 + 1 × 6,100 = 17,200
session_cr = 57,600 + 1 × 62,600 = 120,200
session_reg = 600 + 1 × 600 = 1,200

Verification: 17,200 + 120,200 + 1,200 = 138,600 = 2 × 69,300 = 138,600 ✓
```

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| q1_cache_write | 11,100 | 11,100 | ✅ |
| q1_cache_read | 57,600 | 57,600 | ✅ |
| q1_regular | 600 | 600 | ✅ |
| q2_cache_write | 6,100 | 6,100 | ✅ |
| q2_cache_read | 62,600 | 62,600 | ✅ |
| q2_regular | 600 | 600 | ✅ |
| session_cw | 17,200 | 17,200 | ✅ |
| session_cr | 120,200 | 120,200 | ✅ |
| session_reg | 1,200 | 1,200 | ✅ |
| session sum identity | 138,600 | 138,600 (= 2 × 69,300) | ✅ |

---

## Monthly Tokens & Costs (Spec §3.4–3.5)

```
monthly_cache_write = 300,000 × 17,200 = 5,160,000,000
monthly_cache_read = 300,000 × 120,200 = 36,060,000,000
monthly_regular_input = 300,000 × 1,200 = 360,000,000
monthly_output = 300,000 × (2 × 700) = 420,000,000

cache_write_cost = (5,160,000,000 / 1,000,000) × 3.75 = 5,160 × 3.75 = $19,350.00
cache_read_cost = (36,060,000,000 / 1,000,000) × 0.30 = 36,060 × 0.30 = $10,818.00
regular_input_cost = (360,000,000 / 1,000,000) × 3.00 = 360 × 3.00 = $1,080.00
output_cost = (420,000,000 / 1,000,000) × 15.00 = 420 × 15.00 = $6,300.00

total_model_cost = $19,350.00 + $10,818.00 + $1,080.00 + $6,300.00 = $37,548.00
total_annual = $37,548.00 × 12 = $450,576.00
```

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| monthly_cache_write_tokens | 5,160,000,000 | 5,160,000,000 | ✅ |
| monthly_cache_read_tokens | 36,060,000,000 | 36,060,000,000 | ✅ |
| monthly_regular_input_tokens | 360,000,000 | 360,000,000 | ✅ |
| monthly_output_tokens | 420,000,000 | 420,000,000 | ✅ |
| cache_write_cost | $19,350.00 | $19,350.00 | ✅ |
| cache_read_cost | $10,818.00 | $10,818.00 | ✅ |
| regular_input_cost | $1,080.00 | $1,080.00 | ✅ |
| output_cost | $6,300.00 | $6,300.00 | ✅ |
| total_model_cost_monthly | $37,548.00 | $37,548.00 | ✅ |
| total_model_cost_annual | $450,576.00 | $450,576.00 | ✅ |

### Caching Savings (Spec §3.6)

```
savings_monthly = $131,040.00 - $37,548.00 = $93,492.00
savings_pct = $93,492.00 / $131,040.00 × 100 = 71.35%
```

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| savings_monthly | $93,492.00 | $93,492.00 | ✅ |
| savings_pct | 71.3% | 71.35% | ✅ |

---

## AgentCore Cost (Spec §5)

### Runtime (Spec §5.1–5.2)

```
sessions_per_month = 600,000 / 2 = 300,000
time_per_question_s = (1 + 6) × 4.0 = 28.0s
active_cpu_per_question_s = 28.0 × 0.30 = 8.4s
total_active_cpu_per_session_s = 8.4 × 2 = 16.8s
idle_gaps_s = (2 - 1) × 30 = 30s
total_session_duration_s = (28.0 × 2) + 30 = 86.0s

runtime_cpu_cost = 16.8 × 2 × (0.0895 / 3600) × 300,000 = $250.60
runtime_mem_cost = 86.0 × 4 × (0.00945 / 3600) × 300,000 = $270.90
runtime_total = $250.60 + $270.90 = $521.50
```

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| time_per_question_s | 28.0 | 28.0 | ✅ |
| active_cpu_per_question_s | 8.4 | 8.4 | ✅ |
| total_session_duration_s | 86.0 | 86.0 | ✅ |
| runtime_cpu_cost | $250.60 | $250.60 | ✅ |
| runtime_mem_cost | $270.90 | $270.90 | ✅ |
| runtime_total | $521.50 | $521.50 | ✅ |

### Gateway (Spec §5.3)

```
gateway_invocations = (1 + 6) × 600,000 = 4,200,000 × $0.000005 = $21.00
gateway_searches = 600,000 × $0.000025 = $15.00
gateway_indexing = 6 × $0.0002 = $0.0012
gateway_total = $21.00 + $15.00 + $0.0012 = $36.00
```

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| gateway_invocation_cost | $21.00 | $21.00 | ✅ |
| gateway_search_cost | $15.00 | $15.00 | ✅ |
| gateway_indexing_cost | $0.00 | $0.0012 | ✅ |
| gateway_total | $36.00 | $36.00 | ✅ |

### Memory (Spec §5.4)

```
stm_cost = 2 × 600,000 × $0.00025 = $300.00
ltm_storage_cost = 3 × 300,000 × $0.00075 = $675.00
ltm_retrieval_cost = 1 × 600,000 × $0.0005 = $300.00
memory_total = $300.00 + $675.00 + $300.00 = $1,275.00
```

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| stm_cost | $300.00 | $300.00 | ✅ |
| ltm_storage_cost | $675.00 | $675.00 | ✅ |
| ltm_retrieval_cost | $300.00 | $300.00 | ✅ |
| memory_total | $1,275.00 | $1,275.00 | ✅ |

### BrowserTool (Spec §5.5)

```
BrowserTool has NO I/O wait discount — billed for full duration.
browser_questions = 600,000 (all questions)
browser_vcpus = 2, browser_memory_gb = 4

browser_cpu = 28.0 × 600,000 × 2 × (0.0895 / 3600) = $835.33
browser_mem = 28.0 × 600,000 × 4 × (0.00945 / 3600) = $176.40
browser_total = $835.33 + $176.40 = $1,011.73
```

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| browser_cpu_cost | $835.33 | $835.33 | ✅ |
| browser_mem_cost | $176.40 | $176.40 | ✅ |
| browser_total | $1,011.73 | $1,011.73 | ✅ |

### Total AgentCore (Spec §5.6)

```
total_agentcore = $521.50 + $36.00 + $1,275.00 + $1,011.73 = $2,844.23
```

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| total_agentcore | $2,844.23 | $2,844.23 | ✅ |

---

## Grand Total (Spec §7)

```
total_monthly = $37,548.00 + $2,844.23 = $40,392.23
total_annual = $40,392.23 × 12 = $484,706.76
per_session = $40,392.23 / 300,000 = $0.1346
per_question = $40,392.23 / 600,000 = $0.0673
```

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| total_monthly | $40,392.23 | $40,392.23 | ✅ |
| total_annual | $484,706.76 | $484,706.76 | ✅ |
| per_session | $0.1346 | $0.1346 | ✅ |
| per_question | $0.0673 | $0.0673 | ✅ |

---

## Capacity Check (Spec §6)

```
active_minutes_per_month = 12 × 60 × 22 = 15,840
avg_questions_per_min = 600,000 / 15,840 = 37.8788
avg_rpm = 37.8788 × (6 + 1) = 265.15
peak_rpm = 265.15 × 3.0 = 795.45

base_context = 100 + 1,000 + 4,000 + 3,000 = 8,100
delta = 600
avg_input_per_turn = 8,100 + (600/2) × 6 = 8,100 + 1,800 = 9,900
avg_output_per_turn = (6 × 100 + 100) / 7 = 700 / 7 = 100

avg_tpm = 265.15 × (9,900 + 100 × 5) = 265.15 × 10,400 = 2,757,576
peak_tpm = 2,757,576 × 3.0 = 8,272,727

max_tokens_overhead = max(0, 4,096 - 100) = 3,996
effective_peak_tpm = 8,272,727 + (795.45 × 3,996) = 8,272,727 + 3,178,818 = 11,451,545
```

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| active_minutes | 15,840 | 15,840 | ✅ |
| avg_rpm | 265.15 | 265.15 | ✅ |
| peak_rpm | 795.45 | 795.45 | ✅ |
| avg_input_per_turn | 9,900 | 9,900 | ✅ |
| avg_output_per_turn | 100 | 100 | ✅ |
| avg_tpm | 2,757,576 | 2,757,576 | ✅ |
| peak_tpm | 8,272,727 | 8,272,727 | ✅ |
| max_tokens_overhead | 3,996 | 3,996 | ✅ |
| effective_peak_tpm | 11,451,545 | 11,451,545 | ✅ |

---

## Business Value (Spec §8)

### Dimension 1a — Productivity Increase (Moderate Tier)

```
time_saved_min = 10 - 3 = 7
E = 0.65, F = 0.60

effective_sessions = 300,000 × 0.65 = 195,000
time_saved_hrs = 195,000 × 7 / 60 = 22,750.00
productive_hrs = 22,750.00 × 0.60 = 13,650.00

productivity_value_monthly = 13,650 × 300 = $4,095,000.00
productivity_value_annual = $4,095,000.00 × 12 = $49,140,000.00
```

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| time_saved_min | 7 | 7 | ✅ |
| effective_sessions (Moderate) | 195,000 | 195,000 | ✅ |
| productive_hrs (Moderate) | 13,650 | 13,650 | ✅ |
| productivity_monthly (Moderate) | $4,095,000 | $4,095,000.00 | ✅ |
| productivity_annual (Moderate) | $49,140,000 | $49,140,000.00 | ✅ |

### Dimension 1b — Cost Savings (Moderate Tier)

```
cost_savings_monthly = 13,650 × 35 = $477,750.00
cost_savings_annual = $477,750.00 × 12 = $5,733,000.00
```

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| cost_savings_monthly (Moderate) | $477,750 | $477,750.00 | ✅ |
| cost_savings_annual (Moderate) | $5,733,000 | $5,733,000.00 | ✅ |

### All Tiers — Dim 1a Productivity

```
Conservative (E=0.50, F=0.50):
  effective = 300,000 × 0.50 = 150,000
  time_saved_hrs = 150,000 × 7 / 60 = 17,500.00
  productive_hrs = 17,500.00 × 0.50 = 8,750.00
  monthly = 8,750.00 × 300 = $2,625,000.00
  annual = $31,500,000.00

Optimistic (E=0.80, F=0.70):
  effective = 300,000 × 0.80 = 240,000
  time_saved_hrs = 240,000 × 7 / 60 = 28,000.00
  productive_hrs = 28,000.00 × 0.70 = 19,600.00
  monthly = 19,600.00 × 300 = $5,880,000.00
  annual = $70,560,000.00
```

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| Conservative monthly | $2,625,000 | $2,625,000.00 | ✅ |
| Conservative annual | $31,500,000 | $31,500,000.00 | ✅ |
| Optimistic monthly | $5,880,000 | $5,880,000.00 | ✅ |
| Optimistic annual | $70,560,000 | $70,560,000.00 | ✅ |

### Summary (Spec §8.5)

```
grand_total_annual = $49,140,000 + $0 + $0 = $49,140,000.00
agent_cost_annual = $40,392.23 × 12 = $484,706.76
net_value = $49,140,000.00 - $484,706.76 = $48,655,293.24
roi_pct = ($48,655,293.24 / $484,706.76) × 100 = 10,038%
payback_days = ($484,706.76 / $49,140,000.00) × 365 = 3.60 days
```

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| grand_total_annual | $49,140,000 | $49,140,000.00 | ✅ |
| agent_cost_annual | $484,706.76 | $484,706.76 | ✅ |
| net_value | $48,655,293 | $48,655,293.24 | ✅ |
| roi_pct | 10,038% | 10,038% | ✅ |
| payback_days | ~4 days | 3.60 days | ✅ |

---

## Overall Verdict

| Section | Result |
|---------|:------:|
| Token Calculations | ✅ PASS |
| No-Cache Baseline | ✅ PASS |
| Cache Splits (Q1) | ✅ PASS |
| Cache Splits (Q2+) | ✅ PASS |
| Session Totals | ✅ PASS |
| Sum Identity | ✅ PASS |
| Monthly Tokens | ✅ PASS |
| Monthly Costs | ✅ PASS |
| Caching Savings | ✅ PASS |
| AgentCore Runtime | ✅ PASS |
| AgentCore Gateway | ✅ PASS |
| AgentCore Memory | ✅ PASS |
| AgentCore BrowserTool | ✅ PASS |
| AgentCore Total | ✅ PASS |
| Grand Total | ✅ PASS |
| Capacity Check | ✅ PASS |
| Business Value Dim 1 | ✅ PASS |
| ROI Summary | ✅ PASS |

### Summary
**56 of 56 fields pass.** All intermediate values match spec formulas within 0.1% tolerance. Token calculations, cache splits (Q1 and Q2), session sum identities, AgentCore components (including BrowserTool with no I/O wait discount), capacity check, and business value (all 3 tiers) verified independently. BrowserTool correctly billed for full duration without I/O wait discount. No discrepancies found.
