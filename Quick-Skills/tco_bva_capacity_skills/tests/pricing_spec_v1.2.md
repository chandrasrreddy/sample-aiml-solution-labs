# Bedrock Agent Pricing & Business Value — Specification v1.2

> **Purpose**: This document is the single source of truth for all pricing and business value calculations. The QA judge uses these formulas to independently verify skill output. A human can review this document once to trust all downstream automated testing.

---

## 1. Input Parameters

All calculations start from these inputs. The judge accepts them as-is — no questioning assumptions.

### 1.1 Model Pricing (per 1M tokens)

| Parameter | Symbol | Description |
|---|---|---|
| `input_price` | P_in | Standard input price per 1M tokens |
| `output_price` | P_out | Standard output price per 1M tokens |
| `cache_read_price` | P_cr | Cache read price per 1M tokens (None → 0.0) |
| `cache_write_price` | P_cw | Cache write price per 1M tokens (None → 0.0) |

### 1.2 Workload Shape

| Parameter | Symbol | Default | Description |
|---|---|---|---|
| `sessions_per_month` | S | — (required) | Total sessions per month |
| `questions_per_session` | Q_s | 5 | Questions per session. Fractional values supported (represent weighted average across sessions with varying question counts). |
| `system_prompt_tokens` | T_sys | 1,000 | System prompt size |
| `tool_desc_tokens` | T_tools | 4,000 | Total tool description tokens (all tools combined) |
| `input_tokens` | T_user | 100 | User's question text |
| `rag_chunks` | N_rag | 10 | RAG chunks retrieved per question |
| `rag_tokens_per_chunk` | T_rag_chunk | 300 | Tokens per RAG chunk |
| `tools_invoked` | N_invoke | 10 | Tool calls the model makes per question |
| `tool_call_tokens` | T_call | 100 | Output tokens per tool call (JSON) |
| `tool_result_tokens` | T_result | 500 | Input tokens per tool result |
| `output_tokens` | T_answer | 100 | Final answer tokens |

### 1.3 AgentCore Parameters

| Parameter | Symbol | Default | Description |
|---|---|---|---|
| `num_vcpus` | V | 2 | vCPUs allocated per microVM |
| `peak_memory_gb` | M_gb | 4 | Memory allocated (GB) |
| `io_wait_pct` | W | 0.70 | Fraction of time agent is waiting on I/O (vCPU is FREE during wait) |
| `idle_time_between_questions_s` | T_idle | 30 | User think time between questions in a session |
| `time_per_llm_turn_s` | T_turn | 4.0 | Seconds per LLM invocation |
| `tools_indexed` | N_gw | 50 | Tools indexed in Gateway |
| `stm_events_per_question` | — | 2 | Short-term memory write events per question (reads are free) |
| `ltm_records_per_session` | — | 3 | Long-term memory records extracted per session |
| `ltm_retrievals_per_question` | — | 1 | Long-term memory retrievals per question |

### 1.4 Business Value Parameters

| Parameter | Symbol | Default | Description |
|---|---|---|---|
| `time_without_ai_min` | T_manual | 20 | Minutes per task without AI |
| `time_with_ai_min` | T_ai | 10 | Minutes per task with AI |
| `human_cost_per_hour` | C_human | 75 | Fully-loaded human labor cost/hr |
| `revenue_per_hour` | R_hr | 300 | Revenue generated per productive employee hour |
| `total_customers` | — | 0 | Customer base for Dim 2 (0 = skip) |
| `churn_without_ai_pct` | — | 2.0 | Monthly churn rate without AI (%) |
| `churn_with_ai_pct` | — | 1.0 | Monthly churn rate with AI (%) |
| `revenue_per_customer_year` | — | 1,000 | Annual revenue per customer |
| `annual_sales_revenue` | — | 0 | Annual sales revenue for Dim 3 (0 = skip) |
| `sales_increase_pct` | — | 10.0 | AI-driven sales increase (%) |

**Business Value Tiers** (applied to Dim 1 only):

| Tier | Effectiveness (E) | Efficiency (F) |
|------|:-----------------:|:--------------:|
| Conservative | 50% | 50% |
| Moderate | 65% | 60% |
| Optimistic | 80% | 70% |

### 1.5 Capacity Parameters

| Parameter | Symbol | Default | Description |
|---|---|---|---|
| `rpm_limit` | — | — (required) | Actual RPM quota from `query_quotas()` for the specific model/region |
| `tpm_limit` | — | — (required) | Actual TPM quota from `query_quotas()` for the specific model/region |
| `peak_to_avg_ratio` | — | 3.0 | Peak RPM = average RPM × this factor |
| `active_hours_per_day` | — | 12 | Hours with traffic per day |
| `active_days_per_month` | — | 22 | Business days per month |
| `max_tokens_setting` | — | 4,096 | API max_tokens parameter |
| `output_burndown_rate` | — | 1 | Output TPM multiplier (5 for Claude 3.7+, 1 for others) |

---

## 2. Token Calculation Formulas

### 2.1 Base Context

```
rag_tokens = N_rag × T_rag_chunk
cacheable_base = T_sys + T_tools
base_prompt = cacheable_base + T_user + rag_tokens
```

### 2.2 Tool Delta

```
tool_delta = T_call + T_result
```

### 2.3 Turns Per Question

```
turns = N_invoke + 1
```

### 2.4 Input Tokens Per Question (Compounding)

Each turn re-sends the entire conversation so far:

```
Turn 0:  base_prompt
Turn 1:  base_prompt + 1 × tool_delta
Turn 2:  base_prompt + 2 × tool_delta
...
Turn N:  base_prompt + N_invoke × tool_delta
```

**Total (computed via loop in code):**

```
total_input_per_question = Σ(i=0 to N_invoke) [base_prompt + i × tool_delta]
```

**Closed-form (for verification):**

```
total_input_per_question = turns × base_prompt + tool_delta × N_invoke × turns / 2
```

### 2.5 Output Tokens Per Question

```
total_output_per_question = T_answer + N_invoke × T_call
```

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

### 3.1 Key Concepts

- **cacheable_base** = `T_sys + T_tools` — persists across questions in a session
- **base_prompt** = `cacheable_base + T_user + rag_tokens` — full turn-0 context
- **Billing**: cache_write = will be re-read next turn; cache_read = already cached; regular = last turn's new content (won't be re-read)

### 3.2 Special Case: N_invoke = 0 (No Tools)

When there are no tool invocations, there is only 1 turn per question:

```
Q1: q1_cache_write = base_prompt, q1_cache_read = 0, q1_regular = 0
Q2: q2_cache_write = T_user + rag_tokens, q2_cache_read = cacheable_base, q2_regular = 0
```

### 3.3 Session-Aware Caching Model (N_invoke ≥ 1)

#### Q1: First question in session (nothing cached yet)

| Turn | cache_read | cache_write | regular | Total |
|---|---|---|---|---|
| Turn 0 | 0 | base_prompt | 0 | base_prompt |
| Turn k (1 ≤ k < N) | base_prompt + (k-1)×delta | delta | 0 | base_prompt + k×delta |
| Turn N (final) | base_prompt + (N-1)×delta | 0 | delta | base_prompt + N×delta |

**Q1 totals:**

```
q1_cache_write = base_prompt + (N - 1) × delta
q1_cache_read  = Σ(k=1 to N) [base_prompt + (k-1) × delta]
q1_regular     = delta
```

**Verification**: `q1_cw + q1_cr + q1_reg = total_input_per_question`

#### Q2+: Subsequent questions in session

| Turn | cache_read | cache_write | regular | Total |
|---|---|---|---|---|
| Turn 0 | cacheable_base | T_user + rag_tokens | 0 | base_prompt |
| Turn k (1 ≤ k < N) | base_prompt + (k-1)×delta | delta | 0 | base_prompt + k×delta |
| Turn N (final) | base_prompt + (N-1)×delta | 0 | delta | base_prompt + N×delta |

**Q2 totals:**

```
q2_cache_write = (T_user + rag_tokens) + (N - 1) × delta
q2_cache_read  = cacheable_base + Σ(k=1 to N) [base_prompt + (k-1) × delta]
q2_regular     = delta
```

**Verification**: `q2_cw + q2_cr + q2_reg = total_input_per_question`

### 3.4 Per-Session and Monthly Totals

```
n_subsequent = Q_s - 1

session_cw  = q1_cache_write + n_subsequent × q2_cache_write
session_cr  = q1_cache_read  + n_subsequent × q2_cache_read
session_reg = q1_regular     + n_subsequent × q2_regular

monthly_cache_write   = S × session_cw
monthly_cache_read    = S × session_cr
monthly_regular_input = S × session_reg
```

**Verification identity (MUST hold):**

```
session_cw + session_cr + session_reg = Q_s × total_input_per_question
```

### 3.5 Cache Cost Formulas

```
cache_read_cost    = (monthly_cache_read    / 1,000,000) × P_cr
cache_write_cost   = (monthly_cache_write   / 1,000,000) × P_cw
regular_input_cost = (monthly_regular_input / 1,000,000) × P_in

total_input_cost_with_cache = cache_read_cost + cache_write_cost + regular_input_cost
```

### 3.6 Caching Savings

```
caching_savings_monthly = no_cache_total - total_model_cost
caching_savings_pct = caching_savings_monthly / no_cache_total × 100
```

Note: Savings percentage is computed against the full no-cache cost (input + output), not input-only. This reflects the actual percentage reduction in total bill.

### 3.7 Assumptions

- Prior question-response history is NOT cached across questions (only cacheable_base persists)
- Cache TTL is assumed infinite within a session (no eviction modeled)
- Cache hit rate is assumed 100% within a session

---

## 4. Total Model Cost

```
model_input_cost  = total_input_cost_with_cache  (if caching supported, else no_cache_input_cost)
model_output_cost = (monthly_output_tokens / 1,000,000) × P_out

total_model_cost = model_input_cost + model_output_cost
```

---

## 5. AgentCore Cost

### 5.1 Derived Values

```
sessions_per_month = questions_per_month / questions_per_session
time_per_question_s = (1 + N_invoke) × T_turn
active_cpu_per_question_s = time_per_question_s × (1 - W)
total_active_cpu_per_session_s = active_cpu_per_question_s × Q_s
idle_gaps_s = (Q_s - 1) × T_idle
total_session_duration_s = (time_per_question_s × Q_s) + idle_gaps_s
```

### 5.2 Runtime

vCPU is billed only during active processing (I/O wait is free). Memory is billed for full session duration.

```
runtime_cpu_cost = total_active_cpu_per_session_s × V × (vcpu_price_hr / 3600) × sessions_per_month
runtime_mem_cost = total_session_duration_s × M_gb × (mem_price_hr / 3600) × sessions_per_month
runtime_total = runtime_cpu_cost + runtime_mem_cost
```

### 5.3 Gateway

```
gateway_invocations = (1 + N_invoke) × questions_per_month
gateway_searches = questions_per_month
gateway_inv_cost = gateway_invocations × invocation_price
gateway_search_cost = gateway_searches × search_price
gateway_index_cost = N_gw × indexing_price
gateway_total = gateway_inv_cost + gateway_search_cost + gateway_index_cost
```

### 5.4 Memory

```
stm_cost = stm_events_per_question × questions_per_month × stm_event_price
ltm_storage_cost = ltm_records_per_session × sessions_per_month × ltm_storage_price
ltm_retrieval_cost = ltm_retrievals_per_question × questions_per_month × ltm_retrieval_price
memory_total = stm_cost + ltm_storage_cost + ltm_retrieval_cost
```

Note: STM reads are free — only writes are billed. LTM storage is modeled as a flat monthly cost (not cumulative).

### 5.5 BrowserTool and CodeInterpreter (Optional)

Included only when prices are provided (not None). No I/O wait discount — billed for full duration.

```
browser_total = time_per_question_s × browser_questions × browser_vcpus × (vcpu_price / 3600)
             + time_per_question_s × browser_questions × browser_memory_gb × (mem_price / 3600)
```

Same pattern for CodeInterpreter.

### 5.6 Total AgentCore

```
total_agentcore = runtime_total + gateway_total + memory_total + browser_total + ci_total
```

---

## 6. Capacity Planning

### 6.1 RPM Calculation

```
active_minutes_per_month = active_hours_per_day × 60 × active_days_per_month
avg_questions_per_min = questions_per_month / active_minutes_per_month
avg_rpm = avg_questions_per_min × (N_invoke + 1)    # each question = N+1 LLM calls
peak_rpm = avg_rpm × peak_to_avg_ratio
```

### 6.2 TPM Calculation

```
base_context = T_user + T_sys + T_tools + (N_rag × T_rag_chunk)
delta = T_call + T_result
avg_input_per_turn = base_context + (delta / 2) × N_invoke
avg_output_per_turn = (N_invoke × T_call + T_answer) / (N_invoke + 1)    # weighted average

avg_tpm = avg_rpm × (avg_input_per_turn + avg_output_per_turn × output_burndown_rate)
peak_tpm = avg_tpm × peak_to_avg_ratio
```

### 6.3 Effective TPM (with max_tokens overhead)

At request start, `max_tokens` is reserved from TPM quota regardless of actual output:

```
max_tokens_overhead_per_req = max(0, max_tokens_setting - avg_output_per_turn)
effective_peak_tpm = peak_tpm + (peak_rpm × max_tokens_overhead_per_req)
```

### 6.4 Quota Comparison

`rpm_limit` and `tpm_limit` are REQUIRED parameters — obtained from `query_quotas()` for the specific model and region. No hardcoded fallback.

```
rpm_fits = peak_rpm ≤ rpm_limit
tpm_fits = effective_peak_tpm ≤ tpm_limit
fits = rpm_fits AND tpm_fits
```

---

## 7. Grand Total

```
total_monthly = total_model_cost + total_agentcore
total_annual  = total_monthly × 12
per_session   = total_monthly / sessions_per_month
per_question  = total_monthly / questions_per_month
```

---

## 8. Business Value Formulas

### 8.1 Dimension 1a — Productivity Increase (Revenue Uplift)

Computed for all 3 tiers (Conservative, Moderate, Optimistic):

```
time_saved_min = T_manual - T_ai
effective_sessions = S × E
time_saved_hrs = effective_sessions × time_saved_min / 60
productive_hrs = time_saved_hrs × F
productivity_value_monthly = productive_hrs × R_hr
```

If `time_saved_min < 0`, a warning is issued (rare scenario: AI takes longer than manual).

### 8.2 Dimension 1b — Cost Savings (Mutually Exclusive with 1a)

Uses the same `productive_hrs` as Dim 1a (applies both effectiveness AND efficiency):

```
cost_savings_monthly = productive_hrs × C_human
```

Note: Both 1a and 1b use `productive_hrs` (after efficiency factor). They differ only in the rate applied: `R_hr` for productivity, `C_human` for cost savings.

### 8.3 Dimension 2 — Customer Churn Reduction (Optional)

Included only when `total_customers > 0`:

```
churn_reduction_pp = churn_without_ai_pct - churn_with_ai_pct
customers_retained = total_customers × (churn_reduction_pp / 100)
dim2_annual = customers_retained × revenue_per_customer_year
```

### 8.4 Dimension 3 — Sales Increase from Better CX (Optional)

Included only when `annual_sales_revenue > 0`:

```
dim3_annual = annual_sales_revenue × (sales_increase_pct / 100)
```

### 8.5 Summary (uses Moderate tier for Dim 1a)

```
grand_total_annual = dim1a_moderate_annual + dim2_annual + dim3_annual
agent_cost_annual = agent_cost_monthly × 12
net_value = grand_total_annual - agent_cost_annual
roi_pct = (net_value / agent_cost_annual) × 100    # net ROI as percentage
payback_days = (agent_cost_annual / grand_total_annual) × 365
```

Special cases:
- `agent_cost_annual = 0` → `roi_pct = ∞`
- `grand_total_annual = 0` → `payback_days = ∞`

### 8.6 Human Equivalent (not computed by current code, informational only)

```
hours_equivalent = S × T_manual / 60
fte_equivalent = hours_equivalent / 160
human_cost_equivalent = hours_equivalent × C_human
```

---

## 9. Reference Examples (Hand-Verified)

### Example A: Simple Agent — No Tools, No Caching

**Inputs:**
- sessions_per_month = 10,000, questions_per_session = 1
- system_prompt_tokens = 1,000, tool_desc_tokens = 0
- input_tokens = 100, rag_chunks = 0, tools_invoked = 0
- output_tokens = 200
- P_in = 5.00, P_out = 25.00

**Calculations:**

```
cacheable_base = 1,000 + 0 = 1,000
base_prompt = 1,000 + 100 + 0 = 1,100
turns = 1, delta = 600

total_input_per_question = 1,100
total_output_per_question = 200

questions_per_month = 10,000
monthly_input = 11,000,000
monthly_output = 2,000,000

no_cache_total = $55.00 + $50.00 = $105.00
```

**Cache splits (N=0 special case):**
```
Q1: cw = 1,100, cr = 0, reg = 0  (sum = 1,100 ✓)
```

**Expected:** no_cache_total = **$105.00**

---

### Example B: Medium Agent — 3 Tools, With Caching

**Inputs:**
- sessions_per_month = 50,000, questions_per_session = 2
- system_prompt_tokens = 1,500, tool_desc_tokens = 1,000
- input_tokens = 150, rag_chunks = 5, tools_invoked = 3
- output_tokens = 300
- P_in = 3.00, P_out = 15.00, P_cr = 0.30, P_cw = 3.75

**Calculations:**

```
cacheable_base = 1,500 + 1,000 = 2,500
base_prompt = 2,500 + 150 + 1,500 = 4,150
delta = 600, turns = 4

total_input_per_question = 4,150 + 4,750 + 5,350 + 5,950 = 20,200
total_output_per_question = 300 + 300 = 600

Q1: cw = 5,350, cr = 14,250, reg = 600  (sum = 20,200 ✓)
Q2: cw = 2,850, cr = 16,750, reg = 600  (sum = 20,200 ✓)
Session: cw = 8,200, cr = 31,000, reg = 1,200  (sum = 40,400 = 2 × 20,200 ✓)

total_model_cost = $3,082.50
caching_savings_pct = 55.7%
```

**Expected:** total_model_cost = **$3,082.50**, savings = **55.7%**

---

### Example C: Complex Agent — 5 Tools, Opus, With Caching

**Inputs:**
- sessions_per_month = 100,000, questions_per_session = 3
- system_prompt_tokens = 2,000, tool_desc_tokens = 2,000
- input_tokens = 200, rag_chunks = 10, tools_invoked = 5
- output_tokens = 500
- P_in = 5.00, P_out = 25.00, P_cr = 0.50, P_cw = 6.25

**Calculations:**

```
cacheable_base = 2,000 + 2,000 = 4,000
base_prompt = 4,000 + 200 + 3,000 = 7,200
delta = 600, turns = 6

total_input_per_question = 52,200
total_output_per_question = 1,000

Q1: cw = 9,600, cr = 42,000, reg = 600  (sum = 52,200 ✓)
Q2: cw = 5,600, cr = 46,000, reg = 600  (sum = 52,200 ✓)
Session: cw = 20,800, cr = 134,000, reg = 1,800  (sum = 156,600 = 3 × 52,200 ✓)

total_model_cost = $28,100.00
caching_savings_pct = 67.2%
```

**Expected:** total_model_cost = **$28,100.00**, savings = **67.2%**

---

### Example D: Business Value — Moderate Tier

**Inputs:**
- sessions_per_month = 100,000
- time_without_ai_min = 15, time_with_ai_min = 3
- human_cost_per_hour = 175, revenue_per_hour = 300
- agent_cost_monthly = 43,425

**Calculations (Moderate tier: E=0.65, F=0.60):**

```
time_saved = 15 - 3 = 12 min
effective_sessions = 100,000 × 0.65 = 65,000
time_saved_hrs = 65,000 × 12 / 60 = 13,000
productive_hrs = 13,000 × 0.60 = 7,800

Dim 1a: productivity_value = 7,800 × 300 = $2,340,000/mo
Dim 1b: cost_savings = 7,800 × 175 = $1,365,000/mo

agent_cost_annual = $43,425 × 12 = $521,100
grand_total_annual (1a only) = $2,340,000 × 12 = $28,080,000
net_value = $28,080,000 - $521,100 = $27,558,900
roi_pct = ($27,558,900 / $521,100) × 100 = 5,289%
payback_days = ($521,100 / $28,080,000) × 365 = 6.8 days
```

**Expected:**
- productive_hours = **7,800**
- productivity_value_monthly = **$2,340,000**
- cost_savings_monthly = **$1,365,000**
- roi_pct = **5,289%**
- payback_days = **6.8**

---

### Example E: AgentCore Cost

Uses Example C's workload (100K sessions, 3 Q/session, 5 tools) with us-east-1 AgentCore prices.

**Inputs:**
- questions_per_month = 300,000, questions_per_session = 3
- tools_invoked = 5, tools_indexed = 10
- num_vcpus = 2, peak_memory_gb = 4, io_wait_pct = 0.70
- idle_time_between_questions_s = 30, time_per_llm_turn_s = 4.0
- stm_events_per_question = 2, ltm_records_per_session = 3, ltm_retrievals_per_question = 1
- Prices: vcpu=$0.0895/hr, mem=$0.00945/hr, invocation=$0.000005, search=$0.000025, indexing=$0.0002, stm=$0.00025, ltm_storage=$0.00075, ltm_retrieval=$0.0005

**Calculations:**

```
sessions_per_month = 300,000 / 3 = 100,000
time_per_question_s = (1 + 5) × 4.0 = 24.0s
active_cpu_per_question_s = 24.0 × 0.30 = 7.2s
total_active_cpu_per_session_s = 7.2 × 3 = 21.6s
idle_gaps_s = (3 - 1) × 30 = 60s
total_session_duration_s = (24.0 × 3) + 60 = 132.0s

Runtime:
  cpu = 21.6 × 2 × (0.0895 / 3600) × 100,000 = $107.40
  mem = 132.0 × 4 × (0.00945 / 3600) × 100,000 = $138.60
  total = $246.00

Gateway:
  invocations = (1 + 5) × 300,000 = 1,800,000 × $0.000005 = $9.00
  searches = 300,000 × $0.000025 = $7.50
  indexing = 10 × $0.0002 = $0.002
  total = $16.50

Memory:
  stm = 2 × 300,000 × $0.00025 = $150.00
  ltm_storage = 3 × 100,000 × $0.00075 = $225.00
  ltm_retrieval = 1 × 300,000 × $0.0005 = $150.00
  total = $525.00

total_agentcore = $246.00 + $16.50 + $525.00 = $787.50
```

**Expected:** total_agentcore = **$787.50** (Runtime $246.00, Gateway $16.50, Memory $525.00)

---

### Example F: Capacity Check

Uses Example C's workload with Claude output burndown rate (5×).

**Inputs:**
- questions_per_month = 300,000, sessions_per_month = 100,000
- tools_invoked = 5, input_tokens = 200, output_tokens = 500
- system_prompt_tokens = 2,000, tool_desc_tokens = 2,000
- rag_chunks = 10, rag_tokens_per_chunk = 300
- tool_call_tokens = 100, tool_result_tokens = 500
- max_tokens_setting = 4,096, output_burndown_rate = 5
- peak_to_avg_ratio = 3.0, active_hours_per_day = 12, active_days_per_month = 22
- rpm_limit = 500, tpm_limit = 150,000 (from query_quotas)

**Calculations:**

```
active_minutes_per_month = 12 × 60 × 22 = 15,840
avg_questions_per_min = 300,000 / 15,840 = 18.94
avg_rpm = 18.94 × 6 = 113.64
peak_rpm = 113.64 × 3.0 = 340.91

base_context = 200 + 2,000 + 2,000 + 3,000 = 7,200
delta = 600
avg_input_per_turn = 7,200 + (600 / 2) × 5 = 8,700
avg_output_per_turn = (5 × 100 + 500) / 6 = 166

avg_tpm = 113.64 × (8,700 + 166 × 5) = 113.64 × 9,530 = 1,082,955
peak_tpm = 1,082,955 × 3.0 = 3,248,864

max_tokens_overhead = max(0, 4,096 - 166) = 3,930
effective_peak_tpm = 3,248,864 + (340.91 × 3,930) = 4,588,636

rpm_fits = 340.91 ≤ 500 → True
tpm_fits = 4,588,636 ≤ 150,000 → False
fits = False

rpm_utilization = 68.2%
tpm_utilization = 3,059.1%
```

**Expected:**
- peak_rpm = **340.91** (fits Standard ✓)
- effective_peak_tpm = **4,588,636** (exceeds Standard by 30× ✗)
- fits = **False** (TPM is the bottleneck)

---

### Example G: Business Value with Dims 2 & 3

Extends Example D with churn reduction and sales increase.

**Inputs:**
- sessions_per_month = 100,000, agent_cost_monthly = 43,425
- time_without_ai_min = 15, time_with_ai_min = 3
- human_cost_per_hour = 175, revenue_per_hour = 300
- total_customers = 500,000, churn_without_ai_pct = 3.0, churn_with_ai_pct = 2.0, revenue_per_customer_year = 5,000
- annual_sales_revenue = 500,000,000, sales_increase_pct = 2.0

**Calculations:**

```
# Dim 1a (Moderate) — same as Example D
productivity_value_monthly = $2,340,000
dim1a_annual = $2,340,000 × 12 = $28,080,000

# Dim 2: Churn Reduction
churn_reduction_pp = 3.0 - 2.0 = 1.0 pp
customers_retained = 500,000 × (1.0 / 100) = 5,000
dim2_annual = 5,000 × $5,000 = $25,000,000

# Dim 3: Sales Increase
dim3_annual = $500,000,000 × (2.0 / 100) = $10,000,000

# Summary
grand_total = $28,080,000 + $25,000,000 + $10,000,000 = $63,080,000
agent_cost_annual = $43,425 × 12 = $521,100
net_value = $63,080,000 - $521,100 = $62,558,900
roi_pct = ($62,558,900 / $521,100) × 100 = 12,005%
payback_days = ($521,100 / $63,080,000) × 365 = 3.0 days
```

**Expected:**
- dim2_annual = **$25,000,000**
- dim3_annual = **$10,000,000**
- grand_total = **$63,080,000**
- roi_pct = **12,005%**
- payback_days = **3.0**

---

## 10. Judge Verification Protocol

### 10.1 Self-Test (Runs First)

Before evaluating any test case, the judge MUST:
1. Reproduce all seven reference examples (A through G) using only `run_python`
2. Compare every expected answer to its computed value
3. If ANY expected answer doesn't match → **ABORT** — the judge's logic is broken

### 10.2 Per Test Case Verification

For each test case, the judge:

1. **Compute token counts**: base_prompt, tool_delta, turns, total_input_per_question, total_output_per_question
2. **Compute monthly totals**: monthly_input_tokens, monthly_output_tokens
3. **Compute cache split**: Handle N=0 special case. For N≥1, compute Q1/Q2 splits. Verify sum identity.
4. **Compute costs**: cache costs, output cost, total model cost, no-cache baseline, savings
5. **Compute business value**: all 3 tiers, Dims 2/3 if applicable, summary with net ROI %
6. **Compare ALL intermediate values** to skill output — flag discrepancy > 0.1%

### 10.3 Verdict Criteria

| Result | Condition |
|---|---|
| ✅ **PASS** | All intermediate values within 0.1% of skill output |
| ⚠️ **WARN** | All token/cost math correct, but AgentCore costs differ (AC pricing has variable rates) |
| ❌ **FAIL** | Any token count, cache split, or dollar amount differs by > 1% |

---

## 11. Version History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-04-18 | Initial specification |
| 1.1 | 2026-04-18 | Updated to session-aware caching model; fixed output token formula; updated reference examples B & C |
| 1.2 | 2026-04-20 | Synced all defaults with Python code. Added N=0 cache split special case. Added capacity planning formulas (§6). Updated AgentCore formulas to match code (per-component with I/O wait, idle gaps). Updated business value: Dim 1b now uses productive_hrs (with efficiency factor), ROI is net percentage, added Dims 2/3, 3 tiers, payback_days. Added caching assumptions. Added Examples E (AgentCore), F (Capacity), G (Business Value Dims 2&3). Renamed parameters to match code. |
