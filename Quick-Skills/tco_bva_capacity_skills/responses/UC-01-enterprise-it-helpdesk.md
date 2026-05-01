# UC-01: Enterprise IT Helpdesk Agent — Full Cost Estimate

> **Use Case:** "Estimate the full cost for an IT helpdesk agent using Claude Sonnet 4.6 in us-east-1. 500K sessions/month, 3 questions per session, 5 tool calls per question (ticket lookup, KB search, status update, escalation check, resolution log). Include AgentCore Runtime, Gateway, and Memory. Then check capacity and calculate business value — currently each ticket takes 15 min manually, with AI it takes 4 min. Human cost is $65/hr."

---

## 1. Assumptions

### Workload Profile

| Parameter | Value |
|-----------|-------|
| Region | us-east-1 |
| Model | Claude Sonnet 4.6 |
| Service Tier | Standard Global |
| Sessions/month | 500,000 |
| Questions/session | 3 |
| Questions/month | 1,500,000 |
| Tools per question | 5 (ticket lookup, KB search, status update, escalation check, resolution log) |
| Turns per question | 6 (1 initial + 5 tool calls) |

### Token Profile

| Parameter | Tokens |
|-----------|--------|
| System prompt | 1,000 |
| Tool descriptions (5 tools) | 4,000 |
| User input | 100 |
| RAG chunks | 10 × 300 = 3,000 |
| Tool call output | 100 |
| Tool result input | 500 |
| Final answer output | 100 |
| **Cacheable base** | **5,000** (system + tools) |
| **Base prompt (turn 0)** | **8,100** (cacheable_base + user + RAG) |
| **Delta per tool turn** | **600** (tool_call + tool_result) |
| **Total input/question** | **57,600** |
| **Total output/question** | **600** (100 answer + 5 × 100 tool calls) |

### Model Pricing (Standard Global, per 1M tokens)

| Type | Price |
|------|-------|
| Input | $3.00 |
| Output | $15.00 |
| Cache Read | $0.30 |
| Cache Write | $3.75 |

### AgentCore Pricing (us-east-1)

| Component | Price |
|-----------|-------|
| Runtime vCPU | $0.0895/hr |
| Runtime Memory | $0.00945/hr |
| Gateway Invocations | $0.000005/invocation |
| Gateway Search | $0.000025/search |
| Gateway Indexing | $0.0002/tool |
| STM (writes) | $0.00025/event |
| LTM Storage | $0.00075/record-month |
| LTM Retrieval | $0.0005/retrieval |

---

## 2. Model Cost Breakdown

### With Prompt Caching

| Cost Component | Monthly Tokens | Cost |
|----------------|---------------|------|
| Cache Write | 10,750,000,000 | $40,312.50 |
| Cache Read | 74,750,000,000 | $22,425.00 |
| Regular Input | 900,000,000 | $2,700.00 |
| Output | 900,000,000 | $13,500.00 |
| **Total (with cache)** | | **$78,937.50** |

### Without Caching (Baseline)

| Cost Component | Monthly Tokens | Cost |
|----------------|---------------|------|
| Input | 86,400,000,000 | $259,200.00 |
| Output | 900,000,000 | $13,500.00 |
| **Total (no cache)** | | **$272,700.00** |

### Caching Savings

| Metric | Value |
|--------|-------|
| Monthly savings | $193,762.50 |
| Annual savings | $2,325,150.00 |
| Savings % | **71.1%** |

---

## 3. AgentCore Cost Breakdown

### Runtime

| Component | Calculation | Monthly Cost |
|-----------|------------|-------------|
| vCPU | 21.6s active/session × 2 vCPUs × ($0.0895/3600) × 500K sessions | $537.00 |
| Memory | 132.0s/session × 4 GB × ($0.00945/3600) × 500K sessions | $693.00 |
| **Runtime Total** | | **$1,230.00** |

### Gateway

| Component | Calculation | Monthly Cost |
|-----------|------------|-------------|
| Invocations | 6 turns × 1.5M questions × $0.000005 | $45.00 |
| Search | 1.5M questions × $0.000025 | $37.50 |
| Indexing | 5 tools × $0.0002 | $0.001 |
| **Gateway Total** | | **$82.50** |

### Memory

| Component | Calculation | Monthly Cost |
|-----------|------------|-------------|
| STM (writes) | 2 events × 1.5M questions × $0.00025 | $750.00 |
| LTM Storage | 3 records × 500K sessions × $0.00075 | $1,125.00 |
| LTM Retrieval | 1 retrieval × 1.5M questions × $0.0005 | $750.00 |
| **Memory Total** | | **$2,625.00** |

### AgentCore Total

| Component | Monthly |
|-----------|---------|
| Runtime | $1,230.00 |
| Gateway | $82.50 |
| Memory | $2,625.00 |
| **AgentCore Total** | **$3,937.50** |

---

## 4. Combined Total Cost

| Component | Monthly | Annual |
|-----------|---------|--------|
| Model (Claude Sonnet 4.6) | $78,937.50 | $947,250.00 |
| AgentCore | $3,937.50 | $47,250.00 |
| **Grand Total** | **$82,875.00** | **$994,500.00** |
| Per session | $0.166 | |
| Per question | $0.055 | |

---

## 5. Capacity Check

**Quota Limits (Global cross-region, us-east-1):**
- RPM: 10,000
- TPM: 6,000,000

### RPM Analysis

| Metric | Value |
|--------|-------|
| Avg questions/min | 94.70 (1.5M ÷ 15,840 active min) |
| Avg RPM | 568.18 (94.70 × 6 turns) |
| Peak RPM (3× ratio) | 1,704.55 |
| RPM Limit | 10,000 |
| RPM Utilization | **17.0%** ✅ |

### TPM Analysis

| Metric | Value |
|--------|-------|
| Base context | 8,100 tokens |
| Avg input/turn | 9,600 |
| Avg output/turn | 100 |
| Avg TPM | 5,738,636 |
| Peak TPM (3×) | 17,215,909 |
| max_tokens overhead | 3,996/request |
| Effective Peak TPM | 24,027,273 |
| TPM Limit | 6,000,000 |
| TPM Utilization | **400.5%** ❌ |

### Verdict: ❌ Does Not Fit

RPM fits comfortably (17% utilization), but **TPM exceeds quota by 4×**. The Claude 5× output burndown rate and max_tokens reservation are the primary drivers.

**Optimization Checklist:**
1. **Reduce `max_tokens`**: Currently 4,096 but actual output is ~100 tokens. Setting to 300 would free ~3,796 TPM per request
2. **Enable prompt caching**: Cache reads don't count toward TPM — biggest TPM saver
3. **Reduce RAG chunks**: 10 → 5 saves ~1,500 tokens/turn (compounds across 6 turns)
4. **Request quota increase**: After optimization, request TPM increase to 10M+ for this workload
5. **Multi-region**: Distribute across us-east-1 + us-west-2 for 2× effective quota

---

## 6. Business Value Analysis

### Dimension 1a: Productivity Increase (Revenue Uplift)

| Tier | Effectiveness | Efficiency | Productive Hrs/Mo | Monthly Value | Annual Value |
|------|:------------:|:----------:|:-----------------:|:------------:|:------------:|
| Conservative | 50% | 50% | 22,917 | $6,875,000 | $82,500,000 |
| **Moderate** | **65%** | **60%** | **35,750** | **$10,725,000** | **$128,700,000** |
| Optimistic | 80% | 70% | 51,333 | $15,400,000 | $184,800,000 |

### Dimension 1b: Cost Savings (Alternative View)

| Tier | Productive Hrs/Mo | Monthly Savings | Annual Savings |
|------|:-----------------:|:--------------:|:--------------:|
| Conservative | 22,917 | $1,489,583 | $17,875,000 |
| **Moderate** | **35,750** | **$2,323,750** | **$27,885,000** |
| Optimistic | 51,333 | $3,336,667 | $40,040,000 |

### ROI Summary (Moderate Tier, Dim 1a)

| Metric | Value |
|--------|-------|
| Agent cost (annual) | $994,500 |
| Productivity value (annual) | $128,700,000 |
| Net value | $127,705,500 |
| **ROI** | **12,841%** |
| **Payback period** | **2.8 days** |

### Human Equivalent

| Metric | Value |
|--------|-------|
| Total hours handled | 125,000 hrs/mo (500K × 15 min ÷ 60) |
| FTE equivalent | 781 FTEs (at 160 hrs/mo) |
| Human cost equivalent | $8,125,000/mo |

---

## 7. Step-by-Step Calculation Explanations

### Token Profile

```
cacheable_base = 1,000 (system) + 4,000 (tools) = 5,000
rag_tokens = 10 × 300 = 3,000
base_prompt = 5,000 + 100 (user) + 3,000 (RAG) = 8,100
delta = 100 (tool_call) + 500 (tool_result) = 600
turns = 5 + 1 = 6
```

### Turn-by-Turn Input (Q1)

```
Turn 0: 8,100 (base_prompt)
Turn 1: 8,100 + 1×600 = 8,700
Turn 2: 8,100 + 2×600 = 9,300
Turn 3: 8,100 + 3×600 = 9,900
Turn 4: 8,100 + 4×600 = 10,500
Turn 5: 8,100 + 5×600 = 11,100
Total input/question = 57,600
```

Closed-form: `6 × 8,100 + 600 × 5 × 6/2 = 48,600 + 9,000 = 57,600` ✓

### Output per Question

```
total_output = 100 (answer) + 5 × 100 (tool calls) = 600
```

### Cache Splits (N=5, Q1)

```
Q1 cache_write = base_prompt + (N-1) × delta = 8,100 + 4×600 = 10,500
Q1 cache_read = Σ(k=1..5)[base_prompt + (k-1)×delta]
             = 8,100 + 8,700 + 9,300 + 9,900 + 10,500 = 46,500
Q1 regular = delta = 600
Sum: 10,500 + 46,500 + 600 = 57,600 ✓
```

### Cache Splits (Q2+)

```
Q2 cache_write = (T_user + rag_tokens) + (N-1) × delta = 3,100 + 2,400 = 5,500
Q2 cache_read = cacheable_base + Σ(k=1..5)[base_prompt + (k-1)×delta]
             = 5,000 + 46,500 = 51,500
Q2 regular = delta = 600
Sum: 5,500 + 51,500 + 600 = 57,600 ✓
```

### Per-Session Totals

```
n_subsequent = 3 - 1 = 2
session_cw = 10,500 + 2 × 5,500 = 21,500
session_cr = 46,500 + 2 × 51,500 = 149,500
session_reg = 600 + 2 × 600 = 1,800
Sum: 21,500 + 149,500 + 1,800 = 172,800 = 3 × 57,600 ✓
Output/session = 3 × 600 = 1,800
```

### Monthly Tokens

```
cache_write = 500,000 × 21,500 = 10,750,000,000
cache_read = 500,000 × 149,500 = 74,750,000,000
regular = 500,000 × 1,800 = 900,000,000
output = 500,000 × 1,800 = 900,000,000
```

### Cost Calculation

```
cache_write_cost = 10,750M / 1M × $3.75 = $40,312.50
cache_read_cost = 74,750M / 1M × $0.30 = $22,425.00
regular_cost = 900M / 1M × $3.00 = $2,700.00
output_cost = 900M / 1M × $15.00 = $13,500.00
Total with cache = $78,937.50

No-cache input = (500K × 3 × 57,600) / 1M × $3.00 = 86,400M / 1M × $3.00 = $259,200.00
No-cache output = $13,500.00
No-cache total = $272,700.00

Savings = $272,700 - $78,937.50 = $193,762.50 (71.1%)
```

### AgentCore Calculation

```
sessions = 1,500,000 / 3 = 500,000
time_per_question = (1+5) × 4.0s = 24.0s
active_cpu/question = 24.0 × 0.30 = 7.2s
active_cpu/session = 7.2 × 3 = 21.6s
idle_gaps = (3-1) × 30 = 60s
session_duration = (24.0 × 3) + 60 = 132.0s

Runtime CPU = 21.6 × 2 × (0.0895/3600) × 500,000 = $537.00
Runtime Mem = 132.0 × 4 × (0.00945/3600) × 500,000 = $693.00
Runtime = $1,230.00

Gateway inv = 6 × 1,500,000 × $0.000005 = $45.00
Gateway search = 1,500,000 × $0.000025 = $37.50
Gateway index = 5 × $0.0002 = $0.001
Gateway = $82.50

STM = 2 × 1,500,000 × $0.00025 = $750.00
LTM storage = 3 × 500,000 × $0.00075 = $1,125.00
LTM retrieval = 1 × 1,500,000 × $0.0005 = $750.00
Memory = $2,625.00

AgentCore Total = $1,230.00 + $82.50 + $2,625.00 = $3,937.50
```

### Business Value (Moderate Tier)

```
time_saved = 15 - 4 = 11 min
effective_sessions = 500,000 × 0.65 = 325,000
time_saved_hrs = 325,000 × 11 / 60 = 59,583.33 hrs
productive_hrs = 59,583.33 × 0.60 = 35,750 hrs

Dim 1a (productivity) = 35,750 × $300 = $10,725,000/mo = $128,700,000/yr
Dim 1b (cost savings) = 35,750 × $65 = $2,323,750/mo = $27,885,000/yr

Agent cost annual = $82,875 × 12 = $994,500
Net value = $128,700,000 - $994,500 = $127,705,500
ROI = ($127,705,500 / $994,500) × 100 = 12,841%
Payback = ($994,500 / $128,700,000) × 365 = 2.8 days
```
