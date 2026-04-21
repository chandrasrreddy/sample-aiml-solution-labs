# UC-16 QA Verification Result

## Use Case
> "Will 10K sessions per month with 2 questions per session fit in Flex tier for Nova Pro in us-west-2? 3 tools per question."

## Verification Method
Applied pricing_spec_v1.2.md formulas to the response's stated assumptions.

---

## Token Profile

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| cacheable_base | 5,000 | 1,000 + 4,000 = 5,000 | ✅ |
| rag_tokens | 3,000 | 10 × 300 = 3,000 | ✅ |
| base_prompt | 8,100 | 5,000 + 100 + 3,000 = 8,100 | ✅ |
| delta | 600 | 100 + 500 = 600 | ✅ |
| turns | 4 | 3 + 1 = 4 | ✅ |
| output_per_question | 400 | 100 + 3 × 100 = 400 | ✅ |
| total_input_per_question | 36,000 | 4 × 8,100 + 600 × 3 × 4/2 = 32,400 + 3,600 = 36,000 | ✅ |

## Cache Splits

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| q1_cache_write | 9,300 | 8,100 + (3-1) × 600 = 8,100 + 1,200 = 9,300 | ✅ |
| q1_cache_read | 26,100 | Σ(k=1 to 3)[8,100 + (k-1)×600] = 8,100 + 8,700 + 9,300 = 26,100 | ✅ |
| q1_regular | 600 | delta = 600 | ✅ |
| q1_sum | 36,000 | 9,300 + 26,100 + 600 = 36,000 ✓ | ✅ |
| q2_cache_write | 4,300 | (100 + 3,000) + (3-1) × 600 = 3,100 + 1,200 = 4,300 | ✅ |
| q2_cache_read | 31,100 | 5,000 + Σ(k=1 to 3)[8,100 + (k-1)×600] = 5,000 + 26,100 = 31,100 | ✅ |
| q2_regular | 600 | delta = 600 | ✅ |
| q2_sum | 36,000 | 4,300 + 31,100 + 600 = 36,000 ✓ | ✅ |
| session_cw | 13,600 | 9,300 + 1 × 4,300 = 13,600 | ✅ |
| session_cr | 57,200 | 26,100 + 1 × 31,100 = 57,200 | ✅ |
| session_reg | 1,200 | 600 + 1 × 600 = 1,200 | ✅ |
| session_sum | 72,000 | 13,600 + 57,200 + 1,200 = 72,000 = 2 × 36,000 ✓ | ✅ |

## Model Cost

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| monthly_cache_write_tokens | 136,000,000 | 10,000 × 13,600 = 136,000,000 | ✅ |
| monthly_cache_read_tokens | 572,000,000 | 10,000 × 57,200 = 572,000,000 | ✅ |
| monthly_regular_tokens | 12,000,000 | 10,000 × 1,200 = 12,000,000 | ✅ |
| monthly_output_tokens | 8,000,000 | 10,000 × 800 = 8,000,000 | ✅ |
| cache_write_cost | $0.00 | 136M / 1M × $0.00 = $0.00 | ✅ |
| cache_read_cost | $57.20 | 572M / 1M × $0.10 = $57.20 | ✅ |
| regular_input_cost | $4.80 | 12M / 1M × $0.40 = $4.80 | ✅ |
| output_cost | $12.80 | 8M / 1M × $1.60 = $12.80 | ✅ |
| total_with_cache | $74.80 | $0.00 + $57.20 + $4.80 + $12.80 = $74.80 | ✅ |
| total_annual | $897.60 | $74.80 × 12 = $897.60 | ✅ |
| no_cache_input | $288.00 | 20,000 × 36,000 / 1M × $0.40 = $288.00 | ✅ |
| no_cache_output | $12.80 | 20,000 × 400 / 1M × $1.60 = $12.80 | ✅ |
| no_cache_total | $300.80 | $288.00 + $12.80 = $300.80 | ✅ |
| savings_monthly | $226.00 | $300.80 - $74.80 = $226.00 | ✅ |
| savings_pct | 75.1% | $226.00 / $300.80 × 100 = 75.1% | ✅ |
| per_question | $0.0037 | $74.80 / 20,000 = $0.00374 | ✅ |
| per_session | $0.0075 | $74.80 / 10,000 = $0.00748 | ✅ |

## Capacity Check

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| active_minutes_per_month | 15,840 | 12 × 60 × 22 = 15,840 | ✅ |
| avg_questions_per_min | 1.26 | 20,000 / 15,840 = 1.2626 | ✅ |
| avg_rpm | 5.05 | 1.2626 × 4 = 5.0505 | ✅ |
| peak_rpm | 15.15 | 5.0505 × 3.0 = 15.1515 | ✅ |
| base_context | 8,100 | 100 + 1,000 + 4,000 + 3,000 = 8,100 | ✅ |
| avg_input_per_turn | 9,000 | 8,100 + (600/2) × 3 = 9,000 | ✅ |
| avg_output_per_turn | 100 | (3 × 100 + 100) / 4 = 100 | ✅ |
| output_burndown_rate | 1 | Nova Pro (not Claude) = 1× | ✅ |
| avg_tpm | 45,960 | 5.0505 × (9,000 + 100 × 1) = 45,960 | ✅ |
| peak_tpm | 137,879 | 45,960 × 3.0 = 137,879 | ✅ |
| max_tokens_overhead | 3,996 | max(0, 4,096 - 100) = 3,996 | ✅ |
| effective_peak_tpm | 198,424 | 137,879 + (15.15 × 3,996) = 198,424 | ✅ |
| rpm_fits | ✅ | 15.15 ≤ 500 → True | ✅ |
| tpm_fits | ✅ | 198,424 ≤ 2,000,000 → True | ✅ |
| fits | ✅ | True AND True → True | ✅ |
| rpm_utilization | 3.0% | 15.15 / 500 × 100 = 3.03% | ✅ |
| tpm_utilization | 9.9% | 198,424 / 2,000,000 × 100 = 9.92% | ✅ |

---

## Overall Verdict

| Section | Result |
|---------|:------:|
| Token Profile | ✅ PASS (7/7) |
| Cache Splits | ✅ PASS (12/12) |
| Model Cost | ✅ PASS (17/17) |
| Capacity Check | ✅ PASS (17/17) |

### Summary
**53 of 53 fields pass.** All token counts, cache splits, cost calculations, and capacity check values match the spec formulas exactly. The workload easily fits in Flex tier with only 3% RPM and 10% TPM utilization.

### Notes
- Nova Pro has free cache writes ($0.00/M), which maximizes caching savings to 75.1%.
- Output burndown rate correctly set to 1× for Nova Pro (not Claude's 5×).
- Flex-specific quotas not available in cache; used cross-region on-demand defaults (500 RPM / 2M TPM).
- This is a very low-volume workload — massive headroom in all dimensions.
