# UC-13: Caching Impact Analysis — Full Cost Estimate

> **Use Case:** "Show me the cost difference with and without prompt caching for Claude Sonnet 4.6 in us-east-1. 1M sessions, 5 questions per session, 10 tools invoked, system prompt 2,000 tokens, tool descriptions 4,000 tokens, 10 RAG chunks of 300 tokens each."

---

## 1. Assumptions

### Workload Profile

| Parameter | Value |
|-----------|-------|
| Region | us-east-1 |
| Model | Claude Sonnet 4.6 |
| Sessions/month | 1,000,000 |
| Questions/session | 5 |
| Questions/month | 5,000,000 |
| Tools invoked/question | 10 |
| Turns/question | 11 (10 tool calls + 1 final answer) |

### Token Profile

| Parameter | Tokens | Notes |
|-----------|-------:|-------|
| System prompt | 2,000 | Sent every turn |
| Tool descriptions | 4,000 | Sent every turn |
| User input | 100 | Per question |
| RAG chunks | 10 × 300 = 3,000 | Per question |
| Tool call (output) | 100 | Per tool invocation |
| Tool result (input) | 500 | Per tool invocation |
| Final answer (output) | 100 | Per question |
| **Cacheable prefix** | **6,000** | system + tools |
| **Base prompt (turn 0)** | **9,100** | cacheable_base + user + RAG |
| **Delta per tool turn** | **600** | tool_call + tool_result |
| **Total input/question** | **133,100** | Across 11 turns (compounding) |
| **Total output/question** | **1,100** | 100 answer + 10 × 100 tool calls |

### Model Pricing (Standard Global, per 1M tokens)

| Price Type | $/1M Tokens | Relative to Input |
|------------|------------:|:-----------------:|
| Input | $3.00 | 100% |
| Output | $15.00 | 500% |
| Cache Read | $0.30 | 10% |
| Cache Write | $3.75 | 125% |

---

## 2. How Prompt Caching Works — Detailed Mechanics

### What Gets Cached vs. What Doesn't

Prompt caching exploits the fact that in a multi-turn agent conversation, each LLM call re-sends the entire conversation history. The **unchanged prefix** from the prior turn can be read from cache instead of being processed as new input.

**Cacheable content (persists across turns within a question):**
- System prompt (2,000 tokens) — identical every turn
- Tool descriptions (4,000 tokens) — identical every turn
- All prior turns' content — grows with each tool call

**Cacheable content (persists across questions within a session):**
- System prompt + tool descriptions (6,000 tokens) — the "cacheable base" carries over from Q1 to Q2, Q3, Q4, Q5

**Never cached (always new):**
- The last turn's tool delta (600 tokens) — it won't be re-read since it's the final turn
- User input + RAG chunks change each question (3,100 tokens)

### Turn-by-Turn Breakdown: Q1 (First Question in Session)

| Turn | Total Input | Cache Read | Cache Write | Regular | Action |
|:----:|----------:|----------:|----------:|------:|--------|
| 0 | 9,100 | 0 | 9,100 | 0 | First turn — write entire prompt to cache |
| 1 | 9,700 | 9,100 | 600 | 0 | Read cached prefix, write new tool delta |
| 2 | 10,300 | 9,700 | 600 | 0 | Read cached prefix, write new tool delta |
| 3 | 10,900 | 10,300 | 600 | 0 | Read cached prefix, write new tool delta |
| 4 | 11,500 | 10,900 | 600 | 0 | Read cached prefix, write new tool delta |
| 5 | 12,100 | 11,500 | 600 | 0 | Read cached prefix, write new tool delta |
| 6 | 12,700 | 12,100 | 600 | 0 | Read cached prefix, write new tool delta |
| 7 | 13,300 | 12,700 | 600 | 0 | Read cached prefix, write new tool delta |
| 8 | 13,900 | 13,300 | 600 | 0 | Read cached prefix, write new tool delta |
| 9 | 14,500 | 13,900 | 600 | 0 | Read cached prefix, write new tool delta |
| 10 | 15,100 | 14,500 | 0 | 600 | Last turn — read prefix, delta is regular (won't be re-read) |
| **Total** | **133,100** | **118,000** | **14,500** | **600** | |

**Verification:** 118,000 + 14,500 + 600 = 133,100 ✓

### Cross-Question Caching: Q2–Q5 (Subsequent Questions)

When Q2 starts, the system prompt + tool descriptions (6,000 tokens) are still cached from Q1. Only the new user question + RAG (3,100 tokens) needs to be written.

| Turn | Total Input | Cache Read | Cache Write | Regular | Action |
|:----:|----------:|----------:|----------:|------:|--------|
| 0 | 9,100 | 6,000 | 3,100 | 0 | System+tools cached from Q1; write new user+RAG |
| 1 | 9,700 | 9,100 | 600 | 0 | Read cached prefix, write new tool delta |
| 2–9 | ... | ... | 600 | 0 | Same pattern as Q1 turns 2–9 |
| 10 | 15,100 | 14,500 | 0 | 600 | Last turn — regular input |
| **Total** | **133,100** | **124,000** | **8,500** | **600** | |

**Verification:** 124,000 + 8,500 + 600 = 133,100 ✓

**Key insight:** Q2+ saves 6,000 tokens of cache_write vs Q1 because the cacheable base doesn't need to be re-written. At $3.75/M, that's $0.0225 saved per subsequent question.

### Per-Session Totals (1 × Q1 + 4 × Q2)

| Category | Q1 | Q2 (×4) | Session Total |
|----------|---:|--------:|--------------:|
| Cache Write | 14,500 | 4 × 8,500 = 34,000 | 48,500 |
| Cache Read | 118,000 | 4 × 124,000 = 496,000 | 614,000 |
| Regular Input | 600 | 4 × 600 = 2,400 | 3,000 |
| **Total Input** | **133,100** | **4 × 133,100 = 532,400** | **665,500** |

**Verification:** 48,500 + 614,000 + 3,000 = 665,500 = 5 × 133,100 ✓

---

## 3. Model Cost Breakdown

### With Caching

| Cost Component | Monthly Tokens | Rate ($/M) | Monthly Cost |
|----------------|---------------:|-----------:|-------------:|
| Cache Write | 48,500,000,000 | $3.75 | $181,875.00 |
| Cache Read | 614,000,000,000 | $0.30 | $184,200.00 |
| Regular Input | 3,000,000,000 | $3.00 | $9,000.00 |
| Output | 5,500,000,000 | $15.00 | $82,500.00 |
| **Total** | | | **$457,575.00** |

### Without Caching (Baseline)

| Cost Component | Monthly Tokens | Rate ($/M) | Monthly Cost |
|----------------|---------------:|-----------:|-------------:|
| Input (all at full price) | 665,500,000,000 | $3.00 | $1,996,500.00 |
| Output | 5,500,000,000 | $15.00 | $82,500.00 |
| **Total** | | | **$2,079,000.00** |

### Savings Summary

| Metric | Value |
|--------|------:|
| Monthly savings | **$1,621,425.00** |
| Annual savings | **$19,457,100.00** |
| Savings percentage | **78.0%** |
| With caching (monthly) | $457,575.00 |
| Without caching (monthly) | $2,079,000.00 |

---

## 4. Why Caching Saves 78% — The Math Behind It

### Token Distribution Analysis

Of the 665,500 input tokens per session:
- **92.3%** (614,000) are cache reads at $0.30/M (10% of input price)
- **7.3%** (48,500) are cache writes at $3.75/M (125% of input price)
- **0.5%** (3,000) are regular input at $3.00/M (full price)

The massive savings come from the fact that **92.3% of all input tokens are served from cache at 10% of the regular price**. Even though cache writes cost 25% more than regular input, they represent only 7.3% of tokens.

### Effective Input Price

```
Effective input price = ($181,875 + $184,200 + $9,000) / (665,500M tokens)
                      = $375,075 / 665,500M
                      = $0.5636/M tokens (vs $3.00/M without caching)
```

Caching reduces the effective input price by **81.2%** — from $3.00/M to $0.56/M.

### Why Multi-Turn Agents Benefit Most

With 10 tool invocations, each question requires 11 LLM calls. Each call re-sends the entire conversation, creating massive token compounding:
- Turn 0: 9,100 tokens
- Turn 10: 15,100 tokens (66% larger)
- Total: 133,100 tokens across 11 turns

Without caching, all 133,100 tokens per question are billed at $3.00/M. With caching, most of those re-sent tokens are cache reads at $0.30/M.

**The more tools invoked → the more turns → the more compounding → the bigger the caching benefit.**

---

## 5. Cost Per Unit

| Metric | With Caching | Without Caching |
|--------|-------------:|----------------:|
| Monthly | $457,575.00 | $2,079,000.00 |
| Annual | $5,490,900.00 | $24,948,000.00 |
| Per session | $0.4576 | $2.0790 |
| Per question | $0.0915 | $0.4158 |

---

## 6. Step-by-Step Calculation Explanations

### Token Profile Derivation

```
rag_tokens       = 10 chunks × 300 tokens/chunk = 3,000
cacheable_base   = 2,000 (system) + 4,000 (tools) = 6,000
base_prompt      = 6,000 + 100 (user) + 3,000 (RAG) = 9,100
delta            = 100 (tool call) + 500 (tool result) = 600
turns            = 10 (tools) + 1 = 11
```

### Input Tokens Per Question (Compounding)

```
Turn 0:  9,100
Turn 1:  9,100 + 1×600 = 9,700
Turn 2:  9,100 + 2×600 = 10,300
Turn 3:  9,100 + 3×600 = 10,900
Turn 4:  9,100 + 4×600 = 11,500
Turn 5:  9,100 + 5×600 = 12,100
Turn 6:  9,100 + 6×600 = 12,700
Turn 7:  9,100 + 7×600 = 13,300
Turn 8:  9,100 + 8×600 = 13,900
Turn 9:  9,100 + 9×600 = 14,500
Turn 10: 9,100 + 10×600 = 15,100
─────────────────────────────────
Total:   133,100 tokens

Closed-form: 11 × 9,100 + 600 × 10 × 11/2 = 100,100 + 33,000 = 133,100 ✓
```

### Output Tokens Per Question

```
output_per_question = 100 (final answer) + 10 × 100 (tool calls) = 1,100
```

### Monthly Token Volumes

```
questions/month     = 1,000,000 × 5 = 5,000,000
monthly_input       = 133,100 × 5,000,000 = 665,500,000,000 tokens
monthly_output      = 1,100 × 5,000,000 = 5,500,000,000 tokens
```

### No-Cache Baseline

```
input_cost  = 665,500,000,000 / 1,000,000 × $3.00 = $1,996,500.00
output_cost = 5,500,000,000 / 1,000,000 × $15.00 = $82,500.00
total       = $1,996,500.00 + $82,500.00 = $2,079,000.00
```

### Cache Split Math

```
Q1: cache_write = 9,100 + (10-1)×600 = 14,500
    cache_read  = Σ(k=1..10)[9,100 + (k-1)×600] = 118,000
    regular     = 600
    Sum: 14,500 + 118,000 + 600 = 133,100 ✓

Q2: cache_write = (100 + 3,000) + (10-1)×600 = 8,500
    cache_read  = 6,000 + Σ(k=1..10)[9,100 + (k-1)×600] = 124,000
    regular     = 600
    Sum: 8,500 + 124,000 + 600 = 133,100 ✓

Session: cw  = 14,500 + 4×8,500 = 48,500
         cr  = 118,000 + 4×124,000 = 614,000
         reg = 600 + 4×600 = 3,000
         Sum: 48,500 + 614,000 + 3,000 = 665,500 = 5 × 133,100 ✓
```

### Cached Cost Calculation

```
cache_write_cost   = 48,500,000,000 / 1M × $3.75  = $181,875.00
cache_read_cost    = 614,000,000,000 / 1M × $0.30  = $184,200.00
regular_input_cost = 3,000,000,000 / 1M × $3.00    = $9,000.00
output_cost        = 5,500,000,000 / 1M × $15.00   = $82,500.00
total_with_cache   = $181,875 + $184,200 + $9,000 + $82,500 = $457,575.00
```

### Savings Calculation

```
savings_monthly = $2,079,000.00 - $457,575.00 = $1,621,425.00
savings_pct     = $1,621,425.00 / $2,079,000.00 × 100 = 78.0%
```
