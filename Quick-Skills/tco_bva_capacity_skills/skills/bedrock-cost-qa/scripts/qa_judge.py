"""
Bedrock Cost QA Judge — Spec v1.1 Independent Verification
Runs self-tests against reference examples, then verifies external estimates.
"""
import json, os

# Import the test generator functions (same formulas)
# The judge re-implements the spec formulas for independence

SPEC_EXAMPLES = {
    "A": {
        "desc": "Simple Agent — No Tools, No Caching",
        "params": {
            "sessions_per_month": 10000, "questions_per_session": 1,
            "system_prompt_tokens": 1000, "num_tools": 0,
            "tokens_per_tool_description": 200, "input_tokens_per_question": 100,
            "rag_chunks": 0, "tokens_per_rag_chunk": 300,
            "tools_invoked": 0, "tool_call_tokens": 100,
            "tool_result_tokens": 500, "output_tokens_per_question": 200,
        },
        "prices": {"input": 5.00, "output": 25.00, "cache_read": 0, "cache_write": 0},
        "expected": {
            "base_context": 1100,
            "total_input_per_question": 1100,
            "total_output_per_question": 200,
            "monthly_input_tokens": 11_000_000,
            "monthly_output_tokens": 2_000_000,
            "no_cache_total": 105.00,
        },
    },
    "B": {
        "desc": "Medium Agent — 3 Tools, With Caching",
        "params": {
            "sessions_per_month": 50000, "questions_per_session": 2,
            "system_prompt_tokens": 1500, "num_tools": 5,
            "tokens_per_tool_description": 200, "input_tokens_per_question": 150,
            "rag_chunks": 5, "tokens_per_rag_chunk": 300,
            "tools_invoked": 3, "tool_call_tokens": 100,
            "tool_result_tokens": 500, "output_tokens_per_question": 300,
        },
        "prices": {"input": 3.00, "output": 15.00, "cache_read": 0.30, "cache_write": 3.75},
        "expected": {
            "base_context": 4150, "cacheable_base": 2500,
            "total_input_per_question": 20200,
            "total_output_per_question": 600,
            "q1_cache_write": 5350, "q1_cache_read": 14250, "q1_regular": 600,
            "q2_cache_write": 2850, "q2_cache_read": 16750, "q2_regular": 600,
            "session_cache_write": 8200, "session_cache_read": 31000, "session_regular": 1200,
            "total_model_cost": 3082.50, "caching_savings_pct": 64.0,
        },
    },
    "C": {
        "desc": "Complex Agent — 5 Tools, Opus, With Caching",
        "params": {
            "sessions_per_month": 100000, "questions_per_session": 3,
            "system_prompt_tokens": 2000, "num_tools": 10,
            "tokens_per_tool_description": 200, "input_tokens_per_question": 200,
            "rag_chunks": 10, "tokens_per_rag_chunk": 300,
            "tools_invoked": 5, "tool_call_tokens": 100,
            "tool_result_tokens": 500, "output_tokens_per_question": 500,
        },
        "prices": {"input": 5.00, "output": 25.00, "cache_read": 0.50, "cache_write": 6.25},
        "expected": {
            "base_context": 7200, "cacheable_base": 4000,
            "total_input_per_question": 52200,
            "total_output_per_question": 1000,
            "q1_cache_write": 9600, "q1_cache_read": 42000, "q1_regular": 600,
            "q2_cache_write": 5600, "q2_cache_read": 46000, "q2_regular": 600,
            "session_cache_write": 20800, "session_cache_read": 134000, "session_regular": 1800,
            "total_model_cost": 28100.00, "caching_savings_pct": 73.7,
        },
    },
    "D": {
        "desc": "Business Value — Moderate Scenario",
        "params": {
            "sessions_per_month": 100000,
            "time_without_ai_min": 15, "time_with_ai_min": 3,
            "human_cost_per_hour": 175, "revenue_per_hour": 300,
        },
        "agent_cost": 43425,
        "expected": {
            "effective_sessions": 65000,
            "total_hours_saved": 13000,
            "productive_hours": 7800,
            "productivity_value": 2340000,
            "cost_savings": 2275000,
            "net_1a": 2296575,
            "roi_1a": 53.9,
            "fte_equivalent": 156.25,
            "human_cost_equivalent": 4375000,
        },
    },
}


def _compute_tokens(params):
    T_sys = params["system_prompt_tokens"]
    N_tools = params["num_tools"]
    T_td = params["tokens_per_tool_description"]
    T_user = params["input_tokens_per_question"]
    N_rag = params["rag_chunks"]
    T_rc = params["tokens_per_rag_chunk"]
    N_inv = params["tools_invoked"]
    T_call = params["tool_call_tokens"]
    T_res = params["tool_result_tokens"]
    T_ans = params["output_tokens_per_question"]

    base_context = T_sys + N_tools * T_td + T_user + N_rag * T_rc
    cacheable_base = T_sys + N_tools * T_td
    delta = T_call + T_res
    turns = N_inv + 1
    total_in = turns * base_context + delta * N_inv * turns // 2
    total_out = T_ans + N_inv * T_call
    return base_context, cacheable_base, delta, N_inv, total_in, total_out, T_user, N_rag * T_rc


def _compute_cache(base_prompt, cacheable_base, delta, N, T_user, T_rag, Q_s):
    q1_cw = base_prompt + (N - 1) * delta
    q1_cr = sum(base_prompt + (k - 1) * delta for k in range(1, N + 1))
    q1_reg = delta
    q2_cw = (T_user + T_rag) + (N - 1) * delta
    q2_cr = cacheable_base + sum(base_prompt + (k - 1) * delta for k in range(1, N + 1))
    q2_reg = delta
    n_sub = Q_s - 1
    s_cw = q1_cw + n_sub * q2_cw
    s_cr = q1_cr + n_sub * q2_cr
    s_reg = q1_reg + n_sub * q2_reg
    return q1_cw, q1_cr, q1_reg, q2_cw, q2_cr, q2_reg, s_cw, s_cr, s_reg


def run_self_test():
    """Reproduce all 4 spec reference examples. Returns dict of pass/fail per example."""
    results = {}

    for ex_id in ["A", "B", "C", "D"]:
        ex = SPEC_EXAMPLES[ex_id]
        expected = ex["expected"]
        fields = {}
        all_pass = True

        if ex_id in ("A", "B", "C"):
            p = ex["params"]
            prices = ex["prices"]
            bc, cb, delta, N_inv, tot_in, tot_out, T_user, T_rag = _compute_tokens(p)

            checks = {"base_context": bc, "total_input_per_question": tot_in, "total_output_per_question": tot_out}
            if "cacheable_base" in expected:
                checks["cacheable_base"] = cb

            S = p["sessions_per_month"]
            Q_s = p["questions_per_session"]
            questions = S * Q_s

            if ex_id in ("B", "C"):
                q1_cw, q1_cr, q1_reg, q2_cw, q2_cr, q2_reg, s_cw, s_cr, s_reg = _compute_cache(
                    bc, cb, delta, N_inv, T_user, T_rag, Q_s
                )
                checks.update({
                    "q1_cache_write": q1_cw, "q1_cache_read": q1_cr, "q1_regular": q1_reg,
                    "q2_cache_write": q2_cw, "q2_cache_read": q2_cr, "q2_regular": q2_reg,
                    "session_cache_write": s_cw, "session_cache_read": s_cr, "session_regular": s_reg,
                })
                m_cw, m_cr, m_reg = S * s_cw, S * s_cr, S * s_reg
                cr_cost = (m_cr / 1e6) * prices["cache_read"]
                cw_cost = (m_cw / 1e6) * prices["cache_write"]
                reg_cost = (m_reg / 1e6) * prices["input"]
                out_cost = (tot_out * questions / 1e6) * prices["output"]
                model_cost = cr_cost + cw_cost + reg_cost + out_cost
                no_cache_in = (tot_in * questions / 1e6) * prices["input"]
                savings_pct = round((no_cache_in - (cr_cost + cw_cost + reg_cost)) / no_cache_in * 100, 1)
                checks["total_model_cost"] = round(model_cost, 2)
                checks["caching_savings_pct"] = savings_pct
            else:
                m_in = tot_in * questions
                m_out = tot_out * questions
                checks["monthly_input_tokens"] = m_in
                checks["monthly_output_tokens"] = m_out
                no_cache = round((m_in / 1e6) * prices["input"] + (m_out / 1e6) * prices["output"], 2)
                checks["no_cache_total"] = no_cache

            for field, computed in checks.items():
                exp_val = expected.get(field)
                if exp_val is not None:
                    match = abs(computed - exp_val) < 0.01 * max(abs(exp_val), 1)
                    fields[field] = {"expected": exp_val, "computed": computed, "pass": match}
                    if not match:
                        all_pass = False

        elif ex_id == "D":
            p = ex["params"]
            S = p["sessions_per_month"]
            E, F = 0.65, 0.60
            T_manual, T_ai = p["time_without_ai_min"], p["time_with_ai_min"]
            C_human, R_hr = p["human_cost_per_hour"], p["revenue_per_hour"]
            agent_cost = ex["agent_cost"]

            eff = S * E
            hrs_saved = eff * (T_manual - T_ai) / 60
            prod_hrs = hrs_saved * F
            prod_val = prod_hrs * R_hr
            cost_sav = hrs_saved * C_human
            net_1a = prod_val - agent_cost
            roi_1a = round(prod_val / agent_cost, 1)
            hrs_eq = S * T_manual / 60
            fte = round(hrs_eq / 160, 2)
            human_cost = hrs_eq * C_human

            checks = {
                "effective_sessions": eff, "total_hours_saved": hrs_saved,
                "productive_hours": prod_hrs, "productivity_value": prod_val,
                "cost_savings": cost_sav, "net_1a": net_1a, "roi_1a": roi_1a,
                "fte_equivalent": fte, "human_cost_equivalent": human_cost,
            }
            for field, computed in checks.items():
                exp_val = expected.get(field)
                if exp_val is not None:
                    match = abs(computed - exp_val) < 0.01 * max(abs(exp_val), 1)
                    fields[field] = {"expected": exp_val, "computed": computed, "pass": match}
                    if not match:
                        all_pass = False

        results[ex_id] = {"desc": ex["desc"], "pass": all_pass, "fields": fields}

    return results


def judge_estimate(estimate_data, test_spec=None):
    """Judge an estimate against expected values. Returns comparison report."""
    # If test spec provided, use its expected values
    # Otherwise, recompute from estimate's inputs
    if test_spec:
        expected = test_spec["expected"]
        inputs = test_spec["inputs"]
    else:
        # Recompute from estimate's stated inputs
        inputs = estimate_data.get("inputs", {})
        # Would need to run full computation here
        return {"error": "No test spec provided and estimate doesn't contain enough inputs to recompute"}

    # Compare each field
    comparisons = {}
    for section, section_data in expected.items():
        if isinstance(section_data, dict):
            for field, exp_val in section_data.items():
                if isinstance(exp_val, (int, float)):
                    # Try to find matching value in estimate
                    actual = _find_in_nested(estimate_data, field)
                    if actual is not None:
                        pct_diff = abs(exp_val - actual) / max(abs(exp_val), 0.01) * 100
                        if pct_diff <= 0.1:
                            status = "PASS"
                        elif pct_diff <= 1.0:
                            status = "WARN"
                        else:
                            status = "FAIL"
                        comparisons[f"{section}.{field}"] = {
                            "expected": exp_val, "actual": actual,
                            "pct_diff": round(pct_diff, 2), "status": status,
                        }

    overall = "PASS"
    for comp in comparisons.values():
        if comp["status"] == "FAIL":
            overall = "FAIL"
            break
        if comp["status"] == "WARN" and overall == "PASS":
            overall = "WARN"

    return {"overall": overall, "comparisons": comparisons}


def _find_in_nested(d, key):
    """Recursively search for a key in nested dicts."""
    if isinstance(d, dict):
        if key in d:
            return d[key]
        for v in d.values():
            result = _find_in_nested(v, key)
            if result is not None:
                return result
    return None
