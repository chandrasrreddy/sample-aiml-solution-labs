# UC-09: Real Estate Property Valuation Agent — Full Cost Estimate

> **Use Case:** "Price an agent that helps real estate agents with property valuations. Claude Sonnet 4.6 in us-east-1. 150K sessions/month, 5 questions per session. 7 tools (MLS search, comparable sales, tax records, neighborhood stats, mortgage calculator, market trends, property history). RAG: 12 chunks of property data. Business value: valuations take 40 min manually, 12 min with AI, agent cost $75/hr."

---

## 1. Assumptions

### Workload Profile

| Parameter | Value |
|-----------|-------|
| Region | us-east-1 |
| Model | Claude Sonnet 4.6 |
| Tier / Variant | Standard / Global (Cross-Region) |
| Sessions/month | 150,000 |
| Questions/session | 5 |
| Questions/month | 750,000 |
| Tools | 7 (MLS search, comparable sales, tax records, neighborhood stats, mortgage calculator, market trends, property history) |
| Turns/question | 8 (7 tool invocations + 1 final answer) |

### Token Profile

| Parameter | Value |
|-----------|-------|
| System prompt | 1,000 tokens |
| Tool descriptions | 4,000 tokens (7 tools) |
| User input | 100 tokens |
| RAG chunks | 12 × 300 = 3,600 tokens |
| Tool call (output) | 100 tokens |
| Tool result (input) | 500 tokens |
| Final answer | 100 tokens |
| **Base prompt (turn 0)** | **8,700** = 1,000 + 4,000 + 100 + 3,600 |
| **Cacheable prefix** | **5,000** = 1,000 + 4,000 |
| **Delta per tool turn** | **600** = 100 + 500 |
| **Total input/question** | **86,400** tokens (across 8 turns) |
| **Output/question** | **800** = 100 + 7 × 100 |

### Model Pricing

| Price Type | $/1M tokens | Source |
|-----------|-------------|--------|
| Input | $3.00 | Standard Global, us-east-1 |
| Output | $15.00 | Standard Global, us-east-1 |
| Cache Read | $0.30 | 10% of input |
| Cache Write | $3.75 | 125% of input |

---

## 2. Model Cost Breakdown

### With Prompt Caching

**Per-Question Cache Splits:**

| | Cache Write | Cache Read | Regular Input | Total |
|---|---:|---:|---:|---:|
| Q1 (first in session) | 12,300 | 73,500 | 600 | 86,400 ✓ |
| Q2+ (subsequent) | 7,300 | 78,500 | 600 | 86,400 ✓ |

**Per-Session Totals (5 questions):**

| Category | Tokens |
|----------|-------:|
| Cache Write | 41,500 |
| Cache Read | 387,500 |
| Regular Input | 3,000 |
| Output | 4,000 |
| **Total** | **436,000** (= 5 × 86,400 + 4,000 output ✓) |

**Monthly Cost (With Caching):**

| Component | Monthly Tokens | Cost |
|-----------|---------------:|-----:|
| Cache Write | 6,225,000,000 | $23,343.75 |
| Cache Read | 58,125,000,000 | $17,437.50 |
| Regular Input | 450,000,000 | $1,350.00 |
| Output | 600,000,000 | $9,000.00 |
| **Total** | | **$51,131.25/mo** |

### Without Caching (Baseline)

| Component | Cost |
|-----------|-----:|
| Input (all at $3.00/M) | $194,400.00 |
| Output | $9,000.00 |
| **Total** | **$203,400.00/mo** |

### Caching Savings

| Metric | Value |
|--------|------:|
| Monthly savings | $152,268.75 |
| Annual savings | $1,827,225.00 |
| Savings % | **74.9%** |

---

## 3. Combined Total Cost

*AgentCore not included — not explicitly requested in prompt.*

| Metric | Value |
|--------|------:|
| **Monthly** | **$51,131.25** |
| **Annual** | **$613,575.00** |
| Per session | $0.3409 |
| Per question | $0.0682 |

---

## 4. Capacity Check

**Quotas (Claude Sonnet 4.6, us-east-1, Global):**
- RPM limit: 10,000
- TPM limit: 6,000,000

**Traffic Profile:**
- Active hours: 12h/day × 22 days/month = 15,840 active minutes
- Output burndown rate: 5× (Claude Sonnet 4.6)

| Metric | Value | Status |
|--------|------:|:------:|
| Avg questions/min | 47.35 | |
| Avg RPM | 378.8 (47.35 × 8 turns) | |
| Peak RPM | 1,136 (× 3.0 ratio) | ✅ fits (11% utilization) |
| Avg TPM | 4,280,303 | |
| Peak TPM | 12,840,909 | |
| max_tokens overhead | 3,996/req (4,096 − 100) | |
| Effective Peak TPM | 17,381,818 | ❌ exceeds (290% utilization) |

**Verdict: ❌ Does not fit** — TPM is the bottleneck.

### Optimization Recommendations

1. **Reduce max_tokens**: Set to ~300 instead of 4,096 (actual output is ~100). Frees ~3,796 TPM/request.
2. **Enable prompt caching**: Cache reads do NOT count toward TPM — biggest TPM saver.
3. **Reduce RAG chunks**: 12 chunks × 300 = 3,600 tokens/turn. Can quality be maintained with 6–8 chunks?
4. **Output burndown**: Claude 5× burndown means each output token costs 5 TPM. Constrain output length.
5. **Request quota increase**: After optimization, if still over limit, request TPM increase via AWS console.

---

## 5. Business Value Analysis

### Dimension 1a — Productivity Increase (Revenue Uplift)

| Tier | Effectiveness | Efficiency | Productive Hrs/Mo | Monthly Value | Annual Value |
|------|:------------:|:----------:|------------------:|--------------:|-------------:|
| Conservative | 50% | 50% | 17,500 | $5,250,000 | $63,000,000 |
| **Moderate** | **65%** | **60%** | **27,300** | **$8,190,000** | **$98,280,000** |
| Optimistic | 80% | 70% | 39,200 | $11,760,000 | $141,120,000 |

**Calculation (Moderate):**
- Time saved: 40 − 12 = 28 min/session
- Effective sessions: 150,000 × 65% = 97,500
- Time saved hours: 97,500 × 28 / 60 = 45,500 hrs
- Productive hours: 45,500 × 60% = 27,300 hrs
- Productivity value: 27,300 × $300/hr = $8,190,000/mo

### Dimension 1b — Cost Savings (Mutually Exclusive with 1a)

| Tier | Productive Hrs/Mo | Monthly Savings | Annual Savings |
|------|------------------:|--------------:|-------------:|
| Conservative | 17,500 | $1,312,500 | $15,750,000 |
| **Moderate** | **27,300** | **$2,047,500** | **$24,570,000** |
| Optimistic | 39,200 | $2,940,000 | $35,280,000 |

### ROI Summary (Moderate Tier, Dim 1a only)

| Metric | Value |
|--------|------:|
| Dim 1a (Moderate, annual) | $98,280,000 |
| **Grand total annual value** | **$98,280,000** |
| Agent cost (annual) | $613,575 |
| **Net value** | **$97,666,425** |
| **ROI** | **15,918%** |
| **Payback period** | **~2.3 days** |

---

## 6. Step-by-Step Calculation Explanations

### Token Profile
- Base context: 8,700 = 1,000 (system) + 4,000 (tools) + 100 (user) + 3,600 (RAG: 12 × 300)
- Cacheable prefix: 5,000 = 1,000 (system) + 4,000 (tools)
- Delta per turn: 600 = 100 (tool call) + 500 (tool result)
- Turns per question: 8 = 7 tool invocations + 1
- Output per question: 800 = 100 (response) + 7 × 100 (tool calls)

### Turn-by-Turn Breakdown (Q1)
- Turn 0: 8,700 input → WRITE 8,700 (entire prompt — first turn of session)
- Turn 1: 9,300 input → READ 8,700 + WRITE 600 (new tool delta)
- Turn 2: 9,900 input → READ 9,300 + WRITE 600 (new tool delta)
- Turn 3: 10,500 input → READ 9,900 + WRITE 600 (new tool delta)
- Turn 4: 11,100 input → READ 10,500 + WRITE 600 (new tool delta)
- Turn 5: 11,700 input → READ 11,100 + WRITE 600 (new tool delta)
- Turn 6: 12,300 input → READ 11,700 + WRITE 600 (new tool delta)
- Turn 7: 12,900 input → READ 12,300 + REG 600 (last turn — won't be re-read)
- Total Q1 input: 86,400 tokens across 8 turns

### Cross-Question Caching
- Q2 Turn 0: READ 5,000 (system+tools cached from Q1) + WRITE 3,700 (new user question + RAG)
- Cross-Q caching saves re-writing 5,000 tokens at $3.75/M on each subsequent question

### Cache Math (Monthly)
- Cache write: 6,225,000,000 tokens × $3.75/M = $23,343.75
- Cache read: 58,125,000,000 tokens × $0.30/M = $17,437.50
- Regular input: 450,000,000 tokens × $3.00/M = $1,350.00
- Output: 600,000,000 tokens × $15.00/M = $9,000.00
- Total: $23,343.75 + $17,437.50 + $1,350.00 + $9,000.00 = $51,131.25

### No-Cache Baseline
- Total input/question: 86,400 tokens × 750,000 questions × $3.00/M = $194,400.00
- Total output: 800 tokens × 750,000 questions × $15.00/M = $9,000.00
- Total: $194,400.00 + $9,000.00 = $203,400.00

### Capacity Planning
- Active minutes: 12h × 60 × 22d = 15,840 min
- Avg Q/min: 750,000 ÷ 15,840 = 47.35
- Avg RPM: 47.35 × 8 = 378.8
- Peak RPM: 378.8 × 3.0 = 1,136
- Base context: 8,700; delta: 600
- Avg input/turn: 8,700 + (600/2) × 7 = 10,800
- Avg output/turn: (7 × 100 + 100) / 8 = 100
- Avg TPM: 378.8 × (10,800 + 100 × 5) = 4,280,303
- Peak TPM: 4,280,303 × 3.0 = 12,840,909
- max_tokens overhead: 4,096 − 100 = 3,996
- Effective peak TPM: 12,840,909 + (1,136 × 3,996) = 17,381,818

### Business Value
- Time saved: 40 − 12 = 28 min/session
- Moderate: 150,000 × 65% = 97,500 effective sessions
- Productive hrs: 97,500 × 28/60 × 60% = 27,300 hrs/mo
- Productivity: 27,300 × $300 = $8,190,000/mo → $98,280,000/yr
- Cost savings: 27,300 × $75 = $2,047,500/mo → $24,570,000/yr
- Grand total: $98,280,000/yr
- Net value: $98,280,000 − $613,575 = $97,666,425/yr
- ROI: ($97,666,425 / $613,575) × 100 = 15,918%
- Payback: ($613,575 / $98,280,000) × 365 = ~2.3 days
