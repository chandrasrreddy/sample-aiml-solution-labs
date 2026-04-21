# UC-23 QA Verification Result

## Use Case
> "What's the cost of running an AI agent on Bedrock?"

## Verification Method
Applied pricing_spec_v1.2.md formulas to the response's stated assumptions. All calculations independently reproduced using the spec's closed-form and loop-based formulas.

---

## Assumptions Verified

| Assumption | Applied | Matches Vague UC Rules |
|-----------|---------|:---------------------:|
| Model = Claude Sonnet 4.6 | ✅ | Per "Minimal information" default |
| Region = us-east-1 | ✅ | Per "No region specified" default |
| Sessions = 500,000 | ✅ | Per "Minimal information" default |
| Q/session = 3 | ✅ | Per "Minimal information" default |
| Tools = 3 | ✅ | Per "Minimal information" default |
| Token profile = standard | ✅ | Per "Minimal information" default |

---

## Token Profile

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| rag_tokens | 3,000 | 10 × 300 = 3,000 | ✅ |
| cacheable_base | 5,000 | 1,000 + 4,000 = 5,000 | ✅ |
| base_prompt | 8,100 | 5,000 + 100 + 3,000 = 8,100 | ✅ |
| delta | 600 | 100 + 500 = 600 | ✅ |
| turns | 4 | 3 + 1 = 4 | ✅ |
| total_input_per_question | 36,000 | 8,100 + 8,700 + 9,300 + 9,900 = 36,000 | ✅ |
| total_input (closed-form) | 36,000 | 4 × 8,100 + 600 × 3 × 4/2 = 36,000 | ✅ |
| total_output_per_question | 400 | 100 + 3 × 100 = 400 | ✅ |

---

## Model Cost

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| questions_per_month | 1,500,000 | 500,000 × 3 = 1,500,000 | ✅ |
| monthly_input_tokens | 54,000,000,000 | 36,000 × 1,500,000 = 54,000,000,000 | ✅ |
| monthly_output_tokens | 600,000,000 | 400 × 1,500,000 = 600,000,000 | ✅ |
| no_cache_input_cost | $162,000.00 | (54B / 1M) × $3.00 = $162,000.00 | ✅ |
| no_cache_output_cost | $9,000.00 | (600M / 1M) × $15.00 = $9,000.00 | ✅ |
| no_cache_total | $171,000.00 | $162,000 + $9,000 = $171,000.00 | ✅ |

---

## Cache Splits

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| q1_cache_write | 9,300 | 8,100 + (3-1) × 600 = 9,300 | ✅ |
| q1_cache_read | 26,100 | Σ(k=1→3)[8,100 + (k-1)×600] = 8,100 + 8,700 + 9,300 = 26,100 | ✅ |
| q1_regular | 600 | delta = 600 | ✅ |
| q1_sum | 36,000 | 9,300 + 26,100 + 600 = 36,000 ✓ | ✅ |
| q2_cache_write | 4,300 | (100 + 3,000) + (3-1) × 600 = 4,300 | ✅ |
| q2_cache_read | 31,100 | 5,000 + 8,100 + 8,700 + 9,300 = 31,100 | ✅ |
| q2_regular | 600 | delta = 600 | ✅ |
| q2_sum | 36,000 | 4,300 + 31,100 + 600 = 36,000 ✓ | ✅ |
| session_cw | 17,900 | 9,300 + 2 × 4,300 = 17,900 | ✅ |
| session_cr | 88,300 | 26,100 + 2 × 31,100 = 88,300 | ✅ |
| session_reg | 1,800 | 600 + 2 × 600 = 1,800 | ✅ |
| session_sum | 108,000 | 17,900 + 88,300 + 1,800 = 108,000 = 3 × 36,000 ✓ | ✅ |
| monthly_cw | 8,950,000,000 | 500,000 × 17,900 = 8,950,000,000 | ✅ |
| monthly_cr | 44,150,000,000 | 500,000 × 88,300 = 44,150,000,000 | ✅ |
| monthly_reg | 900,000,000 | 500,000 × 1,800 = 900,000,000 | ✅ |

---

## Cache Costs

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| cache_write_cost | $33,562.50 | (8,950M / 1M) × $3.75 = $33,562.50 | ✅ |
| cache_read_cost | $13,245.00 | (44,150M / 1M) × $0.30 = $13,245.00 | ✅ |
| regular_input_cost | $2,700.00 | (900M / 1M) × $3.00 = $2,700.00 | ✅ |
| output_cost | $9,000.00 | (600M / 1M) × $15.00 = $9,000.00 | ✅ |
| total_model_cost | $58,507.50 | $33,562.50 + $13,245.00 + $2,700.00 + $9,000.00 = $58,507.50 | ✅ |
| savings_monthly | $112,492.50 | $171,000.00 - $58,507.50 = $112,492.50 | ✅ |
| savings_pct | 65.8% | $112,492.50 / $171,000.00 × 100 = 65.8% | ✅ |

---

## Per-Unit Costs

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| per_session | $0.1170 | $58,507.50 / 500,000 = $0.1170 | ✅ |
| per_question | $0.0390 | $58,507.50 / 1,500,000 = $0.0390 | ✅ |
| total_annual | $702,090.00 | $58,507.50 × 12 = $702,090.00 | ✅ |

---

## Capacity Check

| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| active_minutes/month | 15,840 | 12 × 60 × 22 = 15,840 | ✅ |
| avg_questions/min | 94.70 | 1,500,000 / 15,840 = 94.70 | ✅ |
| avg_rpm | 378.79 | 94.70 × 4 = 378.79 | ✅ |
| peak_rpm | 1,136.36 | 378.79 × 3.0 = 1,136.36 | ✅ |
| base_context | 8,100 | 100 + 1,000 + 4,000 + 3,000 = 8,100 | ✅ |
| avg_input/turn | 9,000 | 8,100 + (600/2) × 3 = 9,000 | ✅ |
| avg_output/turn | 100.00 | (3 × 100 + 100) / 4 = 100.00 | ✅ |
| avg_tpm | 3,598,485 | 378.79 × (9,000 + 100 × 5) = 3,598,485 | ✅ |
| peak_tpm | 10,795,455 | 3,598,485 × 3.0 = 10,795,455 | ✅ |
| max_tokens_overhead | 3,996 | max(0, 4,096 - 100) = 3,996 | ✅ |
| effective_peak_tpm | 15,336,364 | 10,795,455 + (1,136.36 × 3,996) = 15,336,364 | ✅ |
| rpm_utilization | 11.4% | 1,136.36 / 10,000 × 100 = 11.4% | ✅ |
| tpm_utilization | 255.6% | 15,336,364 / 6,000,000 × 100 = 255.6% | ✅ |
| rpm_fits | True | 1,136.36 ≤ 10,000 | ✅ |
| tpm_fits | False | 15,336,364 > 6,000,000 | ✅ |
| fits | False | RPM ✓ AND TPM ✗ = False | ✅ |

---

## Overall Verdict

| Section | Result |
|---------|:------:|
| Token Profile | ✅ PASS (8/8) |
| Model Cost | ✅ PASS (6/6) |
| Cache Splits | ✅ PASS (15/15) |
| Cache Costs | ✅ PASS (7/7) |
| Per-Unit Costs | ✅ PASS (3/3) |
| Capacity Check | ✅ PASS (17/17) |

### Summary
**56 of 56 fields pass.** All token counts, cache splits, cost calculations, and capacity metrics match the spec formulas exactly. The vague use case defaults (Claude Sonnet 4.6, us-east-1, 500K sessions, 3 Q/session, 3 tools, standard token profile) were correctly applied per the handling rules for minimal-information prompts.
