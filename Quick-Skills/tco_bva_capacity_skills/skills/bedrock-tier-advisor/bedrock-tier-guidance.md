# Bedrock Tier & Variant Guidance

> Last updated from AWS documentation: April 2026
>
> Sources:
> - [Service tiers for optimizing performance and cost](https://docs.aws.amazon.com/bedrock/latest/userguide/service-tiers-inference.html)
> - [Capacity, Limits, and Cost Optimization](https://docs.aws.amazon.com/bedrock/latest/userguide/capacity-limits-cost-optimization.html)
> - [Cross-Region inference](https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html)
>
> Content was rephrased for compliance with licensing restrictions.

---

## Service Tiers — When to Use What

| Tier | When to Use | Price vs Standard | Throttling Risk | SLA |
|------|------------|:-----------------:|:---------------:|:---:|
| **Flex** | Dev/test, evaluations, content summarization, agentic workflows that tolerate latency | Cheapest | High — best-effort, deprioritized during peak | None |
| **Standard** | Regular production workloads, everyday AI tasks, content generation | Baseline | Medium | Standard |
| **Priority** | Mission-critical customer-facing apps, real-time interactions needing consistent fast responses | Premium (~3.5×) | Low — prioritized over Standard and Flex | Enhanced |
| **Reserved** | Steady high-volume loads, apps that can't tolerate downtime | Fixed monthly commitment | None within reserved capacity | 99.5% uptime |
| **Batch** | Bulk processing, non-time-sensitive (training data gen, report generation, data enrichment) | ~50% of Standard | N/A — async, 24h window | N/A |

**Key insight**: On-demand quota is shared across Flex, Standard, and Priority tiers. Reserved capacity is separate. Upgrading from Standard to Priority doesn't give you more quota — it gives you priority access to the same pool.

---

## Cross-Region Variants — When to Use What

| Variant | When to Use | Cost | Data Residency |
|---------|------------|------|---------------|
| **Global** | Max throughput + cost savings, no geographic restrictions | ~10% cheaper than Regional | Data can go to any AWS commercial region |
| **Geographic** (US, EU, APAC) | Data residency compliance within a geography | Standard pricing | Stays within geographic boundary |
| **Regional** (single region) | Strict data residency to one region, or regulatory requirement | ~10% more than Global | Stays in specified region |

**Key insight**: There is no additional routing cost for cross-region inference. All data remains on the AWS network and is encrypted in transit. Cross-region inference can route to regions not manually enabled in your account.

---

## AWS Recommended Decision Framework

1. **Start with Standard** for most workloads
2. **Downgrade to Flex** for dev/test environments
3. **Upgrade to Priority** only when throttling impacts users (monitor CloudWatch throttle metrics)
4. **Move to Reserved** when consistent load exceeds 40% of on-demand costs
5. **Use Batch** for anything that doesn't need real-time response
6. **Combine approaches**: Reserved for baseline + Standard for bursts + Priority for critical peaks + Batch for offline

For variants: **Choose Global unless you have data residency requirements.** It's cheaper and provides higher throughput.

---

## Default Selection Logic

When the user hasn't specified a tier or variant, apply this logic:

1. Query `extract_bedrock_model_prices(results, all_tiers=True)` to discover available options
2. If the workload is non-interactive (bulk processing, evaluations, offline), recommend **Batch** if available
3. Otherwise, filter to on-demand tiers (exclude Batch, Provisioned, Custom Model) and prefer the one with prompt caching support (`cache_read` price exists)
4. If multiple on-demand tiers have caching, pick the one with the lowest input price
5. If no on-demand tier has caching, pick the cheapest on-demand tier available
6. For variant, prefer Global over Regional (cheaper, higher throughput)
7. Present the selected tier to the user and mention alternatives
