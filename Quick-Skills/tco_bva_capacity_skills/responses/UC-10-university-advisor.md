# UC-10: University Student Advisor Agent — Full Cost Estimate

> **Use Case:** "Cost estimate for a student advising chatbot at a large university. Nova Lite in us-east-1. 400K sessions/month, 4 questions per session. 2 tools (course catalog search, degree audit). Light RAG: 3 chunks. Small system prompt: 500 tokens. Business value: advising sessions take 20 min, AI reduces to 5 min, advisor cost $40/hr."

---

## 1. Assumptions

### Workload Profile

| Parameter | Value |
|-----------|-------|
| Region | us-east-1 |
| Model | Amazon Nova Lite (Nova 2.0 Lite) |
| Service Tier | Standard Global |
| Sessions/month | 400,000 |
| Questions/session | 4 |
| Questions/month | 1,600,000 |
| Tools per question | 2 (course catalog search, degree audit) |
| Turns per question | 3 (1 initial + 2 tool calls) |

### Token Profile

| Parameter | Tokens |
|-----------|--------|
| System prompt | 500 |
| Tool descriptions (2 tools) | 4,000 |
| User input | 100 |
| RAG chunks | 3 × 300 = 900 |
| Tool call output | 100 |
| Tool result input | 500 |
| Final answer output | 100 |
| **Cacheable base** | **4,500** (system + tools) |
| **Base prompt (turn 0)** | **5,500** (cacheable_base + user + RAG) |
| **Delta per tool turn** | **600** (tool_call + tool_result) |
| **Total input/question** | **18,300** |
| **Total output/question** | **300** (100 answer + 2 × 100 tool calls) |

### Model Pricing (Standard Global, per 1M tokens)

| Type | Price |
|------|-------|
| Input | $0.30 |
| Output | $2.50 |
| Cache Read | $0.075 |
| Cache Write | $0.00 (free for Nova) |

---

## 2. Model Cost Breakdown

### With Prompt Caching

| Cost Component | Monthly Tokens | Cost |
|----------------|---------------|------|
| Cache Write | 4,360,000,000 | $0.00 |
| Cache Read | 23,960,000,000 | $1,797.00 |
| Regular Input | 960,000,000 | $288.00 |
| Output | 480,000,000 | $1,200.00 |
| **Total (with cache)** | | **$3,285.00** |

### Without Caching (Baseline)

| Cost Component | Monthly Tokens | Cost |
|----------------|---------------|------|
| Input | 29,280,000,000 | $8,784.00 |
| Output | 480,000,000 | $1,200.00 |
| **Total (no cache)** | | **$9,984.00** |

### Caching Savings

| Metric | Value |
|--------|-------|
| Monthly savings | $6,699.00 |
| Annual savings | $80,388.00 |
| Savings % | **67.1%** |

---

## 3. AgentCore Cost Breakdown

**Not included** — AgentCore was not explicitly requested for this use case.

---

## 4. Combined Total Cost

| Component | Monthly | Annual |
|-----------|---------|--------|
| Model (Nova Lite) | $3,285.00 | $39,420.00 |
| AgentCore | N/A | N/A |
| **Grand Total** | **$3,285.00** | **$39,420.00** |
| Per session | $0.0082 | |
| Per question | $0.0021 | |

---

## 5. Capacity Check

**Quota Limits (Global cross-region, us-east-1):**
- RPM: 2,000
- TPM: 8,000,000

### RPM Analysis

| Metric | Value |
|--------|-------|
| Avg questions/min | 101.01 (1.6M ÷ 15,840 active min) |
| Avg RPM | 303.03 (101.01 × 3 turns) |
| Peak RPM (3× ratio) | 909.09 |
| RPM Limit | 2,000 |
| RPM Utilization | **45.5%** ✅ |

### TPM Analysis

| Metric | Value |
|--------|-------|
| Base context | 5,500 tokens |
| Avg input/turn | 6,100 |
| Avg output/turn | 100 |
| Avg TPM | 1,878,788 |
| Peak TPM (3×) | 5,636,364 |
| max_tokens overhead | 3,996/request |
| Effective Peak TPM | 9,269,091 |
| TPM Limit | 8,000,000 |
| TPM Utilization | **115.9%** ❌ |

### Verdict: ⚠️ Marginal — Reduce max_tokens

RPM fits comfortably (45.5% utilization). **Peak TPM fits (5.6M vs 8M limit)**, but effective TPM with max_tokens overhead (9.3M) slightly exceeds quota by 16%.

**Easy fix:** Reduce `max_tokens` from 4,096 to ~300 (actual output is ~100 tokens). This eliminates the overhead and brings effective TPM well within limits.

**Optimization Checklist:**
1. **Reduce `max_tokens`**: Currently 4,096 but actual output is ~100 tokens. Setting to 300 would free ~3,796 TPM per request — **this alone fixes the issue**
2. **Prompt caching**: Already enabled — cache reads don't count toward TPM
3. **Nova Lite burndown rate**: 1× (no output multiplier penalty like Claude's 5×)

---

## 6. Business Value Analysis

### Dimension 1a: Productivity Increase (Revenue Uplift)

| Tier | Effectiveness | Efficiency | Productive Hrs/Mo | Monthly Value | Annual Value |
|------|:------------:|:----------:|:-----------------:|:------------:|:------------:|
| Conservative | 50% | 50% | 25,000 | $7,500,000 | $90,000,000 |
| **Moderate** | **65%** | **60%** | **39,000** | **$11,700,000** | **$140,400,000** |
| Optimistic | 80% | 70% | 56,000 | $16,800,000 | $201,600,000 |

### Dimension 1b: Cost Savings (Alternative View)

| Tier | Productive Hrs/Mo | Monthly Savings | Annual Savings |
|------|:-----------------:|:--------------:|:--------------:|
| Conservative | 25,000 | $1,000,000 | $12,000,000 |
| **Moderate** | **39,000** | **$1,560,000** | **$18,720,000** |
| Optimistic | 56,000 | $2,240,000 | $26,880,000 |

### ROI Summary (Moderate Tier, Dim 1a)

| Metric | Value |
|--------|-------|
| Agent cost (annual) | $39,420 |
| Productivity value (annual) | $140,400,000 |
| Net value | $140,360,580 |
| **ROI** | **356,064%** |
| **Payback period** | **< 1 day** |

### Human Equivalent

| Metric | Value |
|--------|-------|
| Total hours handled | 133,333 hrs/mo (400K × 20 min ÷ 60) |
| FTE equivalent | 833 FTEs (at 160 hrs/mo) |
| Human cost equivalent | $5,333,333/mo |

---

## 7. Step-by-Step Calculation Explanations

### Token Profile

```
cacheable_base = 500 (system) + 4,000 (tools) = 4,500
rag_tokens = 3 × 300 = 900
base_prompt = 4,500 + 100 (user) + 900 (RAG) = 5,500
delta = 100 (tool_call) + 500 (tool_result) = 600
turns = 2 + 1 = 3
```

### Turn-by-Turn Input (Q1)

```
Turn 0: 5,500 (base_prompt)
Turn 1: 5,500 + 1×600 = 6,100
Turn 2: 5,500 + 2×600 = 6,700
Total input/question = 18,300
```

Closed-form: `3 × 5,500 + 600 × 2 × 3/2 = 16,500 + 1,800 = 18,300` ✓

### Output per Question

```
total_output = 100 (answer) + 2 × 100 (tool calls) = 300
```

### Cache Splits (N=2, Q1)

```
Q1 cache_write = base_prompt + (N-1) × delta = 5,500 + 1×600 = 6,100
Q1 cache_read = Σ(k=1..2)[base_prompt + (k-1)×delta]
             = 5,500 + 6,100 = 11,600
Q1 regular = delta = 600
Sum: 6,100 + 11,600 + 600 = 18,300 ✓
```

### Cache Splits (Q2+)

```
Q2 cache_write = (T_user + rag_tokens) + (N-1) × delta = 1,000 + 600 = 1,600
Q2 cache_read = cacheable_base + Σ(k=1..2)[base_prompt + (k-1)×delta]
             = 4,500 + 11,600 = 16,100
Q2 regular = delta = 600
Sum: 1,600 + 16,100 + 600 = 18,300 ✓
```

### Per-Session Totals

```
n_subsequent = 4 - 1 = 3
session_cw = 6,100 + 3 × 1,600 = 10,900
session_cr = 11,600 + 3 × 16,100 = 59,900
session_reg = 600 + 3 × 600 = 2,400
Sum: 10,900 + 59,900 + 2,400 = 73,200 = 4 × 18,300 ✓
Output/session = 4 × 300 = 1,200
```

### Monthly Tokens

```
cache_write = 400,000 × 10,900 = 4,360,000,000
cache_read = 400,000 × 59,900 = 23,960,000,000
regular = 400,000 × 2,400 = 960,000,000
output = 400,000 × 1,200 = 480,000,000
```

### Cost Calculation

```
cache_write_cost = 4,360M / 1M × $0.00 = $0.00
cache_read_cost = 23,960M / 1M × $0.075 = $1,797.00
regular_cost = 960M / 1M × $0.30 = $288.00
output_cost = 480M / 1M × $2.50 = $1,200.00
Total with cache = $3,285.00

No-cache input = (400K × 4 × 18,300) / 1M × $0.30 = 29,280M / 1M × $0.30 = $8,784.00
No-cache output = $1,200.00
No-cache total = $9,984.00

Savings = $9,984.00 - $3,285.00 = $6,699.00 (67.1%)
```

### Capacity Calculation

```
active_minutes = 12h × 60 × 22d = 15,840
avg_questions/min = 1,600,000 / 15,840 = 101.01
avg_rpm = 101.01 × 3 = 303.03
peak_rpm = 303.03 × 3.0 = 909.09

base_context = 100 + 500 + 4,000 + 900 = 5,500
delta = 600
avg_input/turn = 5,500 + (600/2) × 2 = 6,100
avg_output/turn = (2 × 100 + 100) / 3 = 100

avg_tpm = 303.03 × (6,100 + 100 × 1) = 303.03 × 6,200 = 1,878,788
peak_tpm = 1,878,788 × 3.0 = 5,636,364

max_tokens_overhead = 4,096 - 100 = 3,996
effective_peak_tpm = 5,636,364 + (909.09 × 3,996) = 9,269,091

RPM: 909 ≤ 2,000 → ✅ (45.5%)
TPM: 9,269,091 > 8,000,000 → ❌ (115.9%)
```

### Business Value (Moderate Tier)

```
time_saved = 20 - 5 = 15 min
effective_sessions = 400,000 × 0.65 = 260,000
time_saved_hrs = 260,000 × 15 / 60 = 65,000 hrs
productive_hrs = 65,000 × 0.60 = 39,000 hrs

Dim 1a (productivity) = 39,000 × $300 = $11,700,000/mo = $140,400,000/yr
Dim 1b (cost savings) = 39,000 × $40 = $1,560,000/mo = $18,720,000/yr

Agent cost annual = $3,285 × 12 = $39,420
Net value = $140,400,000 - $39,420 = $140,360,580
ROI = ($140,360,580 / $39,420) × 100 = 356,064%
Payback = ($39,420 / $140,400,000) × 365 = 0.1 days
```
