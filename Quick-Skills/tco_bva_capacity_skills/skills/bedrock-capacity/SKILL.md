---
name: bedrock-capacity
description: >
  Use when checking RPM/TPM capacity limits, quota utilization, throttling risk,
  or tier selection (Flex/Standard/Priority/Reserved) for Amazon Bedrock workloads.
  Handles capacity fit checks, optimization recommendations, and ramp planning.
  Also activate as a follow-up after bedrock-pricing or agentcore-pricing estimates.
  Do NOT use for model pricing (load bedrock-pricing),
  AgentCore infrastructure costs (load agentcore-pricing), or business value ROI (load agent-business-value).
---

# Bedrock Capacity Planning

## Critical Rules

- **ALWAYS use `query_quotas()` for real per-model, per-region RPM/TPM limits.** Never use hardcoded tier ranges — actual limits vary by model.
- **If `bedrock_quotas.json` is missing, say so explicitly.** Do NOT fall back to approximate ranges — they create false confidence.
- **Claude 3.7 and all later Claude models (4.x, Opus, Sonnet, Haiku): always set `output_burndown_rate=5`.** All other models use 1x.
- **Cache reads don't count toward TPM** — this is the biggest TPM saver.
- **`max_tokens` is reserved upfront** — always check for waste (e.g., set to 4096 but output is only ~100).
- **Do NOT recommend a quota increase before walking through optimization.**

## Prerequisites

- Cache file `~/bedrock_quotas.json` must exist
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

### 2. Look Up Real Limits

```python
home = os.path.expanduser("~")
rpm_quotas = query_quotas(home, model_filter="Claude Sonnet 4.6", region_filter="us-west-2",
                          quota_type_filter="RPM", inference_type_filter="On-demand")
tpm_quotas = query_quotas(home, model_filter="Claude Sonnet 4.6", region_filter="us-west-2",
                          quota_type_filter="TPM", inference_type_filter="On-demand")

actual_rpm_limit = rpm_quotas[0]["value"] if rpm_quotas else None
actual_tpm_limit = tpm_quotas[0]["value"] if tpm_quotas else None
```

- If `rpm_quotas` is empty, cache is missing. Tell user to run `--refresh`. Do NOT guess.
- If user does not specify a region or model, ask before proceeding.

### 3. Present Assumptions

Show all workload parameters and ask user to confirm before calculating:
- Questions per month and sessions per month
- Tools invoked per question
- Output burndown rate (5x for Claude 3.7+, 1x for others)
- `max_tokens` setting
- Peak-to-average ratio (default: 3x)
- Active hours per day and active days per month

### 4. Compute Required RPM/TPM

```python
result = check_capacity_fit(
    questions_per_month=1_000_000,
    sessions_per_month=200_000,
    tools_invoked=5,
    output_burndown_rate=5,
    max_tokens_setting=4096,
    peak_to_avg_ratio=3.0,
    active_hours_per_day=12,
    active_days_per_month=22,
)
```

### 5. Compare Against Limits

```python
if actual_rpm_limit:
    rpm_ok = result["peak_rpm"] <= actual_rpm_limit
    tpm_ok = result["effective_peak_tpm"] <= actual_tpm_limit
else:
    print("Quota cache missing. Run --refresh to get actual per-model limits.")
```

### 6. Present Results

- If workload fits: show utilization % for both RPM and TPM
- If workload does NOT fit: walk through the 3-Step Optimization Framework below
- After optimization adjustments: re-run `check_capacity_fit()` to verify

## Key Concepts

| Term | Definition |
|------|-----------|
| **RPM** | Requests/min. Each LLM invocation = 1 request. Agent with N tools = N+1 requests/question |
| **TPM** | Tokens/min. Quota deducted at request start using `max_tokens` (not actual output) |
| **Burndown rate** | Output token multiplier. Claude 3.7+ = 5x (1 output token = 5 TPM). All others = 1x |
| **Effective TPM** | input_tokens + (max_tokens_setting x burndown_rate). Reduce `max_tokens` to free quota |

## When Workload Doesn't Fit: 3-Step Framework

Walk through these in order. Do NOT skip to quota increase.

### Step 1: Optimize

Fill in with actual values from the estimate:

| Check | Question | Impact |
|-------|----------|--------|
| `max_tokens` | Set to 4,096 but output is ~100? Reduce to ~300 | Frees ~3,796 TPM/request |
| Prompt caching | Enabled? Cache reads DON'T count toward TPM | Biggest TPM saver |
| RAG chunks | Can we reduce (e.g., 10 to 5)? | Saves ~1,500 tokens/turn, compounds |
| System prompt | Can it be shorter? | Sent every turn, compounding |
| Tool count | 10 tools x 100 tokens = 1,000/turn. Use dynamic selection? | Reduce per-request |
| Conversation history | How many past turns in context? | Limit to 3-5 |
| Architecture | Monolithic? Split into parent + sub-agents | Fewer tools per agent |
| Output length | Constrain with `max_tokens` + prompt instructions | Claude 5x burndown |

### Step 2: Traffic Profile

| Question | Why |
|----------|-----|
| Peak RPM (P99 over 1-min window)? | Quotas must handle peaks |
| Sustained P90 over 5-min window? | Service team cares about sustained |
| Active hours/days? | Off-peak = lower effective RPM |
| Default: peak = 3x average during active hours | User should validate |

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
| `tier_comparison` | Fit/no-fit against actual quota limits |

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
