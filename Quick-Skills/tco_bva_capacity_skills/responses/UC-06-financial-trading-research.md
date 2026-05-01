# UC-06: Financial Trading Research Agent — Full Cost Estimate

> **Use Case:** Price a research agent for a hedge fund. Claude Opus 4.6 in us-east-1. 100K sessions/month, 8 questions per session. 10 tools (market data API, SEC filings search, earnings transcript search, sentiment analyzer, portfolio analyzer, risk calculator, news aggregator, peer comparison, valuation model, trade simulator). Heavy RAG: 15 chunks of 400 tokens. Output 500 tokens. Business value: analysts spend 30 min per research query, AI reduces to 8 min, analyst cost $150/hr, revenue per hour $500.

---

## 1. Assumptions

### Workload Profile

| Parameter | Value |
|-----------|-------|
| Region | us-east-1 |
| Model | Claude Opus 4.6 |
| Tier / Variant | Standard / Global (Cross-Region) |
| Sessions/month | 100,000 |
| Questions/session | 8 |
| Questions/month | 800,000 |
| Tools | 10 (market data API, SEC filings search, earnings transcript search, sentiment analyzer, portfolio analyzer, risk calculator, news aggregator, peer comparison, valuation model, trade simulator) |
| Turns/question | 11 (10 tool invocations + 1 final answer) |

### Token Profile

| Parameter | Value |
|-----------|-------|
| System prompt | 1,000 tokens |
| Tool descriptions | 4,000 tokens (10 tools) |
| User input | 100 tokens |
| RAG chunks | 15 × 400 = 6,000 tokens |
| Tool call (output) | 100 tokens |
| Tool result (input) | 500 tokens |
| Final answer | 500 tokens |
| **Base prompt (turn 0)** | **11,100** = 1,000 + 4,000 + 100 + 6,000 |
| **Cacheable prefix** | **5,000** = 1,000 + 4,000 |
| **Delta per tool turn** | **600** = 100 + 500 |
| **Total input/question** | **155,100** tokens (across 11 turns) |
| **Output/question** | **1,500** = 500 + 10 × 100 |

### Model Pricing

| Price Type | $/1M tokens | Source |
|-----------|-------------|--------|
| Input | $5.00 | Standard Global, us-east-1 |
| Output | $25.00 | Standard Global, us-east-1 |
| Cache Read | $0.50 | 10% of input |
| Cache Write | $6.25 | 125% of input |

---

## 2. Model Cost Breakdown

### With Prompt Caching

**Per-Question Cache Splits:**

| | Cache Write | Cache Read | Regular Input | Total |
|---|---:|---:|---:|---:|
| Q1 (first in session) | 16,500 | 138,000 | 600 | 155,100 ✓ |
| Q2+ (subsequent) | 11,500 | 143,000 | 600 | 155,100 ✓ |

**Per-Session Totals (8 questions):**

| Category | Tokens |
|----------|-------:|
| Cache Write | 97,000 |
| Cache Read | 1,139,000 |
| Regular Input | 4,800 |
| Output | 12,000 |
| **Total** | **1,252,800** (= 8 × 155,100 + 12,000 output ✓) |

**Monthly Cost (With Caching):**

| Component | Monthly Tokens | Cost |
|-----------|---------------:|-----:|
| Cache Write | 9,700,000,000 | $60,625.00 |
| Cache Read | 113,900,000,000 | $56,950.00 |
| Regular Input | 480,000,000 | $2,400.00 |
| Output | 1,200,000,000 | $30,000.00 |
| **Total** | | **$149,975.00/mo** |

### Without Caching (Baseline)

| Component | Cost |
|-----------|-----:|
| Input (all at $5.00/M) | $620,400.00 |
| Output | $30,000.00 |
| **Total** | **$650,400.00/mo** |

### Caching Savings

| Metric | Value |
|--------|------:|
| Monthly savings | $500,425.00 |
| Annual savings | $6,005,100.00 |
| Savings % | **76.9%** |

---

## 3. Combined Total Cost

*AgentCore not included — not explicitly requested in prompt.*

| Metric | Value |
|--------|------:|
| **Monthly** | **$149,975.00** |
| **Annual** | **$1,799,700.00** |
| Per session | $1.4998 |
| Per question | $0.1875 |

---

## 4. Capacity Check

**Quotas (Claude Opus 4.6, us-east-1, Global):**
- RPM limit: 10,000
- TPM limit: 3,000,000

**Traffic Profile:**
- Active hours: 12h/day × 22 days/month = 15,840 active minutes
- Output burndown rate: 5× (Claude Opus 4.6)

| Metric | Value | Status |
|--------|------:|:------:|
| Avg questions/min | 50.51 | |
| Avg RPM | 555.6 (50.51 × 11 turns) | |
| Peak RPM | 1,667 (× 3.0 ratio) | ✅ fits (17% utilization) |
| Avg TPM | 8,211,111 | |
| Peak TPM | 24,633,333 | |
| max_tokens overhead | 3,960/req (4,096 − 136) | |
| Effective Peak TPM | 31,233,333 | ❌ exceeds (1,041% utilization) |

**Verdict: ❌ Does not fit** — TPM is the bottleneck. Peak TPM exceeds quota by ~10×.

### Optimization Recommendations

1. **Reduce max_tokens**: Set to ~500 instead of 4,096 (actual output is ~136 avg/turn). Frees ~3,960 TPM/request.
2. **Enable prompt caching**: Cache reads do NOT count toward TPM — biggest TPM saver.
3. **Reduce RAG chunks**: 15 chunks × 400 = 6,000 tokens/turn. Can quality be maintained with 8–10 chunks?
4. **Output burndown**: Claude 5× burndown means each output token costs 5 TPM. Constrain output length.
5. **Split into sub-agents**: 10 tools in one agent causes massive compounding. Split into specialized sub-agents (e.g., market data agent, filings agent, risk agent) to reduce per-agent tool count.
6. **Request quota increase**: After optimization, request TPM increase via AWS console. Provide ramp plan showing current and projected usage.

---

## 5. Business Value Analysis

### Dimension 1a — Productivity Increase (Revenue Uplift)

| Tier | Effectiveness | Efficiency | Productive Hrs/Mo | Monthly Value | Annual Value |
|------|:------------:|:----------:|------------------:|--------------:|-------------:|
| Conservative | 50% | 50% | 9,167 | $4,583,333 | $55,000,000 |
| **Moderate** | **65%** | **60%** | **14,300** | **$7,150,000** | **$85,800,000** |
| Optimistic | 80% | 70% | 20,533 | $10,266,667 | $123,200,000 |

**Calculation (Moderate):**
- Time saved: 30 − 8 = 22 min/session
- Effective sessions: 100,000 × 65% = 65,000
- Time saved hours: 65,000 × 22 / 60 = 23,833 hrs
- Productive hours: 23,833 × 60% = 14,300 hrs
- Productivity value: 14,300 × $500/hr = $7,150,000/mo

### Dimension 1b — Cost Savings (Mutually Exclusive with 1a)

| Tier | Productive Hrs/Mo | Monthly Savings | Annual Savings |
|------|------------------:|--------------:|-------------:|
| Conservative | 9,167 | $1,375,000 | $16,500,000 |
| **Moderate** | **14,300** | **$2,145,000** | **$25,740,000** |
| Optimistic | 20,533 | $3,080,000 | $36,960,000 |

### ROI Summary (Moderate Tier, Dim 1a only)

| Metric | Value |
|--------|------:|
| Dim 1a (Moderate, annual) | $85,800,000 |
| **Grand total annual value** | **$85,800,000** |
| Agent cost (annual) | $1,799,700 |
| **Net value** | **$84,000,300** |
| **ROI** | **4,667%** |
| **Payback period** | **~8 days** |

---

## 6. Step-by-Step Calculation Explanations

### Token Profile
- Base context: 11,100 = 1,000 (system) + 4,000 (tools) + 100 (user) + 6,000 (RAG)
- Cacheable prefix: 5,000 = 1,000 (system) + 4,000 (tools)
- Delta per turn: 600 = 100 (tool call) + 500 (tool result)
- Turns per question: 11 = 10 tool invocations + 1
- Output per question: 1,500 = 500 (response) + 10 × 100 (tool calls)

### Turn-by-Turn Breakdown (Q1)
- Turn 0: 11,100 input → WRITE 11,100 (entire prompt — first turn of session)
- Turn 1: 11,700 input → READ 11,100 + WRITE 600 (new tool delta)
- Turn 2: 12,300 input → READ 11,700 + WRITE 600 (new tool delta)
- Turn 3: 12,900 input → READ 12,300 + WRITE 600 (new tool delta)
- Turn 4: 13,500 input → READ 12,900 + WRITE 600 (new tool delta)
- Turn 5: 14,100 input → READ 13,500 + WRITE 600 (new tool delta)
- Turn 6: 14,700 input → READ 14,100 + WRITE 600 (new tool delta)
- Turn 7: 15,300 input → READ 14,700 + WRITE 600 (new tool delta)
- Turn 8: 15,900 input → READ 15,300 + WRITE 600 (new tool delta)
- Turn 9: 16,500 input → READ 15,900 + WRITE 600 (new tool delta)
- Turn 10: 17,100 input → READ 16,500 + REG 600 (last turn — won't be re-read)
- Total Q1 input: 155,100 tokens across 11 turns

### Cross-Question Caching
- Q2 Turn 0: READ 5,000 (system+tools cached from Q1) + WRITE 6,100 (new user question + RAG)
- Cross-Q caching saves re-writing 5,000 tokens at $6.25/M on each subsequent question

### Cache Math (Monthly)
- Cache write: 9,700,000,000 tokens × $6.25/M = $60,625.00
- Cache read: 113,900,000,000 tokens × $0.50/M = $56,950.00
- Regular input: 480,000,000 tokens × $5.00/M = $2,400.00
- Output: 1,200,000,000 tokens × $25.00/M = $30,000.00
- Total: $60,625.00 + $56,950.00 + $2,400.00 + $30,000.00 = $149,975.00

### No-Cache Baseline
- Total input/question: 155,100 tokens × 800,000 questions × $5.00/M = $620,400.00
- Total output: 1,500 tokens × 800,000 questions × $25.00/M = $30,000.00
- Total: $620,400.00 + $30,000.00 = $650,400.00

### Capacity Planning
- Active minutes: 12h × 60 × 22d = 15,840 min
- Avg Q/min: 800,000 ÷ 15,840 = 50.51
- Avg RPM: 50.51 × 11 = 555.6
- Peak RPM: 555.6 × 3.0 = 1,667
- Base context: 11,100; delta: 600
- Avg input/turn: 11,100 + (600/2) × 10 = 14,100
- Avg output/turn: (10 × 100 + 500) / 11 = 136
- Avg TPM: 555.6 × (14,100 + 136 × 5) = 8,211,111
- Peak TPM: 8,211,111 × 3.0 = 24,633,333
- max_tokens overhead: 4,096 − 136 = 3,960
- Effective peak TPM: 24,633,333 + (1,667 × 3,960) = 31,233,333

### Business Value
- Time saved: 30 − 8 = 22 min/session
- Moderate: 100,000 × 65% = 65,000 effective sessions
- Productive hrs: 65,000 × 22/60 × 60% = 14,300 hrs/mo
- Productivity: 14,300 × $500 = $7,150,000/mo → $85,800,000/yr
- Cost savings: 14,300 × $150 = $2,145,000/mo → $25,740,000/yr
- Grand total: $85,800,000/yr
- Net value: $85,800,000 − $1,799,700 = $84,000,300/yr
- ROI: ($84,000,300 / $1,799,700) × 100 = 4,667%
- Payback: ($1,799,700 / $85,800,000) × 365 = ~7.7 days
