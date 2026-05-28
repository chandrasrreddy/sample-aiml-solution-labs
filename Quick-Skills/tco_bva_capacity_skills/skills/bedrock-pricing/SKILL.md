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
- **ALWAYS ask for model family.** If the user has not specified a model family (e.g., "Sonnet", "Opus", "Haiku", "Nova Pro"), ask which family they want. Never assume one.
- **ALWAYS use `list_models()` before `get_model_prices()`.** When the user has not specified an exact model version, call `list_models(cache_dir, region, family)` first, present the available versions to the user, and let them pick. Only then call `get_model_prices()` with the exact model name they chose.
- **NEVER guess model names or versions.** Only present model names returned by `list_models()` — never from your own knowledge. Never assume "latest" — always confirm with the user.
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

Skip all other workflow steps. These functions accept `detail_level="full"` for per-cycle breakdown.

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

### 2. List Available Models (REQUIRED before pricing lookup)

```python
home = os.path.expanduser("~/bedrock_cache")
models = list_models(home, "us-west-2", "Sonnet")
# → ["Claude 3 Sonnet", "Claude 3.5 Sonnet", "Claude 3.5 Sonnet v2",
#    "Claude 3.7 Sonnet", "Claude Sonnet 4", "Claude Sonnet 4.5", "Claude Sonnet 4.6"]
```

- **Present the list to the user** and ask which model version they want.
- **Empty list:** Tell user no models found for that family/region.
- **FileNotFoundError:** Tell user to run `--refresh` to generate the model index.
- **User provides exact model name upfront:** Skip this step, go directly to Step 2b.

### 2b. Get Prices (after user picks a model)

```python
prices = get_model_prices(home, "us-west-2", "Claude Sonnet 4.6")
# → {"input_price": 3.0, "output_price": 15.0, "cache_read_price": 0.3,
#    "cache_write_price": 3.75, "min_cache_tokens": 2048, "model_name": "Claude Sonnet 4.6"}
```

- **ValueError (no match):** Tell user no pricing found, ask to refine.
- **Success:** Proceed to Step 4 (or Step 3 for tier comparison).

### 2c. Browse Tiers (when comparing all pricing tiers for a model)

```python
results = query_model_pricing(home, "us-west-2", model_filter="Claude Sonnet 4.6")
all_prices = extract_bedrock_model_prices(results, all_tiers=True)
```

Only use this path when the user explicitly asks to compare tiers. For standard pricing lookups, use Step 2b.

### 3. Look Up Model Prices (only needed if using Step 2b)

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

**This applies to sub-agent models too.** For each sub-agent model that supports prompt caching (has non-None `cache_read`/`cache_write` in pricing data), include `cache_read_price` and `cache_write_price` in the sub-agent's `model_prices` dict. Do NOT skip caching for sub-agents when their model supports it.

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
- Whether prompt caching is supported and enabled for the sub-agent model
- Key sub-agent params (RAG: chunks, chunk size; Research: iterations, fetch probability)

Only proceed to calculation after user confirms or adjusts values.

### 6. Calculate Cost

> **IMPORTANT:** The examples below use illustrative values only. Always substitute the user's actual values for any parameter they specify. Only use defaults for parameters the user has not provided.

**Fastest path — Single agent with defaults:**

```python
# One-liner when user provides model + region + volume
result = estimate_cost(home, "us-west-2", "Claude Sonnet 4", 10000)

# With overrides:
result = estimate_cost(home, "us-west-2", "Claude Sonnet 4", 10000,
                       questions_per_agent_session=3, system_prompt_tokens=4000)
```

**Standard path — Single agent (no sub-agents):**

```python
# EXAMPLE ONLY — replace values with user-specified inputs
prices = get_model_prices(home, "us-west-2", "Claude Sonnet 4")
result = calculate_agent_session_compounded_cost(
    main_agent_config={
        **prices,
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
main_prices = get_model_prices(home, "us-west-2", "Claude Sonnet 4")
rag_prices = get_model_prices(home, "us-west-2", "Nova 2.0 Lite")
research_prices = get_model_prices(home, "us-west-2", "Claude Haiku 4.5")

result = calculate_agent_session_compounded_cost(
    main_agent_config={
        **main_prices,
        "agent_sessions_per_month": 10000,
        "questions_per_agent_session": 5,
        "tools_passed_to_agent": 10,
        "tools_invoked": 5,
    },
    subagents=[
        {
            "type": "rag",
            "token_params": {
                "rag_n_chunks": 10,
                "rag_chunk_size": 300,
                "output_tokens": 300,
            },
            "model_prices": rag_prices,  # includes cache prices + min_cache_tokens automatically
            "questions_invoked": 3,
        },
        {
            "type": "research",
            "token_params": {
                "n_research_iterations": 4,
                "fetch_probability": 0.5,
                "output_tokens": 1000,
            },
            "model_prices": research_prices,
            "questions_invoked": 0,
        },
    ],
)
```

**Example — Explicit output path:**

```python
# Write report to a specific file instead of the default directory
result = calculate_agent_session_compounded_cost(
    main_agent_config={...},
    output_path="/path/to/my-report.md",
)
```

**Key rules:**
- Only override parameters the user specifies — omitted keys use defaults
- `tools_invoked` must be >= number of sub-agents with `questions_invoked > 0`
- `questions_invoked=0` means pre-session (output added to system_prompt, cached)
- `questions_invoked=N` means invoked as a tool in the first N questions
- Sub-agent `token_params` only need the keys the user wants to override
- `output_path` is optional — if omitted, the report is written to the configured default directory

### 7. Present Results

> **CRITICAL:** Always present the values returned by the function. Never compute your own token counts, costs, or explanations. The function handles all math internally. Your role is to format and present the function's output — not to replicate or override it.

#### Normal flow (file written successfully)

The function writes a full detailed report to a markdown file and returns a compact summary:

```python
# Example return value (values are illustrative):
{
    "file_path": "/Users/x/bedrock_reports/claude-sonnet-4.6_10k-sessions_20260526-143022-a1b2.md",
    "sessions_per_month": 10000,
    "monthly_total": 3247.48,
    "annual_total": 38969.70,
    "session_total": 0.324748,
    "session_total_no_cache": 0.831350,
    "savings_pct": 60.9,
    "main_agent_session_cost": 0.232148,
    "subagent_session_cost": 0.092600,
    "recommended_ttl": "5min",
    "top_cost_driver": "main agent (token compounding)",
    "capacity_profile": {...},  # pass directly to check_capacity_fit()
}
```

**Present the compact summary as a markdown table.** Include the `file_path` so the user knows where the full report is. Include savings % and recommended TTL.

#### Fallback flow (file write failed)

If the function cannot write to any path, it returns the full result dict inline with `_file_write_failed: True`. The function also prints a warning to stderr. In this case:

1. Present the full result using `token_table` and other fields as described below
2. Inform the user that the report could not be saved to a file
3. Suggest the user configure a writable path via `reports.output_dir` in `~/.bedrock_skills/config.yaml`

#### Accessing the full report

The full report is written to the file at `file_path`. It contains all sections in standard order:

1. **Cost Summary** — session/monthly/annual costs, savings %, TTL
2. **Capacity Summary** — fit result table only (RPM/TPM/TPD fits? utilization%)
3. **Pricing Data Freshness** — pricing cache file ages
4. **Model Resolution** — models found, selected
5. **Pricing** — all tiers table, selected tier
6. **Inputs & Assumptions** — main agent + sub-agent parameters
7. **Token Breakdown** — complete per-cycle token breakdown for all agents
8. **Prompt Caching Strategy** — Checkpoint Configuration, Break-Even Analysis, Cost Comparison, TTL Recommendation
9. **Capacity Detailed Calculations** — Profile Derivation (Field|Formula|Value), Tier Limits, Assumptions, RPM, TPM, TPD

#### Capacity planning from the summary

The compact summary includes `capacity_profile` — pass it directly to `check_capacity_fit()`:

```python
cap_result = check_capacity_fit(
    capacity_profile=result["capacity_profile"]["main_agent"],
    questions_per_month=50000,
    tier_limits=tier_limits,
)
```

**Rules:**
- **NEVER generate your own token math or cost calculations** — always present the function's output
- **NEVER manually construct token breakdown tables** — the full report file contains the authoritative breakdown
- Always use markdown tables — never HTML artifacts or `<details>` tags
- For multi-agent estimates, show main agent + each sub-agent's contribution
- Always include savings % and recommended TTL

### 8. Detect Agentic Workloads

- If the user's request involves agents, multi-agent architectures, or orchestrators:
  1. Load `agentcore-pricing` skill
  2. Calculate AgentCore infrastructure costs (Runtime, Gateway, Memory)
  3. Present **combined total** (model + infrastructure) — never model-only for agentic workloads
  4. Load `bedrock-capacity` skill and present the capacity fit check using the `capacity_profile` from the cost result — do NOT recompute tokens

### 9. Completeness Check (MANDATORY — DO NOT SKIP)

Before presenting final results to the user, verify ALL applicable items below. Do NOT present results until every applicable check passes.

| # | Check | Condition | Action if not done |
|---|-------|-----------|-------------------|
| 1 | **AgentCore costs included** | Workload mentions "agent", "multi-agent", "sub-agent", "orchestrator", or "agentic" | Load `agentcore-pricing`, run `calculate_agentcore_cost()`, present combined total |
| 2 | **Capacity fit for EVERY model** | User asked about capacity, limits, RPM, TPM, or "will it fit" | Run `check_capacity_fit()` for each distinct model in the workload (main + all sub-agents) |
| 3 | **Reports in session directory** | Any calculation was performed | Use `create_report_session()` and pass `output_dir` to all calculation functions |
| 4 | **Reports at ~/bedrock_reports/** | Any report was written | Never write to custom paths — always use the default report directory or session directory |
| 5 | **All use cases covered** | User provided multiple use cases or scenarios | Each use case gets its own session directory with complete reports |
| 6 | **Sub-agent models have capacity checks** | Multi-agent workload with sub-agents on different models | Get `tier_limits` for each sub-agent model and run `check_capacity_fit()` separately |

**If any applicable check fails, go back and complete it before responding.**

## Configuration

Parameter defaults are managed by the YAML configuration system in `bedrock_pricing.py`.
Override any default via `~/.bedrock_skills/config.yaml` (user-level) or `./.bedrock_skills.yaml` (project-level).

Run `python3 bedrock_pricing.py --init-config` to generate a commented template showing all
available settings with their current defaults.

**Precedence:** function parameter > environment variable > project config > user config > hardcoded default

**Config values are defaults only.** If the user specifies a value in their prompt, always use
the user's value. Config defaults apply only to parameters the user has not mentioned.

See the config template for the full list of overridable settings in the `agent_defaults`,
`rag_defaults`, `research_defaults`, `capacity`, `pricing_cache`, and `model_preferences` sections.

### Main Agent (`main_agent_config`)

| Parameter | Notes |
|-----------|-------|
| Region | No default — always confirm with user |
| `model_name` | Model name string for capacity planning (e.g., "Claude Sonnet 4.6") |
| Service tier | Discover via `all_tiers=True` — use lowest-cost with prompt caching |
| Inference variant | Discover via `all_tiers=True` — prefer Global if available |
| `questions_per_agent_session` | Questions per session |
| `input_tokens` | User's question text |
| `output_tokens` | Agent's final answer |
| `system_prompt_tokens` | Sent with every LLM call |
| `tools_passed_to_agent` | Number of tools in schema |
| `tool_spec_tokens` | Tokens per tool specification |
| `tools_invoked` | Tool calls per question |
| `tool_call_tokens` | Model output per tool call |
| `tool_result_tokens` | Tokens per tool result |
| `history_mode` | "full" or "condensed" |
| `days_per_month` | For TTL calculation |
| `usage_hours_per_day` | Active hours per day |
| `cache_history_checkpoints` | 0-3 (max 3, Bedrock limit) |

### RAG Sub-Agent (`token_params` for type="rag")

| Parameter | Notes |
|-----------|-------|
| `system_prompt_tokens` | Sub-agent system prompt |
| `n_tools` | Tools available to sub-agent |
| `tool_spec_tokens` | Tokens per tool spec |
| `input_query_tokens` | Query from main agent |
| `tool_call_tokens` | Model output per tool call |
| `rag_n_retrieval_calls` | KB retrieval calls |
| `rag_n_chunks` | Chunks per retrieval |
| `rag_chunk_size` | Tokens per chunk |
| `n_other_tool_calls` | Other tools (reranker, etc.) |
| `other_tool_result_tokens` | Result size for other tools |
| `output_tokens` | Response back to main agent |

### Research Sub-Agent (`token_params` for type="research")

| Parameter | Notes |
|-----------|-------|
| `system_prompt_tokens` | Sub-agent system prompt |
| `n_tools` | Tools available (search, fetch) |
| `tool_spec_tokens` | Tokens per tool spec |
| `input_query_tokens` | Query from main agent |
| `tool_call_tokens` | Model output per tool call |
| `n_research_iterations` | Search→(optional fetch) cycles |
| `fetch_probability` | Chance each search leads to fetch |
| `search_result_tokens` | Tokens from web_search |
| `fetch_result_tokens` | Tokens from web_fetch |
| `output_tokens` | Response back to main agent |

## Report Output

The function always writes a full detailed report to a markdown file and returns a compact summary dict. This keeps token usage low while preserving full detail for the user.

### Session Directory Workflow

When running multiple calculations for the same user question (bedrock pricing + agentcore + BVA), group all reports in a session directory:

```python
# Create session directory once per user question
session_dir = create_report_session(model_name="Claude Sonnet 4.6", volume=10000)

# All calculations write to the same session dir
result = calculate_agent_session_compounded_cost(
    main_agent_config={...},
    output_dir=session_dir,
)
# result["file_path"] → ".../claude-sonnet-4.6_10k-sessions_20260526-143022-a1b2/bedrock-pricing.md"

ac_result = calculate_agentcore_cost(..., output_dir=session_dir)
bva_result = calculate_business_value(..., output_dir=session_dir)
```

The session directory groups all related reports:
```
~/bedrock_reports/claude-sonnet-4.6_10k-sessions_20260526-143022-a1b2/
├── bedrock-pricing.md
├── agentcore.md
└── business-value.md
```

`create_report_session()` enforces the naming convention — the agent passes raw inputs (model name, volume, optional label) and the function handles sanitization and formatting.

### How it works

1. `calculate_agent_session_compounded_cost()` computes full detail internally
2. Writes the complete report (token breakdown, capacity, caching strategy) to a `.md` file
3. Returns a compact summary dict with key metrics + `file_path` + `capacity_profile`

### File location

Reports are written to `~/bedrock_reports/` by default. Configure via:
- `reports.output_dir` in `~/.bedrock_skills/config.yaml` — change default directory
- `output_dir` parameter — write to a session directory (recommended)
- `output_path` parameter — write to a specific file path (overrides output_dir)

Precedence: `output_path` > `output_dir` > generated flat file path.

### Cleanup

Old reports and session directories are automatically cleaned up based on `reports.retention_days` (default: 30 days) when `reports.auto_cleanup` is True. Session directories are deleted based on directory mtime.

Manual cleanup:
```bash
python3 bedrock_pricing.py --cleanup-reports
```

This deletes reports and session directories older than the configured threshold. Files in session directories are subject to deletion along with the directory.

### Failure behavior

If the report cannot be written to any path (session dir → default dir → all fail):
- The function returns the full result dict inline with `_file_write_failed: True`
- A warning is printed to stderr explaining the failure
- The user should configure a writable path via `reports.output_dir` or pass `output_dir`

## Output Structure

### Compact summary (normal return)

| Key | Type | Description |
|-----|------|-------------|
| `file_path` | str | Path to the full detailed report file |
| `session_total` | float | Cost per session (with prompt caching) |
| `session_total_no_cache` | float | Cost per session (no prompt caching) |
| `monthly_total` | float | Monthly cost |
| `annual_total` | float | Annual cost |
| `sessions_per_month` | int | Volume used |
| `savings_pct` | float | Prompt caching savings % |
| `main_agent_session_cost` | float | Main agent portion |
| `subagent_session_cost` | float | Sub-agents portion |
| `recommended_ttl` | str | "5min" or "1hour" |
| `top_cost_driver` | str | Largest cost component |
| `capacity_profile` | dict | Token profile for capacity planning (pass to `check_capacity_fit()`) |

### Inline fallback (file write failed)

When `_file_write_failed` is True, the full result dict is returned inline. Key additional fields:

- **`token_table`** (str) — pre-formatted markdown with complete per-cycle token breakdown. Render verbatim.
- **`capacity_profile_table`** (str) — pre-formatted markdown showing Field | Formula | Value.
- `main_agent.token_result.session` — raw per-cycle token data
- `main_agent.with_cache.per_question` — per-cycle cost with cache action
- `main_agent.explanation` — TTL recommendation, prompt caching strategy
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
