---
name: bedrock-pricing
description: >
  Use when calculating Amazon Bedrock foundation model inference costs, comparing
  model pricing across tiers/regions, or estimating monthly spend for agentic workloads.
  Handles all available inference tiers and variants (as discovered dynamically from the
  pricing cache at runtime), prompt caching savings, multimodal pricing, multi-turn
  compounded cost modeling, and multi-agent architectures (main agent + RAG/research sub-agents).
  Do NOT use for AgentCore infrastructure pricing (load agentcore-pricing),
  RPM/TPM capacity planning (load bedrock-capacity), or business value ROI (load agent-business-value).
---

# Bedrock Model Pricing

## Critical Rules

- **ALWAYS ask for region first.** If the user has not specified a region, ask which region they want before doing anything else. There is no default region — never assume one.
- **NEVER guess model names.** Always call `query_model_pricing()` first. Only present model names returned by the function — never from your own knowledge. If multiple models match, show the list and ask the user to pick. Only proceed when results resolve to exactly one model.
- **NEVER use training data for prices.** All prices must come from the local pricing cache files at runtime.
- **NEVER implement cost formulas manually.** Always use `calculate_agent_session_compounded_cost()`.
- **ALWAYS use user-specified values.** If the user provides a value for any parameter, use that exact value. Default values in examples below are illustrative only — never substitute them for user-provided values.
- **NEVER generate your own calculations or explanations.** Always present the output returned by the function. The function computes all token math, cost breakdowns, and explanations internally. Do not attempt to replicate, summarize, or override the function's output with your own reasoning.
- **If the user describes an agentic workload** (signals: "agent", "multi-agent", "sub-agent", "orchestrator", "agentic"), load `agentcore-pricing` automatically and present combined model + infrastructure costs.

## Token-Only Calculations

If the user asks about token usage/consumption (not pricing), no pricing cache files are needed. Load the script (Step 1) and call directly:
- `calculate_compounded_tokens_for_agent()` — main agent session tokens
- `calculate_rag_subagent_tokens()` — RAG sub-agent tokens per invocation
- `calculate_research_subagent_tokens()` — research sub-agent tokens per invocation

Skip all other workflow steps. Use `detail_level="full"` for per-cycle breakdown.

## Prerequisites

- Pricing cache files must exist in `~/bedrock_cache/` (see Pricing Cache Files section)
- If pricing cache is missing or stale (>7 days), instruct user to refresh:
  ```bash
  # If USE_IN_KIRO or USE_IN_CLAUDE_CODE is set:
  python3 tco_bva_capacity_skills/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh
  # Otherwise (Quick):
  python3 ~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh
  ```

## Pricing Cache Files

| File | Contents |
|------|----------|
| `~/bedrock_cache/bedrock_pricing.json` | 1P Amazon models + newer 3P models |
| `~/bedrock_cache/bedrock_pricing_3p.json` | 3P Marketplace models (Anthropic, etc.) |
| `~/bedrock_cache/bedrock_pricing_service.json` | Very new models |

## Tier and Variant Discovery

Available tiers and variants are **not hardcoded** — they are discovered dynamically from the pricing cache at runtime. New tiers or variants added by AWS will appear automatically after a cache refresh.

```python
# Discover all available tiers/variants for a model (always use this first)
all_prices = extract_bedrock_model_prices(results, all_tiers=True)
# Returns: {"Standard Global": {...}, "Batch Regional": {...}, ...}
# Only tiers that exist in the cache for this model will appear.

# Once you know which tiers exist, query a specific one:
prices = extract_bedrock_model_prices(results, tier="<tier_name>", variant="<variant_name>")

# Multimodal models (includes image/audio/video pricing)
prices = extract_bedrock_model_prices(results, include_multimodal=True)
```

**Rules:**
- Always use `all_tiers=True` first to discover what's available for the model.
- Only present tiers/variants that are returned — never assume a tier exists.
- If the user doesn't specify a tier, show the comparison table from `all_tiers=True`.
- Default to the lowest-cost option with prompt caching support for cost calculations unless the user picks otherwise.

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

This makes all functions available: `query_model_pricing()`, `extract_bedrock_model_prices()`, `calculate_agent_session_compounded_cost()`, and others.

### 1b. Check Pricing Data Freshness (once per session)

```python
cache_status = check_pricing_data_status()
```

**Handle by status:**
- `"ok"` — proceed normally.
- `"stale"` — warn the user that cache is older than 7 days, suggest refresh, but proceed with available data.
- `"partial"` — some files missing. Warn the user which files are absent (results may be incomplete), then proceed.
- `"missing"` — all pricing cache files are missing. **Stop.** Tell the user to run the refresh command from the result and do not attempt queries.

### 2. Resolve Model

```python
home = os.path.expanduser("~/bedrock_cache")
results = query_model_pricing(home, region_filter="us-west-2", provider_filter="Anthropic", model_filter="Haiku")
models_found = sorted(set(r["model"] for r in results))
```

- **0 matches:** Tell user no models found, ask to refine query.
- **1 match:** Proceed to Step 3.
- **Multiple matches:** Present the list, ask user to pick one, then filter:
  ```python
  selected_results = [r for r in results if r["model"] == "Claude Haiku 4.5"]
  ```

### 3. Look Up Model Prices

With a single confirmed model, discover available tiers and extract prices:

```python
# First, discover all available tiers for this model
all_prices = extract_bedrock_model_prices(selected_results, all_tiers=True)
# Returns: {"Standard Global": {"input": 3.0, ...}, "Batch Global": {...}, ...}

# For a specific tier (after user selects or for default calculation):
prices = extract_bedrock_model_prices(selected_results, tier="Standard", variant="Global")
# Returns: {"input": 3.0, "output": 15.0, "cache_read": 0.3, "cache_write": 3.75}
```

- If the user does not specify a tier, use `all_tiers=True` and present a comparison table
- For cost calculations, default to the lowest-cost tier that supports prompt caching (typically the first tier in the results with non-None `cache_read`/`cache_write` values)

### 4. Detect Prompt Caching Support

A model supports prompt caching if `cache_read` and `cache_write` keys exist and are non-None in the extracted prices. Some models (e.g., Amazon Nova) have $0.00 cache write — prompt caching is free for writes.

### 5. Present Assumptions

Show all parameters and their values. Ask the user to confirm before calculating.

**Main agent parameters to surface:**
- Sessions per month
- Questions per session
- Input/output tokens per question
- System prompt tokens
- Number of tools passed and invoked
- Tool call and tool result tokens
- Whether prompt caching is enabled (and supported)
- Tier and variant being used

**Sub-agent parameters (if applicable):**
- Sub-agent type (RAG, research)
- Which questions invoke the sub-agent (or pre-session)
- Sub-agent model and prices
- Key sub-agent params (RAG: chunks, chunk size; Research: iterations, fetch probability)

Only proceed to calculation after user confirms or adjusts values.

### 6. Calculate Cost

> **IMPORTANT:** The examples below use illustrative values only. Always substitute the user's actual values for any parameter they specify. Only use defaults for parameters the user has not provided.

**Example — Single agent (no sub-agents):**

```python
# EXAMPLE ONLY — replace values with user-specified inputs
result = calculate_agent_session_compounded_cost(
    main_agent_config={
        "input_price": prices["input"],
        "output_price": prices["output"],
        "cache_read_price": prices["cache_read"],
        "cache_write_price": prices["cache_write"],
        "agent_sessions_per_month": 10000,
        "questions_per_agent_session": 5,
        "input_tokens": 100,
        "output_tokens": 150,
        "system_prompt_tokens": 2000,
        "tools_passed_to_agent": 10,
        "tool_spec_tokens": 100,
        "tools_invoked": 5,
        "tool_call_tokens": 100,
        "tool_result_tokens": 100,
    }
)
```

**Example — Multi-agent (main + sub-agents):**

```python
# EXAMPLE ONLY — replace values with user-specified inputs
result = calculate_agent_session_compounded_cost(
    main_agent_config={
        "input_price": prices["input"],
        "output_price": prices["output"],
        "cache_read_price": prices["cache_read"],
        "cache_write_price": prices["cache_write"],
        "agent_sessions_per_month": 10000,
        "questions_per_agent_session": 5,
        "input_tokens": 100,
        "output_tokens": 150,
        "system_prompt_tokens": 2000,
        "tools_passed_to_agent": 10,
        "tool_spec_tokens": 100,
        "tools_invoked": 5,
        "tool_call_tokens": 100,
        "tool_result_tokens": 100,
    },
    subagents=[
        {
            "type": "rag",
            "token_params": {
                "rag_n_chunks": 10,
                "rag_chunk_size": 300,
                "output_tokens": 300,
            },
            "model_prices": {"input_price": 1.0, "output_price": 5.0},
            "questions_invoked": 3,
        },
        {
            "type": "research",
            "token_params": {
                "n_research_iterations": 4,
                "fetch_probability": 0.5,
                "output_tokens": 1000,
            },
            "model_prices": {"input_price": 1.0, "output_price": 5.0},
            "questions_invoked": 0,
        },
    ],
)
```

**Key rules:**
- Only override parameters the user specifies — omitted keys use defaults
- `tools_invoked` must be >= number of sub-agents with `questions_invoked > 0`
- `questions_invoked=0` means pre-session (output added to system_prompt, cached)
- `questions_invoked=N` means invoked as a tool in the first N questions
- Sub-agent `token_params` only need the keys the user wants to override

### 7. Present Results

> **CRITICAL:** Always present the values returned by the function. Never compute your own token counts, costs, or explanations. The function handles all math internally. Your role is to format and present the function's output — not to replicate or override it.

#### Summary mode (default)

The function returns `detail_level="summary"` by default:

```python
# Example output structure (values are illustrative):
{
    "session_total": 0.324748,         # per session (with prompt caching)
    "session_total_no_cache": 0.831350, # per session (no prompt caching)
    "monthly_total": 3247.48,
    "annual_total": 38969.70,
    "sessions_per_month": 10000,
    "savings_pct": 60.9,
    "main_agent_session_cost": 0.232148,
    "subagent_session_cost": 0.092600,
    "subagents_summary": [...],
    "recommended_ttl": "5min",
}
```

**Present the actual function output as a markdown table.** Do not substitute example values above — use the real values from the result. Include savings % and recommended TTL.

#### Full mode (detailed breakdown)

If the user asks for detailed breakdown, or the request specifies showing detailed calculations, call with `detail_level="full"`:

```python
result = calculate_agent_session_compounded_cost(
    main_agent_config={...},  # same params as before
    subagents=[...],          # same params as before
    detail_level="full",
)

# The result includes a pre-formatted token breakdown table:
token_table_markdown = result["token_table"]

# And a capacity profile derivation table:
capacity_profile_table = result["capacity_profile_table"]
```

The full result includes:
- **`token_table`** — pre-formatted markdown with complete per-cycle token breakdown for all agents. Render verbatim.
- **`capacity_profile_table`** — pre-formatted markdown showing Field | Formula | Value for how capacity profile values were derived. Render verbatim.

To generate the **complete formatted report** with all sections in the standard order, use `_format_full_output()`:

```python
# After calculating cost and capacity:
full_report = _format_full_output(
    result,
    cache_status=cache_status,       # from check_pricing_data_status()
    models_found=models_found,       # list of model names from resolution
    all_tiers=all_tiers,             # from extract_bedrock_model_prices(all_tiers=True)
    prices=prices,                   # selected prices dict
    tier_limits=tier_limits,         # from get_tier_limits_for_model()
    cap_result=cap_result,           # from check_capacity_fit()
)
# full_report is a complete markdown string — render it directly
```

**Standard section order in `full_report`:**
1. **Cost Summary** — session/monthly/annual costs, savings %, TTL
2. **Capacity Summary** — fit result table only (RPM/TPM/TPD fits? utilization%)
3. **Pricing Data Freshness** — cache file ages
4. **Model Resolution** — models found, selected
5. **Pricing** — all tiers table, selected tier
6. **Inputs & Assumptions** — main agent + sub-agent parameters
7. **Token Breakdown** — `token_table` verbatim (Main Agent, Sub-Agents, Session Summary)
8. **Prompt Caching Strategy** — Checkpoint Configuration, Break-Even Analysis, Cost Comparison, TTL Recommendation
9. **Capacity Detailed Calculations** — Profile Derivation (Field|Formula|Value), Tier Limits, Assumptions, RPM, TPM, TPD

**Rules:**
- **NEVER generate your own token math or cost calculations** — always present the function's output verbatim
- **NEVER manually construct token breakdown tables** — use `result["token_table"]` exclusively
- **NEVER show "how I calculated this"** — the function's `token_table`, `capacity_profile_table`, and explanation dicts contain the authoritative derivation
- Always use markdown tables — never HTML artifacts or `<details>` tags
- For multi-agent estimates, show main agent + each sub-agent's contribution
- Always include savings % and recommended TTL
- When writing to a file, use `_format_full_output()` to produce the complete report

### 8. Detect Agentic Workloads

- If the user's request involves agents, multi-agent architectures, or orchestrators:
  1. Load `agentcore-pricing` skill
  2. Calculate AgentCore infrastructure costs (Runtime, Gateway, Memory)
  3. Present **combined total** (model + infrastructure) — never model-only for agentic workloads
  4. Load `bedrock-capacity` skill and present the capacity fit check using the `capacity_profile` from the cost result — do NOT recompute tokens

## Parameter Defaults

> These are the default values used when the user does not specify a value. **If the user provides a value for any parameter, always use the user's value instead.**

### Main Agent (`main_agent_config`)

| Parameter | Default | Notes |
|-----------|---------|-------|
| Region | (ask user) | No default — always confirm |
| `model_name` | (optional) | Model name string for capacity planning (e.g., "Claude Sonnet 4.6") |
| Service tier | (discover via `all_tiers=True`) | Use lowest-cost tier with prompt caching support |
| Inference variant | (discover via `all_tiers=True`) | Prefer Global if available |
| `questions_per_agent_session` | 5 | Questions per session |
| `input_tokens` | 100 | User's question text |
| `output_tokens` | 150 | Agent's final answer |
| `system_prompt_tokens` | 2000 | Sent with every LLM call |
| `tools_passed_to_agent` | 10 | Number of tools in schema |
| `tool_spec_tokens` | 100 | Tokens per tool specification |
| `tools_invoked` | 5 | Tool calls per question |
| `tool_call_tokens` | 100 | Model output per tool call |
| `tool_result_tokens` | 100 | Tokens per tool result |
| `history_mode` | "full" | "full" or "condensed" |
| `days_per_month` | 30 | For TTL calculation |
| `usage_hours_per_day` | 12 | Active hours per day |
| `cache_history_checkpoints` | 3 | 0-3 (max 3, Bedrock limit) |

### RAG Sub-Agent (`token_params` for type="rag")

| Parameter | Default | Notes |
|-----------|---------|-------|
| `system_prompt_tokens` | 500 | Sub-agent system prompt |
| `n_tools` | 2 | Tools available to sub-agent |
| `tool_spec_tokens` | 100 | Tokens per tool spec |
| `input_query_tokens` | 100 | Query from main agent |
| `tool_call_tokens` | 50 | Model output per tool call |
| `rag_n_retrieval_calls` | 2 | KB retrieval calls |
| `rag_n_chunks` | 10 | Chunks per retrieval |
| `rag_chunk_size` | 300 | Tokens per chunk |
| `n_other_tool_calls` | 1 | Other tools (reranker, etc.) |
| `other_tool_result_tokens` | 200 | Result size for other tools |
| `output_tokens` | 300 | Response back to main agent |

### Research Sub-Agent (`token_params` for type="research")

| Parameter | Default | Notes |
|-----------|---------|-------|
| `system_prompt_tokens` | 500 | Sub-agent system prompt |
| `n_tools` | 2 | Tools available (search, fetch) |
| `tool_spec_tokens` | 50 | Tokens per tool spec |
| `input_query_tokens` | 100 | Query from main agent |
| `tool_call_tokens` | 50 | Model output per tool call |
| `n_research_iterations` | 4 | Search→(optional fetch) cycles |
| `fetch_probability` | 0.5 | Chance each search leads to fetch |
| `search_result_tokens` | 100 | Tokens from web_search |
| `fetch_result_tokens` | 2000 | Tokens from web_fetch |
| `output_tokens` | 1000 | Response back to main agent |

## Output Structure

### Summary mode (default, `detail_level="summary"`)

| Key | Type | Description |
|-----|------|-------------|
| `session_total` | float | Cost per session (with prompt caching) |
| `session_total_no_cache` | float | Cost per session (no prompt caching) |
| `monthly_total` | float | Monthly cost |
| `annual_total` | float | Annual cost |
| `sessions_per_month` | int | Volume used |
| `savings_pct` | float | Prompt caching savings % |
| `main_agent_session_cost` | float | Main agent portion |
| `subagent_session_cost` | float | Sub-agents portion |
| `subagents_summary` | list | Per sub-agent breakdown |
| `recommended_ttl` | str | "5min" or "1hour" |
| `capacity_profile` | dict | Token profile for capacity planning (pass to `check_capacity_fit()`) |

### Full mode (`detail_level="full"`)

All of the above plus:

**Primary outputs for rendering:**
- **`token_table`** (str) — **RENDER VERBATIM.** Pre-formatted markdown with complete per-cycle token breakdown for all agents (main + sub-agents). This is the primary token detail output.
- **`capacity_profile_table`** (str) — **RENDER VERBATIM.** Pre-formatted markdown showing Field | Formula | Value for how capacity profile values were derived from the token data.

**Full report generator (standalone function):**
- `_format_full_output(result, ...)` — generates the complete markdown report with all sections in standard order. Use this when writing output to a file.

**Additional fields (for programmatic access or supplementary presentation):**
- `main_agent.token_result.session` — raw per-cycle token data for each question
- `main_agent.with_cache.per_question` — per-cycle cost with cache action
- `main_agent.explanation` — TTL recommendation, prompt caching strategy, checkpoint analysis
- `subagents[].token_result.cycles` — raw per-cycle token data for each sub-agent
- `subagents[].cost_detail` — cost breakdown per sub-agent invocation

## Formatting Requirements

- Pricing cache file timestamps (data freshness indicator) must be shown
- Use markdown tables grouped by Region → Provider → Model → Tier
- Show both monthly and annual totals
- Include savings % vs no-prompt-caching baseline
- All prices sourced from pricing cache — never from training data
- Token breakdowns come exclusively from `token_table` — never manually constructed

## Related Skills

| Skill | When to load |
|-------|-------------|
| `agentcore-pricing` | User describes an agentic workload needing infrastructure costs |
| `bedrock-capacity` | User asks about RPM/TPM limits or capacity planning |
| `agent-business-value` | User wants ROI, productivity gains, or FTE equivalents |
