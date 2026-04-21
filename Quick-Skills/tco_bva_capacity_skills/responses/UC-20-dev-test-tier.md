# UC-20: Dev/Test Tier Recommendation — Qwen3 235B in us-east-1

> **Use Case:** "I'm prototyping an agent and want the cheapest option. What tier should I use for Qwen3 235B in us-east-1?"

---

## 1. Model Discovery

**Model found in cache:** Qwen3 235B A22B 2507 (text-only variant)

Also available: Qwen3 VL 235B A22B (vision-language variant — not requested)

**Provider:** Alibaba (Qwen)

**Region:** us-east-1

**Important note:** Qwen3 235B is a Regional-only model — no Global (cross-region) variant is available. All tiers use the Regional variant.

---

## 2. Available Tiers & Pricing

All prices are per 1M tokens, converted from per-1K pricing in the cache.

| Tier | Variant | Input ($/M) | Output ($/M) | Cache Read | Cache Write | Notes |
|------|---------|:-----------:|:------------:|:----------:|:-----------:|-------|
| **Flex** | Regional | $0.11 | $0.44 | None | None | ⭐ Cheapest (tied with Batch) |
| **Batch** | Regional | $0.11 | $0.44 | None | None | Cheapest (tied with Flex), but async |
| **Standard** | Regional | $0.22 | $0.88 | None | None | 2× Flex price |
| **Priority** | Regional | $0.385 | $1.54 | None | None | 3.5× Flex price |

**Key observations:**
- No prompt caching support on any tier (cache_read and cache_write are both null)
- Flex and Batch have identical pricing ($0.11/$0.44 per M tokens)
- Standard is exactly 2× the Flex/Batch price
- Priority is ~3.5× the Flex/Batch price

---

## 3. Tier Advisor Recommendation

### 🎯 Recommended: **Flex Regional**

**Why Flex is the right choice for prototyping:**

1. **Cheapest on-demand tier** — $0.11/$0.44 per M tokens (input/output), tied with Batch but available in real-time
2. **Perfect for dev/test** — Flex is explicitly designed for development, testing, evaluations, and experimentation
3. **Real-time responses** — Unlike Batch (which is async with a 24-hour processing window), Flex gives you immediate responses for interactive prototyping
4. **No commitment** — Pay only for what you use, no reserved capacity needed

**Trade-offs to be aware of:**
- **No SLA** — Flex is best-effort; requests may be throttled during peak demand
- **Higher latency risk** — Flex requests are deprioritized behind Standard and Priority traffic
- **No prompt caching** — Qwen3 235B doesn't support prompt caching on any tier, so this isn't a differentiator
- **Not for production** — When you move to production, upgrade to Standard ($0.22/$0.88)

### Decision Framework Applied

| User Signal | Interpretation | Recommendation |
|-------------|---------------|----------------|
| "prototyping" | Dev/test workload | → Flex |
| "cheapest option" | Cost-minimizing | → Flex or Batch |
| Interactive prototyping implied | Needs real-time responses | → Flex (not Batch) |

---

## 4. Alternatives & When to Switch

| Tier | When to Use | Price vs Flex |
|------|------------|:-------------:|
| **Batch** ($0.11/$0.44) | If you can tolerate async processing (24h window) — e.g., bulk test data generation | Same price, but async |
| **Standard** ($0.22/$0.88) | When moving to production or need reliable throughput | 2× more expensive |
| **Priority** ($0.385/$1.54) | Mission-critical, customer-facing with strict latency requirements | 3.5× more expensive |

### Upgrade Path
```
Prototyping → Flex ($0.11/$0.44)
    ↓ (ready for production)
Production → Standard ($0.22/$0.88)
    ↓ (throttling impacts users)
Mission-critical → Priority ($0.385/$1.54)
```

---

## 5. Cost Comparison Example

For a light prototyping workload: 1,000 sessions/month, 3 questions/session, 3 tools per question.

Using default token profile (system: 1,000, tools: 4,000, user: 100, RAG: 10×300, tool_call: 100, tool_result: 500, output: 100):

| Metric | Flex | Standard | Priority |
|--------|:----:|:--------:|:--------:|
| Input $/M | $0.11 | $0.22 | $0.385 |
| Output $/M | $0.44 | $0.88 | $1.54 |
| **Relative cost** | **1×** | **2×** | **3.5×** |

At prototyping scale, all tiers are very affordable — but Flex keeps costs minimal while you iterate.

---

## 6. Summary

| Item | Value |
|------|-------|
| **Model** | Qwen3 235B A22B 2507 |
| **Region** | us-east-1 |
| **Recommended Tier** | Flex Regional |
| **Input Price** | $0.11/M tokens |
| **Output Price** | $0.44/M tokens |
| **Prompt Caching** | Not available |
| **Variant** | Regional only (no Global) |
| **Rationale** | Cheapest real-time tier, ideal for dev/test prototyping |

> **Source:** AWS Pricing API cache, tier guidance from [Service tiers for optimizing performance and cost](https://docs.aws.amazon.com/bedrock/latest/userguide/service-tiers-inference.html)
