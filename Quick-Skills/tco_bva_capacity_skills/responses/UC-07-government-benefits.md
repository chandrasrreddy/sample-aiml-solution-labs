# UC-07: Government Benefits Eligibility Agent — Full Cost Estimate

> **Use Case:** "Cost for a citizen-facing benefits eligibility agent. Nova Pro in us-west-2. 1M sessions/month, 3 questions per session. 4 tools (eligibility rules engine, document validator, case status lookup, appointment scheduler). System prompt 2,000 tokens with policy rules. Business value: case workers spend 25 min per inquiry, AI reduces to 6 min, cost $45/hr."

---

## 1. Assumptions

### Workload Profile

| Parameter | Value |
|-----------|-------|
| Region | us-west-2 |
| Model | Amazon Nova Pro |
| Tier / Variant | Standard / Regional |
| Sessions/month | 1,000,000 |
| Questions/session | 3 |
| Questions/month | 3,000,000 |
| Tools | 4 (eligibility rules engine, document validator, case status lookup, appointment scheduler) |
| Turns/question | 5 (4 tool invocations + 1 final answer) |

### Token Profile

| Parameter | Value |
|-----------|-------|
| System prompt | 2,000 tokens |
| Tool descriptions | 4,000 tokens (4 tools) |
| User input | 100 tokens |
| RAG chunks | 10 × 300 = 3,000 tokens |
| Tool call (output) | 100 tokens |
| Tool result (input) | 500 tokens |
| Final answer | 100 tokens |
| **Base prompt (turn 0)** | **9,100** = 2,000 + 4,000 + 100 + 3,000 |
| **Cacheable prefix** | **6,000** = 2,000 + 4,000 |
| **Delta per tool turn** | **600** = 100 + 500 |
| **Total input/question** | **51,500** tokens (across 5 turns) |
| **Output/question** | **500** = 100 + 4 × 100 |

### Model Pricing

| Price Type | $/1M tokens | Source |
|-----------|-------------|--------|
| Input | $1.00 | Standard Regional, us-west-2 |
| Output | $11.00 | Standard Regional, us-west-2 |
| Cache Read | $0.20 | Standard Regional, us-west-2 |
| Cache Write | $0.00 | Free for Nova Pro |

---

## 2. Model Cost Breakdown

### With Prompt Caching

**Per-Question Cache Splits:**

| | Cache Write | Cache Read | Regular Input | Total |
|---|---:|---:|---:|---:|
| Q1 (first in session) | 10,900 | 40,000 | 600 | 51,500 ✓ |
| Q2+ (subsequent) | 4,900 | 46,000 | 600 | 51,500 ✓ |

**Per-Session Totals (3 questions):**

| Category | Tokens |
|----------|-------:|
| Cache Write | 20,700 |
| Cache Read | 132,000 |
| Regular Input | 1,800 |
| Output | 1,500 |
| **Total** | **156,000** (= 3 × 51,500 + 1,500 output ✓) |

**Monthly Cost (With Caching):**

| Component | Monthly Tokens | Cost |
|-----------|---------------:|-----:|
| Cache Write | 20,700,000,000 | $0.00 |
| Cache Read | 132,000,000,000 | $26,400.00 |
| Regular Input | 1,800,000,000 | $1,800.00 |
| Output | 1,500,000,000 | $16,500.00 |
| **Total** | | **$44,700.00/mo** |

### Without Caching (Baseline)

| Component | Cost |
|-----------|-----:|
| Input (all at $1.00/M) | $154,500.00 |
| Output | $16,500.00 |
| **Total** | **$171,000.00/mo** |

### Caching Savings

| Metric | Value |
|--------|------:|
| Monthly savings | $126,300.00 |
| Annual savings | $1,515,600.00 |
| Savings % | **73.9%** |

---

## 3. Combined Total Cost

*AgentCore not included — not explicitly requested in prompt.*

| Metric | Value |
|--------|------:|
| **Monthly** | **$44,700.00** |
| **Annual** | **$536,400.00** |
| Per session | $0.0447 |
| Per question | $0.0149 |

---

## 4. Capacity Check

**Quotas (Nova Pro, us-west-2, Regional):**
- ⚠️ Quota cache not available — using estimated defaults for Nova Pro
- RPM limit: 1,000 (estimated)
- TPM limit: 300,000 (estimated)

**Traffic Profile:**
- Active hours: 12h/day × 22 days/month = 15,840 active minutes
- Output burndown rate: 1× (Nova Pro — not Claude)

| Metric | Value | Status |
|--------|------:|:------:|
| Avg questions/min | 189.39 | |
| Avg RPM | 946.97 (189.39 × 5 turns) | |
| Peak RPM | 2,841 (× 3.0 ratio) | ❌ exceeds (284% utilization) |
| Avg input/turn | 9,100 + (600/2) × 4 = 10,300 | |
| Avg output/turn | (4 × 100 + 100) / 5 = 100 | |
| Avg TPM | 946.97 × (10,300 + 100 × 1) = 9,858,488 | |
| Peak TPM | 29,575,465 | |
| max_tokens overhead | 3,996/req (4,096 − 100) | |
| Effective Peak TPM | 40,930,101 | ❌ exceeds |

**Verdict: ❌ Does not fit** — Both RPM and TPM exceed estimated limits at 1M sessions/month.

### Optimization Recommendations

1. **Request quota increase**: At 3M questions/month, a quota increase is required. Contact AWS support.
2. **Reduce max_tokens**: Set to ~300 instead of 4,096 (actual output is ~100). Frees ~3,796 TPM/request.
3. **Enable prompt caching**: Cache reads do NOT count toward TPM — biggest TPM saver.
4. **Reduce RAG chunks**: 10 chunks × 300 = 3,000 tokens/turn. Can quality be maintained with 5 chunks?
5. **Multi-region distribution**: Spread traffic across us-west-2 and us-east-1 to double effective quotas.
6. **Run `--refresh` for actual quotas**: `python3 ~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh` to get real per-model limits.

---

## 5. Business Value Analysis

### Dimension 1a — Productivity Increase (Revenue Uplift)

| Tier | Effectiveness | Efficiency | Productive Hrs/Mo | Monthly Value | Annual Value |
|------|:------------:|:----------:|------------------:|--------------:|-------------:|
| Conservative | 50% | 50% | 79,167 | $23,750,000 | $285,000,000 |
| **Moderate** | **65%** | **60%** | **123,500** | **$37,050,000** | **$444,600,000** |
| Optimistic | 80% | 70% | 177,333 | $53,200,000 | $638,400,000 |

**Calculation (Moderate):**
- Time saved: 25 − 6 = 19 min/session
- Effective sessions: 1,000,000 × 65% = 650,000
- Time saved hours: 650,000 × 19 / 60 = 205,833 hrs
- Productive hours: 205,833 × 60% = 123,500 hrs
- Productivity value: 123,500 × $300/hr = $37,050,000/mo

### Dimension 1b — Cost Savings (Mutually Exclusive with 1a)

| Tier | Productive Hrs/Mo | Monthly Savings | Annual Savings |
|------|------------------:|--------------:|-------------:|
| Conservative | 79,167 | $3,562,500 | $42,750,000 |
| **Moderate** | **123,500** | **$5,557,500** | **$66,690,000** |
| Optimistic | 177,333 | $7,980,000 | $95,760,000 |

### ROI Summary (Moderate Tier, Dim 1a)

| Metric | Value |
|--------|------:|
| Dim 1a (Moderate, annual) | $444,600,000 |
| **Grand total annual value** | **$444,600,000** |
| Agent cost (annual) | $536,400 |
| **Net value** | **$444,063,600** |
| **ROI** | **82,786%** |
| **Payback period** | **< 1 day** |

---

## 6. Step-by-Step Calculation Explanations

### Token Profile
- Base context: 9,100 = 2,000 (system) + 4,000 (tools) + 100 (user) + 3,000 (RAG)
- Cacheable prefix: 6,000 = 2,000 (system) + 4,000 (tools)
- Delta per turn: 600 = 100 (tool call) + 500 (tool result)
- Turns per question: 5 = 4 tool invocations + 1
- Output per question: 500 = 100 (response) + 4 × 100 (tool calls)

### Turn-by-Turn Breakdown (Q1)
- Turn 0: 9,100 input → WRITE 9,100 (entire prompt — first turn of session)
- Turn 1: 9,700 input → READ 9,100 + WRITE 600 (new tool delta)
- Turn 2: 10,300 input → READ 9,700 + WRITE 600 (new tool delta)
- Turn 3: 10,900 input → READ 10,300 + WRITE 600 (new tool delta)
- Turn 4: 11,500 input → READ 10,900 + REG 600 (last turn — won't be re-read)
- Total Q1 input: 51,500 tokens across 5 turns

### Cross-Question Caching
- Q2 Turn 0: READ 6,000 (system+tools cached from Q1) + WRITE 3,100 (new user question + RAG)
- Cross-Q caching saves re-writing 6,000 tokens at $0.00/M on each subsequent question (free writes for Nova Pro)

### Cache Math (Monthly)
- Cache write: 20,700,000,000 tokens × $0.00/M = $0.00
- Cache read: 132,000,000,000 tokens × $0.20/M = $26,400.00
- Regular input: 1,800,000,000 tokens × $1.00/M = $1,800.00
- Output: 1,500,000,000 tokens × $11.00/M = $16,500.00
- Total: $0.00 + $26,400.00 + $1,800.00 + $16,500.00 = $44,700.00

### No-Cache Baseline
- Total input/question: 51,500 tokens × 3,000,000 questions × $1.00/M = $154,500.00
- Total output: 500 tokens × 3,000,000 questions × $11.00/M = $16,500.00
- Total: $154,500.00 + $16,500.00 = $171,000.00

### Capacity Planning
- Active minutes: 12h × 60 × 22d = 15,840 min
- Avg Q/min: 3,000,000 ÷ 15,840 = 189.39
- Avg RPM: 189.39 × 5 = 946.97
- Peak RPM: 946.97 × 3.0 = 2,841
- Base context: 9,100; delta: 600
- Avg input/turn: 9,100 + (600/2) × 4 = 10,300
- Avg output/turn: (4 × 100 + 100) / 5 = 100
- Avg TPM: 946.97 × (10,300 + 100 × 1) = 9,858,488
- Peak TPM: 9,858,488 × 3.0 = 29,575,465
- max_tokens overhead: 4,096 − 100 = 3,996
- Effective peak TPM: 29,575,465 + (2,841 × 3,996) = 40,930,101

### Business Value
- Time saved: 25 − 6 = 19 min/session
- Moderate: 1,000,000 × 65% = 650,000 effective sessions
- Productive hrs: 650,000 × 19/60 × 60% = 123,500 hrs/mo
- Productivity: 123,500 × $300 = $37,050,000/mo → $444,600,000/yr
- Cost savings: 123,500 × $45 = $5,557,500/mo → $66,690,000/yr
- Grand total: $444,600,000/yr
- Net value: $444,600,000 − $536,400 = $444,063,600/yr
- ROI: ($444,063,600 / $536,400) × 100 = 82,786%
- Payback: ($536,400 / $444,600,000) × 365 = ~0.4 days
