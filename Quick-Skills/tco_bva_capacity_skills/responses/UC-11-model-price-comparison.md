# UC-11: Simple Model Price Comparison

> **Use Case:** "Compare the pricing for Claude Sonnet 4.6, Nova Pro, and Llama 4 Maverick in us-east-1. Show all available tiers and variants for each. Which is cheapest for a standard on-demand workload?"

---

## Region: us-east-1

All prices are per 1M tokens, sourced from local pricing cache files.

---

## 1. Claude Sonnet 4.6 (Anthropic)

| Tier | Variant | Input ($/M) | Output ($/M) | Cache Read ($/M) | Cache Write ($/M) |
|------|---------|:-----------:|:------------:|:-----------------:|:------------------:|
| Standard | Global | $3.00 | $15.00 | $0.30 | $3.75 |
| Standard | Regional | $3.30 | $16.50 | $0.33 | $4.125 |
| Batch | Global | $1.50 | $7.50 | — | — |
| Batch | Regional | $1.65 | $8.25 | — | — |

**Notes:** Supports prompt caching on Standard tier. No Flex or Priority tiers available. Global variant is ~10% cheaper than Regional.

---

## 2. Nova Pro (Amazon)

| Tier | Variant | Input ($/M) | Output ($/M) | Cache Read ($/M) | Cache Write ($/M) |
|------|---------|:-----------:|:------------:|:-----------------:|:------------------:|
| Standard | Global | $1.25 | $10.00 | — | — |
| Standard | Regional | $1.375 | $4.00 | $0.20 | — |
| Flex | Global | $0.625 | $5.00 | — | — |
| Flex | Regional | $0.40 | $1.60 | $0.20 | — |
| Priority | Global | $2.1875 | $17.50 | — | — |
| Priority | Regional | $2.40625 | $19.25 | $0.20 | — |
| Batch | Global | $0.625 | $5.00 | — | — |
| Batch | Regional | $0.40 | $5.50 | — | — |
| Custom Model | Regional | $0.80 | $3.20 | — | — |

**Notes:** Available across all major tiers (Standard, Flex, Priority, Batch). Cache read available on Regional variants but no cache write pricing found. Standard Regional output ($4.00/M) reflects the latency-optimized variant picked from cache.

---

## 3. Llama 4 Maverick 17B (Meta)

| Tier | Variant | Input ($/M) | Output ($/M) | Cache Read ($/M) | Cache Write ($/M) |
|------|---------|:-----------:|:------------:|:-----------------:|:------------------:|
| Standard | Regional | $0.24 | $0.97 | — | — |
| Batch | Regional | $0.12 | $0.485 | — | — |

**Notes:** Regional only — no Global (cross-region) variant available. No prompt caching support. Only Standard and Batch tiers.

---

## 4. Standard On-Demand Comparison

For a standard on-demand workload, the relevant tier is **Standard** with the cheapest available variant:

| Model | Variant | Input ($/M) | Output ($/M) | Total for 1M in + 1M out |
|-------|---------|:-----------:|:------------:|:-------------------------:|
| **Llama 4 Maverick 17B** | Regional | $0.24 | $0.97 | **$1.21** |
| **Nova Pro** | Global | $1.25 | $10.00 | **$11.25** |
| **Claude Sonnet 4.6** | Global | $3.00 | $15.00 | **$18.00** |

---

## 5. Recommendation

**Cheapest for standard on-demand: Llama 4 Maverick 17B** at $0.24/M input and $0.97/M output.

Maverick is **~15× cheaper** than Claude Sonnet 4.6 and **~9× cheaper** than Nova Pro on a simple per-token basis.

**Trade-offs to consider:**
- **Llama 4 Maverick**: Cheapest by far, but Regional-only (no cross-region), no prompt caching, and limited to Standard + Batch tiers. Smaller model (17B parameters) — may not match Claude Sonnet 4.6 quality for complex reasoning tasks.
- **Nova Pro**: Mid-range pricing with the most tier flexibility (Standard, Flex, Priority, Batch). Partial cache read support on Regional. Good balance of cost and capability.
- **Claude Sonnet 4.6**: Most expensive but supports full prompt caching (read + write), which can reduce effective costs by 50-60% for multi-turn agent workloads. Best reasoning quality of the three.

For pure cost optimization on simple workloads, Maverick wins. For agent workloads with multi-turn conversations, Claude Sonnet 4.6's caching support can significantly close the gap.

---

*Prices sourced from local cache files (bedrock_pricing.json, bedrock_pricing_3p.json, bedrock_pricing_service.json). Cache dated April 19, 2025.*
