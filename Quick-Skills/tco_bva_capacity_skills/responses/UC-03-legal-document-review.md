# UC-03: Legal Document Review Agent — Full Cost Estimate

> **Use Case:** "Price an agent that reviews legal contracts. Claude Opus 4.6 in eu-west-1. 50K sessions/month, 1 question per session (upload doc, get analysis). No tools — pure document analysis. Large RAG: 20 chunks of 500 tokens each. System prompt is 3,000 tokens. Output is long — 1,000 tokens per response. Include capacity check and business value — lawyers spend 45 min per contract review, AI reduces to 10 min, cost is $250/hr."

---

## 1. Assumptions

### Workload Profile

| Parameter | Value |
|-----------|-------|
| Region | eu-west-1 (Ireland) |
| Model | Claude Opus 4.6 |
| Tier / Variant | Standard / Global (Cross-Region) |
| Sessions/month | 50,000 |
| Questions/session | 1 |
| Questions/month | 50,000 |
| Tools invoked | 0 (pure document analysis) |
| Turns/question | 1 |

### Token Profile

| Parameter | Tokens |
|-----------|--------|
| System prompt | 3,000 |
| Tool descriptions | 0 |
| User input | 100 |
| RAG chunks | 20 × 500 = 10,000 |
| Tool call (per call) | 100 |
| Tool result (per result) | 500 |
| Output (final answer) | 1,000 |
| **cacheable_base** | 3,000 (system + tools) |
| **base_prompt** | 13,100 (cacheable_base + user + RAG) |
| **delta** | 600 (tool_call + tool_result) |
| **total_input_per_question** | 13,100 |
| **output_per_question** | 1,000 |

### Model Pricing (Standard Global, eu-west-1)

| Price Type | $/M Tokens |
|------------|-----------|
| Input | $5.00 |
| Output | $25.00 |
| Cache Read | $0.50 |
| Cache Write | $6.25 |

**Note:** Cache write ($6.25) is 125% of input price ($5.00). For this N=0, single-question-per-session workload, caching is **more expensive** than no-cache because every token is cache-written at a higher rate with no subsequent cache reads within the session.

---

## 2. Model Cost Breakdown

### N=0 Special Case — Caching Model

With `tools_invoked=0`, there is only 1 turn per question. The N=0 special case applies:

**Q1 (first and only question in session):**
- cache_write = base_prompt = 13,100
- cache_read = 0
- regular = 0

**Q2 (not applicable — questions_per_session = 1):**
- n_subsequent = 1 - 1 = 0 → no Q2

**Per-Session Totals:**
- session_cw = 13,100 + 0 × 10,100 = 13,100
- session_cr = 0 + 0 × 3,000 = 0
- session_reg = 0 + 0 × 0 = 0
- session_output = 1 × 1,000 = 1,000

**Verification:** session_cw + session_cr + session_reg = 13,100 = 1 × 13,100 ✅

### Monthly Token Volumes

| Category | Tokens |
|----------|--------|
| Cache Write | 50,000 × 13,100 = 655,000,000 |
| Cache Read | 50,000 × 0 = 0 |
| Regular Input | 50,000 × 0 = 0 |
| Output | 50,000 × 1,000 = 50,000,000 |

### With Caching

| Component | Calculation | Cost |
|-----------|-------------|------|
| Cache Write | 655M / 1M × $6.25 | $4,093.75 |
| Cache Read | 0 / 1M × $0.50 | $0.00 |
| Regular Input | 0 / 1M × $5.00 | $0.00 |
| Output | 50M / 1M × $25.00 | $1,250.00 |
| **Total (with cache)** | | **$5,343.75/mo** |

### Without Caching (Baseline)

| Component | Calculation | Cost |
|-----------|-------------|------|
| Input | 50,000 × 13,100 / 1M × $5.00 | $3,275.00 |
| Output | 50,000 × 1,000 / 1M × $25.00 | $1,250.00 |
| **Total (no cache)** | | **$4,525.00/mo** |

### Caching Impact

| Metric | Value |
|--------|-------|
| With caching | $5,343.75/mo |
| Without caching | $4,525.00/mo |
| Savings | **-$818.75/mo (-18.1%)** |

⚠️ **Caching is more expensive for this workload.** With only 1 question per session and no tools, every input token is cache-written at $6.25/M (125% of input price) with zero cache reads. **Recommendation: Use no-cache pricing ($4,525.00/mo) for this workload.**

### Recommended Cost (No Cache)

| Metric | Monthly | Annual |
|--------|---------|--------|
| Total Model Cost | **$4,525.00** | **$54,300.00** |
| Per Session | $0.0905 | — |
| Per Question | $0.0905 | — |

---

## 3. AgentCore Cost Breakdown

**Not applicable.** This is a pure document analysis agent — no AgentCore infrastructure requested.

---

## 4. Combined Total Cost

| Component | Monthly | Annual |
|-----------|---------|--------|
| Model Cost (no cache) | $4,525.00 | $54,300.00 |
| AgentCore | N/A | N/A |
| **Total** | **$4,525.00** | **$54,300.00** |
| Per Session | $0.0905 | — |
| Per Question | $0.0905 | — |

---

## 5. Capacity Check

**Quotas (Claude Opus 4.6, eu-west-1, Global Cross-Region):**
- RPM limit: 10,000
- TPM limit: 3,000,000

**Traffic Profile:**
- Active hours/day: 12
- Active days/month: 22
- Peak-to-average ratio: 3.0×
- Output burndown rate: 5× (Claude model)

### RPM Analysis

| Metric | Value |
|--------|-------|
| Active minutes/month | 12 × 60 × 22 = 15,840 |
| Avg questions/min | 50,000 ÷ 15,840 = 3.16 |
| LLM calls/question | 1 (0 tools + 1) |
| Avg RPM | 3.16 × 1 = 3.16 |
| Peak RPM | 3.16 × 3.0 = **9.47** |
| RPM Limit | 10,000 |
| **RPM Utilization** | **0.1%** ✅ |

### TPM Analysis

| Metric | Value |
|--------|-------|
| Base context | 100 + 3,000 + 0 + 10,000 = 13,100 |
| Avg input/turn | 13,100 |
| Avg output/turn | 1,000 |
| Avg TPM | 3.16 × (13,100 + 1,000 × 5) = 57,134 |
| Peak TPM | 57,134 × 3.0 = 171,402 |
| max_tokens overhead | 4,096 - 1,000 = 3,096/req |
| Effective Peak TPM | 171,402 + (9.47 × 3,096) = **200,720** |
| TPM Limit | 3,000,000 |
| **TPM Utilization** | **6.7%** ✅ |

### Verdict

✅ **Workload fits comfortably.** RPM at 0.1% and TPM at 6.7% utilization — massive headroom.

**Optimization note:** Output burndown rate is 5× for Claude — each output token consumes 5 TPM quota. With 1,000-token outputs, this accounts for 5,000 effective TPM per request. Reducing output length would have 5× impact on TPM.

**Recommendation:** Reduce `max_tokens` from 4,096 to ~2,000 (2× actual output) to free 2,096 TPM/request of reserved overhead.

---

## 6. Business Value Analysis

### Inputs

| Parameter | Value |
|-----------|-------|
| Sessions/month | 50,000 |
| Time without AI | 45 min (manual contract review) |
| Time with AI | 10 min (AI-assisted review) |
| Time saved | 35 min/session |
| Human cost/hr | $250 (lawyer fully-loaded cost) |
| Revenue/hr | $500 (lawyer billable rate) |
| Agent cost/month | $4,525.00 (no-cache model cost) |

### Dimension 1a: Productivity Increase (Revenue Uplift)

| Tier | Effectiveness | Efficiency | Productive Hrs/Mo | Monthly Value | Annual Value |
|------|:------------:|:----------:|------------------:|--------------:|-------------:|
| Conservative | 50% | 50% | 7,292 | $3,645,833 | $43,750,000 |
| **Moderate** | **65%** | **60%** | **11,375** | **$5,687,500** | **$68,250,000** |
| Optimistic | 80% | 70% | 16,333 | $8,166,667 | $98,000,000 |

### Dimension 1b: Cost Savings (Labor Cost Reduction)

| Tier | Productive Hrs/Mo | Monthly Savings | Annual Savings |
|------|------------------:|----------------:|---------------:|
| Conservative | 7,292 | $1,822,917 | $21,875,000 |
| **Moderate** | **11,375** | **$2,843,750** | **$34,125,000** |
| Optimistic | 16,333 | $4,083,333 | $49,000,000 |

### ROI Summary (Moderate Tier, Dim 1a — Productivity)

| Metric | Value |
|--------|-------|
| Gross value (annual) | $68,250,000 |
| Agent cost (annual) | $54,300 |
| **Net value (annual)** | **$68,195,700** |
| **ROI** | **125,590%** |
| **Payback period** | **< 1 day** |

### Human Equivalent

| Metric | Value |
|--------|-------|
| Total manual hours/month | 50,000 × 45 min ÷ 60 = 37,500 hrs |
| FTE equivalent | 37,500 ÷ 160 = ~234 FTEs |
| Human cost equivalent | 37,500 × $250 = $9,375,000/mo |
| AI cost | $4,525/mo |
| **Cost ratio** | **AI is 0.05% of human cost** |

---

## 7. Step-by-Step Calculation Explanations

### Token Profile

```
cacheable_base = 3,000 (system) + 0 (tools) = 3,000
rag_tokens = 20 × 500 = 10,000
base_prompt = 3,000 + 100 (user) + 10,000 (RAG) = 13,100
delta = 100 (tool call) + 500 (tool result) = 600
turns = 0 tools + 1 = 1
output_per_question = 1,000 (response) + 0 × 100 (tool calls) = 1,000
total_input_per_question = 13,100 (single turn)
```

### N=0 Caching Model (Single Turn, Single Question per Session)

```
Q1: cache_write = 13,100, cache_read = 0, regular = 0
    Sum: 13,100 = 13,100 ✅

n_subsequent = 0 (only 1 question per session)

Session totals:
  session_cw = 13,100
  session_cr = 0
  session_reg = 0
  Verification: 13,100 + 0 + 0 = 13,100 = 1 × 13,100 ✅
```

### Monthly Cost Math

```
With cache:
  cache_write: 50,000 × 13,100 = 655,000,000 tokens × $6.25/M = $4,093.75
  cache_read:  50,000 × 0 = 0 tokens × $0.50/M = $0.00
  regular:     50,000 × 0 = 0 tokens × $5.00/M = $0.00
  output:      50,000 × 1,000 = 50,000,000 tokens × $25.00/M = $1,250.00
  Total: $5,343.75/mo

No cache:
  input:  50,000 × 13,100 = 655,000,000 tokens × $5.00/M = $3,275.00
  output: 50,000 × 1,000 = 50,000,000 tokens × $25.00/M = $1,250.00
  Total: $4,525.00/mo

Savings: $4,525.00 - $5,343.75 = -$818.75 (-18.1%)
→ Caching is MORE expensive. Use no-cache pricing.
```

### Capacity Math

```
RPM:
  active_min/month = 12 × 60 × 22 = 15,840
  avg Q/min = 50,000 / 15,840 = 3.16
  avg RPM = 3.16 × 1 = 3.16
  peak RPM = 3.16 × 3.0 = 9.47
  vs limit 10,000 → 0.1% utilization ✅

TPM:
  base_context = 100 + 3,000 + 0 + 10,000 = 13,100
  avg_input/turn = 13,100
  avg_output/turn = 1,000
  avg TPM = 3.16 × (13,100 + 1,000 × 5) = 57,134
  peak TPM = 57,134 × 3.0 = 171,402
  max_tokens overhead = 4,096 - 1,000 = 3,096
  effective peak TPM = 171,402 + (9.47 × 3,096) = 200,720
  vs limit 3,000,000 → 6.7% utilization ✅
```

### Business Value Math (Moderate Tier)

```
time_saved = 45 - 10 = 35 min
effective_sessions = 50,000 × 0.65 = 32,500
time_saved_hrs = 32,500 × 35 / 60 = 18,958.33 hrs
productive_hrs = 18,958.33 × 0.60 = 11,375 hrs

Dim 1a (productivity): 11,375 × $500 = $5,687,500/mo → $68,250,000/yr
Dim 1b (cost savings): 11,375 × $250 = $2,843,750/mo → $34,125,000/yr

agent_cost_annual = $4,525 × 12 = $54,300
net_value = $68,250,000 - $54,300 = $68,195,700
ROI = ($68,195,700 / $54,300) × 100 = 125,590%
payback = ($54,300 / $68,250,000) × 365 = 0.29 days
```
