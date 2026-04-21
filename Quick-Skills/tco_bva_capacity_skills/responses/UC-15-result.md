# UC-15 QA Verification Result

## Use Case
> "I have 20M questions per month on Claude Sonnet 4.6 in us-east-1. 5 tools per question, peak-to-average ratio of 4x, 16 active hours per day, 30 days per month. Does this fit in Standard tier? What about Priority? Use output burndown rate of 5."

## Verification Method
Applied pricing_spec_v1.2.md formulas (§6 Capacity Planning) to the response's stated assumptions. Also verified model cost (§2–4) independently.

---

## Token Profile

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| cacheable_base | 5,000 | 1,000 + 4,000 = 5,000 | ✅ |
| rag_tokens | 3,000 | 10 × 300 = 3,000 | ✅ |
| base_prompt | 8,100 | 5,000 + 100 + 3,000 = 8,100 | ✅ |
| delta | 600 | 100 + 500 = 600 | ✅ |
| turns | 6 | 5 + 1 = 6 | ✅ |
| output_per_question | 600 | 100 + 5 × 100 = 600 | ✅ |
| total_input_per_question | 57,600 | 6 × 8,100 + 600 × 5 × 6/2 = 48,600 + 9,000 = 57,600 | ✅ |

## Capacity Check — RPM

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| active_minutes_per_month | 28,800 | 16 × 60 × 30 = 28,800 | ✅ |
| avg_questions_per_min | 694.44 | 20,000,000 / 28,800 = 694.4444... | ✅ |
| avg_rpm | 4,166.67 | 694.44 × 6 = 4,166.67 | ✅ |
| peak_rpm | 16,667 | 4,166.67 × 4.0 = 16,666.67 | ✅ |
| rpm_limit | 10,000 | query_quotas() → 10,000 (Global) | ✅ |
| rpm_fits | ❌ No | 16,667 > 10,000 → False | ✅ |
| rpm_utilization | 166.7% | 16,667 / 10,000 × 100 = 166.7% | ✅ |

## Capacity Check — TPM

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| base_context | 8,100 | 100 + 1,000 + 4,000 + 3,000 = 8,100 | ✅ |
| avg_input_per_turn | 9,600 | 8,100 + (600/2) × 5 = 8,100 + 1,500 = 9,600 | ✅ |
| avg_output_per_turn | 100 | (5 × 100 + 100) / 6 = 600/6 = 100 | ✅ |
| avg_tpm | 42,083,333 | 4,166.67 × (9,600 + 100 × 5) = 4,166.67 × 10,100 = 42,083,337 ≈ 42,083,333 | ✅ |
| peak_tpm | 168,333,333 | 42,083,333 × 4.0 = 168,333,332 ≈ 168,333,333 | ✅ |
| max_tokens_overhead | 3,996 | max(0, 4,096 − 100) = 3,996 | ✅ |
| effective_peak_tpm | 234,933,333 | 168,333,333 + (16,667 × 3,996) = 168,333,333 + 66,601,332 = 234,934,665 | ⚠️ |
| tpm_limit | 6,000,000 | query_quotas() → 6,000,000 (Global) | ✅ |
| tpm_fits | ❌ No | 234,933,333 > 6,000,000 → False | ✅ |
| tpm_utilization | 3,915.6% | 234,933,333 / 6,000,000 × 100 = 3,915.6% | ✅ |

> **Note on effective_peak_tpm:** The response shows 234,933,333. The spec formula gives 168,333,333 + (16,666.67 × 3,996) = 168,333,333 + 66,599,865 = 234,933,198. The difference (~135) is due to floating-point rounding in peak_rpm (16,666.67 vs 16,667). The code uses integer truncation for avg_output_per_turn. This is within 0.001% — well within the 0.1% tolerance.

## Model Cost

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| questions_per_month | 20,000,000 | 4,000,000 × 5 = 20,000,000 | ✅ |
| total_input_per_question | 57,600 | Σ(i=0..5)[8,100 + i×600] = 8,100+8,700+9,300+9,900+10,500+11,100 = 57,600 | ✅ |
| total_output_per_question | 600 | 100 + 5 × 100 = 600 | ✅ |
| monthly_input_tokens | 1,152,000,000,000 | 57,600 × 20,000,000 = 1,152,000,000,000 | ✅ |
| monthly_output_tokens | 12,000,000,000 | 600 × 20,000,000 = 12,000,000,000 | ✅ |
| no_cache_input_cost | $3,456,000.00 | 1,152,000M × $3.00/M = $3,456,000.00 | ✅ |
| no_cache_output_cost | $180,000.00 | 12,000M × $15.00/M = $180,000.00 | ✅ |
| no_cache_total | $3,636,000.00 | $3,456,000 + $180,000 = $3,636,000.00 | ✅ |
| with_cache_total | $1,006,500.00 | See cache split verification below | ✅ |
| savings_pct | 72.3% | ($3,636,000 − $1,006,500) / $3,636,000 × 100 = 72.3% | ✅ |

## Cache Splits

### Q1 (N=5, first question in session)

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| q1_cache_write | — | base_prompt + (N−1) × delta = 8,100 + 4 × 600 = 10,500 | ✅ |
| q1_cache_read | — | Σ(k=1..5)[8,100 + (k−1)×600] = 8,100+8,700+9,300+9,900+10,500 = 46,500 | ✅ |
| q1_regular | — | delta = 600 | ✅ |
| q1_sum | — | 10,500 + 46,500 + 600 = 57,600 = total_input_per_question ✓ | ✅ |

### Q2+ (subsequent questions)

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| q2_cache_write | — | (100 + 3,000) + (5−1) × 600 = 3,100 + 2,400 = 5,500 | ✅ |
| q2_cache_read | — | 5,000 + Σ(k=1..5)[8,100 + (k−1)×600] = 5,000 + 46,500 = 51,500 | ✅ |
| q2_regular | — | 600 | ✅ |
| q2_sum | — | 5,500 + 51,500 + 600 = 57,600 = total_input_per_question ✓ | ✅ |

### Session Totals (5 Q/session)

| Field | Spec Calculation | Status |
|-------|:----------------:|:------:|
| session_cw | 10,500 + 4 × 5,500 = 10,500 + 22,000 = 32,500 | ✅ |
| session_cr | 46,500 + 4 × 51,500 = 46,500 + 206,000 = 252,500 | ✅ |
| session_reg | 600 + 4 × 600 = 3,000 | ✅ |
| session_sum | 32,500 + 252,500 + 3,000 = 288,000 = 5 × 57,600 ✓ | ✅ |

### Monthly Token Volumes

| Field | Spec Calculation | Status |
|-------|:----------------:|:------:|
| monthly_cw | 4,000,000 × 32,500 = 130,000,000,000 | ✅ |
| monthly_cr | 4,000,000 × 252,500 = 1,010,000,000,000 | ✅ |
| monthly_reg | 4,000,000 × 3,000 = 12,000,000,000 | ✅ |
| monthly_output | 4,000,000 × 3,000 = 12,000,000,000 | ✅ |

### Monthly Costs (With Cache)

| Field | Spec Calculation | Response | Status |
|-------|:----------------:|:--------:|:------:|
| cache_write_cost | 130,000M × $3.75/M = $487,500.00 | $487,500.00 | ✅ |
| cache_read_cost | 1,010,000M × $0.30/M = $303,000.00 | $303,000.00 | ✅ |
| regular_input_cost | 12,000M × $3.00/M = $36,000.00 | $36,000.00 | ✅ |
| output_cost | 12,000M × $15.00/M = $180,000.00 | $180,000.00 | ✅ |
| **total_with_cache** | **$1,006,500.00** | **$1,006,500.00** | ✅ |

**Reconciliation:** $487,500 + $303,000 + $36,000 + $180,000 = $1,006,500 ✓

---

## Overall Verdict

| Section | Result |
|---------|:------:|
| Token Profile | ✅ PASS (7/7) |
| Capacity — RPM | ✅ PASS (7/7) |
| Capacity — TPM | ✅ PASS (10/10, effective_peak_tpm within 0.001%) |
| Model Cost — Totals | ✅ PASS (10/10) |
| Cache Splits — Identity | ✅ PASS (all sum identities hold) |
| Cache Splits — Costs | ✅ PASS (4/4 components match) |
| Standard Tier Verdict | ✅ PASS (correctly identifies ❌ doesn't fit) |
| Priority Tier Verdict | ✅ PASS (correctly notes same quotas, ❌ doesn't fit) |
| Non-default params used | ✅ PASS (4.0× peak, 16h, 30d all applied correctly) |

### Summary

**38 of 38 fields pass.** All capacity calculations use the non-default traffic profile parameters correctly (4.0× peak ratio, 16 active hours, 30 active days). The key finding — active_minutes_per_month = 28,800 (vs default 15,840) — is correctly computed and propagated through all RPM/TPM calculations. Both Standard and Priority tiers correctly identified as insufficient at default quotas. The workload requires ~39× the default TPM quota.

### Key Verification Points for UC-15

1. **Non-default active_minutes_per_month**: 16 × 60 × 30 = 28,800 (not default 12 × 60 × 22 = 15,840) ✅
2. **Non-default peak_to_avg_ratio**: 4.0× applied to both RPM and TPM ✅
3. **Output burndown rate**: 5× applied to avg_output_per_turn in TPM calculation ✅
4. **avg_output_per_turn**: Integer division (5 × 100 + 100) // 6 = 100 ✅
5. **max_tokens overhead**: 4,096 − 100 = 3,996 correctly computed ✅
6. **effective_peak_tpm**: Includes both peak_tpm AND max_tokens overhead ✅
7. **Model cost**: $1,006,500/mo with caching, $3,636,000/mo without — 72.3% savings ✅
