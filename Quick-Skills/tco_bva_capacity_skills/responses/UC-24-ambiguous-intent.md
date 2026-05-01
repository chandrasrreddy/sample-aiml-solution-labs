# UC-24: Ambiguous Intent — Bedrock Pricing Overview

> **Use Case:** "Tell me about Bedrock pricing."

---

## Assumptions Made (not in prompt)

The prompt is ambiguous — "Tell me about Bedrock pricing" could mean many things. Interpreted as a **pricing overview** showing the tier structure, variant options, and price ranges available on Amazon Bedrock. Using **Claude Sonnet 4.6 in us-east-1** as the representative example with all available tiers, plus Nova Pro and Llama 4 Maverick to show the range of pricing across model families.

- **Region:** us-east-1 (default for vague prompts)
- **Representative model:** Claude Sonnet 4.6 (Anthropic) — most popular for agent workloads
- **Additional models:** Nova Pro (Amazon), Llama 4 Maverick 17B (Meta) — to show price range
- **All prices** sourced from local pricing cache files, never from training data

---

## 1. Bedrock Pricing Structure

Amazon Bedrock uses **pay-per-token** pricing for foundation model inference. Prices are quoted **per 1M tokens** and vary by:

- **Model** — different providers and model sizes have different rates
- **Service Tier** — Standard, Flex, Priority, Batch (not all models support all tiers)
- **Inference Variant** — Global (cross-region) or Regional (in-region only)
- **Prompt Caching** — some models offer discounted rates for cached input tokens

---

## 2. Claude Sonnet 4.6 (Anthropic) — All Tiers in us-east-1

| Tier | Variant | Input ($/M) | Output ($/M) | Cache Read ($/M) | Cache Write ($/M) |
|------|---------|:-----------:|:------------:|:-----------------:|:------------------:|
| Standard | Global | $3.00 | $15.00 | $0.30 | $3.75 |
| Standard | Regional | $3.30 | $16.50 | $0.33 | $4.125 |
| Batch | Global | $1.50 | $7.50 | — | — |
| Batch | Regional | $1.65 | $8.25 | — | — |

**Key observations:**
- **Standard** is the default on-demand tier — best for real-time, production workloads
- **Batch** is 50% cheaper but asynchronous (up to 24-hour processing window)
- **Global** variant is ~10% cheaper than Regional (routes requests across regions)
- **Prompt caching** is available on Standard tier only — cache reads are 90% cheaper than standard input
- No Flex or Priority tiers available for this model

---

## 3. Nova Pro (Amazon) — All Tiers in us-east-1

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

**Key observations:**
- Supports **all major tiers** (Standard, Flex, Priority, Batch) — most tier flexibility of any model
- **Flex** tier is cheapest on-demand option but has no SLA and higher throttling risk
- **Priority** tier is ~1.75× Standard price — for latency-sensitive, mission-critical workloads
- Partial cache read support on Regional variants (no cache write pricing)

---

## 4. Llama 4 Maverick 17B (Meta) — All Tiers in us-east-1

| Tier | Variant | Input ($/M) | Output ($/M) | Cache Read ($/M) | Cache Write ($/M) |
|------|---------|:-----------:|:------------:|:-----------------:|:------------------:|
| Standard | Regional | $0.24 | $0.97 | — | — |
| Batch | Regional | $0.12 | $0.485 | — | — |

**Key observations:**
- **Regional only** — no Global (cross-region) variant available
- **No prompt caching** support
- Only Standard and Batch tiers
- By far the cheapest per-token pricing of the three models

---

## 5. Tier Comparison Guide

| Tier | Best For | Trade-offs |
|------|----------|------------|
| **Standard** | Production, real-time workloads | Default choice; supports caching on some models |
| **Flex** | Dev/test, prototyping, cost-sensitive | No SLA, higher throttling risk; not for production |
| **Priority** | Mission-critical, latency-sensitive | ~1.75× Standard price; guaranteed capacity |
| **Batch** | Offline processing, bulk analysis | 50% cheaper; async with up to 24h processing window |

**Variant guidance:**
- **Global (cross-region):** ~10% cheaper, routes requests to least-loaded region. Best default for most workloads.
- **Regional (in-region):** Use when data residency or compliance requires traffic to stay in a specific region.

---

## 6. Standard On-Demand Price Comparison

For a standard on-demand workload using the cheapest available variant per model:

| Model | Provider | Variant | Input ($/M) | Output ($/M) | Caching | Total for 1M in + 1M out |
|-------|----------|---------|:-----------:|:------------:|:-------:|:-------------------------:|
| **Llama 4 Maverick 17B** | Meta | Regional | $0.24 | $0.97 | ❌ | **$1.21** |
| **Nova Pro** | Amazon | Global | $1.25 | $10.00 | Partial | **$11.25** |
| **Claude Sonnet 4.6** | Anthropic | Global | $3.00 | $15.00 | ✅ Full | **$18.00** |

---

## 7. Representative Cost Example

To illustrate how pricing translates to real costs, here's a representative agent workload on each model:

### Workload Profile

| Parameter | Value |
|-----------|-------|
| Sessions/month | 100,000 |
| Questions/session | 5 |
| Tools invoked/question | 10 |
| System prompt | 1,000 tokens |
| Tool descriptions | 4,000 tokens |
| User input | 100 tokens |
| RAG chunks | 10 × 300 tokens |
| Tool call output | 100 tokens |
| Tool result input | 500 tokens |
| Final answer | 100 tokens |

### Token Profile (per question)

| Metric | Value |
|--------|-------|
| Cacheable base (system + tools) | 5,000 tokens |
| Base prompt (+ user + RAG) | 8,100 tokens |
| Delta per tool turn | 600 tokens |
| Turns per question | 11 |
| Total input per question | 122,100 tokens |
| Total output per question | 1,100 tokens |
| Questions per month | 500,000 |
| Monthly input tokens | 61,050,000,000 |
| Monthly output tokens | 550,000,000 |

### Monthly Cost Comparison

| Model | Tier/Variant | With Caching | Without Caching | Savings |
|-------|-------------|:------------:|:---------------:|:-------:|
| **Claude Sonnet 4.6** | Standard Global | **$43,762.50** | $191,400.00 | 77.1% |
| **Nova Pro** | Standard Global | $81,812.50 | $81,812.50 | 0% (no caching) |
| **Llama 4 Maverick** | Standard Regional | $15,185.50 | $15,185.50 | 0% (no caching) |

### Claude Sonnet 4.6 Cost Breakdown (with caching)

| Component | Monthly Cost |
|-----------|:-----------:|
| Cache write | $17,812.50 |
| Cache read | $16,800.00 |
| Regular input | $900.00 |
| Output | $8,250.00 |
| **Total** | **$43,762.50** |

### Cache Split Details (Claude Sonnet 4.6)

| Metric | Q1 (first in session) | Q2+ (subsequent) |
|--------|:--------------------:|:-----------------:|
| Cache write | 13,500 tokens | 8,500 tokens |
| Cache read | 108,000 tokens | 113,000 tokens |
| Regular | 600 tokens | 600 tokens |
| **Sum** | **122,100** | **122,100** |

**Session totals:** cache_write = 47,500 | cache_read = 560,000 | regular = 3,000

**Key insight:** Claude Sonnet 4.6 with prompt caching ($43,762.50/mo) is actually **cheaper** than Nova Pro without caching ($81,812.50/mo) for this multi-turn agent workload, despite having higher per-token rates. Caching reduces effective input costs by 77%.

---

## 8. Summary

Amazon Bedrock pricing is **pay-per-token** with significant variation across models, tiers, and variants:

- **Price range:** From $0.24/M input (Llama 4 Maverick) to $3.00/M input (Claude Sonnet 4.6) on Standard tier
- **Biggest cost lever:** Prompt caching — can reduce total costs by 50-80% for multi-turn agent workloads
- **Cheapest per-token:** Llama 4 Maverick ($1.21 per 1M in + 1M out)
- **Best value for agents:** Claude Sonnet 4.6 with caching — higher per-token rate but lower effective cost due to cache savings
- **Most tier flexibility:** Nova Pro — available across Standard, Flex, Priority, and Batch

For a specific cost estimate, provide your model, region, and workload details (sessions/month, questions/session, tools used).

---

*Prices sourced from local cache files (bedrock_pricing.json, bedrock_pricing_3p.json, bedrock_pricing_service.json).*
