# UC-19: Tier Recommendation — Customer Service Agent on Claude Sonnet 4.6

> **Use Case:** "I'm building a customer service agent on Claude Sonnet 4.6 in us-east-1. It's production, customer-facing. Which tier and variant should I use?"

---

## 1. Available Tiers & Variants for Claude Sonnet 4.6 in us-east-1

Discovered from the Bedrock pricing cache using `extract_bedrock_model_prices(results, all_tiers=True)`:

| Tier + Variant | Input ($/M) | Output ($/M) | Cache Read ($/M) | Cache Write ($/M) | Caching? |
|----------------|:-----------:|:------------:|:-----------------:|:-----------------:|:--------:|
| **Standard Global** | $3.00 | $15.00 | $0.30 | $3.75 | ✅ Yes |
| Standard Regional | $3.30 | $16.50 | $0.33 | $4.125 | ✅ Yes |
| Batch Global | $1.50 | $7.50 | — | — | ❌ No |
| Batch Regional | $1.65 | $8.25 | — | — | ❌ No |

**Note:** Flex and Priority tiers were not found in the pricing cache for Claude Sonnet 4.6 in us-east-1. This means they are either not yet available for this model or not published in the current pricing data.

---

## 2. Recommendation

### ✅ Recommended: Standard Global (with Prompt Caching)

**Reasoning:**

1. **Production + customer-facing → Standard tier.** The AWS decision framework recommends Standard for regular production workloads. Flex has no SLA and high throttling risk — unsuitable for customer-facing applications. Priority would be appropriate for mission-critical latency needs, but it's not available for this model (and costs ~3.5× more when it is).

2. **Global variant → cheaper + higher throughput.** The Global (cross-region) variant is ~10% cheaper than Regional ($3.00 vs $3.30 input, $15.00 vs $16.50 output). Cross-region inference routes traffic across AWS commercial regions on the AWS network, encrypted in transit. Unless you have strict data residency requirements mandating traffic stays in us-east-1, Global is the better choice.

3. **Prompt caching is the biggest cost lever.** Standard Global supports prompt caching with cache reads at $0.30/M (90% discount vs $3.00 input price). For a customer service agent with a stable system prompt and tool descriptions, caching can reduce total costs by 40–60% depending on session length and tool usage. Batch tier does not support caching.

**Pricing summary:**

| Component | Standard Global |
|-----------|:--------------:|
| Input | $3.00/M tokens |
| Output | $15.00/M tokens |
| Cache Read | $0.30/M tokens (10% of input) |
| Cache Write | $3.75/M tokens (125% of input) |

---

## 3. Alternatives with Trade-Offs

### Alternative 1: Batch Global — $1.50/$7.50 per M tokens

- **50% cheaper** than Standard on both input and output
- **Trade-off:** Asynchronous processing with a 24-hour completion window. Not suitable for a real-time customer-facing agent. No prompt caching support.
- **When to use:** If you have offline batch processing needs alongside the real-time agent (e.g., nightly report generation, bulk content moderation), run those workloads on Batch to save 50%.

### Alternative 2: Standard Regional — $3.30/$16.50 per M tokens

- **~10% more expensive** than Standard Global
- **Trade-off:** Data stays within us-east-1 only. Slightly lower throughput since traffic isn't distributed across regions.
- **When to use:** If you have regulatory or compliance requirements that mandate data residency in a single AWS region (e.g., HIPAA, FedRAMP, or internal data governance policies).

### Alternative 3: Batch Regional — $1.65/$8.25 per M tokens

- **Same trade-offs as Batch Global** (async, no caching) plus data residency in us-east-1
- **When to use:** Offline batch workloads with data residency requirements.

---

## 4. Cost Optimization Tips

1. **Enable prompt caching immediately.** With Standard Global, your system prompt and tool descriptions are cached across turns within a session. Cache reads cost 90% less than regular input — this is the single biggest cost optimization available.

2. **Consider a hybrid approach as you scale:**
   - **Standard Global** for real-time customer interactions (with caching)
   - **Batch Global** for any offline processing (analytics, report generation, training data)

3. **Monitor CloudWatch throttle metrics.** If you see consistent throttling on Standard tier impacting customer experience, that's the signal to evaluate Priority tier (when it becomes available for this model) or Reserved capacity for your baseline load.

4. **Watch for Flex/Priority availability.** These tiers are not currently available for Claude Sonnet 4.6 but may be added. Flex could be useful for dev/test environments; Priority for latency-sensitive peaks.

---

## 5. Decision Summary

| Criterion | Your Situation | Recommendation |
|-----------|---------------|----------------|
| Workload type | Production | Standard (not Flex) |
| User-facing? | Yes, customer-facing | Standard with SLA (not Flex) |
| Latency needs | Real-time conversational | Standard (not Batch) |
| Data residency | Not specified | Global (cheaper, higher throughput) |
| Cost optimization | Important for production | Enable prompt caching |

### → **Use Standard Global with prompt caching enabled.**

---

> **Sources:**
> - [Service tiers for optimizing performance and cost](https://docs.aws.amazon.com/bedrock/latest/userguide/service-tiers-inference.html)
> - [Cross-Region inference](https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html)
> - Pricing data from Bedrock Pricing API cache (queried via `extract_bedrock_model_prices`)
