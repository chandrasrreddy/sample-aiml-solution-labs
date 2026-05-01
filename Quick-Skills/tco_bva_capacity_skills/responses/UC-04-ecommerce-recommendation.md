# UC-04: E-Commerce Product Recommendation Chatbot — Full Cost Estimate

> **Use Case:** Cost estimate for a product recommendation chatbot for an online retailer. Nova Pro in us-east-1. 2M sessions/month, 4 questions per session. 3 tools (product search, inventory check, cart add). RAG with 8 chunks of product catalog data. Calculate business value — the retailer has $5B annual revenue and expects 3% sales increase from better CX. Also check if this fits in Standard tier.

---

## 1. Assumptions

### Workload Profile

| Parameter | Value |
|-----------|-------|
| Region | us-east-1 |
| Model | Amazon Nova Pro |
| Tier / Variant | Standard / Regional (in-region) |
| Sessions/month | 2,000,000 |
| Questions/session | 4 |
| Questions/month | 8,000,000 |
| Tools invoked/question | 3 (product search, inventory check, cart add) |
| Turns/question | 4 (3 tools + 1 final) |
| RAG chunks/question | 8 |

### Token Profile

| Parameter | Tokens |
|-----------|--------|
| System prompt | 1,000 |
| Tool descriptions | 4,000 |
| User input | 100 |
| RAG (8 × 300) | 2,400 |
| Cacheable prefix (system + tools) | 5,000 |
| Base prompt (prefix + user + RAG) | 7,500 |
| Tool call (output) | 100 |
| Tool result (input) | 500 |
| Delta per tool turn | 600 |
| Final answer output | 100 |
| Total output/question | 400 (100 answer + 3 × 100 tool calls) |

### Model Pricing (per 1M tokens)

| Price Type | $/1M Tokens | Source |
|------------|-------------|--------|
| Input | $0.80 | Standard Regional, Nova Pro, us-east-1 |
| Output | $3.20 | Standard Regional, Nova Pro, us-east-1 |
| Cache Read | $0.20 | Prompt Caching, Nova Pro, us-east-1 |
| Cache Write | $0.00 | Nova Pro — free cache writes (null → $0.00) |

**Note:** Nova Pro has free cache writes — the cache_write price is $0.00/M tokens. This is a significant cost advantage over models that charge for cache writes.

---

## 2. Model Cost Breakdown

### With Caching (Incremental Prefix Caching)

#### Cache Splits Per Question

**Q1 (first question in session):**

| Category | Tokens |
|----------|--------|
| Cache Write | 8,700 |
| Cache Read | 24,300 |
| Regular Input | 600 |
| **Total** | **33,600** |

**Q2+ (subsequent questions in session):**

| Category | Tokens |
|----------|--------|
| Cache Write | 3,700 |
| Cache Read | 29,300 |
| Regular Input | 600 |
| **Total** | **33,600** |

**Per Session (4 questions):**

| Category | Tokens |
|----------|--------|
| Cache Write | 19,800 |
| Cache Read | 112,200 |
| Regular Input | 2,400 |
| Output | 1,600 |

#### Monthly Token Volumes

| Category | Monthly Tokens |
|----------|---------------|
| Cache Write | 39,600,000,000 |
| Cache Read | 224,400,000,000 |
| Regular Input | 4,800,000,000 |
| Output | 3,200,000,000 |

#### Monthly Cost (With Caching)

| Category | Tokens | Price | Cost |
|----------|--------|-------|------|
| Cache Write | 39.6B | $0.00/M | $0.00 |
| Cache Read | 224.4B | $0.20/M | $44,880.00 |
| Regular Input | 4.8B | $0.80/M | $3,840.00 |
| Output | 3.2B | $3.20/M | $10,240.00 |
| **Total** | | | **$58,960.00/mo** |

### Without Caching (Baseline)

| Category | Calculation | Cost |
|----------|-------------|------|
| Input | 33,600 tokens/Q × 8M Q × $0.80/M | $215,040.00 |
| Output | 400 tokens/Q × 8M Q × $3.20/M | $10,240.00 |
| **Total** | | **$225,280.00/mo** |

### Caching Savings

| Metric | Value |
|--------|-------|
| Monthly savings | $166,320.00 |
| Annual savings | $1,995,840.00 |
| Savings % | **73.8%** |

---

## 3. Combined Total Cost

| Metric | Value |
|--------|-------|
| Model cost (monthly) | $58,960.00 |
| Model cost (annual) | $707,520.00 |
| Per session | $0.0295 |
| Per question | $0.0074 |

*AgentCore not included — not explicitly requested.*

---

## 4. Capacity Check

### Standard Tier Quotas (Nova Pro, us-east-1, On-demand)

| Quota | Limit |
|-------|-------|
| RPM | 250 |
| TPM | 1,000,000 |

### RPM Analysis

| Metric | Value |
|--------|-------|
| Active minutes/month | 15,840 (12h × 60 × 22d) |
| Avg questions/min | 505.05 |
| LLM calls/question | 4 (3 tools + 1) |
| Avg RPM | 2,020.2 |
| Peak RPM (3× ratio) | **6,060.6** |
| RPM limit | 250 |
| RPM utilization | **2,424%** ❌ |

### TPM Analysis

| Metric | Value |
|--------|-------|
| Base context | 7,500 tokens |
| Avg input/turn | 8,400 tokens |
| Avg output/turn | 100 tokens |
| Output burndown rate | 1× (Nova Pro, not Claude) |
| Avg TPM | 17,171,717 |
| Peak TPM (3×) | 51,515,152 |
| max_tokens overhead | 3,996/request |
| Effective peak TPM | **75,733,333** |
| TPM limit | 1,000,000 |
| TPM utilization | **7,573%** ❌ |

### Verdict: ❌ Does NOT Fit in Standard Tier

Both RPM and TPM massively exceed Standard tier quotas. At 2M sessions/month with 4 questions each (8M questions/month), this workload requires:
- **24× the RPM quota** (6,061 peak vs 250 limit)
- **76× the TPM quota** (75.7M effective peak vs 1M limit)

### Recommendations

1. **Quota increase required** — request significantly higher RPM/TPM limits through AWS support
2. **Cross-region inference** — distribute load across multiple regions
3. **Reduce max_tokens** — currently 4,096 but actual output is ~100; reducing to ~300 would free 3,796 TPM/request
4. **Prompt caching** — already enabled; cache reads don't count toward TPM (biggest saver)
5. **Consider Priority or Provisioned tier** — higher quotas available
6. **Phased rollout** — start with lower volume and ramp up as quota increases are granted

---

## 5. Business Value Analysis

### Dimension 1: Time Savings → Productivity Increase

| Parameter | Value |
|-----------|-------|
| Time without AI | 20 min |
| Time with AI | 10 min |
| Time saved | 10 min/session |
| Human cost/hr | $75 |
| Revenue/hr | $300 |

| Tier | Effectiveness | Efficiency | Productive Hrs/Mo | Cost Savings/Mo | Productivity/Mo |
|------|:------------:|:----------:|:-----------------:|:---------------:|:---------------:|
| Conservative | 50% | 50% | 83,333 | $6,250,000 | $25,000,000 |
| **Moderate** | **65%** | **60%** | **130,000** | **$9,750,000** | **$39,000,000** |
| Optimistic | 80% | 70% | 186,667 | $14,000,000 | $56,000,000 |

### Dimension 3: Sales Increase from Better CX

| Parameter | Value |
|-----------|-------|
| Annual sales revenue | $5,000,000,000 |
| AI-driven sales increase | 3.0% |
| **Annual value** | **$150,000,000** |

### Summary (Moderate Tier for Dim 1a)

| Metric | Value |
|--------|-------|
| Dim 1a (Productivity, annual) | $468,000,000 |
| Dim 3 (Sales increase, annual) | $150,000,000 |
| **Grand total (annual)** | **$618,000,000** |
| Agent cost (annual) | $707,520 |
| **Net value** | **$617,292,480** |
| **ROI** | **87,247%** |
| **Payback** | **< 1 day** |

---

## 6. Step-by-Step Calculation Explanations

### Token Profile
- Base context: 7,500 = 1,000 (system) + 4,000 (tools) + 100 (user) + 2,400 (RAG)
- Cacheable prefix: 5,000 = 1,000 (system) + 4,000 (tools)
- Delta per turn: 600 = 100 (tool call) + 500 (tool result)
- Turns per question: 4 = 3 tool invocations + 1
- Output per question: 400 = 100 (response) + 3 × 100 (tool calls)

### Turn-by-Turn Breakdown (Q1)
- Turn 0: 7,500 input tokens → WRITE 7,500 (entire prompt — first turn of session)
- Turn 1: 8,100 input tokens → READ 7,500 (cached prefix) + WRITE 600 (new tool delta)
- Turn 2: 8,700 input tokens → READ 8,100 (cached prefix) + WRITE 600 (new tool delta)
- Turn 3: 9,300 input tokens → READ 8,700 (cached prefix) + REG 600 (last turn — won't be re-read)
- Total Q1 input: 33,600 tokens across 4 turns

### Cross-Question Caching
- Q2 Turn 0: READ 5,000 (system+tools still cached from Q1) + WRITE 2,500 (new user question + RAG)
- Cross-Q caching saves re-writing 5,000 tokens at $0.0/M on each subsequent question

### Cache Math (Monthly)
- Cache write: 39,600,000,000 tokens × $0.0/M = $0.00
- Cache read: 224,400,000,000 tokens × $0.2/M = $44,880.00
- Regular input: 4,800,000,000 tokens × $0.8/M = $3,840.00
- Output: 3,200,000,000 tokens × $3.2/M = $10,240.00
- Total: $0.00 + $44,880.00 + $3,840.00 + $10,240.00 = $58,960.00

### No-Cache Baseline
- Total input/question: 33,600 tokens × 8,000,000 questions × $0.8/M = $215,040.00
- Total output: 400 tokens × 8,000,000 questions × $3.2/M = $10,240.00
- Total: $215,040.00 + $10,240.00 = $225,280.00

### Business Value
- Time saved: 20 min − 10 min = 10 min/session
- Moderate: 2,000,000 sessions × 65% effectiveness = 1,300,000 effective sessions
- Productive hours: 1,300,000 × 10 min ÷ 60 × 60% efficiency = 130,000 hrs/month
- Cost savings: 130,000 hrs × $75/hr = $9,750,000/mo
- Productivity uplift: 130,000 hrs × $300/hr = $39,000,000/mo
- Dim 3: $5,000,000,000/yr × 3.0% = $150,000,000/yr
- Grand total: $468,000,000 (Dim1) + $150,000,000 (Dim3) = $618,000,000/yr
- Agent cost: $58,960/mo × 12 = $707,520/yr
- Net value: $618,000,000 − $707,520 = $617,292,480/yr
- ROI: 87,247%
- Payback: < 1 day
