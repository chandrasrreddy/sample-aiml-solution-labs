---
name: bedrock-cost-test-generator
display_name: Bedrock Cost Test Generator
description: "Generate test cases for Bedrock agent pricing and business value estimates. Activate when the user wants to create test specs, validation cases, or QA fixtures for agent cost calculations — good signals: 'generate test cases', 'create test spec', 'make test fixtures', 'QA data', 'validation cases for pricing'. Produces JSON test specs that the bedrock-cost-qa skill can verify."
icon: "🧪"
trigger: generate bedrock cost test cases
depends-on: [bedrock-pricing]
inputs:
  - name: use_case_name
    description: "Descriptive name for the test case (e.g., 'Enterprise IT Helpdesk Agent')"
    type: string
    required: true
  - name: model
    description: "Bedrock model name (e.g., 'Claude Sonnet 4.6', 'Claude Opus 4.6'). Used to look up prices from cache."
    type: string
    required: true
  - name: region
    description: "AWS region code (e.g., 'us-east-1')"
    type: string
    required: true
  - name: sessions_per_month
    description: "Number of agent sessions per month"
    type: number
    required: true
  - name: questions_per_session
    description: "Questions per session"
    type: number
    default: 3
  - name: tools_invoked
    description: "Tool invocations per question"
    type: number
    default: 5
  - name: num_tools
    description: "Number of tools in the agent's schema"
    type: number
    default: 10
  - name: use_agentcore
    description: "Whether to include AgentCore component costs (Runtime, Gateway, Memory)"
    type: boolean
    default: true
  - name: use_business_value
    description: "Whether to include business value calculations (Dim 1a/1b)"
    type: boolean
    default: true
scripts: [test_generator.py]
tools: [run_python, file_read]
---

## Overview

Generates a JSON test specification file containing all input parameters, expected intermediate values, and expected cost/business-value outputs for a Bedrock agent use case. The test spec is derived entirely from the formulas in `pricing_spec_v1.1.md` — the single source of truth. Output is consumed by the `bedrock-cost-qa` skill for automated verification.

## Workflow

### Step 1: Load Pricing Data
- **Mode**: `deterministic`
- **Tool**: `run_python`
- **Input**: `{{model}}`, `{{region}}`
- **Output**: Model prices (P_in, P_out, P_cr, P_cw) and AgentCore prices from cache

Load the bundled pricing script from `bedrock-pricing` and query model + AgentCore prices:

```python
import sys, os
sys.argv = ['bedrock_pricing.py']
exec(open(os.path.expanduser("~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py")).read())

home = os.path.expanduser("~")
model_results = query_model_pricing(home, region_filter='{{region}}', provider_filter='', model_filter='{{model}}')
prices = extract_bedrock_model_prices(model_results)
ac_results = query_agentcore_pricing(home, '{{region}}')
```

- **Validate**: `prices` dict contains `input`, `output`, `cache_read`, `cache_write` keys with non-zero values
- **On failure**: Tell user to refresh cache: `python3 ~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh`

### Step 2: Compute All Expected Values
- **Mode**: `deterministic`
- **Tool**: `run_python`
- **Input**: All parameters from Step 1 + user inputs

Run the bundled `test_generator.py` script which implements every formula from the spec:

```python
exec(open(os.path.expanduser("~/.quickwork/skills/bedrock-cost-test-generator/scripts/test_generator.py")).read())

test_spec = generate_test_spec(
    use_case_name='{{use_case_name}}',
    sessions_per_month={{sessions_per_month}},
    questions_per_session={{questions_per_session}},
    tools_invoked={{tools_invoked}},
    num_tools={{num_tools}},
    prices=prices,
    ac_prices=ac_results,
    use_agentcore={{use_agentcore}},
    use_business_value={{use_business_value}}
)
```

The script computes:
1. **Token math**: base_context, tool_delta, turns, total_input_per_question, total_output_per_question
2. **Cache splits**: Q1 (cw/cr/reg), Q2+ (cw/cr/reg), session totals, monthly totals
3. **Costs**: no-cache baseline, cache costs, total model cost, caching savings %
4. **AgentCore**: Runtime, Gateway, Memory line items (if enabled)
5. **Business value**: 3 tiers × Dim 1a + 1b (if enabled)
6. **Verification identities**: All sum-check equations from the spec

- **Validate**: All verification identities hold (cache split sums = total_input_per_question, session sums = Q_s × per-question)
- **On failure**: Spec formula bug — do NOT save the test spec; report the failing identity

### Step 3: Save Test Spec
- **Mode**: `deterministic`
- **Tool**: `run_python`
- **Input**: `test_spec` dict from Step 2
- **Output**: JSON file saved to `artifacts/test_spec_{{use_case_name}}.json`

```python
import json
output_path = f"artifacts/test_spec_{use_case_name_slug}.json"
with open(output_path, 'w') as f:
    json.dump(test_spec, f, indent=2)
```

- **Validate**: File exists and is valid JSON
- **On failure**: Check disk space / permissions

### Step 4: Present Summary
- **Mode**: `agentic`
- **Output**: Markdown summary of the test spec with key expected values

Present a table of key expected values:
- Token intermediates (base_context, total_input_per_question, etc.)
- Cost expectations (model cost, AC cost, total, savings %)
- Business value expectations (moderate tier)
- Verification identity results (all pass/fail)

Then offer to run the QA judge:
```
<decision question="Test spec generated. What next?">
<option description="Run the QA judge to verify a cost estimate against this spec">Run QA judge</option>
<option description="Generate another test case with different parameters">Generate another</option>
</decision>
```

## Output

A JSON test spec file with this structure:

```json
{
  "meta": { "name": "...", "model": "...", "region": "...", "generated_at": "..." },
  "inputs": { /* all workload + pricing parameters */ },
  "expected": {
    "tokens": { "base_context": ..., "total_input_per_question": ..., ... },
    "cache_splits": { "q1_cw": ..., "q1_cr": ..., "q2_cw": ..., ... },
    "costs": { "no_cache_total": ..., "total_model_cost": ..., "caching_savings_pct": ..., ... },
    "agentcore": { "runtime": ..., "gateway": ..., "memory": ..., "total": ... },
    "business_value": { "moderate": { "productivity_value": ..., "roi": ... }, ... }
  },
  "verifications": { "q1_sum_check": true, "q2_sum_check": true, "session_sum_check": true, "monthly_sum_check": true }
}
```

## Lessons Learned

### Do
- Always verify all sum-check identities before saving — a test spec with wrong expected values is worse than no spec
- Include ALL intermediate values, not just final costs — the QA judge needs to pinpoint exactly where a calculation diverges
- Use the closed-form formulas for token math (they're verified against turn-by-turn enumeration in the spec)

### Don't
- Don't use training data for prices — always read from cache
- Don't hardcode price values in the script — always pass them as parameters
- Don't generate test specs for models not in the cache

### Common Failures
- Cache files missing → guide user to refresh
- Model name doesn't match cache → fuzzy match via `query_model_pricing`
- AgentCore prices incomplete → the AC cache only has ~16 entries; some components may be missing for certain regions

### When to Ask the User
- When the model name is ambiguous (e.g., "Sonnet" matches multiple versions)
- When business value parameters aren't specified (defaults are used but confirmation is helpful)