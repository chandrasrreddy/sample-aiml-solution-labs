---
name: bedrock-capacity
display_name: Bedrock Capacity Planning
description: "RPM/TPM capacity planning for Amazon Bedrock. Activate when the user asks about requests per minute, tokens per minute, throttling, quotas, capacity limits, tier selection (Flex/Standard/Priority/Reserved), or whether their workload will fit. Also activate as a follow-up to bedrock-pricing or agentcore-pricing estimates."
icon: "📊"
trigger: bedrock capacity check
inputs:
  - name: tier
    description: "Service tier to check against (Flex, Standard, Priority, Reserved). Default: Standard."
    type: string
    required: false
tools: [run_python, file_read]
---

## Overview

Checks if a workload fits within Bedrock RPM/TPM limits and guides optimization when it doesn't. Part of a 4-skill family: `bedrock-pricing`, `agentcore-pricing`, `bedrock-capacity` (this), `agent-business-value`.

## ⚠️ LIMITS RULE

**ALWAYS use `query_quotas()` to get real per-model, per-region RPM/TPM limits.** Do NOT use hardcoded tier ranges — they are inaccurate (actual limits vary wildly by model).

If `bedrock_quotas.json` is missing, **say so explicitly** and guide the user to refresh:
```
python3 ~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh
```

Do NOT fall back to approximate ranges — they create false confidence.

Explanations are embedded directly in function return values via `result["explanation"]` — no separate skill needed.

## Workflow

1. **Load script** → inventory cache
2. **Look up actual limits** → `query_quotas()` for the specific model + region
3. **Compute required RPM/TPM** → `check_capacity_fit()`
4. **Compare** → fits? Show utilization %. Doesn't fit? → 3-step optimization framework
5. **After optimization** → re-run check

### Load Script

```python
import sys, os
sys.argv = ['bedrock_pricing.py']
exec(open(os.path.expanduser("~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py")).read())
```

## Cache File

| Cache File | Contents | Refresh |
|-----------|----------|---------|
| `~/bedrock_quotas.json` | Per-model RPM/TPM/TPD defaults for all regions | `--refresh` |

Multi-region: `--quota-regions "us-west-2,us-east-1,eu-west-1"` | Skip quotas: `--skip-quotas`

## Step 1: Look Up Real Limits

```python
home = os.path.expanduser("~")
rpm_quotas = query_quotas(home, model_filter="Claude Sonnet 4.6", region_filter="us-west-2",
                          quota_type_filter="RPM", inference_type_filter="On-demand")
tpm_quotas = query_quotas(home, model_filter="Claude Sonnet 4.6", region_filter="us-west-2",
                          quota_type_filter="TPM", inference_type_filter="On-demand")

actual_rpm_limit = rpm_quotas[0]["value"] if rpm_quotas else None
actual_tpm_limit = tpm_quotas[0]["value"] if tpm_quotas else None
```

If `rpm_quotas` is empty → cache is missing. Tell user to run `--refresh`. Do NOT guess.

## Step 2: Compute Required RPM/TPM

```python
result = check_capacity_fit(
    questions_per_month=1_000_000,
    sessions_per_month=200_000,
    tools_invoked=10,
    output_burndown_rate=5,      # Claude 3.7 and all later Claude models (4.x, Opus, Sonnet, Haiku) = 5×
    max_tokens_setting=4096,
    peak_to_avg_ratio=3.0,       # peak = 3× average during active hours
    active_hours_per_day=12,
    active_days_per_month=22,
)
```

## Step 3: Compare

```python
if actual_rpm_limit:
    rpm_ok = result["peak_rpm"] <= actual_rpm_limit
    tpm_ok = result["effective_peak_tpm"] <= actual_tpm_limit
else:
    # Cache missing — cannot compare. Tell user to refresh.
    print("⚠️ Quota cache missing. Run --refresh to get actual per-model limits.")
```

## Key Concepts

| Term | Definition |
|------|-----------|
| **RPM** | Requests/min — each LLM invocation = 1 request. Agent with N tools = N+1 requests/question. |
| **TPM** | Tokens/min — quota deducted at request start using `max_tokens` (not actual output). |
| **Burndown rate** | Output token multiplier. **Claude 3.7 and all later Claude models (4.x, Opus, Sonnet, Haiku) = 5×** (1 output = 5 TPM). All others = 1×. |
| **Effective TPM** | input_tokens + max_tokens_setting. Reduce `max_tokens` to free quota. |

## When Workload Doesn't Fit: 3-Step Framework

**Do NOT immediately recommend a quota increase.** Walk through in order:

### Step 1 — Optimize (fill in with actual values from the estimate)

| Check | Question | Impact |
|-------|----------|--------|
| RAG chunks | Can we reduce (e.g. 10→5)? | Saves ~1,500 tokens/turn, compounds |
| System prompt | Can it be shorter? | Sent every turn — compounding |
| Prompt caching | Enabled? **Cache reads DON'T count toward TPM** | Biggest TPM saver |
| `max_tokens` | Set to 4,096 but output is ~100? Reduce to ~300 | Frees ~3,796 TPM/request |
| Conversation history | How many past turns in context? | Limit to 3–5 |
| Tool count | 20 tools × 200 tokens = 4,000/turn. Use dynamic selection? | Reduce per-request |
| Architecture | Monolithic? Split into parent + sub-agents | Fewer tools per agent |
| Output length | Constrain with `max_tokens` + prompt instructions | Claude 5× burndown |

### Step 2 — Traffic Profile

| Question | Why |
|----------|-----|
| Peak RPM (P99 over 1-min window)? | Quotas must handle peaks |
| Sustained P90 over 5-min window? | Service team cares about sustained |
| Active hours/days? | Off-peak = lower effective RPM |
| Default: peak = 3× average during active hours | User should validate |

### Step 3 — Ramp Plan

| Question | Why |
|----------|-----|
| Volume needed now or in 3–6 months? | Capacity allocated in steps |
| Current monthly volume? | Baseline for ramp |
| Consumption trajectory? | Increases granted after demonstrating usage |
| Target at 1 / 3 / 6 months? | Aligns allocation with growth |

## Lessons Learned

### Do
- Auto-run capacity check after cost estimates
- Always use `query_quotas()` for real limits — never hardcoded ranges
- Claude 3.7 and all later Claude models (4.x, Opus, Sonnet, Haiku): always set `output_burndown_rate=5`
- Cache reads don't count toward TPM — biggest saver
- `max_tokens` is reserved upfront — always check for waste
- Present optimization checklist with actual values filled in

### Don't
- Don't use approximate tier ranges — they're misleading
- Don't treat average RPM as peak — apply 3× ratio
- Don't assume 24/7 traffic — ask about active hours
- Don't skip ramp plan — AWS allocates in steps
- Don't recommend quota increase before optimization
