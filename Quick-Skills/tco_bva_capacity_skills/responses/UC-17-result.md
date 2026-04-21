# UC-17 QA Verification Result

## Use Case
> "Calculate business value for an agent that costs $50,000/month. It handles 500K sessions/month. Manual time is 12 min, AI time is 2 min. Human cost is $85/hr. Show me cost savings, not productivity increase."

## Verification Method
Applied pricing_spec_v1.2.md §8 (Business Value Formulas) to the response's stated assumptions. All values independently computed using the spec's closed-form equations.

---

## Business Value — Dimension 1b (Cost Savings, Primary)

### Inputs Verified

| Parameter | Response | Expected | Status |
|-----------|:--------:|:--------:|:------:|
| sessions_per_month | 500,000 | 500,000 | ✅ |
| time_without_ai_min | 12 | 12 | ✅ |
| time_with_ai_min | 2 | 2 | ✅ |
| time_saved_min | 10 | 12 − 2 = 10 | ✅ |
| human_cost_per_hour | $85 | $85 | ✅ |
| agent_cost_monthly | $50,000 | $50,000 | ✅ |

### Conservative Tier (E=50%, F=50%)

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| effective_sessions | 250,000 | 500,000 × 0.50 = 250,000 | ✅ |
| productive_hrs/mo | 20,833 | 250,000 × 10 / 60 × 0.50 = 20,833.33 | ✅ |
| cost_savings_monthly | $1,770,833 | 20,833.33 × $85 = $1,770,833.33 | ✅ |
| cost_savings_annual | $21,250,000 | $1,770,833.33 × 12 = $21,250,000.00 | ✅ |

### Moderate Tier (E=65%, F=60%)

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| effective_sessions | 325,000 | 500,000 × 0.65 = 325,000 | ✅ |
| productive_hrs/mo | 32,500 | 325,000 × 10 / 60 × 0.60 = 32,500.00 | ✅ |
| cost_savings_monthly | $2,762,500 | 32,500.00 × $85 = $2,762,500.00 | ✅ |
| cost_savings_annual | $33,150,000 | $2,762,500.00 × 12 = $33,150,000.00 | ✅ |

### Optimistic Tier (E=80%, F=70%)

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| effective_sessions | 400,000 | 500,000 × 0.80 = 400,000 | ✅ |
| productive_hrs/mo | 46,667 | 400,000 × 10 / 60 × 0.70 = 46,666.67 | ✅ |
| cost_savings_monthly | $3,966,667 | 46,666.67 × $85 = $3,966,666.67 | ✅ |
| cost_savings_annual | $47,600,000 | $3,966,666.67 × 12 = $47,600,000.00 | ✅ |

---

## Business Value — Dimension 1a (Productivity, Alternative)

### Moderate Tier (E=65%, F=60%)

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| productive_hrs/mo | 32,500 | (same as 1b) | ✅ |
| productivity_monthly | $9,750,000 | 32,500 × $300 = $9,750,000.00 | ✅ |
| productivity_annual | $117,000,000 | $9,750,000 × 12 = $117,000,000.00 | ✅ |

---

## ROI Summary — Cost Savings Framing (Moderate)

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| grand_total_annual (1b) | $33,150,000 | $2,762,500 × 12 = $33,150,000 | ✅ |
| agent_cost_annual | $600,000 | $50,000 × 12 = $600,000 | ✅ |
| net_value | $32,550,000 | $33,150,000 − $600,000 = $32,550,000 | ✅ |
| roi_pct | 5,425% | ($32,550,000 / $600,000) × 100 = 5,425% | ✅ |
| payback_days | 6.6 | ($600,000 / $33,150,000) × 365 = 6.61 | ✅ |

## ROI Summary — Productivity Framing (Moderate)

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| grand_total_annual (1a) | $117,000,000 | $9,750,000 × 12 = $117,000,000 | ✅ |
| agent_cost_annual | $600,000 | $50,000 × 12 = $600,000 | ✅ |
| net_value | $116,400,000 | $117,000,000 − $600,000 = $116,400,000 | ✅ |
| roi_pct | 19,400% | ($116,400,000 / $600,000) × 100 = 19,400% | ✅ |
| payback_days | 1.9 | ($600,000 / $117,000,000) × 365 = 1.87 | ✅ |

---

## Dimensions 2 & 3

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| Dim 2 (Churn) | Skipped (total_customers=0) | Correctly skipped | ✅ |
| Dim 3 (Sales) | Skipped (annual_sales_revenue=0) | Correctly skipped | ✅ |

---

## Framing Verification

| Requirement | Status | Notes |
|-------------|:------:|-------|
| User asked for "cost savings, not productivity increase" | ✅ | Dim 1b presented as primary view |
| Dim 1a shown as alternative | ✅ | Included for reference, clearly labeled |
| 1a and 1b mutually exclusive (not added together) | ✅ | Correctly noted in response |
| All 3 tiers shown for Dim 1 | ✅ | Conservative, Moderate, Optimistic all present |
| Agent cost deducted once | ✅ | Single deduction in ROI summary |

---

## Overall Verdict

| Section | Result |
|---------|:------:|
| Dim 1b Cost Savings (Conservative) | ✅ PASS |
| Dim 1b Cost Savings (Moderate) | ✅ PASS |
| Dim 1b Cost Savings (Optimistic) | ✅ PASS |
| Dim 1a Productivity (Moderate) | ✅ PASS |
| ROI Summary (Cost Savings) | ✅ PASS |
| ROI Summary (Productivity) | ✅ PASS |
| Dimension Selection | ✅ PASS |
| Framing (1b primary, 1a alternative) | ✅ PASS |

### Summary
**22 of 22 fields pass.** All business value calculations match spec formulas exactly. The response correctly frames Dim 1b (cost savings) as the primary view per the user's request, with Dim 1a (productivity) shown as an alternative. Dims 2 and 3 correctly skipped (no customer/sales data provided). All three tiers computed and presented.
