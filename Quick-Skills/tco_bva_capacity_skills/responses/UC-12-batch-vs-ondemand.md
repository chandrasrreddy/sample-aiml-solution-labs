# UC-12: Batch vs On-Demand Comparison — Full Cost Estimate

> **Use Case:** "I have a content moderation pipeline that processes 10M documents per month. Each document is 1 question, no tools, 500 input tokens, 50 output tokens. Compare the cost of running this on Claude Haiku 4.5 in Batch mode vs Standard mode in us-west-2."

---

## 1. Assumptions

### Workload Profile

| Parameter | Value |
|-----------|-------|
| Region | us-west-2 (Oregon) |
| Model | Claude Haiku 4.5 |
| Sessions/month | 10,000,000 |
| Questions/session | 1 |
| Questions/month | 10,000,000 |
| Tools invoked | 0 (pure document moderation) |
| Turns/question | 1 |

### Token Profile

| Parameter | Tokens |
|-----------|--------|
| System prompt | 0 |
| Tool descriptions | 0 |
| User input | 500 |
| RAG chunks | 0 × 300 = 0 |
| Tool call (per call) | 100 |
| Tool result (per result) | 500 |
| Output (final answer) | 50 |
| **cacheable_base** | 0 (system + tools) |
| **base_prompt** | 500 (cacheable_base + user + RAG) |
| **delta** | 600 (tool_call + tool_result) |
| **total_input_per_question** | 500 |
| **output_per_question** | 50 |

### Model Pricing — Standard Global (us-west-2)

| Price Type | $/M Tokens |
|------------|-----------|
| Input | $1.00 |
| Output | $5.00 |
| Cache Read | $0.10 |
| Cache Write | $1.25 |

### Model Pricing — Batch Global (us-west-2)

| Price Type | $/M Tokens |
|------------|-----------|
| Input | $0.50 |
| Output | $2.50 |
| Cache Read | N/A (not supported) |
| Cache Write | N/A (not supported) |

**Note:** Batch pricing is exactly 50% of Standard pricing for both input and output tokens. Batch mode does not support prompt caching.

---

## 2. Standard Mode Cost Breakdown

### N=0 Special Case — Caching Model

With `tools_invoked=0` and `questions_per_session=1`, there is only 1 turn per question and no cross-question caching benefit.

**Q1 (first and only question in session):**
- cache_write = base_prompt = 500
- cache_read = 0
- regular = 0

**Per-Session Totals:**
- session_cw = 500
- session_cr = 0
- session_reg = 0
- session_output = 50

**Verification:** 500 + 0 + 0 = 500 = 1 × 500 ✅

### Monthly Token Volumes

| Category | Tokens |
|----------|--------|
| Cache Write | 10,000,000 × 500 = 5,000,000,000 |
| Cache Read | 10,000,000 × 0 = 0 |
| Regular Input | 10,000,000 × 0 = 0 |
| Output | 10,000,000 × 50 = 500,000,000 |

### With Caching

| Component | Calculation | Cost |
|-----------|-------------|------|
| Cache Write | 5,000M / 1M × $1.25 | $6,250.00 |
| Cache Read | 0 / 1M × $0.10 | $0.00 |
| Regular Input | 0 / 1M × $1.00 | $0.00 |
| Output | 500M / 1M × $5.00 | $2,500.00 |
| **Total (with cache)** | | **$8,750.00/mo** |

### Without Caching (Baseline)

| Component | Calculation | Cost |
|-----------|-------------|------|
| Input | 10,000,000 × 500 / 1M × $1.00 | $5,000.00 |
| Output | 10,000,000 × 50 / 1M × $5.00 | $2,500.00 |
| **Total (no cache)** | | **$7,500.00/mo** |

### Caching Impact

| Metric | Value |
|--------|-------|
| With caching | $8,750.00/mo |
| Without caching | $7,500.00/mo |
| Savings | **-$1,250.00/mo (-16.7%)** |

⚠️ **Caching is more expensive for this workload.** With 0 cacheable_base tokens (no system prompt, no tools) and only 1 question per session, every input token is cache-written at $1.25/M (125% of input price) with zero cache reads. **Use no-cache pricing ($7,500.00/mo) for Standard mode.**

### Standard Mode Recommended Cost

| Metric | Monthly | Annual |
|--------|---------|--------|
| Total Model Cost | **$7,500.00** | **$90,000.00** |
| Per Session | $0.00075 | — |
| Per Question | $0.00075 | — |

---

## 3. Batch Mode Cost Breakdown

Batch mode does not support prompt caching. All tokens are billed at the flat Batch rate.

### Monthly Token Volumes

| Category | Tokens |
|----------|--------|
| Input | 10,000,000 × 500 = 5,000,000,000 |
| Output | 10,000,000 × 50 = 500,000,000 |

### Batch Cost

| Component | Calculation | Cost |
|-----------|-------------|------|
| Input | 5,000M / 1M × $0.50 | $2,500.00 |
| Output | 500M / 1M × $2.50 | $1,250.00 |
| **Total** | | **$3,750.00/mo** |

### Batch Mode Cost Summary

| Metric | Monthly | Annual |
|--------|---------|--------|
| Total Model Cost | **$3,750.00** | **$45,000.00** |
| Per Session | $0.000375 | — |
| Per Question | $0.000375 | — |

---

## 4. Side-by-Side Comparison

| Metric | Standard (On-Demand) | Batch | Savings |
|--------|:--------------------:|:-----:|:-------:|
| Input Price ($/M) | $1.00 | $0.50 | 50% cheaper |
| Output Price ($/M) | $5.00 | $2.50 | 50% cheaper |
| Monthly Input Cost | $5,000.00 | $2,500.00 | $2,500.00 |
| Monthly Output Cost | $2,500.00 | $1,250.00 | $1,250.00 |
| **Monthly Total** | **$7,500.00** | **$3,750.00** | **$3,750.00 (50%)** |
| **Annual Total** | **$90,000.00** | **$45,000.00** | **$45,000.00 (50%)** |
| Per Document | $0.00075 | $0.000375 | $0.000375 |
| Prompt Caching | Supported (not beneficial here) | Not supported | — |
| Latency | Real-time | Up to 24 hours | — |

### Key Findings

1. **Batch mode saves exactly 50%** — $3,750/mo ($45,000/yr) compared to Standard on-demand pricing.
2. **Prompt caching provides no benefit** for this workload because:
   - `cacheable_base = 0` (no system prompt, no tool descriptions)
   - `questions_per_session = 1` (no cross-question caching opportunity)
   - With caching enabled, Standard mode would actually cost **more** ($8,750/mo) because cache_write price ($1.25/M) exceeds input price ($1.00/M).
3. **Batch is ideal for content moderation pipelines** — the 24-hour SLA is acceptable for non-real-time document processing.

### Recommendation

✅ **Use Batch mode.** For a content moderation pipeline processing 10M documents/month:
- **$3,750/mo** (Batch) vs **$7,500/mo** (Standard) = **50% savings**
- Annual savings: **$45,000**
- Batch's up-to-24-hour processing window is well-suited for offline content moderation
- No caching benefit in either mode for this workload shape

---

## 5. AgentCore Cost Breakdown

**Not applicable.** This is a simple content moderation pipeline — no AgentCore infrastructure requested.

---

## 6. Capacity Check

**Not applicable for Batch mode.** Batch jobs are queued and processed asynchronously — no RPM/TPM quota concerns.

For Standard mode reference (if real-time processing were needed):
- 10M questions/month ÷ 15,840 active minutes = 631 avg Q/min
- Peak RPM = 631 × 3.0 = 1,894 (1 turn per question)
- This would require adequate RPM quota for Standard mode

---

## 7. Step-by-Step Calculation Explanations

### Token Profile

```
cacheable_base = 0 (system) + 0 (tools) = 0
rag_tokens = 0 × 300 = 0
base_prompt = 0 + 500 (user) + 0 (RAG) = 500
delta = 100 (tool call) + 500 (tool result) = 600
turns = 0 tools + 1 = 1
output_per_question = 50 (response) + 0 × 100 (tool calls) = 50
total_input_per_question = 500 (single turn)
```

### Standard Mode Math

```
No cache (recommended):
  input:  10,000,000 × 500 = 5,000,000,000 tokens × $1.00/M = $5,000.00
  output: 10,000,000 × 50 = 500,000,000 tokens × $5.00/M = $2,500.00
  Total: $7,500.00/mo

With cache (not recommended — more expensive):
  cache_write: 5,000,000,000 tokens × $1.25/M = $6,250.00
  cache_read:  0 tokens × $0.10/M = $0.00
  regular:     0 tokens × $1.00/M = $0.00
  output:      500,000,000 tokens × $5.00/M = $2,500.00
  Total: $8,750.00/mo
  Savings: $7,500.00 - $8,750.00 = -$1,250.00 (-16.7%)
```

### Batch Mode Math

```
input:  10,000,000 × 500 = 5,000,000,000 tokens × $0.50/M = $2,500.00
output: 10,000,000 × 50 = 500,000,000 tokens × $2.50/M = $1,250.00
Total: $3,750.00/mo
```

### Comparison Math

```
Standard (no cache): $7,500.00/mo
Batch:               $3,750.00/mo
Savings:             $7,500.00 - $3,750.00 = $3,750.00/mo (50.0%)
Annual savings:      $3,750.00 × 12 = $45,000.00
```
