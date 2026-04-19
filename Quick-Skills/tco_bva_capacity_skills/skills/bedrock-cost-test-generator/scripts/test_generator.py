"""
Bedrock Cost Test Generator — Spec v1.1 Formula Implementation
Generates JSON test specs with all expected intermediate and final values.
"""
import json, os
from datetime import datetime

# ─── SPEC DEFAULTS ───
DEFAULTS = {
    "system_prompt_tokens": 2000,
    "tokens_per_tool_description": 200,
    "input_tokens_per_question": 200,
    "rag_chunks": 10,
    "tokens_per_rag_chunk": 300,
    "tool_call_tokens": 100,
    "tool_result_tokens": 500,
    "output_tokens_per_question": 500,
    "runtime_vcpus": 2,
    "runtime_memory_gb": 4.0,
    "runtime_wait_pct": 0.70,
    "tools_indexed_in_gateway": 10,
    "time_without_ai_min": 20,
    "time_with_ai_min": 10,
    "human_cost_per_hour": 75,
    "revenue_per_hour": 300,
    "idle_gap_s": 30,
}

BV_TIERS = {
    "conservative": {"effectiveness": 0.50, "efficiency": 0.50},
    "moderate":     {"effectiveness": 0.65, "efficiency": 0.60},
    "optimistic":   {"effectiveness": 0.80, "efficiency": 0.70},
}


def compute_tokens(params):
    """Compute all token intermediates per spec Section 2."""
    T_sys = params["system_prompt_tokens"]
    N_tools = params["num_tools"]
    T_tool_desc = params["tokens_per_tool_description"]
    T_user = params["input_tokens_per_question"]
    N_rag = params["rag_chunks"]
    T_rag_chunk = params["tokens_per_rag_chunk"]
    N_invoke = params["tools_invoked"]
    T_call = params["tool_call_tokens"]
    T_result = params["tool_result_tokens"]
    T_answer = params["output_tokens_per_question"]

    base_context = T_sys + (N_tools * T_tool_desc) + T_user + (N_rag * T_rag_chunk)
    cacheable_base = T_sys + (N_tools * T_tool_desc)
    T_rag = N_rag * T_rag_chunk
    tool_delta = T_call + T_result
    turns = N_invoke + 1

    total_input_per_question = turns * base_context + tool_delta * N_invoke * turns // 2
    total_output_per_question = T_answer + N_invoke * T_call

    return {
        "base_context": base_context,
        "cacheable_base": cacheable_base,
        "T_rag": T_rag,
        "tool_delta": tool_delta,
        "turns": turns,
        "total_input_per_question": total_input_per_question,
        "total_output_per_question": total_output_per_question,
    }


def compute_cache_splits(tokens, params):
    """Compute cache splits per spec Section 3."""
    base_prompt = tokens["base_context"]
    cacheable_base = tokens["cacheable_base"]
    delta = tokens["tool_delta"]
    N = params["tools_invoked"]
    T_user = params["input_tokens_per_question"]
    T_rag = tokens["T_rag"]
    Q_s = params["questions_per_session"]

    # Q1
    q1_cw = base_prompt + (N - 1) * delta
    q1_cr = sum(base_prompt + (k - 1) * delta for k in range(1, N + 1))
    q1_reg = delta

    # Q2+
    q2_cw = (T_user + T_rag) + (N - 1) * delta
    q2_cr = cacheable_base + sum(base_prompt + (k - 1) * delta for k in range(1, N + 1))
    q2_reg = delta

    # Session
    n_sub = Q_s - 1
    session_cw = q1_cw + n_sub * q2_cw
    session_cr = q1_cr + n_sub * q2_cr
    session_reg = q1_reg + n_sub * q2_reg

    # Verifications
    q1_check = q1_cw + q1_cr + q1_reg == tokens["total_input_per_question"]
    q2_check = q2_cw + q2_cr + q2_reg == tokens["total_input_per_question"]
    session_check = session_cw + session_cr + session_reg == Q_s * tokens["total_input_per_question"]

    return {
        "q1_cache_write": q1_cw, "q1_cache_read": q1_cr, "q1_regular": q1_reg,
        "q2_cache_write": q2_cw, "q2_cache_read": q2_cr, "q2_regular": q2_reg,
        "session_cache_write": session_cw, "session_cache_read": session_cr, "session_regular": session_reg,
        "verifications": {"q1_sum_check": q1_check, "q2_sum_check": q2_check, "session_sum_check": session_check},
    }


def compute_costs(tokens, cache_splits, params, prices):
    """Compute all costs per spec Sections 2.7, 3.4, 4."""
    S = params["sessions_per_month"]
    Q_s = params["questions_per_session"]
    questions = S * Q_s
    P_in, P_out = prices["input"], prices["output"]
    P_cr, P_cw = prices["cache_read"], prices["cache_write"]

    monthly_input = tokens["total_input_per_question"] * questions
    monthly_output = tokens["total_output_per_question"] * questions

    # No-cache baseline
    no_cache_input = (monthly_input / 1e6) * P_in
    no_cache_output = (monthly_output / 1e6) * P_out
    no_cache_total = no_cache_input + no_cache_output

    # Monthly cache totals
    monthly_cw = S * cache_splits["session_cache_write"]
    monthly_cr = S * cache_splits["session_cache_read"]
    monthly_reg = S * cache_splits["session_regular"]

    monthly_sum_check = monthly_cw + monthly_cr + monthly_reg == monthly_input

    # Cache costs
    cache_read_cost = (monthly_cr / 1e6) * P_cr
    cache_write_cost = (monthly_cw / 1e6) * P_cw
    regular_input_cost = (monthly_reg / 1e6) * P_in
    total_input_with_cache = cache_read_cost + cache_write_cost + regular_input_cost
    output_cost = (monthly_output / 1e6) * P_out
    total_model_cost = total_input_with_cache + output_cost

    savings = no_cache_input - total_input_with_cache
    savings_pct = round(savings / no_cache_input * 100, 1) if no_cache_input > 0 else 0

    return {
        "questions_per_month": questions,
        "monthly_input_tokens": monthly_input,
        "monthly_output_tokens": monthly_output,
        "monthly_cache_write": monthly_cw,
        "monthly_cache_read": monthly_cr,
        "monthly_regular": monthly_reg,
        "monthly_sum_check": monthly_sum_check,
        "no_cache_input_cost": round(no_cache_input, 2),
        "no_cache_output_cost": round(no_cache_output, 2),
        "no_cache_total": round(no_cache_total, 2),
        "cache_read_cost": round(cache_read_cost, 2),
        "cache_write_cost": round(cache_write_cost, 2),
        "regular_input_cost": round(regular_input_cost, 2),
        "total_input_with_cache": round(total_input_with_cache, 2),
        "output_cost": round(output_cost, 2),
        "total_model_cost": round(total_model_cost, 2),
        "caching_savings_monthly": round(savings, 2),
        "caching_savings_pct": savings_pct,
    }


def compute_agentcore(params, ac_prices):
    """Compute AgentCore costs per spec Section 5."""
    S = params["sessions_per_month"]
    Q_s = params["questions_per_session"]
    N_invoke = params["tools_invoked"]
    questions = S * Q_s

    V = params.get("runtime_vcpus", 2)
    M_gb = params.get("runtime_memory_gb", 4.0)
    W = params.get("runtime_wait_pct", 0.70)
    N_gw = params.get("tools_indexed_in_gateway", params.get("num_tools", 10))

    # Extract unit prices from AC results
    def get_ac_price(sub_key):
        for item in ac_prices:
            sc = item.get("sub_component", "")
            if sub_key in sc:
                return float(item["dimensions"][0]["price_usd"])
        return 0

    rt_vcpu_hr = get_ac_price("Runtime:Consumption-based:vCPU")
    rt_gb_hr = get_ac_price("Runtime:Consumption-based:Memory")
    gw_invoc = get_ac_price("Gateway:Consumption-based:API-Invocations")
    gw_search = get_ac_price("Gateway:Consumption-based:Search-API")
    gw_index = get_ac_price("Gateway:Consumption-based:Tool-Indexing")
    stm_event = get_ac_price("Memory:Consumption-based:Short-Term-Memory")
    ltm_store = get_ac_price("Memory:Consumption-based:Long-Term-Memory-Storage:Built-in-memory")
    ltm_retrieve = get_ac_price("Memory:Consumption-based:Long-Term-Memory-Retrieval")

    # Runtime
    time_per_q_s = (1 + N_invoke) * 4
    active_pct = 1 - W
    active_cpu_per_session = time_per_q_s * active_pct * Q_s
    session_duration_s = (time_per_q_s * Q_s) + (Q_s - 1) * params.get("idle_gap_s", 30)

    runtime_cpu = active_cpu_per_session * V * (rt_vcpu_hr / 3600) * S
    runtime_mem = session_duration_s * M_gb * (rt_gb_hr / 3600) * S
    runtime_total = runtime_cpu + runtime_mem

    # Gateway
    gw_invocations = (1 + N_invoke) * questions
    gw_searches = questions
    gateway_total = gw_invocations * gw_invoc + gw_searches * gw_search + N_gw * gw_index

    # Memory
    stm_cost = 2 * questions * stm_event
    ltm_storage = 3 * S * ltm_store
    ltm_retrieval = questions * ltm_retrieve
    memory_total = stm_cost + ltm_storage + ltm_retrieval

    total_ac = runtime_total + gateway_total + memory_total

    return {
        "unit_prices": {
            "runtime_vcpu_hr": rt_vcpu_hr, "runtime_gb_hr": rt_gb_hr,
            "gateway_invocation": gw_invoc, "gateway_search": gw_search, "gateway_index": gw_index,
            "stm_event": stm_event, "ltm_store": ltm_store, "ltm_retrieve": ltm_retrieve,
        },
        "runtime_cpu": round(runtime_cpu, 2),
        "runtime_mem": round(runtime_mem, 2),
        "runtime_total": round(runtime_total, 2),
        "gateway_total": round(gateway_total, 2),
        "memory_stm": round(stm_cost, 2),
        "memory_ltm_storage": round(ltm_storage, 2),
        "memory_ltm_retrieval": round(ltm_retrieval, 2),
        "memory_total": round(memory_total, 2),
        "total_agentcore": round(total_ac, 2),
    }


def compute_business_value(params, total_monthly):
    """Compute business value per spec Section 7."""
    S = params["sessions_per_month"]
    T_manual = params.get("time_without_ai_min", 20)
    T_ai = params.get("time_with_ai_min", 10)
    C_human = params.get("human_cost_per_hour", 75)
    R_hr = params.get("revenue_per_hour", 300)

    time_saved = T_manual - T_ai
    hours_equiv = S * T_manual / 60
    fte_equiv = hours_equiv / 160
    human_cost_equiv = hours_equiv * C_human

    tiers = {}
    for name, factors in BV_TIERS.items():
        E = factors["effectiveness"]
        F = factors["efficiency"]
        eff_sessions = S * E
        hours_saved = eff_sessions * time_saved / 60
        productive_hrs = hours_saved * F
        prod_value = productive_hrs * R_hr
        cost_savings = hours_saved * C_human
        net_1a = prod_value - total_monthly
        net_1b = cost_savings - total_monthly
        roi_1a = round(prod_value / total_monthly, 1) if total_monthly > 0 else 0
        roi_1b = round(cost_savings / total_monthly, 1) if total_monthly > 0 else 0

        tiers[name] = {
            "effective_sessions": eff_sessions,
            "hours_saved": hours_saved,
            "productive_hours": productive_hrs,
            "productivity_value": round(prod_value, 2),
            "cost_savings": round(cost_savings, 2),
            "net_1a": round(net_1a, 2),
            "net_1b": round(net_1b, 2),
            "roi_1a": roi_1a,
            "roi_1b": roi_1b,
        }

    return {
        "hours_equivalent": hours_equiv,
        "fte_equivalent": round(fte_equiv, 1),
        "human_cost_equivalent": round(human_cost_equiv, 2),
        "tiers": tiers,
    }


def generate_test_spec(use_case_name, sessions_per_month, questions_per_session,
                       tools_invoked, num_tools, prices, ac_prices=None,
                       use_agentcore=True, use_business_value=True, **overrides):
    """Generate a complete test spec JSON."""
    params = {**DEFAULTS}
    params.update({
        "sessions_per_month": sessions_per_month,
        "questions_per_session": questions_per_session,
        "tools_invoked": tools_invoked,
        "num_tools": num_tools,
    })
    params.update(overrides)

    tokens = compute_tokens(params)
    cache_splits = compute_cache_splits(tokens, params)
    costs = compute_costs(tokens, cache_splits, params, prices)

    total_monthly = costs["total_model_cost"]
    ac_data = None
    if use_agentcore and ac_prices:
        ac_data = compute_agentcore(params, ac_prices)
        total_monthly += ac_data["total_agentcore"]

    bv_data = None
    if use_business_value:
        bv_data = compute_business_value(params, total_monthly)

    spec = {
        "meta": {
            "name": use_case_name,
            "spec_version": "1.1",
            "generated_at": datetime.now().isoformat(),
        },
        "inputs": {
            "prices": prices,
            "workload": params,
        },
        "expected": {
            "tokens": tokens,
            "cache_splits": {k: v for k, v in cache_splits.items() if k != "verifications"},
            "costs": costs,
        },
        "verifications": {
            **cache_splits["verifications"],
            "monthly_sum_check": costs["monthly_sum_check"],
        },
    }

    if ac_data:
        spec["expected"]["agentcore"] = ac_data
    if bv_data:
        spec["expected"]["business_value"] = bv_data

    spec["expected"]["grand_total"] = {
        "total_monthly": round(total_monthly, 2),
        "total_annual": round(total_monthly * 12, 2),
        "per_session": round(total_monthly / sessions_per_month, 4),
        "per_question": round(total_monthly / (sessions_per_month * questions_per_session), 4),
    }

    return spec
