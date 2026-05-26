---
name: agent-business-value
description: >
  Use when calculating business value, ROI, or cost justification for AI agents.
  Handles three dimensions: (1) Time Savings as productivity increase or cost reduction,
  (2) Customer Churn Reduction from better CX, (3) Sales Increase from better CX.
  Works standalone or alongside bedrock-pricing/agentcore-pricing estimates.
  Do NOT use for model pricing (load bedrock-pricing),
  AgentCore infrastructure costs (load agentcore-pricing), or capacity planning (load bedrock-capacity).
---

# Agent Business Value

## Critical Rules

- **ALWAYS use `calculate_business_value()` to produce estimates.** Never implement business value formulas manually.
- **Dimensions 1a and 1b are mutually exclusive** — same time savings, different framing (revenue uplift vs. labor cost reduction). Never add them together.
- **Dimensions 2 and 3 are optional add-ons** — additive with Dim 1 (different value streams). Only apply to customer-facing agents.
- **Agent cost is deducted once from grand total**, not per dimension.
- **Never fabricate customer data** — if web lookup fails, say so and ask the user.

## Prerequisites

- The pricing script must be loaded (provides `calculate_business_value()`)
- If combining with a pricing estimate, `bedrock-pricing` or `agentcore-pricing` should have already run in the conversation (to provide `agent_cost_monthly`)

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

### 2. Present Dimension Menu

Show the user which dimensions are available and ask which apply:

| # | Dimension | Default | Notes |
|---|-----------|---------|-------|
| **1a** | Productivity Increase (revenue uplift) | Selected | Mutually exclusive with 1b |
| **1b** | Cost Savings (labor cost reduction) | Available | Mutually exclusive with 1a |
| **2** | Customer Churn Reduction | Unselected | Customer-facing agents only |
| **3** | Sales Increase from Better CX | Unselected | Customer-facing agents only |

- If user asks for Dims 2 or 3 without a customer name, prompt for it
- Do NOT auto-include Dims 2/3 — only for customer-facing agents

### 3. Customer Data Lookup (if customer name provided)

Search for: annual revenue, employees, customer base, churn rate, industry.

```
Search: "{customer_name} annual revenue employees headcount 2024 2025"
revenue_per_hour = annual_revenue / employees / 2000
```

- Be transparent — share what you found, note gaps, let user decide
- For Dims 2/3: also search for total customers, churn rate, annual sales revenue

### 4. Present Assumptions

Show all parameters and their values. Ask user to confirm before calculating:
- Sessions per month
- Agent cost (from prior pricing run or user-provided)
- Time without AI vs. time with AI
- Agent effectiveness % and efficiency factor %
- Human cost/hr and revenue/hr
- For Dim 2: total customers, churn rates, revenue per customer
- For Dim 3: annual sales revenue, sales increase %

### 5. Calculate Business Value

```python
result = calculate_business_value(
    sessions_per_month=1_000_000,
    agent_cost_monthly=44497,
    # Dim 1
    time_without_ai_min=20,
    time_with_ai_min=10,
    human_cost_per_hour=75,
    revenue_per_hour=300,
    # Dim 2 (set total_customers=0 to skip)
    total_customers=100_000,
    churn_without_ai_pct=2.0,
    churn_with_ai_pct=1.0,
    revenue_per_customer_year=1000,
    # Dim 3 (set annual_sales_revenue=0 to skip)
    annual_sales_revenue=100_000_000,
    sales_increase_pct=10.0,
)
```

### 6. Present Results

Structure the output as:
1. **Selected dimensions** — which ones were calculated
2. **Assumptions table** — all inputs with sources
3. **Per-dimension results** — show all 3 tiers (conservative/moderate/aggressive) for Dim 1
4. **Grand total** — combined value, net of agent cost, ROI %, payback days
5. **Research citations** — BCG, Harvard, Gartner references that support defaults
6. **Sensitivity note** — which parameters have the biggest impact

- Show annual projections — monthly looks small to stakeholders
- Auto-detect agent cost from prior pricing runs in the conversation

### 7. Offer Follow-ups

- Add more dimensions
- Adjust assumptions
- Different customer
- Switch between 1a and 1b

## Configuration

Business value defaults are managed by the YAML configuration system in `bedrock_pricing.py`.
Override any default via `~/.bedrock_skills/config.yaml` (user-level) or `./.bedrock_skills.yaml` (project-level).

Run `python3 bedrock_pricing.py --init-config` to generate a commented template showing all
available settings with their current defaults.

**Precedence:** function parameter > environment variable > project config > user config > hardcoded default

**Config values are defaults only.** If the user specifies a value in their prompt, always use
the user's value. Config defaults apply only to parameters the user has not mentioned.

See the `business_value_defaults` section in the config template for overridable settings:
`time_without_ai_min`, `time_with_ai_min`, `human_cost_per_hour`, `revenue_per_hour`,
`agent_effectiveness_pct`, `efficiency_factor_pct`, `churn_without_ai_pct`, `churn_with_ai_pct`,
`sales_increase_pct`.

### Research Sources

| Parameter | Source |
|-----------|--------|
| Time savings (30–50% acceleration) | BCG |
| Agent effectiveness (40% quality lift) | Harvard/BCG |
| Efficiency factor (reclaimed time utilization) | Gartner |
| Human cost/hr ($75 fully-loaded) | McKinsey/BCG |
| Revenue/hr (~$600K rev/employee fallback) | Industry benchmarks |
| Churn prediction (82% accuracy) | AI churn prediction research |
| Sales increase (15–20% in general trade) | BCG |

## Explanation Rendering

`result["explanation"]` contains:

| Section | What it shows |
|---------|---------------|
| `dim1_time_savings` | Hours saved, productive hours, value calculation |
| `dim2_churn_reduction` | Customers retained, revenue preserved (if Dim 2 selected) |
| `dim3_sales_increase` | Revenue uplift from better CX (if Dim 3 selected) |
| `summary` | Grand total, net value, ROI, payback period |

### Rules for rendering:
- Default: show summary with per-dimension totals and ROI
- On demand: format full explanation as markdown
- Always use markdown — never HTML artifacts or `<details>` tags
- Always show all 3 tiers for Dim 1 — gives stakeholders a range

## Related Skills

| Skill | When to load |
|-------|-------------|
| `bedrock-pricing` | Need model cost to feed into `agent_cost_monthly` |
| `agentcore-pricing` | Need infrastructure cost to feed into `agent_cost_monthly` |
| `bedrock-capacity` | Verify workload fits before building business case |
