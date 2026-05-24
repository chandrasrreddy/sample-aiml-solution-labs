---
name: bedrock-capacity
description: >
  Use when checking RPM/TPM capacity limits, quota utilization, throttling risk,
  or capacity fit for Amazon Bedrock workloads.
  Handles capacity fit checks against real quota limits, optimization recommendations, and ramp planning.
  Also activate as a follow-up after bedrock-pricing or agentcore-pricing estimates.
  Do NOT use for model pricing (load bedrock-pricing),
  AgentCore infrastructure costs (load agentcore-pricing), or business value ROI (load agent-business-value).
---

# Bedrock Capacity Planning

## Critical Rules

- **ALWAYS get real RPM/TPM limits from `query_quotas()`.** Never assume, hardcode, or guess values. If the cache is missing or returns no results for the model/region, tell the user explicitly.
- **Claude 3.7 and all later Claude models (4.x, Opus, Sonnet, Haiku): always set `output_burndown_rate=5`.** All other models use 1x.
- **Prompt cache reads don't count toward TPM** — this is the biggest TPM saver.
- **`max_tokens` is reserved upfront** — always check for waste (e.g., set to 4096 but output is only ~100).
- **Do NOT recommend a quota increase before walking through optimization.**

## Prerequisites

- Cache file `~/bedrock_cache/bedrock_quotas.json` must exist
- If missing or stale, instruct user to refresh:
  ```bash
  # If USE_IN_KIRO or USE_IN_CLAUDE_CODE is set:
  python3 tco_bva_capacity_skills/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh
  # Otherwise (Quick):
  python3 ~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh
  ```
- For multi-region: `--quota-regions "us-west-2,us-east-1,eu-west-1"`

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

### 1b. Check Pricing Data Freshness (once per session)

```python
cache_status = check_pricing_data_status()
```

**Handle by status:**
- `"ok"` — proceed normally.
- `"stale"` — warn the user that cache is older than 7 days, suggest refresh, but proceed with available data.
- `"partial"` or `"missing"` — if `bedrock_quotas.json` is in `cache_status["missing"]`, **stop**. Tell the user to run `cache_status["refresh_command"]` and do not attempt queries.

### 2. Obtain the Token Profile

**If `calculate_agent_session_compounded_cost()` was already called** in this conversation (e.g., user asked for pricing first), use the `capacity_profile` from its output. Do NOT recompute tokens.

**If starting fresh** (user asks for capacity directly), compute the token profile:

```python
# Example — substitute user's actual workload parameters
token_result = calculate_compounded_tokens_for_agent(
    questions_per_agent_session=5,
    input_tokens=100,
    output_tokens=150,
    system_prompt_tokens=2000,
    tools_passed_to_agent=10,
    tool_spec_tokens=100,
    tools_invoked=5,
    tool_call_tokens=100,
    tool_result_tokens=100,  # or list: [300, 100, 100, 100, 100] if sub-agent returns larger results
    detail_level="full",
)

capacity_profile = build_capacity_profile_from_tokens(
    token_result, sessions_per_month=100000, model_name="Claude Sonnet 4.6"
)
```

For multi-agent workloads, include sub-agent token profiles:

```python
rag_tokens = calculate_rag_subagent_tokens(rag_n_chunks=10, output_tokens=300, detail_level="full")

capacity_profile = build_capacity_profile_from_tokens(
    token_result, sessions_per_month=100000,
    model_name="Claude Sonnet 4.6",
    sub_agents=[{
        "type": "rag", "model_name": "Claude Haiku 4.5",
        "token_result": rag_tokens, "invocations_per_session": 3,
    }]
)
```

### 3. Look Up Real Limits

For **each model** in the capacity_profile, get quota limits:

```python
home = os.path.expanduser("~/bedrock_cache")
# Example — use the user's actual model and region
tier_limits = get_tier_limits_for_model(home, model_name="Claude Sonnet 4.6", region="us-west-2")
# Returns: {"rpm_high": 10000, "tpm_high": 6000000, "tpd_high": 8640000000} or None
```

- If `get_tier_limits_for_model()` returns `None`, quota data is missing. Tell user to run `--refresh`. Do NOT guess.
- If user does not specify a region or model, ask before proceeding.

### 4. Aggregate by Model (multi-agent only)

If the workload has sub-agents, use `aggregate_capacity_by_model()` to group load by model. Same-model agents have their RPM/TPM/TPD summed against shared quotas.

```python
# For multi-agent workloads:
# sessions_per_month and questions_per_month are derived from the capacity_profile
# automatically — no need to pass them separately.
per_model = aggregate_capacity_by_model(capacity_profile)
# Returns: {"Claude Sonnet 4.6": {"capacity_profile": {...}, ...}, "Claude Haiku 4.5": {...}}

# For single-agent workloads, skip this step and use capacity_profile["main_agent"] directly.
```

### 5. Check Capacity Fit

Run `check_capacity_fit()` for **each model**:

```python
# Single-agent: use capacity_profile["main_agent"] directly
result = check_capacity_fit(
    capacity_profile=capacity_profile["main_agent"],
    questions_per_month=500000,
    output_burndown_rate=5,  # 5 for Claude 3.7+, 1 for others
    max_tokens_setting=4096,
    peak_to_avg_ratio=3.0,
    active_hours_per_day=12,
    active_days_per_month=22,
    tier_limits=tier_limits,  # from get_tier_limits_for_model()
)

# Multi-agent: iterate per_model from aggregate_capacity_by_model()
for model_name, model_data in per_model.items():
    tier_limits = get_tier_limits_for_model(home, model_name=model_name, region="us-west-2")
    if tier_limits is None:
        # No quota data — tell user to refresh
        continue
    result = check_capacity_fit(
        capacity_profile=model_data["capacity_profile"],
        questions_per_month=model_data["questions_per_month"],
        output_burndown_rate=5,  # 5 for Claude 3.7+, 1 for others
        tier_limits=tier_limits,
    )
```

### 6. Present Results

Always present a **per-model** side-by-side comparison showing:
- **Quota limits** (RPM, TPM, TPD) from `bedrock_quotas.json` via `query_quotas()`
- **Required capacity** (peak RPM, effective peak TPM, estimated TPD) from `check_capacity_fit()`
- **Fit verdict** (✅ fits / ❌ exceeds) and utilization % for each

Example format (per model):

| Metric | Your Workload (Peak) | Quota Limit | Fits? | Utilization |
|--------|---------------------|-------------|-------|-------------|
| RPM | 568 | 10,000 | ✅ | 6% |
| TPM | 6,039,394 | 6,000,000 | ❌ | 101% |
| TPD | 846,590,909 | 8,640,000,000 | ✅ | 10% |

- If workload fits: highlight utilization % and note any metrics close to the limit
- If workload does NOT fit: walk through the 3-Step Optimization Framework below
- After optimization adjustments: recompute the token profile and re-run `check_capacity_fit()` to verify

## Key Concepts

| Term | Definition |
|------|-----------|
| **RPM** | Requests/min. Each LLM invocation = 1 request. Agent invoking N tools per question = N+1 requests/question |
| **TPM** | Tokens/min. Quota deducted at request start using `max_tokens` (not actual output) |
| **Burndown rate** | Output token multiplier. Claude 3.7+ = 5x (1 output token = 5 TPM). All others = 1x |
| **Effective TPM** | Peak TPM inflated by max_tokens reservation. Each request reserves max_tokens upfront — the gap between max_tokens and actual output wastes quota. Reduce max_tokens to free capacity. |
| **TPD** | Tokens/day. Daily aggregate token consumption across all questions. Some models have a hard daily cap that cannot be exceeded regardless of RPM/TPM headroom. |

## When Workload Doesn't Fit: 3-Step Framework

Walk through these in order. Do NOT skip to quota increase.

### Step 1: Optimize

Fill in with actual values from the estimate:

| Check | Question | Impact |
|-------|----------|--------|
| `max_tokens` | Set higher than actual output? e.g., 4,096 but output is ~100 — reduce to ~300 | Frees significant TPM/request (e.g., ~3,796 per request) |
| Prompt caching | Enabled? Prompt cache reads DON'T count toward TPM | Biggest TPM saver |
| Sub-agent RAG chunks | Can we reduce chunks in the RAG sub-agent? e.g., 10 to 5 at 300 tokens each | Reduces sub-agent's TPM/TPD consumption |
| System prompt | Can it be shorter? | Sent every turn, compounding |
| Tool count | e.g., 10 tools × 100 tokens = 1,000/turn. Use dynamic selection? | Reduce per-request |
| Conversation history | How many past turns in context? | Limit to 3-5 |
| Sub-agent response size | Can sub-agents return shorter summaries? | Compounds in main agent context across turns |
| Output length | Constrain with `max_tokens` + prompt instructions | Claude 5x burndown |

### Step 2: Traffic Profile

| Question | Why |
|----------|-----|
| Peak RPM (P99 over 1-min window)? | Quotas must handle peaks |
| Sustained P90 over 5-min window? | Service team cares about sustained |
| Active hours/days? | Off-peak = lower effective RPM |
| e.g., peak = 3× average during active hours | Ask user to validate their actual peak-to-average ratio |

### Step 3: Ramp Plan

| Question | Why |
|----------|-----|
| Volume needed now or in 3-6 months? | Capacity allocated in steps |
| Current monthly volume? | Baseline for ramp |
| Consumption trajectory? | Increases granted after demonstrating usage |
| Target at 1 / 3 / 6 months? | Aligns allocation with growth |

## Defaults

| Parameter | Default | Notes |
|-----------|---------|-------|
| Output burndown rate | 5x (Claude 3.7+) | 1x for all other models |
| max_tokens setting | 4,096 | Check for waste, reduce if actual output is small |
| Peak-to-average ratio | 3.0x | Peak = 3x average during active hours |
| Active hours/day | 12 | Ask user to validate |
| Active days/month | 22 | Business days |

## Explanation Rendering

`result["explanation"]` contains:

| Section | What it shows |
|---------|---------------|
| `rpm_calculation` | How peak RPM was derived |
| `tpm_calculation` | How effective peak TPM was derived |
| `tpd_calculation` | How estimated daily token consumption was derived |
| `tier_comparison` | Fit/no-fit against actual quota limits (RPM, TPM, TPD) |

### Rules for rendering:
- Default: show fit/no-fit summary with utilization %
- On demand: format explanation sections as markdown
- Always use markdown, never HTML artifacts or details tags

## Related Skills

| Skill | When to load |
|-------|-------------|
| `bedrock-pricing` | User needs model cost estimates alongside capacity check |
| `agentcore-pricing` | User needs AgentCore infrastructure costs |
| `agent-business-value` | User wants ROI or business case after capacity is confirmed |
