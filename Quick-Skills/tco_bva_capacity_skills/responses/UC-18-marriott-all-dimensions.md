# UC-18: Marriott — All Three Dimensions Business Value Analysis

> **Use Case:** "Calculate business value for Marriott. 2M sessions/month, agent cost $320K/month. Time without AI 12 min, with AI 3 min, human cost $35/hr, revenue per hour $59. Also: 210M loyalty members, churn 1.5% without AI, 1.2% with AI, $120 revenue per member per year. Annual sales revenue $23.7B, expect 2% increase from better CX."

---

## 1. Assumptions

### Business Value Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Sessions/month | 2,000,000 | User-provided |
| Agent cost/month | $320,000 | User-provided |
| Time without AI | 12 min | User-provided |
| Time with AI | 3 min | User-provided |
| Time saved | 9 min | Calculated |
| Human cost/hr | $35 | User-provided |
| Revenue/hr | $59 | User-provided |
| Total loyalty members | 210,000,000 | User-provided |
| Churn without AI | 1.5% | User-provided |
| Churn with AI | 1.2% | User-provided |
| Revenue/member/year | $120 | User-provided |
| Annual sales revenue | $23,700,000,000 | User-provided |
| Sales increase % | 2.0% | User-provided |

### Business Value Tiers (Dim 1 only)

| Tier | Effectiveness (E) | Efficiency (F) |
|------|:-----------------:|:--------------:|
| Conservative | 50% | 50% |
| Moderate | 65% | 60% |
| Optimistic | 80% | 70% |

---

## 2. Dimension 1a — Productivity Increase (Revenue Uplift)

| Metric | Conservative | Moderate | Optimistic |
|--------|:-----------:|:--------:|:----------:|
| Effective sessions | 1,000,000 | 1,300,000 | 1,600,000 |
| Time saved (hrs/mo) | 150,000 | 195,000 | 240,000 |
| Productive hours/mo | 75,000 | 117,000 | 168,000 |
| **Monthly value** | **$4,425,000** | **$6,903,000** | **$9,912,000** |
| **Annual value** | **$53,100,000** | **$82,836,000** | **$118,944,000** |

### Dimension 1b — Cost Savings (Alternative Framing)

| Metric | Conservative | Moderate | Optimistic |
|--------|:-----------:|:--------:|:----------:|
| Productive hours/mo | 75,000 | 117,000 | 168,000 |
| **Monthly savings** | **$2,625,000** | **$4,095,000** | **$5,880,000** |
| **Annual savings** | **$31,500,000** | **$49,140,000** | **$70,560,000** |

> Note: Dim 1a and 1b are mutually exclusive — same time savings, different framing. Summary uses Dim 1a (productivity).

---

## 3. Dimension 2 — Customer Churn Reduction

| Metric | Value |
|--------|------:|
| Churn reduction | 1.5% − 1.2% = 0.3 pp |
| Customers retained | 210,000,000 × 0.3% = **630,000** |
| Revenue per member/year | $120 |
| **Annual value** | **$75,600,000** |

---

## 4. Dimension 3 — Sales Increase from Better CX

| Metric | Value |
|--------|------:|
| Annual sales revenue | $23,700,000,000 |
| AI-driven sales increase | 2.0% |
| **Annual value** | **$474,000,000** |

---

## 5. Grand Total & ROI Summary

| Metric | Annual Value |
|--------|------------:|
| Dim 1a (Moderate — Productivity) | $82,836,000 |
| Dim 2 (Churn Reduction) | $75,600,000 |
| Dim 3 (Sales Increase) | $474,000,000 |
| **Gross Business Value** | **$632,436,000** |
| Agent Cost ($320K/mo × 12) | ($3,840,000) |
| **Net Business Value** | **$628,596,000** |
| **ROI** | **16,370%** |
| **Payback Period** | **~2 days** |

---

## 6. Step-by-Step Calculation Explanations

### Dim 1: Time Savings (Moderate Tier)

```
time_saved = 12 min − 3 min = 9 min/session
effective_sessions = 2,000,000 × 65% = 1,300,000
time_saved_hrs = 1,300,000 × 9 / 60 = 195,000 hrs/month
productive_hrs = 195,000 × 60% = 117,000 hrs/month

Productivity (1a): 117,000 × $59/hr = $6,903,000/mo → $82,836,000/yr
Cost savings (1b): 117,000 × $35/hr = $4,095,000/mo → $49,140,000/yr
```

### Dim 2: Churn Reduction

```
churn_reduction = 1.5% − 1.2% = 0.3 pp
customers_retained = 210,000,000 × (0.3 / 100) = 630,000
dim2_annual = 630,000 × $120 = $75,600,000/yr
```

### Dim 3: Sales Increase

```
dim3_annual = $23,700,000,000 × 2.0% = $474,000,000/yr
```

### Summary

```
grand_total = $82,836,000 + $75,600,000 + $474,000,000 = $632,436,000/yr
agent_cost_annual = $320,000 × 12 = $3,840,000/yr
net_value = $632,436,000 − $3,840,000 = $628,596,000/yr
roi = ($628,596,000 / $3,840,000) × 100 = 16,370%
payback = ($3,840,000 / $632,436,000) × 365 = 2.2 days
```

---

## 7. Key Observations

1. **Dim 3 dominates**: At $474M/yr, the 2% sales increase on $23.7B revenue dwarfs the other dimensions. This is typical for large-revenue enterprises — even small CX-driven sales lifts produce massive absolute numbers.

2. **Dim 2 is significant**: 210M loyalty members × 0.3pp churn reduction = 630,000 retained members generating $75.6M/yr. The large customer base amplifies even a small churn improvement.

3. **Dim 1 is the most conservative**: At $82.8M/yr (Moderate), productivity gains from 2M sessions are substantial but represent only 13% of total value.

4. **Agent cost is negligible**: $3.84M/yr against $632M in value — the ROI is astronomical (16,370%) with a ~2-day payback.

5. **Sensitivity note**: These are modeled estimates. Actual results depend on AI adoption rates, true churn causality, and CX-to-sales conversion. The Dim 3 figure ($474M) assumes a direct causal link between AI-improved CX and sales — stakeholders should validate this assumption.
