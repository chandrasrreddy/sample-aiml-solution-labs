# Bedrock Agent Pricing & Business Value — Specification v1.1

> **Purpose**: This document is the single source of truth for all pricing and business value calculations. The QA judge uses these formulas to independently verify skill output. A human can review this document once to trust all downstream automated testing.

---

## 1. Input Parameters

All calculations start from these inputs. The judge accepts them as-is — no questioning assumptions.

### 1.1 Model Pricing (per 1M tokens)

| Parameter | Symbol | Description |
|---|---|---|
| `input_price` | P_in | Standard input price per 1M tokens |
| `output_price` | P_out | Standard output price per 1M tokens |
| `cache_read_price` | P_cr | Cache read price per 1M tokens |
| `cache_write_price` | P_cw | Cache write price per 1M tokens |

### 1.2 Workload Shape

| Parameter | Symbol | Default | Description |
|---|---|---|---|
| `sessions_per_month` | S | — | Total sessions per month |
| `questions_per_session` | Q_s | 3 | Questions per session |
| `system_prompt_tokens` | T_sys | 2,000 | System prompt size |
| `num_tools_provided` | N_tools | 10 | Number of tools in schema |
| `tokens_per_tool_description` | T_tool_desc | 200 | Tokens per tool JSON schema |
| `input_tokens_per_question` | T_user | 200 | User's question text |
| `rag_chunks` | N_rag | 10 | RAG chunks retrieved per question |
| `tokens_per_rag_chunk` | T_rag_chunk | 300 | Tokens per RAG chunk |
| `tools_invoked_per_question` | N_invoke | 5 | Tool calls the model makes per question |
| `tool_call_tokens` | T_call | 100 | Output tokens per tool call (JSON) |
| `tool_result_tokens` | T_result | 500 | Input tokens per tool result |
| `output_tokens_per_question` | T_answer | 500 | Final answer tokens |

### 1.3 AgentCore Parameters

| Parameter | Symbol | Default | Description |
|---|---|---|---|
| `runtime_vcpus` | V | 2 | vCPUs allocated |
| `runtime_memory_gb` | M_gb | 4.0 | Memory allocated (GB) |
| `runtime_wait_pct` | W | 0.70 | % of time agent is idle/waiting |
| `use_memory_short_term` | — | true | Short-term memory enabled |
| `use_memory_long_term` | — | true | Long-term memory enabled |
| `use_gateway` | — | true | API gateway enabled |
| `tools_indexed_in_gateway` | N_gw | 10 | Tools indexed in gateway |

### 1.4 Business Value Parameters

| Parameter | Symbol | Default | Description |
|---|---|---|---|
| `time_without_ai_min` | T_manual | 20 | Minutes per task without AI |
| `time_with_ai_min` | T_ai | 10 | Minutes per task with AI |
| `human_cost_per_hour` | C_human | 75 | Fully-loaded human labor cost/hr |
| `agent_effectiveness_pct` | E | 65% | % sessions where agent delivers quality results |
| `efficiency_factor_pct` | F | 60% | % of reclaimed time used productively |
| `revenue_per_hour` | R_hr | 300 | Revenue generated per productive employee hour |

---

## 2. Token Calculation Formulas

### 2.1 Base Context

The base context is the fixed portion of tokens sent on every turn of a question:

```
base_context = T_sys + (N_tools × T_tool_desc) + T_user + (N_rag × T_rag_chunk)
```

### 2.2 Tool Delta

Each tool invocation adds this many tokens to the conversation context:

```
tool_delta = T_call + T_result
```

Note: `T_call` is output from the model (tool invocation JSON), `T_result` is input to the model (tool response). Both become part of the context for subsequent turns.

### 2.3 Turns Per Question

```
turns = N_invoke + 1
```

Turn 0 is the initial call (model receives context, decides to call first tool). Turns 1 through N_invoke each append one tool exchange and may call another tool or produce the final answer.

### 2.4 Input Tokens Per Question (Compounding)

Each turn re-sends the entire conversation so far. The input tokens grow with each turn:

```
Turn 0:  base_context
Turn 1:  base_context + 1 × tool_delta
Turn 2:  base_context + 2 × tool_delta
...
Turn N:  base_context + N_invoke × tool_delta
```

**Total input tokens per question:**

```
total_input_per_question = Σ(i=0 to N_invoke) [base_context + i × tool_delta]
                        = (N_invoke + 1) × base_context + tool_delta × N_invoke × (N_invoke + 1) / 2
```

**Closed-form (for verification):**

```
total_input_per_question = turns × base_context + tool_delta × N_invoke × turns / 2
```

### 2.5 Output Tokens Per Question

```
total_output_per_question = T_answer + N_invoke × T_call
```

The model outputs `T_call` tokens for each tool invocation, plus `T_answer` tokens for the final response.

### 2.6 Monthly Totals (Before Caching)

```
questions_per_month = S × Q_s

monthly_input_tokens  = total_input_per_question × questions_per_month
monthly_output_tokens = total_output_per_question × questions_per_month
```

### 2.7 No-Cache Cost (Baseline)

```
no_cache_input_cost  = (monthly_input_tokens / 1,000,000) × P_in
no_cache_output_cost = (monthly_output_tokens / 1,000,000) × P_out
no_cache_total       = no_cache_input_cost + no_cache_output_cost
```

---

## 3. Prompt Caching Model

Bedrock prompt caching uses **prefix matching**: the cache matches from the start of the prompt forward. In a multi-turn agent, the prompt grows each turn by appending tool exchanges. The model distinguishes between Q1 (first question in session) and Q2+ (subsequent questions where system prompt + tool descriptions are already cached).

### 3.1 Key Concepts

- **cacheable_base** = `T_sys + (N_tools × T_tool_desc)` — system prompt + tool descriptions (persists across questions in a session)
- **base_prompt** = `cacheable_base + T_user + T_rag` — full turn-0 context (changes each question due to new user input + RAG)
- **Billing classification**: cache_write = content that WILL be re-read on the next turn; cache_read = prefix already in cache; regular = content on the LAST turn that won't be re-read

### 3.2 Session-Aware Caching Model

#### Q1: First question in session (nothing cached yet)

| Turn | cache_read | cache_write | regular | Total |
|---|---|---|---|---|
| Turn 0 | 0 | base_prompt | 0 | base_prompt |
| Turn k (1 ≤ k < N) | base_prompt + (k-1)×delta | delta | 0 | base_prompt + k×delta |
| Turn N (final) | base_prompt + (N-1)×delta | 0 | delta | base_prompt + N×delta |

**Q1 totals:**

```
q1_cache_write = base_prompt + (N - 1) × delta

q1_cache_read = Σ(k=1 to N) [base_prompt + (k-1) × delta]
             = N × base_prompt + delta × N × (N-1) / 2

q1_regular = delta
```

**Verification**: `q1_cw + q1_cr + q1_reg = total_input_per_question`

#### Q2+: Subsequent questions in session

On turn 0, `cacheable_base` (sys+tools) is already in cache from the prior question → **cache_read**. The new `T_user + T_rag` extends the checkpoint → **cache_write** (will be re-read on turn 1).

| Turn | cache_read | cache_write | regular | Total |
|---|---|---|---|---|
| Turn 0 | cacheable_base | T_user + T_rag | 0 | base_prompt |
| Turn k (1 ≤ k < N) | base_prompt + (k-1)×delta | delta | 0 | base_prompt + k×delta |
| Turn N (final) | base_prompt + (N-1)×delta | 0 | delta | base_prompt + N×delta |

**Q2 totals:**

```
q2_cache_write = (T_user + T_rag) + (N - 1) × delta

q2_cache_read = cacheable_base + Σ(k=1 to N) [base_prompt + (k-1) × delta]
             = cacheable_base + N × base_prompt + delta × N × (N-1) / 2

q2_regular = delta
```

**Verification**: `q2_cw + q2_cr + q2_reg = total_input_per_question`

Note: Q2 has MORE cache_read and LESS cache_write than Q1 because `cacheable_base` tokens are read from cache rather than written.

### 3.3 Per-Session and Monthly Totals

**Per session (Q_s questions: 1 × Q1 + (Q_s - 1) × Q2):**

```
n_subsequent = Q_s - 1

session_cw  = q1_cache_write + n_subsequent × q2_cache_write
session_cr  = q1_cache_read  + n_subsequent × q2_cache_read
session_reg = q1_regular     + n_subsequent × q2_regular
```

**Monthly:**

```
monthly_cache_write   = S × session_cw
monthly_cache_read    = S × session_cr
monthly_regular_input = S × session_reg
```

**Verification identity (MUST hold):**

```
session_cw + session_cr + session_reg = Q_s × total_input_per_question
monthly_cache_write + monthly_cache_read + monthly_regular_input = monthly_input_tokens
```

### 3.4 Cache Cost Formulas

```
cache_read_cost    = (monthly_cache_read    / 1,000,000) × P_cr
cache_write_cost   = (monthly_cache_write   / 1,000,000) × P_cw
regular_input_cost = (monthly_regular_input / 1,000,000) × P_in

total_input_cost_with_cache = cache_read_cost + cache_write_cost + regular_input_cost
```

### 3.5 Caching Savings

```
caching_savings_monthly = no_cache_input_cost - total_input_cost_with_cache
caching_savings_pct = caching_savings_monthly / no_cache_input_cost × 100
```

## 4. Total Model Cost

```
model_input_cost  = total_input_cost_with_cache  (if caching supported, else no_cache_input_cost)
model_output_cost = (monthly_output_tokens / 1,000,000) × P_out

total_model_cost = model_input_cost + model_output_cost
```

---

## 5. AgentCore Cost

### 5.1 Runtime

```
active_pct = 1 - runtime_wait_pct
runtime_hours = sessions_per_month × (average_session_duration_min / 60) × active_pct

# Pricing: per vCPU-hour and per GB-hour (from AgentCore pricing tables)
# Approximate: $0.00417/vCPU-sec, $0.000463/GB-sec
# Or use the monthly bundled rate if available

runtime_cost = runtime_hours × (V × vcpu_rate + M_gb × gb_rate)
```

Note: The exact AgentCore runtime pricing may vary. The judge should compare to the skill's stated AgentCore cost and verify internal consistency (components sum to total).

### 5.2 Gateway

```
gateway_cost = tools_indexed_in_gateway × gateway_per_tool_rate × sessions_per_month
```

### 5.3 Memory

```
memory_cost = sessions_per_month × (short_term_rate + long_term_rate)
```

### 5.4 Total AgentCore

```
total_agentcore = runtime_cost + gateway_cost + memory_cost
```

---

## 6. Grand Total

```
total_monthly = total_model_cost + total_agentcore
total_annual  = total_monthly × 12

per_session  = total_monthly / sessions_per_month
per_question = total_monthly / questions_per_month
```

---

## 7. Business Value Formulas

### 7.1 Dimension 1a — Productivity Increase (Revenue Uplift)

```
effective_sessions = sessions_per_month × (agent_effectiveness_pct / 100)
time_saved_per_session_min = time_without_ai_min - time_with_ai_min
total_hours_saved = effective_sessions × time_saved_per_session_min / 60
productive_hours = total_hours_saved × (efficiency_factor_pct / 100)
productivity_value_monthly = productive_hours × revenue_per_hour
net_value_1a = productivity_value_monthly - total_monthly
```

### 7.2 Dimension 1b — Cost Savings (Alternative View, Mutually Exclusive with 1a)

```
effective_sessions = sessions_per_month × (agent_effectiveness_pct / 100)
total_hours_saved = effective_sessions × time_saved_per_session_min / 60
cost_savings_monthly = total_hours_saved × human_cost_per_hour
net_value_1b = cost_savings_monthly - total_monthly
```

### 7.3 ROI

```
roi_1a = productivity_value_monthly / total_monthly
roi_1b = cost_savings_monthly / total_monthly
```

### 7.4 Human Equivalent

```
hours_equivalent = sessions_per_month × time_without_ai_min / 60
fte_equivalent = hours_equivalent / 160    # 160 working hours per month
human_cost_equivalent = hours_equivalent × human_cost_per_hour
```

---

## 8. Reference Examples (Hand-Verified)

### Example A: Simple Agent — No Tools, No Caching

**Inputs:**
- sessions_per_month = 10,000
- questions_per_session = 1
- system_prompt_tokens = 1,000
- num_tools_provided = 0
- tokens_per_tool_description = 200
- input_tokens_per_question = 100
- rag_chunks = 0
- tokens_per_rag_chunk = 300
- tools_invoked_per_question = 0
- tool_call_tokens = 100
- tool_result_tokens = 500
- output_tokens_per_question = 200
- input_price = 5.00 (per 1M)
- output_price = 25.00 (per 1M)

**Calculations:**

```
base_context = 1,000 + (0 × 200) + 100 + (0 × 300) = 1,100
tool_delta = 100 + 500 = 600
turns = 0 + 1 = 1

total_input_per_question = 1 × 1,100 + 600 × 0 × 1 / 2 = 1,100
total_output_per_question = 200 + 0 × 100 = 200

questions_per_month = 10,000 × 1 = 10,000
monthly_input_tokens = 1,100 × 10,000 = 11,000,000
monthly_output_tokens = 200 × 10,000 = 2,000,000

no_cache_input_cost = (11,000,000 / 1,000,000) × 5.00 = $55.00
no_cache_output_cost = (2,000,000 / 1,000,000) × 25.00 = $50.00
no_cache_total = $105.00
```

**Expected answers:**
- total_input_per_question = **1,100**
- total_output_per_question = **200**
- monthly_input_tokens = **11,000,000**
- monthly_output_tokens = **2,000,000**
- no_cache_total = **$105.00**

---

### Example B: Medium Agent — 3 Tools, With Caching

**Inputs:**
- sessions_per_month = 50,000
- questions_per_session = 2
- system_prompt_tokens = 1,500
- num_tools_provided = 5
- tokens_per_tool_description = 200
- input_tokens_per_question = 150
- rag_chunks = 5
- tokens_per_rag_chunk = 300
- tools_invoked_per_question = 3
- tool_call_tokens = 100
- tool_result_tokens = 500
- output_tokens_per_question = 300
- input_price = 3.00 (Sonnet)
- output_price = 15.00
- cache_read_price = 0.30
- cache_write_price = 3.75

**Calculations:**

```
base_context = 1,500 + (5 × 200) + 150 + (5 × 300) = 1,500 + 1,000 + 150 + 1,500 = 4,150
tool_delta = 100 + 500 = 600
turns = 3 + 1 = 4
questions_per_month = 50,000 × 2 = 100,000

# Input tokens per question (compounding)
Turn 0: 4,150
Turn 1: 4,150 + 600 = 4,750
Turn 2: 4,150 + 1,200 = 5,350
Turn 3: 4,150 + 1,800 = 5,950

total_input_per_question = 4,150 + 4,750 + 5,350 + 5,950 = 20,200

# Closed-form check: 4 × 4,150 + 600 × 3 × 4 / 2 = 16,600 + 3,600 = 20,200 ✓

total_output_per_question = 300 + 3 × 100 = 600

# Monthly totals
monthly_input_tokens = 20,200 × 100,000 = 2,020,000,000  (2.02B)
monthly_output_tokens = 600 × 100,000 = 60,000,000  (60M)

# No-cache baseline
no_cache_input_cost = (2,020,000,000 / 1,000,000) × 3.00 = $6,060.00
no_cache_output_cost = (60,000,000 / 1,000,000) × 15.00 = $900.00

# Session-aware caching (2 questions/session)
cacheable_base = 1,500 + 1,000 = 2,500
base_prompt = 4,150 (as above)
delta = 600, N = 3

# Q1 (first question — nothing cached)
q1_cw = 4,150 + (3-1) × 600 = 4,150 + 1,200 = 5,350
q1_cr = (4,150) + (4,150+600) + (4,150+1,200) = 4,150 + 4,750 + 5,350 = 14,250
q1_reg = 600
# Verify: 5,350 + 14,250 + 600 = 20,200 ✓

# Q2 (subsequent — sys+tools cached from Q1)
q2_cw = (150 + 1,500) + (3-1) × 600 = 1,650 + 1,200 = 2,850
q2_cr = 2,500 + 4,150 + 4,750 + 5,350 = 16,750
q2_reg = 600
# Verify: 2,850 + 16,750 + 600 = 20,200 ✓

# Per session (1 Q1 + 1 Q2)
session_cw = 5,350 + 1 × 2,850 = 8,200
session_cr = 14,250 + 1 × 16,750 = 31,000
session_reg = 600 + 1 × 600 = 1,200
# Verify: 8,200 + 31,000 + 1,200 = 40,400 = 2 × 20,200 ✓

# Monthly (50,000 sessions)
monthly_cw = 8,200 × 50,000 = 410,000,000   (410M)
monthly_cr = 31,000 × 50,000 = 1,550,000,000  (1.55B)
monthly_reg = 1,200 × 50,000 = 60,000,000   (60M)

# Cache costs
cache_read_cost = (1,550,000,000 / 1,000,000) × 0.30 = $465.00
cache_write_cost = (410,000,000 / 1,000,000) × 3.75 = $1,537.50
regular_input_cost = (60,000,000 / 1,000,000) × 3.00 = $180.00

total_input_with_cache = $465.00 + $1,537.50 + $180.00 = $2,182.50

output_cost = $900.00

total_model_cost = $2,182.50 + $900.00 = $3,082.50

# Caching savings
savings = $6,060.00 - $2,182.50 = $3,877.50
savings_pct = $3,877.50 / $6,060.00 × 100 = 64.0%
```

**Expected answers:**
- base_context = **4,150**
- cacheable_base = **2,500**
- total_input_per_question = **20,200**
- total_output_per_question = **600**
- q1: cache_write = **5,350**, cache_read = **14,250**, regular = **600**
- q2: cache_write = **2,850**, cache_read = **16,750**, regular = **600**
- session: cache_write = **8,200**, cache_read = **31,000**, regular = **1,200** (total = **40,400** = 2 × 20,200 ✓)
- monthly: cache_write = **410,000,000**, cache_read = **1,550,000,000**, regular = **60,000,000**
- cache_read_cost = $465.00, cache_write_cost = $1,537.50, regular_cost = $180.00
- total_input_with_cache = **$2,182.50**
- total_model_cost = **$3,082.50**
- caching_savings_pct = **64.0%**

---

### Example C: Complex Agent — 5 Tools, Opus, With Caching

**Inputs:**
- sessions_per_month = 100,000
- questions_per_session = 3
- system_prompt_tokens = 2,000
- num_tools_provided = 10
- tokens_per_tool_description = 200
- input_tokens_per_question = 200
- rag_chunks = 10
- tokens_per_rag_chunk = 300
- tools_invoked_per_question = 5
- tool_call_tokens = 100
- tool_result_tokens = 500
- output_tokens_per_question = 500
- input_price = 5.00 (Opus)
- output_price = 25.00
- cache_read_price = 0.50
- cache_write_price = 6.25

**Calculations:**

```
base_context = 2,000 + (10 × 200) + 200 + (10 × 300) = 2,000 + 2,000 + 200 + 3,000 = 7,200
tool_delta = 100 + 500 = 600
turns = 5 + 1 = 6
questions_per_month = 100,000 × 3 = 300,000

# Input per question (compounding)
Turn 0: 7,200
Turn 1: 7,200 + 600 = 7,800
Turn 2: 7,200 + 1,200 = 8,400
Turn 3: 7,200 + 1,800 = 9,000
Turn 4: 7,200 + 2,400 = 9,600
Turn 5: 7,200 + 3,000 = 10,200

total_input_per_question = 7,200 + 7,800 + 8,400 + 9,000 + 9,600 + 10,200 = 52,200

# Closed-form: 6 × 7,200 + 600 × 5 × 6 / 2 = 43,200 + 9,000 = 52,200 ✓

total_output_per_question = 500 + 5 × 100 = 1,000

# Monthly
monthly_input_tokens = 52,200 × 300,000 = 15,660,000,000  (15.66B)
monthly_output_tokens = 1,000 × 300,000 = 300,000,000  (300M)

# No-cache baseline
no_cache_input_cost = (15,660,000,000 / 1,000,000) × 5.00 = $78,300.00
no_cache_output_cost = (300,000,000 / 1,000,000) × 25.00 = $7,500.00

# Session-aware caching (3 questions/session)
cacheable_base = 2,000 + 2,000 = 4,000
base_prompt = 7,200 (as above)
delta = 600, N = 5

# Q1 (first question — nothing cached)
q1_cw = 7,200 + (5-1) × 600 = 7,200 + 2,400 = 9,600
q1_cr = 7,200 + 7,800 + 8,400 + 9,000 + 9,600 = 42,000
q1_reg = 600
# Verify: 9,600 + 42,000 + 600 = 52,200 ✓

# Q2+ (subsequent — sys+tools cached from prior Q)
q2_cw = (200 + 3,000) + (5-1) × 600 = 3,200 + 2,400 = 5,600
q2_cr = 4,000 + 7,200 + 7,800 + 8,400 + 9,000 + 9,600 = 46,000
q2_reg = 600
# Verify: 5,600 + 46,000 + 600 = 52,200 ✓

# Per session (1 Q1 + 2 Q2)
session_cw = 9,600 + 2 × 5,600 = 20,800
session_cr = 42,000 + 2 × 46,000 = 134,000
session_reg = 600 + 2 × 600 = 1,800
# Verify: 20,800 + 134,000 + 1,800 = 156,600 = 3 × 52,200 ✓

# Monthly (100,000 sessions)
monthly_cw = 20,800 × 100,000 = 2,080,000,000  (2.08B)
monthly_cr = 134,000 × 100,000 = 13,400,000,000  (13.4B)
monthly_reg = 1,800 × 100,000 = 180,000,000  (180M)

# Cache costs
cache_read_cost = (13,400,000,000 / 1,000,000) × 0.50 = $6,700.00
cache_write_cost = (2,080,000,000 / 1,000,000) × 6.25 = $13,000.00
regular_input_cost = (180,000,000 / 1,000,000) × 5.00 = $900.00

total_input_with_cache = $6,700.00 + $13,000.00 + $900.00 = $20,600.00

output_cost = $7,500.00

total_model_cost = $20,600.00 + $7,500.00 = $28,100.00

# Caching savings
savings = $78,300.00 - $20,600.00 = $57,700.00
savings_pct = $57,700.00 / $78,300.00 × 100 = 73.7%
```

**Expected answers:**
- base_context = **7,200**
- cacheable_base = **4,000**
- total_input_per_question = **52,200**
- total_output_per_question = **1,000**
- q1: cache_write = **9,600**, cache_read = **42,000**, regular = **600**
- q2: cache_write = **5,600**, cache_read = **46,000**, regular = **600**
- session (3 Qs): cache_write = **20,800**, cache_read = **134,000**, regular = **1,800** (total = **156,600** = 3 × 52,200 ✓)
- monthly: cache_write = **2,080,000,000**, cache_read = **13,400,000,000**, regular = **180,000,000**
- cache_read_cost = $6,700.00, cache_write_cost = $13,000.00, regular_cost = $900.00
- total_input_with_cache = **$20,600.00**
- total_model_cost = **$28,100.00**
- caching_savings_pct = **73.7%**

---

### Example D: Business Value — Moderate Scenario

**Inputs:**
- sessions_per_month = 100,000
- time_without_ai_min = 15
- time_with_ai_min = 3
- human_cost_per_hour = 175
- agent_effectiveness_pct = 65
- efficiency_factor_pct = 60
- revenue_per_hour = 300
- agent_monthly_cost = 43,425

**Calculations:**

```
# Dimension 1a: Productivity Increase
effective_sessions = 100,000 × 0.65 = 65,000
time_saved_per_session = 15 - 3 = 12 min
total_hours_saved = 65,000 × 12 / 60 = 13,000 hours
productive_hours = 13,000 × 0.60 = 7,800 hours
productivity_value = 7,800 × 300 = $2,340,000
net_value_1a = $2,340,000 - $43,425 = $2,296,575
roi_1a = $2,340,000 / $43,425 = 53.9x

# Dimension 1b: Cost Savings
cost_savings = 13,000 × 175 = $2,275,000
net_value_1b = $2,275,000 - $43,425 = $2,231,575
roi_1b = $2,275,000 / $43,425 = 52.4x

# Human equivalent
hours_equivalent = 100,000 × 15 / 60 = 25,000 hours
fte_equivalent = 25,000 / 160 = 156.25 FTEs
human_cost_equivalent = 25,000 × 175 = $4,375,000
```

**Expected answers:**
- effective_sessions = **65,000**
- total_hours_saved = **13,000**
- productive_hours = **7,800**
- productivity_value_monthly = **$2,340,000**
- net_value_1a = **$2,296,575**
- roi_1a = **53.9x**
- cost_savings_monthly = **$2,275,000**
- fte_equivalent = **156.25**
- human_cost_equivalent = **$4,375,000**

---

## 9. Judge Verification Protocol

### 9.1 Self-Test (Runs First)

Before evaluating any test case, the judge MUST:
1. Reproduce all four reference examples (A, B, C, D) using only `run_python`
2. Compare every expected answer to its computed value
3. If ANY expected answer doesn't match → **ABORT** — the judge's logic is broken

### 9.2 Per Test Case Verification

For each test case, the judge:

1. **Compute token counts**: base_context, tool_delta, turns, total_input_per_question, total_output_per_question
2. **Compute monthly totals**: monthly_input_tokens, monthly_output_tokens
3. **Compute cache split**: cache_read, cache_write, regular per question; verify identity (sum = total)
4. **Compute costs**: cache costs, output cost, total model cost, no-cache baseline, savings
5. **Compute business value**: hours saved, productivity value, cost savings, ROI
6. **Compare ALL intermediate values** to skill output — flag discrepancy > 0.1%

### 9.3 Verdict Criteria

| Result | Condition |
|---|---|
| ✅ **PASS** | All intermediate values within 0.1% of skill output |
| ⚠️ **WARN** | All token/cost math correct, but AgentCore costs differ (AgentCore pricing has variable rates) |
| ❌ **FAIL** | Any token count, cache split, or dollar amount differs by > 1% |

---

## 10. Version History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-04-18 | Initial specification |
| 1.1 | 2026-04-18 | Updated to session-aware caching model (matches skill code); fixed output token formula; updated reference examples B & C |
