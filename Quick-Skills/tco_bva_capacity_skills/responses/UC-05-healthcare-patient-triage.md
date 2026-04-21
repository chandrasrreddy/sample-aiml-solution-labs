# UC-05: Healthcare Patient Triage Agent — Full Cost Estimate

> **Use Case:** Estimate costs for a patient triage agent at a hospital network. Claude Sonnet 4.6 in us-east-1. 200K sessions/month, 6 questions per session. 4 tools (symptom checker, appointment scheduler, medical record lookup, insurance verifier). System prompt is 2,500 tokens (medical guidelines). RAG: 10 chunks. Business value: triage calls take 20 min without AI, 7 min with AI, nurse cost $55/hr. 500K patients, 3% monthly churn without AI, 2.2% with AI, $2,000 revenue per patient per year.

---

## 1. Assumptions

### Workload Profile

| Parameter | Value |
|-----------|-------|
| Region | us-east-1 |
| Model | Claude Sonnet 4.6 |
| Tier / Variant | Standard / Global (Cross-Region) |
| Sessions/month | 200,000 |
| Questions/session | 6 |
| Questions/month | 1,200,000 |
| Tools | 4 (symptom checker, appointment scheduler, medical record lookup, insurance verifier) |
| Turns/question | 5 (4 tool invocations + 1 final answer) |

### Token Profile

| Parameter | Value |
|-----------|-------|
| System prompt | 2,500 tokens |
| Tool descriptions | 4,000 tokens (4 tools) |
| User input | 100 tokens |
| RAG chunks | 10 × 300 = 3,000 tokens |
| Tool call (output) | 100 tokens |
| Tool result (input) | 500 tokens |
| Final answer | 100 tokens |
| **Base prompt (turn 0)** | **9,600** = 2,500 + 4,000 + 100 + 3,000 |
| **Cacheable prefix** | **6,500** = 2,500 + 4,000 |
| **Delta per tool turn** | **600** = 100 + 500 |
| **Total input/question** | **54,000** tokens (across 5 turns) |
| **Output/question** | **500** = 100 + 4 × 100 |

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
| Q1 (first in session) | 11,400 | 42,000 | 600 | 54,000 ✓ |
| Q2+ (subsequent) | 4,900 | 48,500 | 600 | 54,000 ✓ |

**Per-Session Totals (6 questions):**

| Category | Tokens |
|----------|-------:|
| Cache Write | 35,900 |
| Cache Read | 284,500 |
| Regular Input | 3,600 |
| Output | 3,000 |
| **Total** | **327,000** (= 6 × 54,000 + 3,000 output ✓) |

**Monthly Cost (With Caching):**

| Component | Monthly Tokens | Cost |
|-----------|---------------:|-----:|
| Cache Write | 7,180,000,000 | $26,925.00 |
| Cache Read | 56,900,000,000 | $17,070.00 |
| Regular Input | 720,000,000 | $2,160.00 |
| Output | 600,000,000 | $9,000.00 |
| **Total** | | **$55,155.00/mo** |

### Without Caching (Baseline)

| Component | Cost |
|-----------|-----:|
| Input (all at $3.00/M) | $194,400.00 |
| Output | $9,000.00 |
| **Total** | **$203,400.00/mo** |

### Caching Savings

| Metric | Value |
|--------|------:|
| Monthly savings | $148,245.00 |
| Annual savings | $1,778,940.00 |
| Savings % | **72.9%** |

---

## 3. Combined Total Cost

*AgentCore not included — not explicitly requested in prompt.*

| Metric | Value |
|--------|------:|
| **Monthly** | **$55,155.00** |
| **Annual** | **$661,860.00** |
| Per session | $0.2758 |
| Per question | $0.0460 |

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
| Avg questions/min | 75.76 | |
| Avg RPM | 378.8 (75.76 × 5 turns) | |
| Peak RPM | 1,136 (× 3.0 ratio) | ✅ fits (11% utilization) |
| Avg TPM | 4,280,303 | |
| Peak TPM | 12,840,909 | |
| max_tokens overhead | 3,996/req (4,096 − 100) | |
| Effective Peak TPM | 17,381,818 | ❌ exceeds (290% utilization) |

**Verdict: ❌ Does not fit** — TPM is the bottleneck.

### Optimization Recommendations

1. **Reduce max_tokens**: Set to ~300 instead of 4,096 (actual output is ~100). Frees ~3,796 TPM/request.
2. **Enable prompt caching**: Cache reads do NOT count toward TPM — biggest TPM saver.
3. **Reduce RAG chunks**: 10 chunks × 300 = 3,000 tokens/turn. Can quality be maintained with 5 chunks?
4. **Output burndown**: Claude 5× burndown means each output token costs 5 TPM. Constrain output length.
5. **Request quota increase**: After optimization, if still over limit, request TPM increase via AWS console.

---

## 5. Business Value Analysis

### Dimension 1a — Productivity Increase (Revenue Uplift)

| Tier | Effectiveness | Efficiency | Productive Hrs/Mo | Monthly Value | Annual Value |
|------|:------------:|:----------:|------------------:|--------------:|-------------:|
| Conservative | 50% | 50% | 10,833 | $3,250,000 | $39,000,000 |
| **Moderate** | **65%** | **60%** | **16,900** | **$5,070,000** | **$60,840,000** |
| Optimistic | 80% | 70% | 24,267 | $7,280,000 | $87,360,000 |

**Calculation (Moderate):**
- Time saved: 20 − 7 = 13 min/session
- Effective sessions: 200,000 × 65% = 130,000
- Time saved hours: 130,000 × 13 / 60 = 28,167 hrs
- Productive hours: 28,167 × 60% = 16,900 hrs
- Productivity value: 16,900 × $300/hr = $5,070,000/mo

### Dimension 1b — Cost Savings (Mutually Exclusive with 1a)

| Tier | Productive Hrs/Mo | Monthly Savings | Annual Savings |
|------|------------------:|--------------:|-------------:|
| Conservative | 10,833 | $595,833 | $7,150,000 |
| **Moderate** | **16,900** | **$929,500** | **$11,154,000** |
| Optimistic | 24,267 | $1,334,667 | $16,016,000 |

### Dimension 2 — Customer Churn Reduction

| Parameter | Value |
|-----------|------:|
| Total patients | 500,000 |
| Churn without AI | 3.0% monthly |
| Churn with AI | 2.2% monthly |
| Churn reduction | 0.8 pp |
| Patients retained | 4,000 |
| Revenue/patient/year | $2,000 |
| **Annual value** | **$8,000,000** |

### ROI Summary (Moderate Tier, Dim 1a + Dim 2)

| Metric | Value |
|--------|------:|
| Dim 1a (Moderate, annual) | $60,840,000 |
| Dim 2 (annual) | $8,000,000 |
| **Grand total annual value** | **$68,840,000** |
| Agent cost (annual) | $661,860 |
| **Net value** | **$68,178,140** |
| **ROI** | **10,301%** |
| **Payback period** | **~4 days** |

---

## 6. Step-by-Step Calculation Explanations

### Token Profile
- Base context: 9,600 = 2,500 (system) + 4,000 (tools) + 100 (user) + 3,000 (RAG)
- Cacheable prefix: 6,500 = 2,500 (system) + 4,000 (tools)
- Delta per turn: 600 = 100 (tool call) + 500 (tool result)
- Turns per question: 5 = 4 tool invocations + 1
- Output per question: 500 = 100 (response) + 4 × 100 (tool calls)

### Turn-by-Turn Breakdown (Q1)
- Turn 0: 9,600 input → WRITE 9,600 (entire prompt — first turn of session)
- Turn 1: 10,200 input → READ 9,600 + WRITE 600 (new tool delta)
- Turn 2: 10,800 input → READ 10,200 + WRITE 600 (new tool delta)
- Turn 3: 11,400 input → READ 10,800 + WRITE 600 (new tool delta)
- Turn 4: 12,000 input → READ 11,400 + REG 600 (last turn — won't be re-read)
- Total Q1 input: 54,000 tokens across 5 turns

### Cross-Question Caching
- Q2 Turn 0: READ 6,500 (system+tools cached from Q1) + WRITE 3,100 (new user question + RAG)
- Cross-Q caching saves re-writing 6,500 tokens at $3.75/M on each subsequent question

### Cache Math (Monthly)
- Cache write: 7,180,000,000 tokens × $3.75/M = $26,925.00
- Cache read: 56,900,000,000 tokens × $0.30/M = $17,070.00
- Regular input: 720,000,000 tokens × $3.00/M = $2,160.00
- Output: 600,000,000 tokens × $15.00/M = $9,000.00
- Total: $26,925.00 + $17,070.00 + $2,160.00 + $9,000.00 = $55,155.00

### No-Cache Baseline
- Total input/question: 54,000 tokens × 1,200,000 questions × $3.00/M = $194,400.00
- Total output: 500 tokens × 1,200,000 questions × $15.00/M = $9,000.00
- Total: $194,400.00 + $9,000.00 = $203,400.00

### Capacity Planning
- Active minutes: 12h × 60 × 22d = 15,840 min
- Avg Q/min: 1,200,000 ÷ 15,840 = 75.76
- Avg RPM: 75.76 × 5 = 378.8
- Peak RPM: 378.8 × 3.0 = 1,136
- Base context: 9,600; delta: 600
- Avg input/turn: 9,600 + (600/2) × 4 = 10,800
- Avg output/turn: (4 × 100 + 100) / 5 = 100
- Avg TPM: 378.8 × (10,800 + 100 × 5) = 4,280,303
- Peak TPM: 4,280,303 × 3.0 = 12,840,909
- max_tokens overhead: 4,096 − 100 = 3,996
- Effective peak TPM: 12,840,909 + (1,136 × 3,996) = 17,381,818

### Business Value
- Time saved: 20 − 7 = 13 min/session
- Moderate: 200,000 × 65% = 130,000 effective sessions
- Productive hrs: 130,000 × 13/60 × 60% = 16,900 hrs/mo
- Productivity: 16,900 × $300 = $5,070,000/mo → $60,840,000/yr
- Cost savings: 16,900 × $55 = $929,500/mo → $11,154,000/yr
- Dim 2: (3.0% − 2.2%) × 500,000 = 4,000 patients × $2,000 = $8,000,000/yr
- Grand total: $60,840,000 + $8,000,000 = $68,840,000/yr
- Net value: $68,840,000 − $661,860 = $68,178,140/yr
- ROI: ($68,178,140 / $661,860) × 100 = 10,301%
- Payback: ($661,860 / $68,840,000) × 365 = ~3.5 days
