# UC-08: Manufacturing Quality Control Agent — Full Cost Estimate

> **Use Case:** Estimate costs for a quality control agent in a factory. Claude Sonnet 4.6 in eu-central-1. 300K sessions/month, 2 questions per session. 6 tools (defect image analyzer, production line status, parts inventory, maintenance scheduler, quality report generator, supplier lookup). Include BrowserTool for accessing the factory dashboard. Business value: QC inspections take 10 min manually, 3 min with AI, inspector cost $35/hr.

---

## 1. Assumptions

### Workload Profile

| Parameter | Value |
|-----------|-------|
| Region | eu-central-1 |
| Model | Claude Sonnet 4.6 |
| Tier / Variant | Standard / Global (Cross-Region) |
| Sessions/month | 300,000 |
| Questions/session | 2 |
| Questions/month | 600,000 |
| Tools | 6 (defect image analyzer, production line status, parts inventory, maintenance scheduler, quality report generator, supplier lookup) |
| Turns/question | 7 (6 tool invocations + 1 final answer) |

### Token Profile

| Parameter | Value |
|-----------|-------|
| System prompt | 1,000 tokens |
| Tool descriptions | 4,000 tokens (6 tools) |
| User input | 100 tokens |
| RAG chunks | 10 × 300 = 3,000 tokens |
| Tool call (output) | 100 tokens |
| Tool result (input) | 500 tokens |
| Final answer | 100 tokens |
| **Base prompt (turn 0)** | **8,100** = 1,000 + 4,000 + 100 + 3,000 |
| **Cacheable prefix** | **5,000** = 1,000 + 4,000 |
| **Delta per tool turn** | **600** = 100 + 500 |
| **Total input/question** | **69,300** tokens (across 7 turns) |
| **Output/question** | **700** = 100 + 6 × 100 |

### Model Pricing

| Price Type | $/1M tokens | Source |
|-----------|-------------|--------|
| Input | $3.00 | Standard Global, eu-central-1 |
| Output | $15.00 | Standard Global, eu-central-1 |
| Cache Read | $0.30 | 10% of input |
| Cache Write | $3.75 | 125% of input |

### AgentCore Pricing (eu-central-1)

| Component | Price | Unit |
|-----------|-------|------|
| Runtime vCPU | $0.0895 | per vCPU-Hour |
| Runtime Memory | $0.00945 | per GB-Hour |
| Gateway Invocations | $0.000005 | per invocation |
| Gateway Search | $0.000025 | per search |
| Gateway Indexing | $0.0002 | per tool-month |
| STM Events | $0.00025 | per event |
| LTM Storage | $0.00075 | per record-month |
| LTM Retrieval | $0.0005 | per retrieval |
| BrowserTool vCPU | $0.0895 | per vCPU-Hour |
| BrowserTool Memory | $0.00945 | per GB-Hour |

---

## 2. Model Cost Breakdown

### With Prompt Caching

**Per-Question Cache Splits:**

| | Cache Write | Cache Read | Regular Input | Total |
|---|---:|---:|---:|---:|
| Q1 (first in session) | 11,100 | 57,600 | 600 | 69,300 ✓ |
| Q2+ (subsequent) | 6,100 | 62,600 | 600 | 69,300 ✓ |

**Per-Session Totals (2 questions):**

| Category | Tokens |
|----------|-------:|
| Cache Write | 17,200 |
| Cache Read | 120,200 |
| Regular Input | 1,200 |
| Output | 1,400 |
| **Total** | **140,000** (= 2 × 69,300 + 1,400 output ✓) |

**Monthly Cost (With Caching):**

| Component | Monthly Tokens | Cost |
|-----------|---------------:|-----:|
| Cache Write | 5,160,000,000 | $19,350.00 |
| Cache Read | 36,060,000,000 | $10,818.00 |
| Regular Input | 360,000,000 | $1,080.00 |
| Output | 420,000,000 | $6,300.00 |
| **Total** | | **$37,548.00/mo** |

### Without Caching (Baseline)

| Component | Cost |
|-----------|-----:|
| Input (all at $3.00/M) | $124,740.00 |
| Output | $6,300.00 |
| **Total** | **$131,040.00/mo** |

### Caching Savings

| Metric | Value |
|--------|------:|
| Monthly savings | $93,492.00 |
| Annual savings | $1,121,904.00 |
| Savings % | **71.3%** |

---

## 3. AgentCore Cost Breakdown

### Runtime

| Component | Calculation | Cost |
|-----------|------------|-----:|
| Time per question | (6 + 1) × 4.0s = 28.0s | |
| Active CPU per question | 28.0s × 30% = 8.4s | |
| Active CPU per session | 8.4s × 2 Qs = 16.8s | |
| Idle gaps | (2 − 1) × 30s = 30s | |
| Session duration | (28.0s × 2) + 30s = 86.0s | |
| **vCPU cost** | 16.8s × 2 vCPU × ($0.0895/3600) × 300,000 | **$250.60** |
| **Memory cost** | 86.0s × 4 GB × ($0.00945/3600) × 300,000 | **$270.90** |
| **Runtime total** | | **$521.50** |

### Gateway

| Component | Calculation | Cost |
|-----------|------------|-----:|
| Invocations | (6 + 1) × 600,000 = 4,200,000 × $0.000005 | $21.00 |
| Search | 600,000 × $0.000025 | $15.00 |
| Indexing | 6 × $0.0002 | $0.00 |
| **Gateway total** | | **$36.00** |

### Memory

| Component | Calculation | Cost |
|-----------|------------|-----:|
| STM | 2 events × 600,000 × $0.00025 | $300.00 |
| LTM Storage | 3 records × 300,000 × $0.00075 | $675.00 |
| LTM Retrieval | 1 × 600,000 × $0.0005 | $300.00 |
| **Memory total** | | **$1,275.00** |

### BrowserTool (No I/O Wait Discount)

| Component | Calculation | Cost |
|-----------|------------|-----:|
| Browser questions | 600,000 (all questions use dashboard) | |
| BrowserTool vCPU | 28.0s × 600,000 × 2 vCPU × ($0.0895/3600) | $835.33 |
| BrowserTool Memory | 28.0s × 600,000 × 4 GB × ($0.00945/3600) | $176.40 |
| **BrowserTool total** | | **$1,011.73** |

> **Note:** BrowserTool has NO I/O wait discount — billed for full duration (28.0s per question).

### Total AgentCore

| Component | Monthly Cost |
|-----------|------------:|
| Runtime | $521.50 |
| Gateway | $36.00 |
| Memory | $1,275.00 |
| BrowserTool | $1,011.73 |
| **Total AgentCore** | **$2,844.23** |

---

## 4. Combined Total Cost

| Metric | Value |
|--------|------:|
| Model cost | $37,548.00 |
| AgentCore cost | $2,844.23 |
| **Monthly total** | **$40,392.23** |
| **Annual total** | **$484,706.76** |
| Per session | $0.1346 |
| Per question | $0.0673 |

---

## 5. Capacity Check

**Quotas:** eu-central-1 quota cache not available. Using us-east-1 defaults as proxy.
- RPM limit: 10,000 (estimated)
- TPM limit: 6,000,000 (estimated)

**Traffic Profile:**
- Active hours: 12h/day × 22 days/month = 15,840 active minutes
- Output burndown rate: 5× (Claude Sonnet 4.6)

| Metric | Value | Status |
|--------|------:|:------:|
| Avg questions/min | 37.88 | |
| Avg RPM | 265.15 (37.88 × 7 turns) | |
| Peak RPM | 795.45 (× 3.0 ratio) | ✅ fits (~8% utilization) |
| Avg input/turn | 8,100 + (600/2) × 6 = 9,900 | |
| Avg output/turn | (6 × 100 + 100) / 7 = 100 | |
| Avg TPM | 265.15 × (9,900 + 100 × 5) = 2,757,576 | |
| Peak TPM | 2,757,576 × 3.0 = 8,272,727 | |
| max_tokens overhead | 3,996/req (4,096 − 100) | |
| Effective Peak TPM | 8,272,727 + (795.45 × 3,996) = 11,451,545 | ❌ exceeds (191% utilization) |

**Verdict: ❌ Does not fit** — TPM is the bottleneck.

### Optimization Recommendations

1. **Reduce max_tokens**: Set to ~300 instead of 4,096 (actual output is ~100). Frees ~3,796 TPM/request.
2. **Enable prompt caching**: Cache reads do NOT count toward TPM — biggest TPM saver.
3. **Reduce RAG chunks**: 10 chunks × 300 = 3,000 tokens/turn. Can quality be maintained with 5 chunks?
4. **Output burndown**: Claude 5× burndown means each output token costs 5 TPM. Constrain output length.
5. **Request quota increase**: After optimization, if still over limit, request TPM increase via AWS console.

---

## 6. Business Value Analysis

### Dimension 1a — Productivity Increase (Revenue Uplift)

| Tier | Effectiveness | Efficiency | Productive Hrs/Mo | Monthly Value | Annual Value |
|------|:------------:|:----------:|------------------:|--------------:|-------------:|
| Conservative | 50% | 50% | 8,750 | $2,625,000 | $31,500,000 |
| **Moderate** | **65%** | **60%** | **13,650** | **$4,095,000** | **$49,140,000** |
| Optimistic | 80% | 70% | 19,600 | $5,880,000 | $70,560,000 |

**Calculation (Moderate):**
- Time saved: 10 − 3 = 7 min/session
- Effective sessions: 300,000 × 65% = 195,000
- Time saved hours: 195,000 × 7 / 60 = 22,750 hrs
- Productive hours: 22,750 × 60% = 13,650 hrs
- Productivity value: 13,650 × $300/hr = $4,095,000/mo

### Dimension 1b — Cost Savings (Mutually Exclusive with 1a)

| Tier | Productive Hrs/Mo | Monthly Savings | Annual Savings |
|------|------------------:|--------------:|-------------:|
| Conservative | 8,750 | $306,250 | $3,675,000 |
| **Moderate** | **13,650** | **$477,750** | **$5,733,000** |
| Optimistic | 19,600 | $686,000 | $8,232,000 |

### ROI Summary (Moderate Tier, Dim 1a only)

| Metric | Value |
|--------|------:|
| Dim 1a (Moderate, annual) | $49,140,000 |
| **Grand total annual value** | **$49,140,000** |
| Agent cost (annual) | $484,706.76 |
| **Net value** | **$48,655,293** |
| **ROI** | **10,038%** |
| **Payback period** | **~4 days** |

---

## 7. Step-by-Step Calculation Explanations

### Token Profile
- Base context: 8,100 = 1,000 (system) + 4,000 (tools) + 100 (user) + 3,000 (RAG)
- Cacheable prefix: 5,000 = 1,000 (system) + 4,000 (tools)
- Delta per turn: 600 = 100 (tool call) + 500 (tool result)
- Turns per question: 7 = 6 tool invocations + 1
- Output per question: 700 = 100 (response) + 6 × 100 (tool calls)

### Turn-by-Turn Breakdown (Q1)
- Turn 0: 8,100 input → WRITE 8,100 (entire prompt — first turn of session)
- Turn 1: 8,700 input → READ 8,100 + WRITE 600 (new tool delta)
- Turn 2: 9,300 input → READ 8,700 + WRITE 600 (new tool delta)
- Turn 3: 9,900 input → READ 9,300 + WRITE 600 (new tool delta)
- Turn 4: 10,500 input → READ 9,900 + WRITE 600 (new tool delta)
- Turn 5: 11,100 input → READ 10,500 + WRITE 600 (new tool delta)
- Turn 6: 11,700 input → READ 11,100 + REG 600 (last turn — won't be re-read)
- Total Q1 input: 69,300 tokens across 7 turns

### Cross-Question Caching
- Q2 Turn 0: READ 5,000 (system+tools cached from Q1) + WRITE 3,100 (new user question + RAG)
- Cross-Q caching saves re-writing 5,000 tokens at $3.75/M on each subsequent question

### Cache Math (Monthly)
- Cache write: 5,160,000,000 tokens × $3.75/M = $19,350.00
- Cache read: 36,060,000,000 tokens × $0.30/M = $10,818.00
- Regular input: 360,000,000 tokens × $3.00/M = $1,080.00
- Output: 420,000,000 tokens × $15.00/M = $6,300.00
- Total: $19,350.00 + $10,818.00 + $1,080.00 + $6,300.00 = $37,548.00

### No-Cache Baseline
- Total input/question: 69,300 tokens × 600,000 questions × $3.00/M = $124,740.00
- Total output: 700 tokens × 600,000 questions × $15.00/M = $6,300.00
- Total: $124,740.00 + $6,300.00 = $131,040.00

### AgentCore
- Runtime vCPU: 16.8s × 2 × ($0.0895/3600) × 300,000 = $250.60
- Runtime Memory: 86.0s × 4 × ($0.00945/3600) × 300,000 = $270.90
- Gateway: (7 × 600,000 × $5e-6) + (600,000 × $2.5e-5) + (6 × $0.0002) = $36.00
- Memory: (2 × 600,000 × $0.00025) + (3 × 300,000 × $0.00075) + (1 × 600,000 × $0.0005) = $1,275.00
- BrowserTool: 28.0s × 600,000 × 2 × ($0.0895/3600) + 28.0s × 600,000 × 4 × ($0.00945/3600) = $1,011.73
- Total AgentCore: $521.50 + $36.00 + $1,275.00 + $1,011.73 = $2,844.23

### Capacity Planning
- Active minutes: 12h × 60 × 22d = 15,840 min
- Avg Q/min: 600,000 ÷ 15,840 = 37.88
- Avg RPM: 37.88 × 7 = 265.15
- Peak RPM: 265.15 × 3.0 = 795.45
- Base context: 8,100; delta: 600
- Avg input/turn: 8,100 + (600/2) × 6 = 9,900
- Avg output/turn: (6 × 100 + 100) / 7 = 100
- Avg TPM: 265.15 × (9,900 + 100 × 5) = 2,757,576
- Peak TPM: 2,757,576 × 3.0 = 8,272,727
- max_tokens overhead: 4,096 − 100 = 3,996
- Effective peak TPM: 8,272,727 + (795.45 × 3,996) = 11,451,545

### Business Value
- Time saved: 10 − 3 = 7 min/session
- Moderate: 300,000 × 65% = 195,000 effective sessions
- Productive hrs: 195,000 × 7/60 × 60% = 13,650 hrs/mo
- Productivity: 13,650 × $300 = $4,095,000/mo → $49,140,000/yr
- Cost savings: 13,650 × $35 = $477,750/mo → $5,733,000/yr
- Grand total: $49,140,000/yr
- Net value: $49,140,000 − $484,706.76 = $48,655,293/yr
- ROI: ($48,655,293 / $484,706.76) × 100 = 10,038%
- Payback: ($484,706.76 / $49,140,000) × 365 = ~3.6 days
