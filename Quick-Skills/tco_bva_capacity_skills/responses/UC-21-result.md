# UC-21 QA Verification Result

## Use Case
> "How much would it cost to run a Claude Sonnet agent with 1M sessions per month?"

## Verification Method
Applied pricing_spec_v1.2.md formulas to the response's stated assumptions. All calculations independently reproduced using spec §2–§6.

---

## Assumptions Verification
| Field | Response | Expected (per execute_test_cases.md) | Status |
|-------|:--------:|:------------------------------------:|:------:|
| Region | us-east-1 | us-east-1 (default when not specified) | ✅ PASS |
| Model | Claude Sonnet 4.6 | Claude Sonnet 4.6 (latest Sonnet) | ✅ PASS |
| Sessions/month | 1,000,000 | 1,000,000 (from prompt) | ✅ PASS |
| Questions/session | 5 | 5 (default) | ✅ PASS |
| Tools invoked | 10 | 10 (default) | ✅ PASS |
| Token profile | Standard defaults | Standard defaults | ✅ PASS |
| Assumptions documented | Yes (top of response) | Required for vague UCs | ✅ PASS |

## Model Pricing
| Field | Response | Cache Query Result | Status |
|-------|:--------:|:------------------:|:------:|
| Input price | $3.00/M | $3.00/M (Standard Global) | ✅ PASS |
| Output price | $15.00/M | $15.00/M (Standard Global) | ✅ PASS |
| Cache read price | $0.30/M | $0.30/M (10% of input) | ✅ PASS |
| Cache write price | $3.75/M | $3.75/M (125% of input) | ✅ PASS |

## Token Profile
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| cacheable_base | 5,000 | 1,000 + 4,000 = 5,000 | ✅ PASS |
| base_prompt | 8,100 | 5,000 + 100 + 3,000 = 8,100 | ✅ PASS |
| delta | 600 | 100 + 500 = 600 | ✅ PASS |
| turns | 11 | 10 + 1 = 11 | ✅ PASS |
| output_per_question | 1,100 | 100 + 10 × 100 = 1,100 | ✅ PASS |
| total_input_per_question | 122,100 | 11 × 8,100 + 600 × 10 × 11/2 = 122,100 | ✅ PASS |

## Cache Splits
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| q1_cache_write | 13,500 | 8,100 + 9 × 600 = 13,500 | ✅ PASS |
| q1_cache_read | 108,000 | Σ(k=1..10)[8,100 + (k-1)×600] = 108,000 | ✅ PASS |
| q1_regular | 600 | delta = 600 | ✅ PASS |
| q1_sum | 122,100 | 13,500 + 108,000 + 600 = 122,100 ✓ | ✅ PASS |
| q2_cache_write | 8,500 | (100 + 3,000) + 9 × 600 = 8,500 | ✅ PASS |
| q2_cache_read | 113,000 | 5,000 + Σ(k=1..10)[8,100 + (k-1)×600] = 113,000 | ✅ PASS |
| q2_regular | 600 | delta = 600 | ✅ PASS |
| q2_sum | 122,100 | 8,500 + 113,000 + 600 = 122,100 ✓ | ✅ PASS |
| session_cw | 47,500 | 13,500 + 4 × 8,500 = 47,500 | ✅ PASS |
| session_cr | 560,000 | 108,000 + 4 × 113,000 = 560,000 | ✅ PASS |
| session_reg | 3,000 | 600 + 4 × 600 = 3,000 | ✅ PASS |
| session_sum | 610,500 | 5 × 122,100 = 610,500 ✓ | ✅ PASS |

## Model Cost
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| monthly_cw_tokens | 47,500,000,000 | 1M × 47,500 = 47.5B | ✅ PASS |
| monthly_cr_tokens | 560,000,000,000 | 1M × 560,000 = 560B | ✅ PASS |
| monthly_reg_tokens | 3,000,000,000 | 1M × 3,000 = 3B | ✅ PASS |
| monthly_out_tokens | 5,500,000,000 | 1M × 5,500 = 5.5B | ✅ PASS |
| cache_write_cost | $178,125.00 | 47.5B / 1M × $3.75 = $178,125.00 | ✅ PASS |
| cache_read_cost | $168,000.00 | 560B / 1M × $0.30 = $168,000.00 | ✅ PASS |
| regular_input_cost | $9,000.00 | 3B / 1M × $3.00 = $9,000.00 | ✅ PASS |
| output_cost | $82,500.00 | 5.5B / 1M × $15.00 = $82,500.00 | ✅ PASS |
| total_model_cost | $437,625.00 | $178,125 + $168,000 + $9,000 + $82,500 = $437,625.00 | ✅ PASS |
| no_cache_input_cost | $1,831,500.00 | 610.5B / 1M × $3.00 = $1,831,500.00 | ✅ PASS |
| no_cache_output_cost | $82,500.00 | 5.5B / 1M × $15.00 = $82,500.00 | ✅ PASS |
| no_cache_total | $1,914,000.00 | $1,831,500 + $82,500 = $1,914,000.00 | ✅ PASS |
| savings_monthly | $1,476,375.00 | $1,914,000 - $437,625 = $1,476,375.00 | ✅ PASS |
| savings_pct | 77.1% | $1,476,375 / $1,914,000 × 100 = 77.1% | ✅ PASS |
| per_session | $0.4376 | $437,625 / 1,000,000 = $0.4376 | ✅ PASS |
| per_question | $0.0875 | $437,625 / 5,000,000 = $0.0875 | ✅ PASS |
| annual | $5,251,500.00 | $437,625 × 12 = $5,251,500.00 | ✅ PASS |

## Capacity Check
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| active_minutes/month | 15,840 | 12 × 60 × 22 = 15,840 | ✅ PASS |
| avg_questions/min | 315.66 | 5,000,000 / 15,840 = 315.66 | ✅ PASS |
| avg_rpm | 3,472 | 315.66 × 11 = 3,472.22 | ✅ PASS |
| peak_rpm | 10,417 | 3,472.22 × 3.0 = 10,416.67 | ✅ PASS |
| base_context | 8,100 | 100 + 1,000 + 4,000 + 3,000 = 8,100 | ✅ PASS |
| avg_input/turn | 11,100 | 8,100 + (600/2) × 10 = 11,100 | ✅ PASS |
| avg_output/turn | 100 | (10 × 100 + 100) / 11 = 100 | ✅ PASS |
| avg_tpm | 40,277,778 | 3,472.22 × (11,100 + 100×5) = 40,277,778 | ✅ PASS |
| peak_tpm | 120,833,333 | 40,277,778 × 3.0 = 120,833,333 | ✅ PASS |
| max_tokens_overhead | 3,996 | 4,096 − 100 = 3,996 | ✅ PASS |
| effective_peak_tpm | 162,458,333 | 120,833,333 + (10,417 × 3,996) = 162,458,333 | ✅ PASS |
| rpm_utilization | 20,833% | 10,417 / 50 × 100 = 20,833% | ✅ PASS |
| tpm_utilization | 40,615% | 162,458,333 / 400,000 × 100 = 40,615% | ✅ PASS |
| fits | False | RPM ❌ + TPM ❌ = False | ✅ PASS |
| output_burndown_rate | 5× | Claude Sonnet 4.6 = Claude 3.7+ → 5× | ✅ PASS |

---

## Overall Verdict
| Section | Result |
|---------|:------:|
| Assumptions | ✅ PASS (7/7) |
| Model Pricing | ✅ PASS (4/4) |
| Token Profile | ✅ PASS (6/6) |
| Cache Splits | ✅ PASS (12/12) |
| Model Cost | ✅ PASS (15/15) |
| Capacity Check | ✅ PASS (16/16) |

### Summary
**60 of 60 fields pass.** All token counts, cache splits, cost calculations, and capacity metrics match the spec formulas exactly. The response correctly applies default assumptions for the vague prompt (no region → us-east-1, Claude Sonnet → Claude Sonnet 4.6, standard token profile with 5 Q/session and 10 tools). Assumptions are properly documented at the top of the response. Capacity check correctly identifies that 1M sessions/month with this agent profile massively exceeds default on-demand quotas (RPM 208× over, TPM 406× over), requiring a committed throughput agreement.
