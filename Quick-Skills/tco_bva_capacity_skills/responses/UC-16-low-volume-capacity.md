# UC-16: Low-Volume Capacity Check — Full Cost Estimate

> **Use Case:** "Will 10K sessions per month with 2 questions per session fit in Flex tier for Nova Pro in us-west-2? 3 tools per question."

---

## 1. Assumptions

### Workload Profile

| Parameter | Value |
|-----------|-------|
| Region | us-west-2 |
| Model | Nova Pro |
| Tier | Flex Regional (in-region) |
| Sessions/month | 10,000 |
| Questions/session | 2 |
| Questions/month | 20,000 |
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

### Model Pricing (Flex Regional, per 1M tokens)

| Component | Price |
|-----------|-------|
| Input | $0.40 |
| Output | $1.60 |
| Cache read | $0.10 |
| Cache write | $0.00 (free for Nova) |

> **Note:** Nova Pro in us-west-2 has free cache writes ($0.00/M). Flex tier pricing is Regional (in-region) only — no cross-region Flex pricing available for Nova Pro.

### Capacity Quotas (from query_quotas — Cross-Region On-Demand)

| Quota | Limit | Source |
|-------|-------|--------|
| RPM | 500 | Cross-region model inference requests per minute for Amazon Nova Pro |
| TPM | 2,000,000 | Cross-region model inference tokens per minute for Amazon Nova Pro |

> **Note:** Flex tier does not have separate Flex-specific quotas in the cache. Using on-demand cross-region defaults as the baseline. Flex tier may have different actual limits — consult AWS documentation for Flex-specific quota details.

---

## 2. Model Cost Breakdown

### With Caching

| Component | Monthly Tokens | Monthly Cost |
|-----------|---------------|-------------|
| Cache write | 136,000,000 | $0.00 |
| Cache read | 572,000,000 | $57.20 |
| Regular input | 12,000,000 | $4.80 |
| Output | 8,000,000 | $12.80 |
| **Total (with cache)** | — | **$74.80** |

### Without Caching (Baseline)

| Component | Monthly Cost |
|-----------|-------------|
| Input | $288.00 |
| Output | $12.80 |
| **Total (no cache)** | **$300.80** |

### Savings

| Metric | Value |
|--------|-------|
| Monthly savings | $226.00 |
| Annual savings | $2,712.00 |
| Savings % | **75.1%** |

### Per-Unit Costs

| Metric | Value |
|--------|-------|
| Per question | $0.0037 |
| Per session | $0.0075 |
| Monthly | $74.80 |
| Annual | $897.60 |

---

## 3. Capacity Check — Flex Tier

### RPM Calculation

| Step | Calculation | Result |
|------|-------------|--------|
| Active minutes/month | 12h × 60 × 22d | **15,840 min** |
| Avg questions/min | 20,000 ÷ 15,840 | **1.26 Q/min** |
| LLM calls/question | 3 tools + 1 | **4 calls** |
| Avg RPM | 1.26 × 4 | **5.05 RPM** |
| Peak RPM | 5.05 × 3.0× | **15.15 RPM** |
| RPM limit | — | 500 |
| **RPM fits?** | 15.15 ≤ 500 | **✅ Yes** |
| RPM utilization | 15.15 / 500 | **3.0%** |

### TPM Calculation

| Step | Calculation | Result |
|------|-------------|--------|
| Base context | 100 + 1,000 + 4,000 + 3,000 | **8,100 tokens** |
| Delta | 100 + 500 | **600 tokens** |
| Avg input/turn | 8,100 + (600/2) × 3 | **9,000 tokens** |
| Avg output/turn | (3 × 100 + 100) / 4 | **100 tokens** |
| Output burndown rate | 1× (Nova Pro, not Claude) | **1×** |
| Avg TPM | 5.05 × (9,000 + 100 × 1) | **45,960 TPM** |
| Peak TPM | 45,960 × 3.0× | **137,879 TPM** |
| max_tokens overhead | 4,096 − 100 | **3,996/req** |
| Effective peak TPM | 137,879 + (15.15 × 3,996) | **198,424 TPM** |
| TPM limit | — | 2,000,000 |
| **TPM fits?** | 198,424 ≤ 2,000,000 | **✅ Yes** |
| TPM utilization | 198,424 / 2,000,000 | **9.9%** |

### Flex Tier Verdict

| Check | Result |
|-------|--------|
| RPM | ✅ 15.15 peak vs 500 limit (3.0% utilization) |
| TPM | ✅ 198,424 effective peak vs 2,000,000 limit (9.9% utilization) |
| **Overall** | **✅ Easily fits in Flex tier** |

> This is a very low-volume workload. At only 3% RPM utilization and 10% TPM utilization, there is massive headroom. The workload could scale ~33× before hitting RPM limits and ~10× before hitting TPM limits.

---

## 4. Summary

| Metric | Value |
|--------|-------|
| Model cost (with caching) | **$74.80/mo** ($897.60/yr) |
| Model cost (no caching) | $300.80/mo ($3,609.60/yr) |
| Caching savings | 75.1% |
| Per question | $0.0037 |
| Per session | $0.0075 |
| Capacity fit | ✅ Easily fits (3% RPM, 10% TPM) |

**Answer: Yes, 10K sessions/month with 2 questions per session and 3 tools per question easily fits in Flex tier for Nova Pro in us-west-2.** The workload uses only 3% of RPM quota and 10% of TPM quota, with significant room to grow. The monthly cost with Flex pricing and prompt caching is just $74.80.

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

### Turn-by-Turn (Q1)

```
Turn 0: 8,100 input → WRITE 8,100 (entire prompt — first turn)
Turn 1: 8,700 input → READ 8,100 + WRITE 600 (new tool delta)
Turn 2: 9,300 input → READ 8,700 + WRITE 600
Turn 3: 9,900 input → READ 9,300 + REG 600 (last turn)
Total Q1 input: 36,000 tokens across 4 turns
```

### Cache Splits

```
Q1: cache_write = 9,300, cache_read = 26,100, regular = 600 (sum = 36,000 ✓)
Q2: cache_write = 4,300, cache_read = 31,100, regular = 600 (sum = 36,000 ✓)
Session (2 Q): cache_write = 13,600, cache_read = 57,200, regular = 1,200 (sum = 72,000 = 2 × 36,000 ✓)
```

### Monthly Token Volumes

```
monthly_cache_write = 10,000 × 13,600 = 136,000,000
monthly_cache_read = 10,000 × 57,200 = 572,000,000
monthly_regular = 10,000 × 1,200 = 12,000,000
monthly_output = 10,000 × 800 = 8,000,000
```

### Cost Calculation

```
cache_write_cost = 136,000,000 / 1M × $0.00 = $0.00
cache_read_cost = 572,000,000 / 1M × $0.10 = $57.20
regular_input_cost = 12,000,000 / 1M × $0.40 = $4.80
output_cost = 8,000,000 / 1M × $1.60 = $12.80
total_with_cache = $0.00 + $57.20 + $4.80 + $12.80 = $74.80
```

### No-Cache Baseline

```
total_input_per_question = 8,100 + 8,700 + 9,300 + 9,900 = 36,000
no_cache_input = 20,000 × 36,000 / 1M × $0.40 = $288.00
no_cache_output = 20,000 × 400 / 1M × $1.60 = $12.80
no_cache_total = $288.00 + $12.80 = $300.80
savings = $300.80 - $74.80 = $226.00 (75.1%)
```

### RPM Calculation

```
active_minutes_per_month = 12 × 60 × 22 = 15,840
avg_questions_per_min = 20,000 / 15,840 = 1.26
avg_rpm = 1.26 × 4 = 5.05
peak_rpm = 5.05 × 3.0 = 15.15
```

### TPM Calculation

```
base_context = 100 + 1,000 + 4,000 + 3,000 = 8,100
avg_input_per_turn = 8,100 + (600/2) × 3 = 9,000
avg_output_per_turn = (3 × 100 + 100) / 4 = 100
avg_tpm = 5.05 × (9,000 + 100 × 1) = 45,960
peak_tpm = 45,960 × 3.0 = 137,879
max_tokens_overhead = 4,096 - 100 = 3,996
effective_peak_tpm = 137,879 + (15.15 × 3,996) = 198,424
```
