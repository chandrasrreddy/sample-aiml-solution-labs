# UC-23: Minimal Information — Full Cost Estimate

> **Use Case:** "What's the cost of running an AI agent on Bedrock?"

---

## Assumptions Made (not in prompt)

The original prompt provides no specifics — no model, region, volume, tools, or workload shape. The following defaults were applied per the vague use case handling rules:

| Assumption | Value | Rationale |
|-----------|-------|-----------|
| **Model** | Claude Sonnet 4.6 | Default for unspecified model |
| **Region** | us-east-1 | Default for unspecified region |
| **Sessions/month** | 500,000 | Default for minimal information |
| **Questions/session** | 3 | Default for minimal information |
| **Tools invoked/question** | 3 | Default for minimal information |
| **Service tier** | Standard Global | Default tier |
| **Token profile** | Standard defaults | See token profile table below |

---

## 1. Assumptions

### Workload Profile

| Parameter | Value |
|-----------|-------|
| Region | us-east-1 |
| Model | Claude Sonnet 4.6 |
| Service Tier | Standard Global |
| Sessions/month | 500,000 |
| Questions/session | 3 |
| Questions/month | 1,500,000 |
| Tools invoked/question | 3 |
| Turns/question | 4 (3 tool + 1 final) |

### Token Profile

| Parameter | Value |
|-----------|-------|
| System prompt tokens | 1,000 |
| Tool description tokens | 4,000 |
| User input tokens | 100 |
| RAG chunks | 10 |
| Tokens per RAG chunk | 300 |
| RAG tokens total | 3,000 |
| Tool call tokens (output) | 100 |
| Tool result tokens (input) | 500 |
| Output tokens (final answer) | 100 |
| Cacheable base (sys + tools) | 5,000 |
| Base prompt (cacheable + user + RAG) | 8,100 |
| Delta per tool turn (call + result) | 600 |
| Total input per question | 36,000 |
| Total output per question | 400 |

### Model Pricing (Standard Global, us-east-1)

| Component | Price per 1M tokens |
|-----------|:-------------------:|
| Input | $3.00 |
| Output | $15.00 |
| Cache Read | $0.30 |
| Cache Write | $3.75 |

---

## 2. Model Cost Breakdown

### Turn-by-Turn Input (per question)

| Turn | Context | Input Tokens |
|:----:|---------|:------------:|
| 0 | base_prompt | 8,100 |
| 1 | base_prompt + 1×delta | 8,700 |
| 2 | base_prompt + 2×delta | 9,300 |
| 3 | base_prompt + 3×delta | 9,900 |
| **Total** | | **36,000** |

### Output per question

| Component | Tokens |
|-----------|:------:|
| 3 tool calls × 100 | 300 |
| Final answer | 100 |
| **Total** | **400** |

### Cache Splits

**Q1 (first question in session):**

| Category | Tokens |
|----------|:------:|
| Cache write | 9,300 |
| Cache read | 26,100 |
| Regular | 600 |
| **Sum** | **36,000** ✓ |

**Q2+ (subsequent questions):**

| Category | Tokens |
|----------|:------:|
| Cache write | 4,300 |
| Cache read | 31,100 |
| Regular | 600 |
| **Sum** | **36,000** ✓ |

**Per session (3 questions):**

| Category | Tokens |
|----------|:------:|
| Cache write | 17,900 |
| Cache read | 88,300 |
| Regular input | 1,800 |
| Output | 1,200 |

**Session identity check:** 17,900 + 88,300 + 1,800 = 108,000 = 3 × 36,000 ✓

### Monthly Token Volumes

| Category | Monthly Tokens |
|----------|:--------------:|
| Cache write | 8,950,000,000 |
| Cache read | 44,150,000,000 |
| Regular input | 900,000,000 |
| Output | 600,000,000 |

### With Caching (Monthly)

| Component | Cost |
|-----------|-----:|
| Cache write | $33,562.50 |
| Cache read | $13,245.00 |
| Regular input | $2,700.00 |
| Output | $9,000.00 |
| **Total Model Cost** | **$58,507.50** |

### Without Caching Baseline (Monthly)

| Component | Cost |
|-----------|-----:|
| Input (no cache) | $162,000.00 |
| Output | $9,000.00 |
| **Total (no cache)** | **$171,000.00** |

### Caching Savings

| Metric | Value |
|--------|------:|
| Monthly savings | $112,492.50 |
| Savings % | 65.8% |

---

## 3. Combined Total Cost

| Metric | Monthly | Annual |
|--------|--------:|-------:|
| Model cost (with caching) | $58,507.50 | $702,090.00 |
| Per session | $0.1170 | — |
| Per question | $0.0390 | — |

> **Note:** AgentCore infrastructure costs are not included because the prompt did not describe an agentic architecture. If this agent runs on AgentCore (Runtime, Gateway, Memory), add those costs separately.

---

## 4. Capacity Check

**Quota source:** `bedrock_quotas.json` — Global inference for Claude Sonnet 4.6 in us-east-1

| Quota | Limit |
|-------|------:|
| RPM | 10,000 |
| TPM | 6,000,000 |

**Parameters:** peak-to-avg ratio = 3.0×, active hours = 12/day, active days = 22/month, output burndown rate = 5× (Claude 4.x), max_tokens = 4,096

### RPM Analysis

| Metric | Value |
|--------|------:|
| Active minutes/month | 15,840 |
| Avg questions/min | 94.70 |
| Avg RPM | 378.79 |
| Peak RPM (3×) | 1,136.36 |
| RPM limit | 10,000 |
| **RPM utilization** | **11.4%** ✅ |

### TPM Analysis

| Metric | Value |
|--------|------:|
| Base context | 8,100 |
| Avg input/turn | 9,000 |
| Avg output/turn | 100 |
| Avg TPM | 3,598,485 |
| Peak TPM (3×) | 10,795,455 |
| max_tokens overhead/req | 3,996 |
| Effective peak TPM | 15,336,364 |
| TPM limit | 6,000,000 |
| **TPM utilization** | **255.6%** ❌ |

### Verdict: ❌ Does Not Fit

RPM fits comfortably (11.4%), but **TPM exceeds quota by 2.6×**. The main driver is the `max_tokens` overhead — 4,096 is reserved per request but actual output is only ~100 tokens.

### Optimization Checklist

| Area | Current | Recommended Action | Impact |
|------|---------|-------------------|--------|
| `max_tokens` | 4,096 (actual output ~100) | Reduce to ~300 | Frees ~3,796 TPM/request — **biggest lever** |
| RAG chunks | 10 × 300 = 3,000 tokens | Reduce to 5 chunks if quality allows | Saves ~1,500 tokens/turn, compounds across turns |
| System prompt | 1,000 tokens | Shorten instructions | Sent every turn — compounding effect |
| Prompt caching | Enabled | Verify — cache reads don't count toward TPM | Biggest TPM saver |
| Output length | ~100 tokens (×5 burndown) | Constrain with prompt instructions | Each output token = 5 TPM |
| Tool count | 3 tools | Already low — no action needed | — |

**Key insight:** Reducing `max_tokens` from 4,096 to 300 would drop effective peak TPM from 15.3M to ~12.0M. Combined with reducing RAG chunks to 5, the workload would likely fit within the 6M TPM quota.

---

## 5. Summary

| Item | Value |
|------|------:|
| **Monthly model cost** | **$58,507.50** |
| **Annual model cost** | **$702,090.00** |
| Cost per session | $0.117 |
| Cost per question | $0.039 |
| Caching savings | 65.8% ($112,492.50/mo) |
| RPM utilization | 11.4% ✅ |
| TPM utilization | 255.6% ❌ |
| Capacity verdict | Does not fit — optimize `max_tokens` first |

> **Source:** AWS Pricing API cache (Standard Global tier), `bedrock_quotas.json` (Global inference quotas)
