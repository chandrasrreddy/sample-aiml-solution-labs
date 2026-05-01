# UC-21: No Region Specified — Full Cost Estimate

> **Use Case:** "How much would it cost to run a Claude Sonnet agent with 1M sessions per month?"

---

## Assumptions Made (not in prompt)

The prompt does not specify region, model version, questions/session, tools, or token profile. The following defaults were applied per `execute_test_cases.md` guidance:

| Parameter | Assumed Value | Reason |
|-----------|:------------:|--------|
| Region | us-east-1 | Default when no region specified |
| Model | Claude Sonnet 4.6 | "Claude Sonnet" → latest Sonnet version |
| Questions/session | 5 | Standard default |
| Tools invoked | 10 | Standard default |
| Token profile | Standard | All default token parameters |

---

## 1. Assumptions

### Workload Profile

| Parameter | Value |
|-----------|:-----:|
| Region | us-east-1 |
| Model | Claude Sonnet 4.6 |
| Tier | Standard (Global) |
| Sessions/month | 1,000,000 |
| Questions/session | 5 |
| Questions/month | 5,000,000 |
| Tools invoked/question | 10 |
| Turns/question | 11 |

### Token Profile

| Parameter | Value |
|-----------|------:|
| System prompt | 1,000 |
| Tool descriptions | 4,000 |
| User input | 100 |
| RAG chunks | 10 × 300 = 3,000 |
| Tool call (output) | 100 |
| Tool result (input) | 500 |
| Final answer (output) | 100 |
| **Cacheable base** | **5,000** (system + tools) |
| **Base prompt** | **8,100** (cacheable + user + RAG) |
| **Delta per tool turn** | **600** (call + result) |
| **Output per question** | **1,100** (100 answer + 10 × 100 calls) |

### Model Pricing (per 1M tokens)

| Price Type | $/M tokens | Source |
|-----------|:----------:|--------|
| Input | $3.00 | Standard Global, from cache |
| Output | $15.00 | Standard Global, from cache |
| Cache Read | $0.30 | 10% of input price |
| Cache Write | $3.75 | 125% of input price |

---

## 2. Model Cost Breakdown

### With Caching

| Component | Monthly Tokens | $/M | Monthly Cost |
|-----------|---------------:|----:|-----------:|
| Cache Write | 47,500,000,000 | $3.75 | $178,125.00 |
| Cache Read | 560,000,000,000 | $0.30 | $168,000.00 |
| Regular Input | 3,000,000,000 | $3.00 | $9,000.00 |
| Output | 5,500,000,000 | $15.00 | $82,500.00 |
| **Total** | | | **$437,625.00** |

### Without Caching (Baseline)

| Component | Monthly Cost |
|-----------|------------:|
| Input (all at $3.00/M) | $1,831,500.00 |
| Output | $82,500.00 |
| **Total** | **$1,914,000.00** |

### Caching Savings

| Metric | Value |
|--------|------:|
| Monthly savings | $1,476,375.00 |
| Annual savings | $17,716,500.00 |
| Savings % | **77.1%** |

---

## 3. Combined Total Cost (Model Only)

| Metric | Value |
|--------|------:|
| Monthly | $437,625.00 |
| Annual | $5,251,500.00 |
| Per session | $0.4376 |
| Per question | $0.0875 |

> **Note:** AgentCore infrastructure costs are not included as the prompt describes a generic "agent" without specifying AgentCore deployment. Add AgentCore costs if deploying on Bedrock AgentCore.

---

## 4. Capacity Check

**Quota source:** `query_quotas()` — Claude 3.5 Sonnet V2 on-demand in us-east-1 (closest available to Claude Sonnet 4.6 in cache)

| Metric | Value |
|--------|------:|
| RPM limit | 50 |
| TPM limit | 400,000 |

### RPM Analysis

| Step | Calculation | Result |
|------|------------|-------:|
| Active minutes/month | 12h × 60 × 22d | 15,840 |
| Avg questions/min | 5,000,000 ÷ 15,840 | 315.66 |
| LLM calls/question | 10 tools + 1 | 11 |
| Avg RPM | 315.66 × 11 | 3,472 |
| Peak RPM (3× ratio) | 3,472 × 3.0 | **10,417** |
| RPM utilization | 10,417 / 50 | **20,833%** ❌ |

### TPM Analysis

| Step | Calculation | Result |
|------|------------|-------:|
| Base context | 100 + 1,000 + 4,000 + 3,000 | 8,100 |
| Avg input/turn | 8,100 + (600/2) × 10 | 11,100 |
| Avg output/turn | (10 × 100 + 100) / 11 | 100 |
| Avg TPM | 3,472 × (11,100 + 100×5) | 40,277,778 |
| Peak TPM | 40,277,778 × 3.0 | 120,833,333 |
| max_tokens overhead | 4,096 − 100 = 3,996/req | — |
| Effective peak TPM | 120,833,333 + (10,417 × 3,996) | **162,458,333** |
| TPM utilization | 162,458,333 / 400,000 | **40,615%** ❌ |

### Verdict: ❌ Does Not Fit

Both RPM and TPM massively exceed default on-demand quotas. At 1M sessions/month with 5 Q/session and 10 tools, this workload requires:

- **RPM:** ~10,400 peak vs 50 limit (208× over)
- **TPM:** ~162M effective peak vs 400K limit (406× over)

### Recommendations

1. **Request quota increase** — this volume requires a committed throughput agreement with AWS
2. **Cross-region inference** — distribute load across multiple regions
3. **Reduce max_tokens** from 4,096 to ~300 (actual output is ~100 tokens) to free TPM quota
4. **Enable prompt caching** — cache reads don't count toward TPM
5. **Output burndown rate is 5×** for Claude — each output token consumes 5 TPM quota; reducing output length has 5× impact

---

## 5. Step-by-Step Calculation Explanations

### Token Profile

```
cacheable_base = 1,000 (system) + 4,000 (tools) = 5,000
rag_tokens = 10 × 300 = 3,000
base_prompt = 5,000 + 100 (user) + 3,000 (RAG) = 8,100
delta = 100 (tool call) + 500 (tool result) = 600
turns = 10 tools + 1 = 11
output_per_question = 100 (answer) + 10 × 100 (tool calls) = 1,100
```

### Turn-by-Turn (Q1)

```
Turn 0:  8,100 input → WRITE 8,100
Turn 1:  8,700 input → READ 8,100 + WRITE 600
Turn 2:  9,300 input → READ 8,700 + WRITE 600
...
Turn 9:  13,500 input → READ 12,900 + WRITE 600
Turn 10: 14,100 input → READ 13,500 + REG 600 (last turn)

Total Q1 input: 122,100 tokens across 11 turns
```

### Cache Splits

```
Q1: cache_write = 13,500, cache_read = 108,000, regular = 600
    Sum = 13,500 + 108,000 + 600 = 122,100 ✓

Q2: cache_write = 8,500, cache_read = 113,000, regular = 600
    Sum = 8,500 + 113,000 + 600 = 122,100 ✓

Session (5 Qs): cw = 13,500 + 4 × 8,500 = 47,500
                cr = 108,000 + 4 × 113,000 = 560,000
                reg = 600 + 4 × 600 = 3,000
                Sum = 47,500 + 560,000 + 3,000 = 610,500 = 5 × 122,100 ✓
```

### Monthly Cost Math

```
Cache write:   1,000,000 × 47,500 / 1M × $3.75 = $178,125.00
Cache read:    1,000,000 × 560,000 / 1M × $0.30 = $168,000.00
Regular input: 1,000,000 × 3,000 / 1M × $3.00 = $9,000.00
Output:        1,000,000 × 5,500 / 1M × $15.00 = $82,500.00
Total:         $437,625.00

No-cache input: 5,000,000 × 122,100 / 1M × $3.00 = $1,831,500.00
No-cache output: 5,000,000 × 1,100 / 1M × $15.00 = $82,500.00
No-cache total: $1,914,000.00

Savings: $1,914,000 - $437,625 = $1,476,375 (77.1%)
```
