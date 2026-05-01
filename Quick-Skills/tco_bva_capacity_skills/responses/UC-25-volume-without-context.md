# UC-25: Volume Without Context — Full Cost Estimate

> **Use Case:** "I have 10 million questions per month. How much will this cost on Bedrock?"

---

## Assumptions Made (not in prompt)

The prompt provides only volume (10M questions/month) with no model, region, workload shape, or use case context. Per the vague use case handling rules:

| Assumption | Value | Rationale |
|-----------|-------|-----------|
| Model | Claude Sonnet 4.6 | Default for unspecified workload |
| Region | us-east-1 | Default region |
| Tier | Standard Global (cross-region) | Default tier |
| Sessions/month | 2,000,000 | 10M questions ÷ 5 Q/session |
| Questions/session | 5 | Standard assumption for unspecified workload |
| Tools invoked | 3 | Moderate default for unspecified workload |
| Token profile | Standard defaults | All default values from pricing spec |

---

## 1. Assumptions

### Workload Profile

| Parameter | Value |
|-----------|-------|
| Region | us-east-1 |
| Model | Claude Sonnet 4.6 |
| Tier | Standard Global (cross-region) |
| Sessions/month | 2,000,000 |
| Questions/session | 5 |
| Questions/month | 10,000,000 |
| Tools invoked/question | 3 |
| Turns/question | 4 (3 tools + 1) |

### Token Profile (Standard Defaults)

| Parameter | Value |
|-----------|-------|
| System prompt | 1,000 tokens |
| Tool descriptions | 4,000 tokens |
| User input | 100 tokens |
| RAG chunks | 10 × 300 = 3,000 tokens |
| Tool call (output) | 100 tokens |
| Tool result (input) | 500 tokens |
| Final output | 100 tokens |
| **Cacheable base** | **5,000** (1,000 + 4,000) |
| **Base prompt** | **8,100** (5,000 + 100 + 3,000) |
| **Delta per tool turn** | **600** (100 + 500) |
| **Output per question** | **400** (100 + 3 × 100) |

### Model Pricing (Standard Global, per 1M tokens)

| Component | Price |
|-----------|-------|
| Input | $3.00 |
| Output | $15.00 |
| Cache read | $0.30 |
| Cache write | $3.75 |

---

## 2. Model Cost Breakdown

### With Caching

| Component | Monthly Tokens | Monthly Cost |
|-----------|---------------|-------------|
| Cache write | 53,000,000,000 | $198,750.00 |
| Cache read | 301,000,000,000 | $90,300.00 |
| Regular input | 6,000,000,000 | $18,000.00 |
| Output | 4,000,000,000 | $60,000.00 |
| **Total (with cache)** | — | **$367,050.00** |

### Without Caching (Baseline)

| Component | Monthly Cost |
|-----------|-------------|
| Input | $1,080,000.00 |
| Output | $60,000.00 |
| **Total (no cache)** | **$1,140,000.00** |

### Savings

| Metric | Value |
|--------|-------|
| Monthly savings | $772,950.00 |
| Annual savings | $9,275,400.00 |
| Savings % | **67.8%** |

### Per-Unit Costs

| Metric | Value |
|--------|-------|
| Per question | $0.0367 |
| Per session | $0.1835 |
| Monthly | $367,050.00 |
| Annual | $4,404,600.00 |

---

## 3. Capacity Check — Standard Tier

### Quota Limits (from query_quotas)

| Quota | Limit | Source |
|-------|-------|--------|
| RPM | 10,000 | Global cross-region model inference requests per minute for Anthropic Claude Sonnet 4.6 |
| TPM | 6,000,000 | Global cross-region model inference tokens per minute for Anthropic Claude Sonnet 4.6 |

### RPM Calculation

| Step | Calculation | Result |
|------|-------------|--------|
| Active minutes/month | 12h × 60 × 22d | **15,840 min** |
| Avg questions/min | 10,000,000 ÷ 15,840 | **631.31 Q/min** |
| LLM calls/question | 3 tools + 1 | **4 calls** |
| Avg RPM | 631.31 × 4 | **2,525.25 RPM** |
| Peak RPM | 2,525.25 × 3.0× | **7,575.76 RPM** |
| RPM limit | — | 10,000 |
| **RPM fits?** | 7,575.76 ≤ 10,000 | **✅ Yes** |
| RPM utilization | 7,575.76 / 10,000 | **75.8%** |

### TPM Calculation

| Step | Calculation | Result |
|------|-------------|--------|
| Base context | 100 + 1,000 + 4,000 + 3,000 | **8,100 tokens** |
| Delta | 100 + 500 | **600 tokens** |
| Avg input/turn | 8,100 + (600/2) × 3 | **9,000 tokens** |
| Avg output/turn | (3 × 100 + 100) / 4 | **100 tokens** |
| Output burndown rate | 5× (Claude Sonnet 4.6) | **5×** |
| Avg TPM | 2,525.25 × (9,000 + 100 × 5) | **23,989,899 TPM** |
| Peak TPM | 23,989,899 × 3.0× | **71,969,697 TPM** |
| max_tokens overhead | 4,096 − 100 | **3,996/req** |
| Effective peak TPM | 71,969,697 + (7,575.76 × 3,996) | **102,242,424 TPM** |
| TPM limit | — | 6,000,000 |
| **TPM fits?** | 102,242,424 ≤ 6,000,000 | **❌ No** |
| TPM utilization | 102,242,424 / 6,000,000 | **1,704%** |

### Capacity Verdict

| Check | Result |
|-------|--------|
| RPM | ✅ 7,576 peak vs 10,000 limit (75.8% utilization) |
| TPM | ❌ 102,242,424 effective peak vs 6,000,000 limit (1,704% utilization) |
| **Overall** | **❌ Does NOT fit in Standard tier** |

> **Bottleneck: TPM.** At 10M questions/month with 3 tools and Claude's 5× output burndown rate, the effective peak TPM exceeds the Standard quota by ~17×. This workload requires significant optimization or a quota increase.

### Optimization Checklist

| Area | Current | Action |
|------|---------|--------|
| RAG chunks | 10 × 300 = 3,000 tokens | Reduce chunks or tokens per chunk |
| System prompt | 1,000 tokens | Shorten instructions, remove redundancy |
| Prompt caching | Enabled | Cache reads do NOT count toward TPM — biggest saver |
| max_tokens | 4,096 (actual output ~100) | **Reduce to ~300 to free 3,996 TPM/request** |
| Tool count | 3 tools | Use AC Gateway dynamic tool selection |
| Output length | ~100 tokens (×5 burndown) | Constrain with max_tokens and prompt instructions |
| Architecture | Single agent | Split into parent + sub-agents to reduce compounding |

---

## 4. Summary

| Metric | Value |
|--------|-------|
| Model cost (with caching) | **$367,050/mo** ($4,404,600/yr) |
| Model cost (no caching) | $1,140,000/mo ($13,680,000/yr) |
| Caching savings | 67.8% |
| Per question | $0.0367 |
| Per session | $0.1835 |
| Capacity fit | ❌ TPM bottleneck (1,704% utilization) |

**Answer: 10 million questions per month on Claude Sonnet 4.6 in us-east-1 costs approximately $367,050/month ($4.4M/year) with prompt caching enabled.** Without caching, the cost would be $1.14M/month. However, this volume significantly exceeds Standard tier TPM quotas — a quota increase or workload optimization is required before deployment.

---

## 5. Step-by-Step Calculation Explanations

### Token Profile

```
cacheable_base = 1,000 (system) + 4,000 (tools) = 5,000
rag_tokens = 10 × 300 = 3,000
base_prompt = 5,000 + 100 (user) + 3,000 (RAG) = 8,100
delta = 100 (tool call) + 500 (tool result) = 600
turns = 3 + 1 = 4
output_per_question = 100 (answer) + 3 × 100 (tool calls) = 400
```

### Turn-by-Turn Input (per question)

```
Turn 0: 8,100 tokens (base_prompt)
Turn 1: 8,700 tokens (base_prompt + 1 × 600)
Turn 2: 9,300 tokens (base_prompt + 2 × 600)
Turn 3: 9,900 tokens (base_prompt + 3 × 600)
Total input per question: 36,000 tokens
```

### Cache Splits

```
Q1: cache_write = 9,300, cache_read = 26,100, regular = 600 (sum = 36,000 ✓)
Q2: cache_write = 4,300, cache_read = 31,100, regular = 600 (sum = 36,000 ✓)

Per session (5 Q):
  cache_write = 9,300 + 4 × 4,300 = 26,500
  cache_read = 26,100 + 4 × 31,100 = 150,500
  regular = 600 + 4 × 600 = 3,000
  output = 5 × 400 = 2,000
  Sum check: 26,500 + 150,500 + 3,000 = 180,000 = 5 × 36,000 ✓
```

### Monthly Token Volumes

```
monthly_cache_write = 2,000,000 × 26,500 = 53,000,000,000
monthly_cache_read = 2,000,000 × 150,500 = 301,000,000,000
monthly_regular = 2,000,000 × 3,000 = 6,000,000,000
monthly_output = 2,000,000 × 2,000 = 4,000,000,000
```

### Cost Calculation (With Cache)

```
cache_write_cost = 53,000,000,000 / 1M × $3.75 = $198,750.00
cache_read_cost = 301,000,000,000 / 1M × $0.30 = $90,300.00
regular_input_cost = 6,000,000,000 / 1M × $3.00 = $18,000.00
output_cost = 4,000,000,000 / 1M × $15.00 = $60,000.00
total_with_cache = $198,750.00 + $90,300.00 + $18,000.00 + $60,000.00 = $367,050.00
```

### No-Cache Baseline

```
total_input_per_question = 36,000
monthly_input = 10,000,000 × 36,000 = 360,000,000,000
no_cache_input = 360,000,000,000 / 1M × $3.00 = $1,080,000.00
no_cache_output = 4,000,000,000 / 1M × $15.00 = $60,000.00
no_cache_total = $1,080,000.00 + $60,000.00 = $1,140,000.00
savings = $1,140,000.00 - $367,050.00 = $772,950.00 (67.8%)
```

### RPM Calculation

```
active_minutes_per_month = 12 × 60 × 22 = 15,840
avg_questions_per_min = 10,000,000 / 15,840 = 631.31
avg_rpm = 631.31 × 4 = 2,525.25
peak_rpm = 2,525.25 × 3.0 = 7,575.76
```

### TPM Calculation

```
base_context = 100 + 1,000 + 4,000 + 3,000 = 8,100
avg_input_per_turn = 8,100 + (600/2) × 3 = 9,000
avg_output_per_turn = (3 × 100 + 100) / 4 = 100
avg_tpm = 2,525.25 × (9,000 + 100 × 5) = 23,989,899
peak_tpm = 23,989,899 × 3.0 = 71,969,697
max_tokens_overhead = 4,096 - 100 = 3,996
effective_peak_tpm = 71,969,697 + (7,575.76 × 3,996) = 102,242,424
```
