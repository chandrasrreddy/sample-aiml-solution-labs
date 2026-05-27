---
name: agentcore-pricing
description: >
  Use when estimating Amazon Bedrock AgentCore infrastructure costs including Runtime,
  Gateway, Memory, BrowserTool, CodeInterpreter, or Evaluations. Handles combined
  agent cost estimates (model inference + AgentCore infrastructure) and multi-agent
  architectures (parent + sub-agents).
  Do NOT use for model-only pricing (load bedrock-pricing),
  RPM/TPM capacity planning (load bedrock-capacity), or business value ROI (load agent-business-value).
---

# AgentCore Pricing

## Critical Rules

- **NEVER use training data for prices.** All prices must come from the local pricing cache files at runtime.
- **NEVER implement billing formulas manually.** Always use `calculate_agentcore_cost()` and `calculate_evaluation_cost()`.
- **Only include components explicitly requested.** If user says "run in AC Runtime," add ONLY Runtime — do not auto-add Gateway, Memory, etc.
- **STM reads are free** — only writes are billed.
- **vCPU is free during I/O wait** — do not apply I/O wait discount to BrowserTool or CodeInterpreter.

## Prerequisites

- Cache file `~/bedrock_cache/bedrock_pricing_agentcore.json` must exist
- If missing or stale (>7 days), instruct user to refresh:
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

### 1b. Check Pricing Data Freshness (once per session)

```python
cache_status = check_pricing_data_status()
```

**Handle by status:**
- `"ok"` — proceed normally.
- `"stale"` — warn the user that cache is older than 7 days, suggest refresh, but proceed with available data.
- `"partial"` or `"missing"` — if `bedrock_pricing_agentcore.json` is in `cache_status["missing"]`, **stop**. Tell the user to run `cache_status["refresh_command"]` and do not attempt queries.

### 2. Look Up AgentCore Prices

```python
home = os.path.expanduser("~/bedrock_cache")
ac_prices = query_agentcore_pricing(home, region_filter="us-east-1")
```

- If user needs a combined estimate (model + infrastructure), also call `query_model_pricing()` for the model prices
- If user does not specify a region, ask which region they want

### 3. Present Assumptions

Show all parameters and their values. Ask the user to confirm before calculating. Key parameters to surface:
- Questions per month and per session
- Tools invoked per question
- vCPU count and memory allocation
- I/O wait percentage
- Which components are included (Runtime, Gateway, Memory, BrowserTool, CodeInterpreter, Evaluations)

### 4. Calculate AgentCore Cost

```python
result = calculate_agentcore_cost(
    runtime_vcpu_price_hr=0.0895,    # from cache
    runtime_mem_price_hr=0.00945,    # from cache
    gateway_invocation_price=5e-6,   # from cache
    gateway_search_price=2.5e-5,     # from cache
    gateway_indexing_price=0.0002,   # from cache
    stm_event_price=0.00025,         # from cache
    ltm_storage_price=0.00075,       # from cache
    ltm_retrieval_price=0.0005,      # from cache
    # Optional: BrowserTool (None = not included)
    browser_vcpu_price_hr=None,
    browser_mem_price_hr=None,
    # Optional: CodeInterpreter (None = not included)
    ci_vcpu_price_hr=None,
    ci_mem_price_hr=None,
    # Workload
    questions_per_month=1_000_000,
    questions_per_session=5,
    tools_invoked=5,
    tools_indexed=50,
    # Runtime
    num_vcpus=2,
    peak_memory_gb=4,
    io_wait_pct=0.70,
    idle_time_between_questions_s=30,
    # Report output (optional — session directory from create_report_session)
    output_dir=session_dir,
)
# Returns compact summary: file_path, total_monthly, total_annual, component breakdowns
```

The function writes a detailed report to a file and returns a compact summary dict. See "Report Output" section below.

### 5. Calculate Evaluations (if requested)

```python
eval_result = calculate_evaluation_cost(
    questions_per_month=1_000_000,
    sessions_per_month=200_000,
    sampling_rate=0.10,
    num_builtin_evaluators=3,
    builtin_input_price=2.40,    # from cache
    builtin_output_price=12.00,  # from cache
)
```

### 6. For Combined Estimates (Model + Infrastructure)

- Load `bedrock-pricing` to get model inference costs via `calculate_agent_cost_with_incremental_caching()`
- Sum model cost + AgentCore cost for the grand total
- Present per-component breakdown showing where spend goes

### 7. Present Results

The function returns a compact summary with key metrics. Present it as a markdown table:

```python
# Example compact summary (values are illustrative):
{
    "file_path": "/Users/x/bedrock_reports/claude-sonnet-4.6_1m-sessions_20260526-143022-a1b2/agentcore.md",
    "total_monthly": 1234.56,
    "total_annual": 14814.72,
    "runtime_monthly": 800.00,
    "gateway_monthly": 300.00,
    "memory_monthly": 134.56,
    "browser_monthly": 0.00,
    "code_interpreter_monthly": 0.00,
    "sessions_per_month": 200000,
    "questions_per_month": 1000000,
    "top_cost_component": "runtime (65%)",
}
```

- Present the compact summary as a markdown table
- Include `file_path` so the user knows where the full report is
- Highlight the top cost component
- If the user asks for detailed breakdown, direct them to the report file

### 8. Completeness Check (MANDATORY — DO NOT SKIP)

Before presenting final results to the user, verify ALL applicable items below. Do NOT present results until every applicable check passes.

| # | Check | Condition | Action if not done |
|---|-------|-----------|-------------------|
| 1 | **Combined total presented** | AgentCore was calculated alongside model inference | Present model cost + AgentCore cost + grand total — never AgentCore in isolation without context |
| 2 | **Reports in session directory** | Model inference was also calculated | Use `create_report_session()` and write both `bedrock-pricing.md` and `agentcore.md` to the same session directory |
| 3 | **Only requested components included** | User specified which components (Runtime, Gateway, Memory, etc.) | Do NOT auto-add components the user didn't mention — only Runtime, Gateway, Memory are defaults for agentic workloads |
| 4 | **All use cases covered** | User provided multiple use cases or scenarios | Each use case gets its own AgentCore calculation with appropriate parameters |
| 5 | **Prices from cache** | Any calculation was performed | All component prices came from `query_agentcore_pricing()` — never hardcoded or assumed |

**If any applicable check fails, go back and complete it before responding.**

## Report Output

The function always writes a detailed report to a markdown file and returns a compact summary.

### Session Directory Workflow

When running multiple calculations for the same user question, group reports in a session directory:

```python
# Create session directory once per user question
session_dir = create_report_session(model_name="Claude Sonnet 4.6", volume=1000000)

# All calculations write to the same session dir
result = calculate_agentcore_cost(..., output_dir=session_dir)
eval_result = calculate_evaluation_cost(..., output_dir=session_dir)
```

The session directory contains all related reports:
```
~/bedrock_reports/claude-sonnet-4.6_1m-sessions_20260526-143022-a1b2/
├── agentcore.md
└── evaluations.md
```

### Failure Behavior

If the report cannot be written (unwritable directory), the function:
1. Tries the session directory
2. Falls back to a flat file in the default reports directory
3. If all writes fail: returns the full result dict inline with `_file_write_failed: True`

### Cleanup

Reports are subject to auto-cleanup after the configured retention period (`reports.retention_days`, default 30 days). Files in session directories are deleted along with the directory.

## Multi-Agent Architecture

When user describes parent + sub-agents, calculate model inference for **each agent separately**:

| Agent | Default Config |
|-------|---------------|
| **Parent (router)** | All questions, no tools, cheap model (Nova Lite), 1 turn/Q |
| **Sub-agents** | Their fraction of questions, own model/tools/prompt caching profile |
| **Shared Runtime** | Scale vCPU/memory proportionally (e.g., 3 agents × 2 vCPU = 6 vCPU) |

Present each agent's cost individually, then sum for the architecture total.

## Configuration

AgentCore defaults are managed by the YAML configuration system in `bedrock_pricing.py`.
Override any default via `~/.bedrock_skills/config.yaml` (user-level) or `./.bedrock_skills.yaml` (project-level).

Run `python3 bedrock_pricing.py --init-config` to generate a commented template showing all
available settings with their current defaults.

**Precedence:** function parameter > environment variable > project config > user config > hardcoded default

**Config values are defaults only.** If the user specifies a value in their prompt, always use
the user's value. Config defaults apply only to parameters the user has not mentioned.

See the `agentcore_defaults` section in the config template for overridable settings.

| Parameter | Notes |
|-----------|-------|
| Questions/session | Ask user if not specified |
| Tools invoked/question | Ask user if not specified |
| Tools indexed | Flat monthly fee |
| vCPUs | Default microVM |
| Peak memory | Default microVM |
| I/O wait % | vCPU is FREE during I/O wait |
| Idle time between Qs | User think time |
| STM events/question | Question + response |
| LTM records/session | Built-in extraction |
| LTM retrievals/question | Context lookup |
| Eval sampling rate | Main cost lever |
| Eval built-in evaluators | Helpfulness, Correctness, Safety |

## Cache Key Reference

| Component | Cache Key Pattern |
|-----------|------------------|
| Runtime vCPU | `Runtime:Consumption-based:vCPU` → per vCPU-Hour |
| Runtime Memory | `Runtime:Consumption-based:Memory` → per GB-Hour |
| Gateway Invocations | `Gateway:Consumption-based:API-Invocations` |
| Gateway Search | `Gateway:Consumption-based:Search-API` |
| Gateway Indexing | `Gateway:Consumption-based:Tool-Indexing` |
| STM | `Memory:Consumption-based:Short-Term-Memory` |
| LTM Storage | `Memory:Consumption-based:Long-Term-Memory-Storage:Built-in-memory` |
| LTM Retrieval | `Memory:Consumption-based:Long-Term-Memory-Retrieval` |
| BrowserTool vCPU | `BrowserTool:Consumption-based:vCPU` |
| BrowserTool Memory | `BrowserTool:Consumption-based:Memory` |
| CodeInterpreter vCPU | `CodeInterpreter:Consumption-based:vCPU` |
| CodeInterpreter Memory | `CodeInterpreter:Consumption-based:Memory` |
| Evaluations Built-in Input | `Evaluations:Consumption-based:BuiltIn-Input:Tier1` |
| Evaluations Built-in Output | `Evaluations:Consumption-based:BuiltIn-Output:Tier1` |
| Evaluations Custom | `Evaluations:Consumption-based:CustomEvaluators:Tier1` |

## Explanation Rendering

The detailed breakdown is written to the report file. It contains these sections:

| Section | What it shows |
|---------|---------------|
| `session_profile` | Session duration and active time |
| `runtime` | vCPU + memory cost breakdown |
| `gateway` | Invocations, search, indexing costs |
| `memory` | STM + LTM costs |
| `grand_total` | Sum of all components |
| `cost_composition` | Percentage breakdown by component |

### Rules for rendering:
- Default: present the compact summary table, mention file_path for full details
- If user asks for breakdown: direct them to the report file
- If `_file_write_failed` is True: the full result is inline — format the explanation dict as markdown
- Always use markdown — never HTML artifacts or `<details>` tags
- Never re-compute — the explanation dict is already in the report file

## Related Skills

| Skill | When to load |
|-------|-------------|
| `bedrock-pricing` | Need model inference prices for combined estimates |
| `bedrock-capacity` | User asks about RPM/TPM limits or provisioned throughput |
| `agent-business-value` | User wants ROI, productivity gains, or FTE equivalents |
