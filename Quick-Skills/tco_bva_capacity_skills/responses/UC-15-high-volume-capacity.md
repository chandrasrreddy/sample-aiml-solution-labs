# UC-15: High-Volume Capacity Check — Full Cost Estimate

> **Use Case:** "I have 20M questions per month on Claude Sonnet 4.6 in us-east-1. 5 tools per question, peak-to-average ratio of 4x, 16 active hours per day, 30 days per month. Does this fit in Standard tier? What about Priority? Use output burndown rate of 5."

---

## 1. Assumptions

### Workload Profile

| Parameter | Value |
|-----------|-------|
| Region | us-east-1 |
| Model | Claude Sonnet 4.6 |
| Tier | Standard Global (cross-region) |
| Questions/month | 20,000,000 |
| Sessions/month | 4,000,000 (5 Q/session default) |
| Questions/session | 5 |
| Tools invoked/question | 5 |
| Turns/question | 6 (5 tools + 1) |

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
| **Output per question** | **600** (100 + 5 × 100) |

### Model Pricing (Standard Global, per 1M tokens)

| Component | Price |
|-----------|-------|
| Input | $3.00 |
| Output | $15.00 |
| Cache read | $0.30 |
| Cache write | $3.75 |

### Traffic Profile (Non-Default)

| Parameter | Value | Default |
|-----------|-------|---------|
| Peak-to-average ratio | **4.0×** | 3.0× |
| Active hours/day | **16** | 12 |
| Active days/month | **30** | 22 |
| Output burndown rate | **5** | 1 |
| max_tokens setting | 4,096 | 4,096 |

---

## 2. Model Cost Breakdown

### With Caching

| Component | Monthly Tokens | Monthly Cost |
|-----------|---------------|-------------|
| Cache write | 130,000,000,000 | $487,500.00 |
| Cache read | 1,010,000,000,000 | $303,000.00 |
| Regular input | 12,000,000,000 | $36,000.00 |
| Output | 12,000,000,000 | $180,000.00 |
| **Total (with cache)** | — | **$1,006,500.00** |

### Without Caching (Baseline)

| Component | Monthly Cost |
|-----------|-------------|
| Input | $3,456,000.00 |
| Output | $180,000.00 |
| **Total (no cache)** | **$3,636,000.00** |

### Savings

| Metric | Value |
|--------|-------|
| Monthly savings | $2,629,500.00 |
| Annual savings | $31,554,000.00 |
| Savings % | **72.3%** |

### Per-Unit Costs

| Metric | Value |
|--------|-------|
| Per question | $0.0503 |
| Per session | $0.2516 |
| Monthly | $1,006,500.00 |
| Annual | $12,078,000.00 |

---

## 3. Capacity Check — Standard Tier

### Quotas (from query_quotas, Global inference)

| Quota | Limit |
|-------|-------|
| RPM | 10,000 |
| TPM | 6,000,000 |

### RPM Calculation

| Step | Calculation | Result |
|------|-------------|--------|
| Active minutes/month | 16h × 60 × 30d | **28,800 min** |
| Avg questions/min | 20,000,000 ÷ 28,800 | **694.44 Q/min** |
| LLM calls/question | 5 tools + 1 | **6 calls** |
| Avg RPM | 694.44 × 6 | **4,166.67 RPM** |
| Peak RPM | 4,166.67 × 4.0× | **16,667 RPM** |
| RPM limit | — | 10,000 |
| **RPM fits?** | 16,667 > 10,000 | **❌ No** |
| RPM utilization | 16,667 / 10,000 | **166.7%** |

### TPM Calculation

| Step | Calculation | Result |
|------|-------------|--------|
| Base context | 100 + 1,000 + 4,000 + 3,000 | **8,100 tokens** |
| Delta | 100 + 500 | **600 tokens** |
| Avg input/turn | 8,100 + (600/2) × 5 | **9,600 tokens** |
| Avg output/turn | (5 × 100 + 100) / 6 | **100 tokens** |
| Avg TPM | 4,166.67 × (9,600 + 100 × 5) | **42,083,333 TPM** |
| Peak TPM | 42,083,333 × 4.0× | **168,333,333 TPM** |
| max_tokens overhead | 4,096 − 100 | **3,996/req** |
| Effective peak TPM | 168,333,333 + (16,667 × 3,996) | **234,933,333 TPM** |
| TPM limit | — | 6,000,000 |
| **TPM fits?** | 234,933,333 > 6,000,000 | **❌ No** |
| TPM utilization | 234,933,333 / 6,000,000 | **3,915.6%** |

### Standard Tier Verdict

| Check | Result |
|-------|--------|
| RPM | ❌ 16,667 peak vs 10,000 limit (167% utilization) |
| TPM | ❌ 234,933,333 effective peak vs 6,000,000 limit (3,916% utilization) |
| **Overall** | **❌ Does NOT fit in Standard tier** |

---

## 4. Capacity Check — Priority Tier

Priority tier for Claude Sonnet 4.6 in us-east-1 uses the **same RPM/TPM quota limits** as Standard (10,000 RPM / 6,000,000 TPM per the quota cache). Priority provides higher throughput guarantees and lower latency, but the default quota limits are identical.

| Check | Result |
|-------|--------|
| RPM | ❌ 16,667 peak vs 10,000 limit (167% utilization) |
| TPM | ❌ 234,933,333 effective peak vs 6,000,000 limit (3,916% utilization) |
| **Overall** | **❌ Does NOT fit in Priority tier at default quotas** |

> **Note:** Priority tier quotas can be increased via AWS support request. The workload requires ~39× the default TPM quota — this would need a significant quota increase or architectural changes.

---

## 5. Optimization Checklist

| Area | Current | Recommended Action | Impact |
|------|---------|-------------------|--------|
| RAG chunks | 10 × 300 = 3,000 tokens | Reduce to 5 chunks | Saves ~1,500 tokens/turn, compounds across 6 turns |
| System prompt | 1,000 tokens | Shorten instructions | Sent every turn — compounding effect |
| Prompt caching | Enabled | Cache reads DON'T count toward TPM | Biggest TPM saver |
| max_tokens | 4,096 (actual output ~100) | Reduce to ~300 | Frees 3,996 TPM/request × 16,667 peak RPM = 66.6M TPM |
| Tool count | 5 tools × 800 = 4,000 tokens | Use AC Gateway dynamic selection | Reduce per-request tool descriptions |
| Output length | ~100 tokens (×5 burndown) | Constrain with max_tokens + prompt | Each output token = 5× TPM impact |
| Architecture | Single agent, 5 tools | Split into parent + sub-agents | Fewer tools per agent, lower compounding |

### Key Insight: max_tokens Waste

The biggest quick win is reducing `max_tokens` from 4,096 to ~300. With actual output of ~100 tokens, the current setting wastes **3,996 TPM per request**. At peak RPM of 16,667, that's **66.6M TPM of pure overhead** — more than the actual token consumption.

### Traffic Profile Considerations

| Question | Current | Impact |
|----------|---------|--------|
| Peak-to-average ratio | 4.0× | Higher than default 3.0× — validate with actual P99 data |
| Active hours | 16h/day | Near 24/7 — less room for off-peak absorption |
| Active days | 30/month | Full month — no weekend relief |

### Ramp Plan Needed

At 20M questions/month, this workload requires:
- **~17K RPM** (1.7× default quota)
- **~235M effective TPM** (39× default quota)

This requires a formal capacity request to AWS. Recommended approach:
1. Start with a smaller volume and demonstrate usage
2. Request quota increases in steps (e.g., 3× → 10× → 40×)
3. Consider multi-region distribution to spread load

---

## 6. Step-by-Step Calculation Explanations

### Token Profile

```
cacheable_base = 1,000 (system) + 4,000 (tools) = 5,000
rag_tokens = 10 × 300 = 3,000
base_prompt = 5,000 + 100 (user) + 3,000 (RAG) = 8,100
delta = 100 (tool call) + 500 (tool result) = 600
turns = 5 + 1 = 6
output_per_question = 100 (answer) + 5 × 100 (tool calls) = 600
```

### Turn-by-Turn (Q1)

```
Turn 0: 8,100 input → WRITE 8,100 (entire prompt — first turn)
Turn 1: 8,700 input → READ 8,100 + WRITE 600 (new tool delta)
Turn 2: 9,300 input → READ 8,700 + WRITE 600
Turn 3: 9,900 input → READ 9,300 + WRITE 600
Turn 4: 10,500 input → READ 9,900 + WRITE 600
Turn 5: 11,100 input → READ 10,500 + REG 600 (last turn)
Total Q1 input: 57,600 tokens across 6 turns
```

### RPM Calculation

```
active_minutes_per_month = 16 × 60 × 30 = 28,800
avg_questions_per_min = 20,000,000 / 28,800 = 694.44
avg_rpm = 694.44 × 6 = 4,166.67
peak_rpm = 4,166.67 × 4.0 = 16,666.67
```

### TPM Calculation

```
base_context = 100 + 1,000 + 4,000 + 3,000 = 8,100
avg_input_per_turn = 8,100 + (600/2) × 5 = 9,600
avg_output_per_turn = (5 × 100 + 100) / 6 = 100
avg_tpm = 4,166.67 × (9,600 + 100 × 5) = 42,083,333
peak_tpm = 42,083,333 × 4.0 = 168,333,333
max_tokens_overhead = 4,096 - 100 = 3,996
effective_peak_tpm = 168,333,333 + (16,667 × 3,996) = 234,933,333
```
