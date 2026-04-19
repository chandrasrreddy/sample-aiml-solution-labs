---
name: agent-business-value
display_name: Agent Business Value
description: "Calculate business value of AI agents across three dimensions: (1) Time Savings → productivity increase or cost savings, (2) Customer Churn Reduction from better CX, (3) Sales Increase from better CX. Activate when the user asks about agent business value, ROI, time savings, productivity gains, cost justification, business case for agents, customer experience impact, churn reduction, or 'what's the value of this agent'. Works standalone or alongside bedrock-pricing / agentcore-pricing estimates. Part of a 4-skill family."
icon: "💎"
trigger: agent business value
depends-on: [bedrock-pricing, agentcore-pricing]
inputs:
  - name: customer_name
    description: "Customer name — triggers web lookup for revenue, headcount, customer base, churn. Strongly recommended for Dims 2 & 3."
    type: string
    required: false
  - name: sessions_per_month
    description: "Number of agent sessions per month."
    type: number
    required: true
tools: [run_python, web_search, url_fetch]
---

## Overview

Calculates business value of deploying an AI agent across up to three dimensions. Produces a Markdown summary with assumptions, calculations, research citations, and an HTML chart. Designed as the "so what?" layer on top of `bedrock-pricing` and `agentcore-pricing`.

## ⚠️ CALCULATION RULE

**ALWAYS use `calculate_business_value()` to produce estimates.** Fully parameterized — pass all values as arguments.

**NEVER implement business value formulas manually.**

Explanations are embedded directly in function return values via `result["explanation"]` — no separate skill needed.

### Load Script

```python
import sys, os
sys.argv = ['bedrock_pricing.py']
exec(open(os.path.expanduser("~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py")).read())
```

## Workflow

### Step 0: Gather Inputs & Dimension Selection
Present the dimension menu. Determine which dimensions apply:

| # | Dimension | Default | Notes |
|---|-----------|---------|-------|
| **1a** | ☑️ Productivity Increase (revenue uplift) | **Selected** | Mutually exclusive with 1b |
| **1b** | ☐ Cost Savings (labor cost reduction) | Available | Mutually exclusive with 1a |
| **2** | ☐ Customer Churn Reduction | Unselected | Customer-facing agents |
| **3** | ☐ Sales Increase from Better CX | Unselected | Customer-facing agents |

- 1a and 1b are **mutually exclusive** — same time savings, different framing
- 2 and 3 are **optional add-ons** — additive with Dim 1 (different value streams)
- Agent cost deducted **once** from grand total (not per dimension)
- If user asks for Dims 2/3 without a customer name, prompt for it

### Step 1: Customer Data Lookup (if customer_name provided)
Web search for: annual revenue, employees, customer base, churn rate, industry.

```
Search: "{customer_name} annual revenue employees headcount 2024 2025"
revenue_per_hour = annual_revenue / employees / 2000
```

For Dims 2/3: search for total customers, churn rate, annual sales revenue. Be transparent — share what you found, note gaps, let user decide.

### Step 2: Calculate

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
# Returns: dim1_cost_savings, dim1_productivity (all 3 tiers),
#          dim2, dim3, summary (grand_total, net_value, roi_pct, payback_days)
```

### Step 3: Present Results — Markdown Summary
Structure: Header → Selected dimensions → Assumptions table → Per-dimension results → Grand total with ROI → Research citations → Sensitivity note

### Step 4: Present Results — HTML Chart
Load `highcharts` and `html_design` skills. Show per-dimension contributions + agent cost.

### Step 5: Offer Follow-ups
Add more dimensions, adjust assumptions, different customer, switch 1a↔1b.

## Defaults & Sources

### Dimension 1: Time Savings
| Parameter | Default | Source |
|-----------|---------|--------|
| Time without AI | 20 min | BCG: 30–50% acceleration |
| Time with AI | 10 min | 50% reduction |
| Agent effectiveness | 65% (moderate) | Harvard/BCG: 40% quality lift |
| Efficiency factor | 60% (moderate) | Gartner: reclaimed time utilization |
| Human cost/hr | $75 | McKinsey/BCG fully-loaded range |
| Revenue/hr | $300 | ~$600K rev/employee fallback |

### Dimension 2: Churn Reduction
| Parameter | Default | Source |
|-----------|---------|--------|
| Churn without AI | 2% | SaaS/enterprise typical |
| Churn with AI | 1% | AI churn prediction 82% accuracy |
| Total customers | 100,000 | Ask user / web lookup |
| Revenue/customer/yr | $1,000 | Ask user / web lookup |

### Dimension 3: Sales Increase
| Parameter | Default | Source |
|-----------|---------|--------|
| Sales increase % | 10% | BCG: 15–20% in general trade |
| Annual sales revenue | $100M | Ask user / web lookup |

## Lessons Learned

### Do
- Present dimension menu upfront — not every dimension applies
- Always show all 3 tiers for Dim 1 — gives stakeholders a range
- Cite research (BCG, Harvard, Gartner) — makes defaults defensible
- Auto-detect agent cost from prior pricing runs in conversation
- Show annual projections — monthly looks small
- Be transparent about web lookup results

### Don't
- Don't auto-include Dims 2/3 — only for customer-facing agents
- Don't add 1a + 1b — they're mutually exclusive
- Don't fabricate customer data — if lookup fails, say so
- Don't skip assumptions table — transparency builds trust

### When to Ask
- Sessions per month (required)
- Which dimensions apply (default: 1a only)
- Customer name (encourage for Dims 2/3)
- Churn rates / customer count if web lookup fails
