# UC-02: Airline Booking & Disruption Agent Multi-Agent — Full Cost Estimate

> **Use Case:** "I'm building a multi-agent system for a major airline. Parent router on Nova Lite, three sub-agents on Claude Sonnet 4.6: (1) Booking agent — 45% traffic, 4 tools, (2) Flight status & rebooking agent — 35% traffic, 6 tools, (3) Loyalty & complaints agent — 20% traffic, 3 tools. 3M sessions/month, 5 questions per session, us-west-2. Include AgentCore. Calculate business value — manual handle time is 18 min, with AI 5 min, human cost $40/hr. The airline has 80M loyalty members, 2% monthly churn without AI, 1.5% with AI, $200 revenue per member per year."

---

## 1. Assumptions

### Workload Profile

| Parameter | Parent Router | Booking Agent | Flight Status Agent | Loyalty Agent |
|-----------|:------------:|:-------------:|:-------------------:|:-------------:|
| Region | us-west-2 | us-west-2 | us-west-2 | us-west-2 |
| Model | Nova Lite | Claude Sonnet 4.6 | Claude Sonnet 4.6 | Claude Sonnet 4.6 |
| Traffic share | 100% | 45% | 35% | 20% |
| Sessions/month | 3,000,000 | 1,350,000 | 1,050,000 | 600,000 |
| Questions/session | 5 | 5 | 5 | 5 |
| Questions/month | 15,000,000 | 6,750,000 | 5,250,000 | 3,000,000 |
| Tools invoked | 0 | 4 | 6 | 3 |
| Turns/question | 1 | 5 | 7 | 4 |

### Token Profile

| Parameter | Parent Router | Sub-Agents (all 3) |
|-----------|:------------:|:------------------:|
| System prompt tokens | 500 | 1,000 |
| Tool description tokens | 0 | 4,000 |
| User input tokens | 100 | 100 |
| RAG chunks | 0 | 10 |
| Tokens per RAG chunk | 300 | 300 |
| RAG tokens | 0 | 3,000 |
| Tool call tokens (output) | 100 | 100 |
| Tool result tokens (input) | 500 | 500 |
| Output tokens | 50 | 100 |
| Delta per tool turn | 600 | 600 |
| Base prompt | 600 | 8,100 |
| Cacheable base | 500 | 5,000 |

### Model Pricing (per 1M tokens, Standard Global)

| Model | Input | Output | Cache Read | Cache Write |
|-------|------:|-------:|-----------:|------------:|
| Nova Lite (us-west-2) | $0.30 | $2.50 | $0.075 | N/A |
| Claude Sonnet 4.6 (us-west-2) | $3.00 | $15.00 | $0.30 | $3.75 |

### AgentCore Pricing (us-west-2)

| Component | Unit | Price |
|-----------|------|------:|
| Runtime vCPU | vCPU-Hour | $0.0895 |
| Runtime Memory | GB-Hour | $0.00945 |
| Gateway Invocations | per invocation | $0.000005 |
| Gateway Search | per invocation | $0.000025 |
| Gateway Tool Indexing | per tool-month | $0.0002 |
| STM (Short-Term Memory) | per event | $0.00025 |
| LTM Storage (Built-in) | per record-month | $0.00075 |
| LTM Retrieval | per retrieval | $0.0005 |

---

## 2. Model Cost Breakdown

### 2a. Parent Router (Nova Lite)

| Component | Monthly Cost |
|-----------|------------:|
| Cache read | $450.00 |
| Cache write | $0.00 |
| Regular input | $0.00 |
| Output | $1,875.00 |
| **Total with caching** | **$2,325.00** |
| No-cache baseline | $4,575.00 |
| Savings | $2,250.00 (49.2%) |

### 2b. Booking Agent (Claude Sonnet 4.6, 45% traffic)

| Component | Monthly Cost |
|-----------|------------:|
| Cache write | $149,343.75 |
| Cache read | $81,000.00 |
| Regular input | $12,150.00 |
| Output | $50,625.00 |
| **Total with caching** | **$293,118.75** |
| No-cache baseline | $992,250.00 |
| Savings | $699,131.25 (70.5%) |

### 2c. Flight Status & Rebooking Agent (Claude Sonnet 4.6, 35% traffic)

| Component | Monthly Cost |
|-----------|------------:|
| Cache write | $139,781.25 |
| Cache read | $97,020.00 |
| Regular input | $9,450.00 |
| Output | $55,125.00 |
| **Total with caching** | **$301,376.25** |
| No-cache baseline | $1,146,600.00 |
| Savings | $845,223.75 (73.7%) |

### 2d. Loyalty & Complaints Agent (Claude Sonnet 4.6, 20% traffic)

| Component | Monthly Cost |
|-----------|------------:|
| Cache write | $59,625.00 |
| Cache read | $27,090.00 |
| Regular input | $5,400.00 |
| Output | $18,000.00 |
| **Total with caching** | **$110,115.00** |
| No-cache baseline | $342,000.00 |
| Savings | $231,885.00 (67.8%) |

### 2e. Combined Model Cost

| Agent | Monthly Cost | % of Total |
|-------|------------:|:----------:|
| Parent Router (Nova Lite) | $2,325.00 | 0.3% |
| Booking Agent (Sonnet 4.6) | $293,118.75 | 41.5% |
| Flight Status Agent (Sonnet 4.6) | $301,376.25 | 42.6% |
| Loyalty Agent (Sonnet 4.6) | $110,115.00 | 15.6% |
| **Total Model Cost** | **$706,935.00** | 100% |
| No-cache baseline | $2,485,425.00 | — |
| **Overall caching savings** | **$1,778,490.00 (71.5%)** | — |

---

## 3. AgentCore Cost Breakdown

### AgentCore Parameters

| Parameter | Value |
|-----------|-------|
| Questions/month | 15,000,000 |
| Sessions/month | 3,000,000 |
| Tools invoked (weighted avg) | 5 (0.45×4 + 0.35×6 + 0.20×3 = 4.5 ≈ 5) |
| Tools indexed | 13 (4+6+3) |
| vCPUs | 6 (3 sub-agents × 2) |
| Peak memory | 4 GB |
| I/O wait | 70% |
| Idle time between Qs | 30s |
| Time per question | (5+1) × 4s = 24.0s |
| Session duration | 5 × 24s + 4 × 30s = 240s (4 min) |

### Runtime

| Component | Calculation | Monthly Cost |
|-----------|-------------|------------:|
| vCPU | 36.0s/session × 6 vCPU × $0.0895/hr ÷ 3600 × 3M sessions | $16,110.00 |
| Memory | 240.0s × 4 GB × $0.00945/hr ÷ 3600 × 3M sessions | $7,560.00 |
| **Runtime Total** | | **$23,670.00** |

### Gateway

| Component | Calculation | Monthly Cost |
|-----------|-------------|------------:|
| Invocations | (5+1) × 15M = 90M × $0.000005 | $450.00 |
| Search | 15M × $0.000025 | $375.00 |
| Tool Indexing | 13 × $0.0002 | $0.00 |
| **Gateway Total** | | **$825.00** |

### Memory

| Component | Calculation | Monthly Cost |
|-----------|-------------|------------:|
| STM | 2 events/Q × 15M × $0.00025 | $7,500.00 |
| LTM Storage | 3 records/session × 3M × $0.00075 | $6,750.00 |
| LTM Retrieval | 1/Q × 15M × $0.0005 | $7,500.00 |
| **Memory Total** | | **$21,750.00** |

### AgentCore Total

| Component | Monthly | Annual | % |
|-----------|--------:|-------:|:-:|
| Runtime | $23,670.00 | $284,040.00 | 51% |
| Gateway | $825.00 | $9,900.00 | 2% |
| Memory | $21,750.00 | $261,000.00 | 47% |
| **Total AgentCore** | **$46,245.00** | **$554,940.00** | 100% |

---

## 4. Combined Total Cost

| Component | Monthly | Annual |
|-----------|--------:|-------:|
| Model Inference (all agents) | $706,935.00 | $8,483,220.00 |
| AgentCore Infrastructure | $46,245.00 | $554,940.00 |
| **Grand Total** | **$753,180.00** | **$9,038,160.00** |
| Per session (3M/mo) | $0.2511 | — |
| Per question (15M/mo) | $0.0502 | — |

---

## 5. Capacity Check

Checked against Claude Sonnet on-demand quotas in us-west-2 for the **Booking Agent** (heaviest sub-agent: 6.75M questions/month, 4 tools).

| Metric | Value |
|--------|------:|
| Active minutes/month | 15,840 (12h × 60 × 22d) |
| Avg questions/min | 426.1 |
| LLM calls/question | 5 (4 tools + 1) |
| Avg RPM | 2,130.7 |
| **Peak RPM** | **6,392** |
| RPM quota | 250 |
| RPM utilization | **2,557%** ❌ |
| Avg input/turn | 9,300 tokens |
| Avg output/turn | 100 tokens |
| Avg TPM | 20,880,682 |
| Peak TPM | 62,642,045 |
| max_tokens overhead | 3,996/request |
| **Effective peak TPM** | **88,184,659** |
| TPM quota | 2,000,000 |
| TPM utilization | **4,409%** ❌ |

**Verdict: ❌ Does NOT fit on Standard tier defaults.**

The booking agent alone exceeds both RPM (26×) and TPM (44×) quotas. This is expected for a 3M session/month airline workload. Recommendations:

1. **Request quota increase** — this is a major airline production workload requiring Priority tier or custom allocation
2. **Reduce max_tokens** from 4,096 to ~300 (actual output is ~100 tokens) — frees ~3,996 TPM/request
3. **Enable prompt caching** — cache reads don't count toward TPM
4. **Consider multi-region** — split traffic across us-west-2 and us-east-1
5. **Priority tier** — provides higher quotas for production workloads

---

## 6. Business Value Analysis

### Dimension 1a — Productivity Increase (Revenue Uplift)

| Parameter | Value |
|-----------|-------|
| Time without AI | 18 min |
| Time with AI | 5 min |
| Time saved | 13 min |
| Human cost/hr | $40 |
| Revenue/hr | $300 |
| Agent cost/month | $753,180 |

| Tier | Effectiveness | Efficiency | Productive Hrs/Mo | Monthly Value | Annual Value |
|------|:------------:|:----------:|------------------:|--------------:|-------------:|
| Conservative | 50% | 50% | 162,500 | $48,750,000 | $585,000,000 |
| **Moderate** | **65%** | **60%** | **253,500** | **$76,050,000** | **$912,600,000** |
| Optimistic | 80% | 70% | 364,000 | $109,200,000 | $1,310,400,000 |

### Dimension 1b — Cost Savings (Alternative View)

| Tier | Productive Hrs/Mo | Monthly Savings | Annual Savings |
|------|------------------:|----------------:|---------------:|
| Conservative | 162,500 | $6,500,000 | $78,000,000 |
| **Moderate** | **253,500** | **$10,140,000** | **$121,680,000** |
| Optimistic | 364,000 | $14,560,000 | $174,720,000 |

### Dimension 2 — Customer Churn Reduction

| Parameter | Value |
|-----------|-------|
| Total loyalty members | 80,000,000 |
| Churn without AI | 2.0% monthly |
| Churn with AI | 1.5% monthly |
| Churn reduction | 0.5 percentage points |
| Customers retained | 400,000 |
| Revenue per member/year | $200 |
| **Annual value** | **$80,000,000** |

### ROI Summary (Moderate Tier, Dim 1a + Dim 2)

| Metric | Value |
|--------|------:|
| Dim 1a (Productivity, Moderate) | $912,600,000/yr |
| Dim 2 (Churn Reduction) | $80,000,000/yr |
| **Grand Total Value** | **$992,600,000/yr** |
| Agent Cost | $9,038,160/yr |
| **Net Value** | **$983,561,840/yr** |
| **ROI** | **10,882%** |
| **Payback** | **3.3 days** |

---

## 7. Step-by-Step Calculation Explanations

### Token Profile

**Parent Router (Nova Lite):**
- cacheable_base = 500 + 0 = 500
- base_prompt = 500 + 100 + 0 = 600
- turns = 0 + 1 = 1
- total_input_per_question = 600
- total_output_per_question = 50
- questions/month = 3M × 5 = 15M

**Sub-Agents (Claude Sonnet 4.6):**
- cacheable_base = 1,000 + 4,000 = 5,000
- rag_tokens = 10 × 300 = 3,000
- base_prompt = 5,000 + 100 + 3,000 = 8,100
- delta = 100 + 500 = 600

**Booking (4 tools):** turns=5, total_input = 8,100 + 8,700 + 9,300 + 9,900 + 10,500 = 46,500; output = 100 + 4×100 = 500
**Flight (6 tools):** turns=7, total_input = Σ(8,100 + i×600) for i=0..6 = 69,300; output = 100 + 6×100 = 700
**Loyalty (3 tools):** turns=4, total_input = 8,100 + 8,700 + 9,300 + 9,900 = 36,000; output = 100 + 3×100 = 400

### Cache Math (Booking Agent Example)

**Q1 (first question, N=4):**
- cache_write = base_prompt + (N-1)×delta = 8,100 + 3×600 = 9,900
- cache_read = Σ(k=1..4)[8,100 + (k-1)×600] = 8,100 + 8,700 + 9,300 + 9,900 = 36,000
- regular = delta = 600
- Sum check: 9,900 + 36,000 + 600 = 46,500 ✓

**Q2+ (subsequent, N=4):**
- cache_write = (100 + 3,000) + (4-1)×600 = 3,100 + 1,800 = 4,900
- cache_read = 5,000 + Σ(k=1..4)[8,100 + (k-1)×600] = 5,000 + 36,000 = 41,000
- regular = 600
- Sum check: 4,900 + 41,000 + 600 = 46,500 ✓

**Session (5 questions):**
- session_cw = 9,900 + 4×4,900 = 29,500
- session_cr = 36,000 + 4×41,000 = 200,000
- session_reg = 600 + 4×600 = 3,000
- Sum check: 29,500 + 200,000 + 3,000 = 232,500 = 5 × 46,500 ✓

**Monthly (1.35M sessions):**
- monthly_cw = 1,350,000 × 29,500 = 39,825,000,000 tokens
- monthly_cr = 1,350,000 × 200,000 = 270,000,000,000 tokens
- monthly_reg = 1,350,000 × 3,000 = 4,050,000,000 tokens

**Costs:**
- cache_write = 39,825M / 1M × $3.75 = $149,343.75
- cache_read = 270,000M / 1M × $0.30 = $81,000.00
- regular = 4,050M / 1M × $3.00 = $12,150.00
- output = 1,350,000 × 5 × 500 / 1M × $15.00 = $50,625.00
- Total = $293,118.75

### AgentCore Calculation

- time_per_question = (5+1) × 4s = 24s
- active_cpu_per_question = 24 × 0.30 = 7.2s
- total_active_cpu_per_session = 7.2 × 5 = 36s
- idle_gaps = (5-1) × 30 = 120s
- session_duration = (24 × 5) + 120 = 240s

### Business Value Calculation (Moderate)

- time_saved = 18 - 5 = 13 min
- effective_sessions = 3,000,000 × 0.65 = 1,950,000
- time_saved_hrs = 1,950,000 × 13 / 60 = 422,500 hrs
- productive_hrs = 422,500 × 0.60 = 253,500 hrs
- Dim 1a: 253,500 × $300 = $76,050,000/mo → $912,600,000/yr
- Dim 1b: 253,500 × $40 = $10,140,000/mo → $121,680,000/yr
- Dim 2: (2.0% - 1.5%) × 80M = 400,000 retained × $200 = $80,000,000/yr
- Grand total: $912,600,000 + $80,000,000 = $992,600,000/yr
- Agent cost: $753,180 × 12 = $9,038,160/yr
- Net value: $992,600,000 - $9,038,160 = $983,561,840
- ROI: ($983,561,840 / $9,038,160) × 100 = 10,882%
- Payback: ($9,038,160 / $992,600,000) × 365 = 3.3 days
