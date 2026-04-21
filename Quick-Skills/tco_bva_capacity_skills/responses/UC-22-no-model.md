# UC-22: No Model Specified — Customer Support Agent Cost Estimate

> **Use Case:** "I need to build a customer support agent in us-east-1. 500K sessions per month, 5 questions per session, 3 tools. How much will it cost?"

---

## Assumptions Made (not in prompt)

The original prompt does not specify a model. Per the vague use case handling rules:

| Missing Parameter | Assumed Value | Rationale |
|-------------------|---------------|-----------|
| **Model** | Claude Sonnet 4.6 | Default for unspecified model |
| **Tier / Variant** | Standard Global | Default for production workloads |
| **System prompt tokens** | 1,000 | Standard token profile |
| **Tool description tokens** | 4,000 | Standard token profile (3 tools) |
| **User input tokens** | 100 | Standard token profile |
| **Output tokens** | 100 | Standard token profile |
| **RAG chunks** | 10 × 300 tokens | Standard token profile |
| **Tool call tokens** | 100 | Standard token profile |
| **Tool result tokens** | 500 | Standard token profile |

---

## 1. Assumptions

### Workload Profile

| Parameter | Value |
|-----------|-------|
| Region | us-east-1 |
| Model | Claude Sonnet 4.6 |
| Tier / Variant | Standard Global |
| Sessions/month | 500,000 |
| Questions/session | 5 |
| Questions/month | 2,500,000 |
| Tools invoked/question | 3 |
| Turns/question | 4 (3 tool turns + 1 final answer) |

### Token Profile

| Parameter | Value |
|-----------|-------|
| System prompt (T_sys) | 1,000 |
| Tool descriptions (T_tools) | 4,000 |
| User input (T_user) | 100 |
| RAG chunks | 10 × 300 = 3,000 |
| Tool call output (T_call) | 100 |
| Tool result input (T_result) | 500 |
| Final answer output (T_answer) | 100 |
| **Cacheable base** | 5,000 (T_sys + T_tools) |
| **Base prompt** | 8,100 (5,000 + 100 + 3,000) |
| **Delta per tool turn** | 600 (T_call + T_result) |
| **Total input/question** | 36,000 |
| **Total output/question** | 400 |

### Model Pricing (Standard Global, per 1M tokens)

| Price Type | $/1M tokens |
|------------|:-----------:|
| Input | $3.00 |
| Output | $15.00 |
| Cache Read | $0.30 |
| Cache Write | $3.75 |

---

## 2. Model Cost Breakdown

### With Prompt Caching

| Component | Monthly Tokens | Cost |
|-----------|:--------------:|-----:|
| Cache Write | 13,250,000,000 | $49,687.50 |
| Cache Read | 75,250,000,000 | $22,575.00 |
| Regular Input | 1,500,000,000 | $4,500.00 |
| Output | 1,000,000,000 | $15,000.00 |
| **Total (with cache)** | | **$91,762.50** |

### Without Caching (Baseline)

| Component | Monthly Tokens | Cost |
|-----------|:--------------:|-----:|
| Input | 90,000,000,000 | $270,000.00 |
| Output | 1,000,000,000 | $15,000.00 |
| **Total (no cache)** | | **$285,000.00** |

### Caching Savings

| Metric | Value |
|--------|------:|
| Monthly savings | $193,237.50 |
| Annual savings | $2,318,850.00 |
| Savings % | **67.8%** |

---

## 3. Cache Split Details

### Q1 (First question in session)

| Category | Tokens |
|----------|-------:|
| Cache Write | 9,300 |
| Cache Read | 26,100 |
| Regular | 600 |
| **Sum** | **36,000** ✓ |

### Q2+ (Subsequent questions)

| Category | Tokens |
|----------|-------:|
| Cache Write | 4,300 |
| Cache Read | 31,100 |
| Regular | 600 |
| **Sum** | **36,000** ✓ |

### Per Session

| Category | Tokens |
|----------|-------:|
| Cache Write | 9,300 + 4 × 4,300 = 26,500 |
| Cache Read | 26,100 + 4 × 31,100 = 150,500 |
| Regular | 600 + 4 × 600 = 3,000 |
| Output | 5 × 400 = 2,000 |
| **Session identity** | 26,500 + 150,500 + 3,000 = 180,000 = 5 × 36,000 ✓ |

---

## 4. Total Cost Summary

| Metric | Monthly | Annual |
|--------|--------:|-------:|
| Model Cost (with cache) | $91,762.50 | $1,101,150.00 |
| Per session | $0.1835 | — |
| Per question | $0.0367 | — |

---

## 5. Capacity Check

**Quota source:** Cross-region inference quotas for Claude Sonnet 4.6 in us-east-1

| Parameter | Value |
|-----------|------:|
| RPM Limit | 10,000 |
| TPM Limit | 6,000,000 |
| Output burndown rate | 5× (Claude 4.x) |
| Peak-to-avg ratio | 3.0× |
| Active hours/day | 12 |
| Active days/month | 22 |

### RPM Analysis

| Metric | Value |
|--------|------:|
| Active minutes/month | 15,840 |
| Avg questions/min | 157.83 |
| Avg RPM | 631.31 (157.83 × 4 turns) |
| Peak RPM (3× ratio) | 1,893.94 |
| RPM Limit | 10,000 |
| RPM Utilization | **18.9%** ✅ |

### TPM Analysis

| Metric | Value |
|--------|------:|
| Base context | 8,100 |
| Avg input/turn | 9,000 |
| Avg output/turn | 100 |
| Avg TPM | 5,997,475 |
| Peak TPM | 17,992,424 |
| max_tokens overhead | 3,996/request |
| Effective Peak TPM | 25,560,606 |
| TPM Limit | 6,000,000 |
| TPM Utilization | **426.0%** ❌ |

### Verdict: ❌ Does NOT Fit

RPM fits comfortably (18.9%), but **TPM exceeds quota by 4.3×**. The 5× output burndown rate for Claude models and the max_tokens reservation are the primary drivers.

### Optimization Checklist

| Area | Current | Recommended Action |
|------|---------|-------------------|
| max_tokens | 4,096 (actual output ~100) | Reduce to ~300 → frees 3,796 TPM/request |
| RAG chunks | 10 × 300 = 3,000 tokens | Reduce to 5 chunks if quality allows |
| System prompt | 1,000 tokens | Shorten if possible |
| Prompt caching | Enabled | Cache reads don't count toward TPM — biggest saver |
| Output length | ~100 tokens (×5 burndown) | Constrain with max_tokens + prompt instructions |
| Tool count | 3 tools | Already lean — no change needed |

---

## 6. Step-by-Step Calculation Explanations

### Token Profile

```
cacheable_base = T_sys + T_tools = 1,000 + 4,000 = 5,000
rag_tokens = 10 × 300 = 3,000
base_prompt = cacheable_base + T_user + rag_tokens = 5,000 + 100 + 3,000 = 8,100
delta = T_call + T_result = 100 + 500 = 600
turns = N_invoke + 1 = 3 + 1 = 4
```

### Turn-by-Turn Input (Q1)

```
Turn 0: base_prompt = 8,100
Turn 1: 8,100 + 1 × 600 = 8,700
Turn 2: 8,100 + 2 × 600 = 9,300
Turn 3: 8,100 + 3 × 600 = 9,900
total_input_per_question = 8,100 + 8,700 + 9,300 + 9,900 = 36,000

Closed-form: 4 × 8,100 + 600 × 3 × 4 / 2 = 32,400 + 3,600 = 36,000 ✓
```

### Output Per Question

```
total_output_per_question = T_answer + N_invoke × T_call = 100 + 3 × 100 = 400
```

### Monthly Totals (Before Caching)

```
questions_per_month = 500,000 × 5 = 2,500,000
monthly_input = 36,000 × 2,500,000 = 90,000,000,000
monthly_output = 400 × 2,500,000 = 1,000,000,000
```

### No-Cache Baseline

```
no_cache_input = (90,000,000,000 / 1,000,000) × $3.00 = $270,000.00
no_cache_output = (1,000,000,000 / 1,000,000) × $15.00 = $15,000.00
no_cache_total = $285,000.00
```

### Cache Splits

**Q1 (N=3 ≥ 1):**
```
q1_cache_write = base_prompt + (N-1) × delta = 8,100 + 2 × 600 = 9,300
q1_cache_read = Σ(k=1 to 3)[base_prompt + (k-1) × delta]
             = 8,100 + 8,700 + 9,300 = 26,100
q1_regular = delta = 600
Sum: 9,300 + 26,100 + 600 = 36,000 ✓
```

**Q2+ (N=3 ≥ 1):**
```
q2_cache_write = (T_user + rag_tokens) + (N-1) × delta = 3,100 + 1,200 = 4,300
q2_cache_read = cacheable_base + Σ(k=1 to 3)[base_prompt + (k-1) × delta]
             = 5,000 + 26,100 = 31,100
q2_regular = delta = 600
Sum: 4,300 + 31,100 + 600 = 36,000 ✓
```

**Per Session:**
```
n_subsequent = 5 - 1 = 4
session_cw = 9,300 + 4 × 4,300 = 26,500
session_cr = 26,100 + 4 × 31,100 = 150,500
session_reg = 600 + 4 × 600 = 3,000
Identity: 26,500 + 150,500 + 3,000 = 180,000 = 5 × 36,000 ✓
```

**Monthly Tokens:**
```
monthly_cw = 500,000 × 26,500 = 13,250,000,000
monthly_cr = 500,000 × 150,500 = 75,250,000,000
monthly_reg = 500,000 × 3,000 = 1,500,000,000
monthly_out = 500,000 × 2,000 = 1,000,000,000
```

### Cache Costs

```
cache_write_cost = (13,250,000,000 / 1,000,000) × $3.75 = $49,687.50
cache_read_cost = (75,250,000,000 / 1,000,000) × $0.30 = $22,575.00
regular_input_cost = (1,500,000,000 / 1,000,000) × $3.00 = $4,500.00
output_cost = (1,000,000,000 / 1,000,000) × $15.00 = $15,000.00
total_model_cost = $49,687.50 + $22,575.00 + $4,500.00 + $15,000.00 = $91,762.50
```

### Savings

```
savings_monthly = $285,000.00 - $91,762.50 = $193,237.50
savings_pct = $193,237.50 / $285,000.00 × 100 = 67.8%
```

---

> **Source:** AWS Pricing API cache (Standard Global tier). Prompt caching enabled by default for Claude Sonnet 4.6.
