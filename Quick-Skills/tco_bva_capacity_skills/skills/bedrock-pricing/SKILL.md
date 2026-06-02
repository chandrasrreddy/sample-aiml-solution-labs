---
name: bedrock-pricing
description: >
  Use when calculating Amazon Bedrock foundation model inference costs, comparing
  model pricing across tiers/regions, or estimating monthly spend for agentic workloads.
  Handles Standard/Priority/Flex/Batch tiers, Global/Regional variants, prompt caching
  savings, multimodal pricing, and multi-turn agent cost modeling.
  Do NOT use for AgentCore infrastructure pricing (load agentcore-pricing),
  RPM/TPM capacity planning (load bedrock-capacity), or business value ROI (load agent-business-value).
---

# Bedrock Model Pricing

## Critical Rules

- **NEVER use training data for prices.** All prices must come from cached JSON files at runtime.
- **NEVER implement cost formulas manually.** Always use `calculate_agent_cost_with_incremental_caching()`.
- **If the user describes an agentic workload** (signals: "agent", "multi-agent", "sub-agent", "orchestrator", "agentic"), load `agentcore-pricing` automatically and present combined model + infrastructure costs.

## Prerequisites

- Cache files must exist in `~/` (see Cache Files section)
- If cache is missing or stale (>7 days), instruct user to refresh:
  ```bash
  # If USE_IN_KIRO or USE_IN_CLAUDE_CODE is set:
  python3 tco_bva_capacity_skills/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh
  # Otherwise (Quick):
  python3 ~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh
  ```

## Workflow

### 1. Load the Pricing Script

```python
import sys, os
sys.argv = ['bedrock_pricing.py']

if os.environ.get("USE_IN_KIRO") or os.environ.get("USE_IN_CLAUDE_CODE"):
    script = "tco_bva_capacity_skills/skills/bedrock-pricing/scripts/bedrock_pricing.py"
else:
    script = os.path.expanduser("~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py")

if not os.path.exists(script):
    raise RuntimeError(
        f"bedrock_pricing.py not found at: {script}\n"
        f"If using Kiro/Claude Code, set USE_IN_KIRO=1 or USE_IN_CLAUDE_CODE=1.\n"
        f"If using Quick, ensure the script is installed at the expected path."
    )

exec(open(script).read())
```

This makes all functions available: `query_model_pricing()`, `extract_bedrock_model_prices()`, `calculate_agent_cost_with_incremental_caching()`, and others.

### 2. Look Up Model Prices

```python
home = os.path.expanduser("~")
results = query_model_pricing(home, region_filter="us-east-1", provider_filter="Anthropic", model_filter="Sonnet 4.6")
prices = extract_bedrock_model_prices(results)
# Returns: {"input": 3.0, "output": 15.0, "cache_read": 0.3, "cache_write": 3.75}
```

- If the user does not specify a region, ask which region(s) they want
- If the user does not specify a tier, use `all_tiers=True` and present a comparison table
- Default to **Standard Global** for cost calculations unless user picks otherwise

### 3. Detect Caching Support

A model supports prompt caching if `cache_read` and `cache_write` keys exist and are non-None in the extracted prices. Some models (e.g., Amazon Nova) have $0.00 cache write — caching is free for writes.

### 4. Present Assumptions

Show all parameters and their values. Ask the user to confirm before calculating. Key parameters to surface:
- Sessions per month
- Questions per session
- Input/output tokens per question
- System prompt tokens
- Number of tools passed and invoked
- RAG chunks and tokens per chunk
- Whether prompt caching is enabled (and supported)
- Tier and variant being used

Only proceed to calculation after user confirms or adjusts values.

### 5. Calculate Cost

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
    tools_passed_to_agent=10,
    tool_spec_tokens=100,
    rag_chunks=10,
    rag_tokens_per_chunk=300,
    tools_invoked=5,
    tool_call_tokens=100,
    tool_result_tokens=100,
)
```

Pass all workload-specific values as arguments. The function handles incremental prefix caching, multi-turn compounding, and session-aware Q1/Q2+ logic internally.

### 6. Present Results

1. Show a summary markdown table with: monthly cost (cached), no-cache baseline, savings %, per-session and per-question costs
2. Include cache file timestamps to show data freshness
3. Offer: *"Want to see the step-by-step breakdown?"*

- If user asks for the breakdown, read `result["explanation"]` (already computed — no re-run needed) and format as markdown headers + bullet lists

### 7. Detect Agentic Workloads

- If the user's request involves agents, multi-agent architectures, or orchestrators:
  1. Load `agentcore-pricing` skill
  2. Calculate AgentCore infrastructure costs (Runtime, Gateway, Memory)
  3. Present **combined total** (model + infrastructure) — never model-only for agentic workloads

## Tier and Variant Options

```python
# All tiers comparison (when user doesn't specify)
all_prices = extract_bedrock_model_prices(results, all_tiers=True)

# Specific tier/variant combinations
prices = extract_bedrock_model_prices(results, variant="Regional")
prices = extract_bedrock_model_prices(results, tier="Priority")
prices = extract_bedrock_model_prices(results, tier="Batch")
prices = extract_bedrock_model_prices(results, tier="Flex", variant="Regional")

# Multimodal models (Nova — includes image/audio/video pricing)
prices = extract_bedrock_model_prices(results, include_multimodal=True)
```

Only show tiers that exist for the model — not all models have all tiers.

## Cache Files

| File | Contents |
|------|----------|
| `~/bedrock_pricing.json` | 1P Amazon models + newer 3P models |
| `~/bedrock_pricing_3p.json` | 3P Marketplace models (Anthropic, etc.) |
| `~/bedrock_pricing_service.json` | Very new models |

## Model Defaults

| Parameter | Default | Notes |
|-----------|---------|-------|
| Region | (ask user) | No default — always confirm |
| Service tier | Standard | Standard/Priority/Flex/Batch |
| Inference variant | Global (cross-region) | Global or Regional |
| Input tokens/question | 100 | User's question text |
| Output tokens/question | 100 | Model's response text |
| System prompt tokens | 1,000 | Sent with every LLM call |
| Tools passed to agent | 10 | Number of tools in schema |
| Tool spec tokens | 100 | Tokens per tool specification |
| Tools invoked/question | 5 | Tool calls per question |
| Tool result tokens | 100 | Tokens per tool result |
| Prompt caching | Enabled | Default ON for supported models |
| RAG chunks | 10 | Per question |
| Tokens per RAG chunk | 300 | |

## Explanation Rendering

Every cost function returns `result["explanation"]` with structured breakdown sections:

| Section | What it shows |
|---------|---------------|
| `token_profile` | Token counts per turn |
| `turn_by_turn_q1` | Q1 cache split per turn |
| `cross_question_caching` | Q2+ cache behavior |
| `cache_math` | Monthly cache read/write/regular totals |
| `no_cache_baseline` | Cost without caching |
| `monthly_rollup` | Final monthly/annual totals |
| `prices_used` | Prices from cache (for auditability) |

### Rules for rendering explanations:
- Default: show summary only, offer breakdown on demand
- Always use markdown — never HTML artifacts or `<details>` tags
- Never re-compute — the explanation dict is already in memory
- For multi-agent estimates, show all agents' breakdowns

## Output Format

All outputs must include:
- Cache file timestamps (data freshness indicator)
- Markdown tables grouped by Region → Provider → Model → Tier
- Both monthly and annual totals
- Savings % vs no-caching baseline
- All prices sourced from cache — never from training data

## Related Skills

| Skill | When to load |
|-------|-------------|
| `agentcore-pricing` | User describes an agentic workload needing infrastructure costs |
| `bedrock-capacity` | User asks about RPM/TPM limits or capacity planning |
| `agent-business-value` | User wants ROI, productivity gains, or FTE equivalents |
