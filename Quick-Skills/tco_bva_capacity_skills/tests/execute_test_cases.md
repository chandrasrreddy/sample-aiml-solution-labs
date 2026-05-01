# Execute Test Cases — Instructions

## Purpose

Execute all 25 use cases from `tests/use_cases.md`, generate response files, and verify each against the pricing spec. Each use case is self-contained: generate → verify → save both files → move to next.

---

## Execution Rules

1. **Do not stop until all 25 use cases are complete.** If context gets long, work in batches but always continue.
2. **Run up to 5 use cases in parallel** if the system supports it (Kiro sub-agents). Otherwise run sequentially.
3. **Do not ask for user input.** If a use case is vague or missing information, make reasonable assumptions and document them.
4. **Batch order:** UC-01 to UC-05, then UC-06 to UC-10, then UC-11 to UC-15, then UC-16 to UC-20, then UC-21 to UC-25.

---

## Per Use Case: Generate + Verify

### Step 1: Generate Response

1. Read the use case prompt from `tests/use_cases.md`.
2. Use the Bedrock pricing skills (`bedrock-pricing`, `agentcore-pricing`, `bedrock-capacity`, `agent-business-value`, `bedrock-tier-advisor`) to produce a complete cost estimate — exactly as a user would by pasting the prompt.
3. If the use case requires inputs not specified in the prompt, make reasonable assumptions and proceed. Do not ask clarifying questions.
4. Save the response to `responses/UC-{XX}-{slug}.md`.

### Step 2: Verify Against Spec

Immediately after generating the response:

1. Extract the Assumptions section (Workload Profile, Token Profile, Model Pricing) from the response file just created.
2. Apply the formulas from `tests/pricing_spec_v1.2.md` to independently compute all values.
3. Compare each computed value against the response file's stated values.
4. Save the verification result to `responses/UC-{XX}-result.md`.

### Step 3: Move to Next

Proceed to the next use case. Do not wait for user confirmation.

---

## File Naming

| File | Pattern | Example |
|------|---------|---------|
| Response | `responses/UC-{XX}-{slug}.md` | `responses/UC-01-enterprise-it-helpdesk.md` |
| Verification | `responses/UC-{XX}-result.md` | `responses/UC-01-result.md` |

Where `{XX}` is zero-padded (01–25) and `{slug}` is a short kebab-case description.

---

## Response File Format

Each response file MUST follow this structure:

```markdown
# UC-{XX}: {Use Case Title} — Full Cost Estimate

> **Use Case:** {Original prompt text from use_cases.md}

---

## 1. Assumptions

### Workload Profile
(Table: region, model, sessions, questions/session, tools, turns)

### Token Profile
(Table: system prompt, tool descriptions, user input, RAG, tool call/result, output, base context, cacheable prefix, delta, output per question)

### Model Pricing
(Table: input, output, cache_read, cache_write — with tier, variant, region)

### AgentCore Pricing (if applicable)
(Table: component prices from cache)

---

## 2. Model Cost Breakdown
(With caching: cache_write, cache_read, regular, output → total)
(Without caching baseline)
(Savings % and amounts)

---

## 3. AgentCore Cost Breakdown (if applicable)
(Runtime: vCPU + Memory)
(Gateway: invocations + search + indexing)
(Memory: STM + LTM storage + LTM retrieval)

---

## 4. Combined Total Cost
(Model + AgentCore = monthly/annual, per-session, per-question)

---

## 5. Capacity Check
(RPM: avg → peak → vs quota limit)
(TPM: avg → peak → effective peak → vs quota limit)
(Verdict and optimization checklist if doesn't fit)

---

## 6. Business Value Analysis (if applicable)
(3 tiers, Dim 2/3 if applicable, ROI summary)

---

## 7. Step-by-Step Calculation Explanations
(Token profile, turn-by-turn, cross-Q caching, cache math, no-cache baseline, AgentCore, capacity, business value)
```

---

## Verification Result File Format

```markdown
# UC-{XX} QA Verification Result

## Use Case
> {Original prompt}

## Verification Method
Applied pricing_spec_v1.2.md formulas to the response's stated assumptions.

---

## Model Cost
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|

## Cache Splits
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|

## AgentCore Cost (if applicable)
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|

## Capacity Check
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|

## Business Value (if applicable)
| Field | Response | Spec Calculation | Status |
|-------|:--------:|:----------------:|:------:|

---

## Overall Verdict
| Section | Result |
|---------|:------:|

### Summary
{X} of {Y} fields pass. {Description of any failures.}
```

---

## Handling Vague Use Cases (UC-21 through UC-25)

These intentionally omit required information. Make these assumptions without asking:

- **No region specified:** Use us-east-1
- **No model specified:** Use Claude Sonnet 4.6
- **Minimal information:** Use Claude Sonnet 4.6, us-east-1, 500K sessions, 3 Q/session, 3 tools, standard token profile
- **Ambiguous intent:** Treat as pricing comparison — show all tiers for Claude Sonnet 4.6 in us-east-1
- **Volume without context:** Assume Claude Sonnet 4.6, us-east-1, derive sessions from stated volume

Document all assumptions made under a "Assumptions Made (not in prompt)" section at the top of the response.

---

## After All 25 Complete

1. Count total PASS/FAIL across all result files.
2. List any systematic issues found.
3. Print a summary table:

```markdown
| UC | Response Generated | Verification | Pass/Fail |
|:--:|:------------------:|:------------:|:---------:|
| 01 | ✅ | ✅ | 31/33 PASS |
| 02 | ✅ | ✅ | 33/33 PASS |
| ... | ... | ... | ... |
```
