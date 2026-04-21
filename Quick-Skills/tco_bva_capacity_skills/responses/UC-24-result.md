# UC-24 QA Verification Result

## Use Case
> "Tell me about Bedrock pricing."

## Verification Method
Applied pricing_spec_v1.2.md formulas to the response's stated assumptions. This is a pricing overview use case — verification focuses on the representative cost example (Claude Sonnet 4.6 Standard Global) and the per-token prices reported for all three models.

---

## Per-Token Prices (from cache)

### Claude Sonnet 4.6 — us-east-1
| Tier/Variant | Field | Response | Cache Value | Status |
|-------------|-------|:--------:|:-----------:|:------:|
| Standard Global | Input | $3.00 | $3.00 | ✅ |
| Standard Global | Output | $15.00 | $15.00 | ✅ |
| Standard Global | Cache Read | $0.30 | $0.30 | ✅ |
| Standard Global | Cache Write | $3.75 | $3.75 | ✅ |
| Standard Regional | Input | $3.30 | $3.30 | ✅ |
| Standard Regional | Output | $16.50 | $16.50 | ✅ |
| Standard Regional | Cache Read | $0.33 | $0.33 | ✅ |
| Standard Regional | Cache Write | $4.125 | $4.125 | ✅ |
| Batch Global | Input | $1.50 | $1.50 | ✅ |
| Batch Global | Output | $7.50 | $7.50 | ✅ |
| Batch Regional | Input | $1.65 | $1.65 | ✅ |
| Batch Regional | Output | $8.25 | $8.25 | ✅ |

### Nova Pro — us-east-1
| Tier/Variant | Field | Response | Cache Value | Status |
|-------------|-------|:--------:|:-----------:|:------:|
| Standard Global | Input | $1.25 | $1.25 | ✅ |
| Standard Global | Output | $10.00 | $10.00 | ✅ |
| Standard Regional | Input | $1.375 | $1.375 | ✅ |
| Standard Regional | Output | $4.00 | $4.00 | ✅ |
| Flex Global | Input | $0.625 | $0.625 | ✅ |
| Flex Global | Output | $5.00 | $5.00 | ✅ |
| Flex Regional | Input | $0.40 | $0.40 | ✅ |
| Flex Regional | Output | $1.60 | $1.60 | ✅ |
| Priority Global | Input | $2.1875 | $2.1875 | ✅ |
| Priority Global | Output | $17.50 | $17.50 | ✅ |
| Batch Global | Input | $0.625 | $0.625 | ✅ |
| Batch Global | Output | $5.00 | $5.00 | ✅ |

### Llama 4 Maverick 17B — us-east-1
| Tier/Variant | Field | Response | Cache Value | Status |
|-------------|-------|:--------:|:-----------:|:------:|
| Standard Regional | Input | $0.24 | $0.24 | ✅ |
| Standard Regional | Output | $0.97 | $0.97 | ✅ |
| Batch Regional | Input | $0.12 | $0.12 | ✅ |
| Batch Regional | Output | $0.485 | $0.485 | ✅ |

---

## Token Profile (Claude Sonnet 4.6 Representative Example)
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| cacheable_base | 5,000 | 1,000 + 4,000 = 5,000 | ✅ |
| base_prompt | 8,100 | 5,000 + 100 + 3,000 = 8,100 | ✅ |
| delta | 600 | 100 + 500 = 600 | ✅ |
| turns | 11 | 10 + 1 = 11 | ✅ |
| total_input_per_question | 122,100 | Σ(i=0..10)[8,100 + i×600] = 11×8,100 + 600×10×11/2 = 89,100 + 33,000 = 122,100 | ✅ |
| total_output_per_question | 1,100 | 100 + 10×100 = 1,100 | ✅ |
| questions_per_month | 500,000 | 100,000 × 5 = 500,000 | ✅ |
| monthly_input_tokens | 61,050,000,000 | 122,100 × 500,000 = 61,050,000,000 | ✅ |
| monthly_output_tokens | 550,000,000 | 1,100 × 500,000 = 550,000,000 | ✅ |

---

## Cache Splits (Claude Sonnet 4.6)
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| Q1 cache_write | 13,500 | 8,100 + 9×600 = 13,500 | ✅ |
| Q1 cache_read | 108,000 | Σ(k=1..10)[8,100 + (k-1)×600] = 10×8,100 + 600×(0+1+...+9) = 81,000 + 27,000 = 108,000 | ✅ |
| Q1 regular | 600 | delta = 600 | ✅ |
| Q1 sum | 122,100 | 13,500 + 108,000 + 600 = 122,100 ✓ | ✅ |
| Q2 cache_write | 8,500 | (100 + 3,000) + 9×600 = 3,100 + 5,400 = 8,500 | ✅ |
| Q2 cache_read | 113,000 | 5,000 + Σ(k=1..10)[8,100 + (k-1)×600] = 5,000 + 108,000 = 113,000 | ✅ |
| Q2 regular | 600 | delta = 600 | ✅ |
| Q2 sum | 122,100 | 8,500 + 113,000 + 600 = 122,100 ✓ | ✅ |
| Session cache_write | 47,500 | 13,500 + 4×8,500 = 47,500 | ✅ |
| Session cache_read | 560,000 | 108,000 + 4×113,000 = 560,000 | ✅ |
| Session regular | 3,000 | 600 + 4×600 = 3,000 | ✅ |
| Session sum | 610,500 | 5 × 122,100 = 610,500 ✓ | ✅ |

---

## Model Cost (Claude Sonnet 4.6 with caching)
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| Monthly cache_write tokens | 4,750,000,000 | 100,000 × 47,500 = 4,750,000,000 | ✅ |
| Monthly cache_read tokens | 56,000,000,000 | 100,000 × 560,000 = 56,000,000,000 | ✅ |
| Monthly regular tokens | 300,000,000 | 100,000 × 3,000 = 300,000,000 | ✅ |
| Cache write cost | $17,812.50 | 4,750 × $3.75 = $17,812.50 | ✅ |
| Cache read cost | $16,800.00 | 56,000 × $0.30 = $16,800.00 | ✅ |
| Regular input cost | $900.00 | 300 × $3.00 = $900.00 | ✅ |
| Output cost | $8,250.00 | 550 × $15.00 = $8,250.00 | ✅ |
| **Total with cache** | **$43,762.50** | $17,812.50 + $16,800.00 + $900.00 + $8,250.00 = **$43,762.50** | ✅ |
| No-cache input cost | $183,150.00 | 61,050 × $3.00 = $183,150.00 | ✅ |
| No-cache output cost | $8,250.00 | 550 × $15.00 = $8,250.00 | ✅ |
| **No-cache total** | **$191,400.00** | $183,150.00 + $8,250.00 = **$191,400.00** | ✅ |
| Savings monthly | $147,637.50 | $191,400.00 − $43,762.50 = $147,637.50 | ✅ |
| Savings % | 77.1% | $147,637.50 / $191,400.00 × 100 = 77.14% | ✅ |

---

## Model Cost (Nova Pro Standard Global — no caching)
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| No-cache input | $76,312.50 | 61,050 × $1.25 = $76,312.50 | ✅ |
| No-cache output | $5,500.00 | 550 × $10.00 = $5,500.00 | ✅ |
| **No-cache total** | **$81,812.50** | $76,312.50 + $5,500.00 = **$81,812.50** | ✅ |
| Caching savings | 0% | No caching support (cache_read=None, cache_write=None) | ✅ |

---

## Model Cost (Llama 4 Maverick Standard Regional — no caching)
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|
| No-cache input | $14,652.00 | 61,050 × $0.24 = $14,652.00 | ✅ |
| No-cache output | $533.50 | 550 × $0.97 = $533.50 | ✅ |
| **No-cache total** | **$15,185.50** | $14,652.00 + $533.50 = **$15,185.50** | ✅ |
| Caching savings | 0% | No caching support (cache_read=None, cache_write=None) | ✅ |

---

## Simple Comparison Verification
| Model | Response Total (1M in + 1M out) | Spec Calculation | Status |
|-------|:-------------------------------:|:----------------:|:------:|
| Llama 4 Maverick | $1.21 | $0.24 + $0.97 = $1.21 | ✅ |
| Nova Pro | $11.25 | $1.25 + $10.00 = $11.25 | ✅ |
| Claude Sonnet 4.6 | $18.00 | $3.00 + $15.00 = $18.00 | ✅ |

---

## Overall Verdict
| Section | Result |
|---------|:------:|
| Per-Token Prices (Claude Sonnet 4.6) | ✅ 12/12 |
| Per-Token Prices (Nova Pro) | ✅ 12/12 |
| Per-Token Prices (Llama 4 Maverick) | ✅ 4/4 |
| Token Profile | ✅ 9/9 |
| Cache Splits | ✅ 12/12 |
| Model Cost (Claude Sonnet 4.6) | ✅ 12/12 |
| Model Cost (Nova Pro) | ✅ 4/4 |
| Model Cost (Llama 4 Maverick) | ✅ 4/4 |
| Simple Comparison | ✅ 3/3 |

### Summary
**72 of 72 fields pass.** All per-token prices match cache values. All token calculations, cache splits, and cost figures for the representative example independently verified against pricing_spec_v1.2.md formulas. The response correctly identifies caching as the biggest cost lever and accurately notes which models support it.
