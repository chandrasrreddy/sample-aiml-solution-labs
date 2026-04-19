---
name: bedrock-pricing
display_name: Bedrock Model Pricing
description: "Get pricing for Amazon Bedrock foundation models. Activate when the user asks about Bedrock model pricing, inference costs, model comparison, or token costs across regions/tiers. For AgentCore component pricing, load agentcore-pricing. For RPM/TPM capacity planning, load bedrock-capacity."
icon: "💰"
trigger: get bedrock pricing
inputs:
  - name: region
    description: "AWS region code (e.g. us-east-1). If not specified, asks the user which region(s) they want."
    type: string
    required: false
  - name: provider
    description: "Provider/model family (e.g. Anthropic, Meta, Mistral AI, Amazon). Fuzzy matched."
    type: string
    required: false
  - name: model
    description: "Model name (e.g. 'Claude Sonnet 4', 'Nova Pro', 'Llama 4'). Fuzzy matched."
    type: string
    required: false
scripts: [bedrock_pricing.py]
tools: [run_python, file_read]
---

## CRITICAL RULE — NO TRAINING DATA

**NEVER use your training data for prices.** ALL must come from cached JSON files. If missing, tell user to refresh: `python3 ~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh`

## ⚠️ AGENT INTENT DETECTION — HARD RULE

**If the user describes an agent, multi-agent architecture, sub-agents, or any agentic workload** (signals: "agent", "multi-agent", "sub-agent", "orchestrator", "parent agent", "routing agent", "agentic"), you MUST:

1. **Assume AgentCore by default.** Load `agentcore-pricing` automatically and calculate both model inference AND AgentCore infrastructure costs (Runtime, Gateway, Memory). Present a **combined total** — not just model costs.
2. **Never present model-only costs as the "total" for an agent workload.** The combined estimate (model + AgentCore infra) is the default output for any agentic workload.

## Overview

Queries local cached pricing JSON files for Bedrock foundation model per-unit prices. Supports Standard/Priority/Flex tiers, Global/Regional variants, batch, reserved, and prompt caching. Part of a 4-skill family: `bedrock-pricing` (this), `agentcore-pricing`, `bedrock-capacity`, `agent-business-value`.

## ⚠️ CALCULATION RULE

**ALWAYS use `calculate_agent_cost_with_incremental_caching()` to produce cost estimates.** This function is fully parameterized — pass all workload-specific values as arguments. It implements incremental prefix caching correctly.

**NEVER implement caching math, multi-turn compounding, or cost formulas manually.**

Explanations are embedded directly in function return values via `result["explanation"]` — no separate skill needed.

## ⚠️ EXPLANATION RENDERING — ON-DEMAND MARKDOWN

Every cost function returns `result["explanation"]` — a structured dict with step-by-step breakdown of how the numbers were calculated. **Do NOT emit this by default.**

### Pattern:
1. **Default output**: Show summary table + key numbers as markdown. Offer: *"Want to see the step-by-step breakdown?"*
2. **On demand**: When user asks, read `result["explanation"]` from the Python namespace (already computed — no re-run needed) and format as **markdown inline in chat**.
3. **Show all agents**: When explaining a multi-agent estimate, show all agents' breakdowns, not just the top cost driver.

### Rules:
- **Always markdown** — never HTML artifacts for explanations
- **No `<details>` tags** — they don't render interactively in chat or session tabs
- **No re-computation** — the explanation dict is already in memory from the estimate run
- **No explainability skill** — it is deleted. This function-embedded approach replaces it entirely

### Explanation sections per function:
| Function | Sections in `result["explanation"]` |
|----------|-------------------------------------|
| `calculate_agent_cost_with_incremental_caching()` | `token_profile`, `turn_by_turn_q1`, `cross_question_caching`, `cache_math`, `no_cache_baseline`, `monthly_rollup`, `prices_used` |
| `calculate_agentcore_cost()` | `session_profile`, `runtime`, `gateway`, `memory`, `grand_total`, `cost_composition` |
| `calculate_evaluation_cost()` | `sampling`, `trace_size`, `builtin_evaluators`, `custom_llm_evaluators`, `custom_code_evaluators`, `grand_total` |
| `calculate_business_value()` | `dim1_time_savings`, `dim2_churn_reduction` (conditional), `dim3_sales_increase` (conditional), `summary` |
| `check_capacity_fit()` | `rpm_calculation`, `tpm_calculation`, `tier_comparison` |

To render: iterate over the dict keys, format as markdown headers + bullet lists. Values are pre-formatted strings ready for display.

## Workflow

1. **Load inventory cache** (Step 1)
2. **Look up prices** → `query_model_pricing()` + `extract_bedrock_model_prices()`
3. **Detect caching support** → check for cache-read/cache-write entries in results
4. **Calculate cost** → `calculate_agent_cost_with_incremental_caching()` — pass prices + workload params
5. **Present results** → show assumptions, breakdown, no-cache baseline, savings %

## Cache Files

| Cache File | Contents |
|-----------|----------|
| `~/bedrock_pricing.json` | 1P Amazon models + newer 3P models |
| `~/bedrock_pricing_3p.json` | 3P Marketplace models (Anthropic, etc.) |
| `~/bedrock_pricing_service.json` | Very new models |

Fallback path for 3P: `~/My Strands Examples/bedrock_pricing_3p.json`

**Cache refresh**: `python3 ~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh`

**Cache staleness**: The script automatically warns (via stderr) when any cache file is older than 7 days. If you see this warning in the output, advise the user to refresh: `python3 ~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh`

## Step 1: Load Inventory Cache

Always runs first:

```python
import sys, os
sys.argv = ['bedrock_pricing.py']
exec(open(os.path.expanduser("~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py")).read())
# Functions available: query_model_pricing(), query_agentcore_pricing(),
# calculate_agent_cost_with_incremental_caching(), calculate_agentcore_cost(),
# calculate_business_value(), calculate_evaluation_cost(), check_capacity_fit()
```

## Step 2: Look Up Prices

```python
home = os.path.expanduser("~")
results = query_model_pricing(home, region_filter="us-east-1", provider_filter="Anthropic", model_filter="Sonnet 4.6")
prices = extract_bedrock_model_prices(results)
# prices = {"input": 3.0, "output": 15.0, "cache_read": 0.3, "cache_write": 3.75}
```

### Tier Summary (when user doesn't specify a tier)

When the user asks for pricing without specifying a tier, use `all_tiers=True` to show a quick comparison:

```python
all_prices = extract_bedrock_model_prices(results, all_tiers=True)
# all_prices = {
#   "Standard Global":  {"input": 3.0, "output": 15.0, "cache_read": 0.3, "cache_write": 3.75},
#   "Standard Regional": {"input": 3.3, "output": 16.5, "cache_read": 0.33, ...},
#   "Batch Global":     {"input": 1.5, "output": 7.5, ...},
#   "Priority Global":  {"input": ..., "output": ..., ...},  # only if model supports it
#   "Flex Global":      {"input": ..., "output": ..., ...},  # only if model supports it
# }
```

Present the tier summary as a markdown table. Default to **Standard Global** for cost calculations, but let the user pick a different tier. Not all models have all tiers — only show what's available.

### Specific Tier or Variant

```python
# Regional (in-region) pricing
prices = extract_bedrock_model_prices(results, variant="Regional")

# Priority tier
prices = extract_bedrock_model_prices(results, tier="Priority")

# Batch pricing
prices = extract_bedrock_model_prices(results, tier="Batch")

# Flex tier, regional
prices = extract_bedrock_model_prices(results, tier="Flex", variant="Regional")
```

### Multimodal Models (Nova)

For models with image/audio/video token pricing:

```python
prices = extract_bedrock_model_prices(results, include_multimodal=True)
# prices = {"input": ..., "output": ..., "cache_read": ..., "cache_write": ...,
#           "image_input": ..., "audio_input": ..., "video_input": ...}
```

## Step 3: Detect Caching Support

A model supports prompt caching if `cache_read` and `cache_write` keys exist in the extracted prices (non-None). Some models (e.g., Amazon Nova) have `$0.00` cache write price — caching is free for writes.

## Step 4: Calculate Cost

```python
result = calculate_agent_cost_with_incremental_caching(
    input_price=prices["input"],
    output_price=prices["output"],
    cache_read_price=prices["cache_read"],
    cache_write_price=prices["cache_write"],
    sessions_per_month=100_000,
    questions_per_session=5,
    input_tokens=100,
    output_tokens=100,
    system_prompt_tokens=1000,
    tool_desc_tokens=500,
    rag_chunks=10,
    rag_tokens_per_chunk=300,
    tools_invoked=3,
    tool_call_tokens=100,
    tool_result_tokens=500,
)
# Returns: with_cache, no_cache, savings_monthly, savings_pct, assumptions, per_question, per_session
```

Always present the savings comparison (cached vs no-cache baseline).

## Model Defaults

| Parameter | Default | Notes |
|-----------|---------|-------|
| Region | (ask user) | No default |
| Service tier | Standard | Standard/Priority/Flex |
| Inference variant | Global (cross-region) | Global or Regional |
| Input tokens/question | 100 | User's actual question text |
| Output tokens/question | 100 | Model's response text |
| System prompt tokens | 1,000 | Sent with every LLM call |
| Prompt caching | **Enabled** | Default ON for supported models |
| RAG chunks | 10 | Per question |
| Tokens per RAG chunk | 300 | |

## Usagetype Patterns for Cache Pricing

| Cache File | Cache Read Pattern | Cache Write Pattern |
|-----------|-------------------|-------------------|
| AmazonBedrock (1P) | `{Model}-cache-read-input-token-count{-tier}{-variant}` | `{Model}-cache-write-input-token-count{-tier}{-variant}` |
| AmazonBedrockFoundationModels (3P) | `CacheReadInputTokenCount{_LCtx}{_Global}` | `CacheWriteInputTokenCount{_LCtx}{_Global}` |
| AmazonBedrockService | `{Model}-cache-read-input-token-count{-long-context}-cross-region-global` | `{Model}-cache-write-input-token-count{-long-context}-cross-region-global` |

## Output Format

All outputs should include:
- Cache file timestamps (data freshness)
- All pricing from cache — never from training data
- Markdown tables grouped by Region → Provider → Model → Tier
- Both monthly and annual totals
- Savings % vs no-caching baseline

## Lessons Learned

### Do
- Always run cache inventory first
- Read ALL prices from cache files at runtime
- Show the complete math breakdown — users want to verify
- Apply prompt caching by default when supported
- For agent workloads, follow the **Agent Intent Detection** rule above — load `agentcore-pricing` proactively
- Auto-suggest loading `bedrock-capacity` for RPM/TPM planning

### Don't
- NEVER use training data for prices
- NEVER implement cost formulas manually — always use the function
- Don't hardcode provider/model/region lists — extract from cache
- Don't skip caching savings display
