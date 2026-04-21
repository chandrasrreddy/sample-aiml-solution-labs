# UC-17: Cost Savings Framing — Business Value Analysis

> **Use Case:** "Calculate business value for an agent that costs $50,000/month. It handles 500K sessions/month. Manual time is 12 min, AI time is 2 min. Human cost is $85/hr. Show me cost savings, not productivity increase."

---

## 1. Assumptions

### Business Value Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Sessions/month | 500,000 | User provided |
| Agent cost (monthly) | $50,000 | User provided |
| Time without AI | 12 min | User provided |
| Time with AI | 2 min | User provided |
| Time saved per session | 10 min | Calculated |
| Human cost/hr | $85 | User provided (fully loaded) |
| Revenue/hr | $300 | Default (computed but not primary) |
| Dimensions selected | **1b (Cost Savings)** | User requested "cost savings, not productivity increase" |

### Business Value Tiers

| Tier | Effectiveness (E) | Efficiency (F) | Source |
|------|:-----------------:|:--------------:|--------|
| Conservative | 50% | 50% | BCG/Harvard lower bound |
| Moderate | 65% | 60% | BCG/Harvard midpoint |
| Optimistic | 80% | 70% | BCG/Harvard upper bound |

> **Effectiveness** = % of sessions where AI meaningfully helps (not all sessions benefit equally)
> **Efficiency** = % of reclaimed time that converts to productive work (Gartner: not all saved time is utilized)

---

## 2. Primary View: Dimension 1b — Cost Savings

This is the framing you asked for: how much labor cost does the AI agent eliminate?

### All Three Tiers

| Tier | Effective Sessions | Productive Hours/mo | Cost Savings/mo | Cost Savings/yr |
|------|-------------------:|--------------------:|----------------:|----------------:|
| **Conservative** | 250,000 | 20,833 | **$1,770,833** | **$21,250,000** |
| **Moderate** | 325,000 | 32,500 | **$2,762,500** | **$33,150,000** |
| **Optimistic** | 400,000 | 46,667 | **$3,966,667** | **$47,600,000** |

### Moderate Tier Walkthrough

```
Time saved       = 12 min − 2 min = 10 min/session
Effective sessions = 500,000 × 65% = 325,000
Time saved (hrs) = 325,000 × 10 min ÷ 60 = 54,167 hrs
Productive hours = 54,167 × 60% efficiency = 32,500 hrs/mo
Cost savings     = 32,500 hrs × $85/hr = $2,762,500/mo
```

### ROI Summary (Cost Savings Framing, Moderate)

| Metric | Value |
|--------|------:|
| Annual cost savings | $33,150,000 |
| Agent cost (annual) | $600,000 |
| **Net value** | **$32,550,000/yr** |
| **ROI** | **5,425%** |
| **Payback period** | **6.6 days** |

---

## 3. Alternative View: Dimension 1a — Productivity Increase

For reference, here's the same time savings framed as revenue uplift (using $300/hr revenue per productive hour):

| Tier | Productive Hours/mo | Productivity Value/mo | Productivity Value/yr |
|------|--------------------:|----------------------:|----------------------:|
| Conservative | 20,833 | $6,250,000 | $75,000,000 |
| Moderate | 32,500 | $9,750,000 | $117,000,000 |
| Optimistic | 46,667 | $14,000,000 | $168,000,000 |

### ROI Summary (Productivity Framing, Moderate)

| Metric | Value |
|--------|------:|
| Annual productivity value | $117,000,000 |
| Agent cost (annual) | $600,000 |
| Net value | $116,400,000/yr |
| ROI | 19,400% |
| Payback period | 1.9 days |

> **Note:** Dims 1a and 1b are mutually exclusive — they represent the same time savings, just framed differently. Cost savings ($85/hr) is the more conservative, defensible metric. Productivity uplift ($300/hr) captures the revenue potential of reclaimed time.

---

## 4. Human Equivalent (Informational)

| Metric | Value |
|--------|------:|
| Total manual hours replaced | 100,000 hrs/mo |
| FTE equivalent | 625 FTEs |
| Human cost equivalent | $8,500,000/mo |

This agent handles the equivalent workload of ~625 full-time employees at $85/hr.

---

## 5. Dimensions Not Included

| Dimension | Status | Reason |
|-----------|--------|--------|
| Dim 2: Customer Churn Reduction | ⏭️ Skipped | No customer base data provided (total_customers=0) |
| Dim 3: Sales Increase from Better CX | ⏭️ Skipped | No annual sales revenue provided (annual_sales_revenue=0) |

---

## 6. Step-by-Step Calculation Explanations

### Time Savings (All Tiers)

**Conservative (E=50%, F=50%):**
```
effective_sessions = 500,000 × 0.50 = 250,000
time_saved_hrs = 250,000 × 10 min ÷ 60 = 41,667 hrs
productive_hrs = 41,667 × 0.50 = 20,833 hrs/mo
cost_savings = 20,833 × $85 = $1,770,833/mo → $21,250,000/yr
```

**Moderate (E=65%, F=60%):**
```
effective_sessions = 500,000 × 0.65 = 325,000
time_saved_hrs = 325,000 × 10 min ÷ 60 = 54,167 hrs
productive_hrs = 54,167 × 0.60 = 32,500 hrs/mo
cost_savings = 32,500 × $85 = $2,762,500/mo → $33,150,000/yr
```

**Optimistic (E=80%, F=70%):**
```
effective_sessions = 500,000 × 0.80 = 400,000
time_saved_hrs = 400,000 × 10 min ÷ 60 = 66,667 hrs
productive_hrs = 66,667 × 0.70 = 46,667 hrs/mo
cost_savings = 46,667 × $85 = $3,966,667/mo → $47,600,000/yr
```

### ROI (Cost Savings, Moderate)
```
grand_total_annual = $33,150,000
agent_cost_annual = $50,000 × 12 = $600,000
net_value = $33,150,000 − $600,000 = $32,550,000
roi_pct = ($32,550,000 / $600,000) × 100 = 5,425%
payback_days = ($600,000 / $33,150,000) × 365 = 6.6 days
```

---

## 7. Research Citations

| Claim | Source |
|-------|--------|
| 30–50% task acceleration with AI | BCG × Harvard (2023): "How People Create—and Destroy—Value with Generative AI" |
| 40% quality improvement | Harvard Business School (2023): AI-assisted consultants study |
| Reclaimed time utilization 50–70% | Gartner (2024): "Not all saved time converts to productive output" |
| Effectiveness/efficiency tiers | Composite of BCG, Harvard, Gartner research |

---

## 8. Sensitivity Note

These estimates are sensitive to the effectiveness and efficiency assumptions. The three-tier range gives stakeholders a realistic band:
- **Conservative** ($21.3M/yr): Assumes only half of sessions benefit and half of saved time is utilized
- **Moderate** ($33.2M/yr): The recommended planning figure
- **Optimistic** ($47.6M/yr): Upper bound if adoption and utilization are high

The agent cost of $600K/yr is a small fraction of even the conservative estimate, making this a high-confidence investment.
