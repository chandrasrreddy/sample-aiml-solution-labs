# UC-14 QA Verification Result

## Use Case
> "Compare Claude Sonnet 4.6 pricing across us-east-1, eu-west-1, and ap-northeast-1. Show Standard Global vs Standard Regional for each."

## Verification Method
Independently queried the Bedrock pricing cache for Claude Sonnet 4.6 in each region using `query_model_pricing()` and `extract_bedrock_model_prices()` with explicit tier/variant parameters. Compared extracted prices against the response file's stated values.

---

## Pricing Verification — us-east-1

### Standard Global
| Field | Response | Cache Query | Status |
|:------|:--------:|:-----------:|:------:|
| Input | $3.00 | $3.00 | ✅ |
| Output | $15.00 | $15.00 | ✅ |
| Cache Read | $0.30 | $0.30 | ✅ |
| Cache Write | $3.75 | $3.75 | ✅ |

### Standard Regional
| Field | Response | Cache Query | Status |
|:------|:--------:|:-----------:|:------:|
| Input | $3.30 | $3.30 | ✅ |
| Output | $16.50 | $16.50 | ✅ |
| Cache Read | $0.33 | $0.33 | ✅ |
| Cache Write | $4.125 | $4.125 | ✅ |

---

## Pricing Verification — eu-west-1

### Standard Global
| Field | Response | Cache Query | Status |
|:------|:--------:|:-----------:|:------:|
| Input | $3.00 | $3.00 | ✅ |
| Output | $15.00 | $15.00 | ✅ |
| Cache Read | $0.30 | $0.30 | ✅ |
| Cache Write | $3.75 | $3.75 | ✅ |

### Standard Regional
| Field | Response | Cache Query | Status |
|:------|:--------:|:-----------:|:------:|
| Input | $3.30 | $3.30 | ✅ |
| Output | $16.50 | $16.50 | ✅ |
| Cache Read | $0.33 | $0.33 | ✅ |
| Cache Write | $4.125 | $4.125 | ✅ |

---

## Pricing Verification — ap-northeast-1

### Standard Global
| Field | Response | Cache Query | Status |
|:------|:--------:|:-----------:|:------:|
| Input | $3.00 | $3.00 | ✅ |
| Output | $15.00 | $15.00 | ✅ |
| Cache Read | $0.30 | $0.30 | ✅ |
| Cache Write | $3.75 | $3.75 | ✅ |

### Standard Regional
| Field | Response | Cache Query | Status |
|:------|:--------:|:-----------:|:------:|
| Input | $3.30 | $3.30 | ✅ |
| Output | $16.50 | $16.50 | ✅ |
| Cache Read | $0.33 | $0.33 | ✅ |
| Cache Write | $4.125 | $4.125 | ✅ |

---

## Regional Premium Verification

| Field | Stated Premium | Calculated Premium | Status |
|:------|:--------------:|:------------------:|:------:|
| Input | +10.0% | (3.30 - 3.00) / 3.00 × 100 = 10.0% | ✅ |
| Output | +10.0% | (16.50 - 15.00) / 15.00 × 100 = 10.0% | ✅ |
| Cache Read | +10.0% | (0.33 - 0.30) / 0.30 × 100 = 10.0% | ✅ |
| Cache Write | +10.0% | (4.125 - 3.75) / 3.75 × 100 = 10.0% | ✅ |

---

## Variant Availability Verification

| Region | Standard Global | Standard Regional | Batch Global | Batch Regional | Status |
|:-------|:---------------:|:-----------------:|:------------:|:--------------:|:------:|
| us-east-1 | ✅ Found | ✅ Found | ✅ Found | ✅ Found | ✅ |
| eu-west-1 | ✅ Found | ✅ Found | ✅ Found | ✅ Found | ✅ |
| ap-northeast-1 | ✅ Found | ✅ Found | ✅ Found | ✅ Found | ✅ |

---

## Overall Verdict

| Section | Result |
|:--------|:------:|
| us-east-1 Standard Global | ✅ PASS |
| us-east-1 Standard Regional | ✅ PASS |
| eu-west-1 Standard Global | ✅ PASS |
| eu-west-1 Standard Regional | ✅ PASS |
| ap-northeast-1 Standard Global | ✅ PASS |
| ap-northeast-1 Standard Regional | ✅ PASS |
| Regional Premium Calculation | ✅ PASS |
| Variant Availability | ✅ PASS |

### Summary
**28 of 28 fields pass.** All prices in the response match the cache query results exactly. The 10% Regional premium is correctly calculated across all price components. Variant availability is accurately reported for all three regions.
