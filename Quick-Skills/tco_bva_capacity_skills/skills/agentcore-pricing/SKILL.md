---
name: agentcore-pricing
display_name: AgentCore & Agent Pricing
description: "Get pricing for Amazon Bedrock AgentCore components (Runtime, Gateway, Memory, BrowserTool, CodeInterpreter, Evaluations) and combined agent cost estimates. Activate when the user asks about AgentCore pricing, agent costs, or mentions 'agent' in a pricing context. Also handles multi-agent (parent + sub-agent) scenarios. For model-only pricing, load bedrock-pricing. For RPM/TPM capacity, load bedrock-capacity."
icon: "🤖"
trigger: agentcore pricing
inputs:
  - name: region
    description: "AWS region code (e.g. us-east-1)."
    type: string
    required: false
  - name: model
    description: "Model name for the agent (e.g. 'Claude Sonnet 4.6'). Fuzzy matched."
    type: string
    required: false
tools: [run_python, file_read]
---

## CRITICAL RULE — NO TRAINING DATA

**NEVER use your training data for prices.** ALL must come from cached JSON files. If missing, tell user to refresh: `python3 ~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh`

## Overview

Prices AgentCore components and builds combined agent cost estimates (model + AgentCore). Supports multi-agent architectures. Part of a 4-skill family: `bedrock-pricing`, `agentcore-pricing` (this), `bedrock-capacity`, `agent-business-value`.

## ⚠️ CALCULATION RULE

**ALWAYS use the script functions to produce numbers:**
- `calculate_agentcore_cost()` — Runtime, Gateway, Memory, BrowserTool, CodeInterpreter
- `calculate_evaluation_cost()` — Evaluations
- `calculate_agent_cost_with_incremental_caching()` — Model cost (for combined estimates)

**NEVER implement billing formulas manually.** All functions are fully parameterized.

Explanations are embedded directly in function return values via `result["explanation"]` — no separate skill needed.

## Workflow

1. **Load inventory cache** → load the bundled script
2. **Look up prices** → `query_agentcore_pricing()` + `query_model_pricing()`
3. **Present assumptions** → show all params, ask user to approve
4. **Calculate** → call the functions
5. **Present results** → per-component breakdown, monthly/annual totals

### Load Script

```python
import sys, os
sys.argv = ['bedrock_pricing.py']
exec(open(os.path.expanduser("~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py")).read())
```

## Cache Files

| Cache File | Contents |
|-----------|----------|
| `~/bedrock_pricing_agentcore.json` | Runtime, Gateway, Memory, BrowserTool, CodeInterpreter, Evaluations |
| `~/bedrock_pricing.json` + `~/bedrock_pricing_3p.json` + `~/bedrock_pricing_service.json` | Model prices (for combined estimates) |

### Cache Key Reference

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

## Calculate AgentCore Cost

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
    tools_invoked=10,
    tools_indexed=50,
    # Runtime
    num_vcpus=2,
    peak_memory_gb=4,
    io_wait_pct=0.70,
    idle_time_between_questions_s=30,
)
# Returns: runtime, gateway, memory, browser, code_interpreter, total_monthly, total_annual
```

## Calculate Evaluations

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

## Scoping Rule

**Only include components explicitly requested.** If user says "run in AC Runtime," add ONLY Runtime — don't auto-add Gateway, Memory, etc.

## Defaults

| Parameter | Default | Notes |
|-----------|---------|-------|
| Questions/session | 5 | Ask user if not specified |
| Tools invoked/question | 10 | Ask user if not specified |
| Tools indexed | 50 | Flat monthly fee |
| vCPUs | 2 | Default microVM |
| Peak memory | 4 GB | Default microVM |
| I/O wait % | 70% | vCPU is FREE during I/O wait |
| Idle time between Qs | 30 sec | User think time |
| STM events/question | 2 | Question + response |
| LTM records/session | 3 | Built-in extraction |
| LTM retrievals/question | 1 | Context lookup |
| Eval sampling rate | 10% | Main cost lever |
| Eval built-in evaluators | 3 | Helpfulness, Correctness, Safety |

## Multi-Agent Architecture

When user describes parent + sub-agents, calculate model inference for **each agent separately**:

| Agent | Default Config |
|-------|---------------|
| **Parent** | All questions, no tools (pure routing), cheap model (Nova Lite), 1 turn/Q |
| **Sub-agents** | Their fraction of questions, own model/tools/caching profile |
| **Shared Runtime** | Scale vCPU/memory proportionally (e.g. 3 agents × 2 vCPU = 6 vCPU) |

## Lessons Learned

### Do
- Distinguish questions from sessions — questions are primary input, sessions derived
- Present assumptions and wait for approval before calculating
- Show both monthly and annual totals
- Highlight I/O wait benefit: "vCPU is free during I/O wait"
- Only include explicitly requested AC components

### Don't
- Don't confuse questions with sessions
- Don't hardcode prices — always read from cache
- Don't apply I/O wait discount to BrowserTool or CodeInterpreter
- Don't charge for STM reads — only writes are billed
- Don't auto-include components the user didn't ask for
