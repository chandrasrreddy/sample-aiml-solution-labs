#!/usr/bin/env python3
"""
test_config.py — Unit tests for the YAML configuration system in bedrock_pricing.py.

Covers 13 test groups:
  1. Schema and utilities (_deep_merge, _validate_config, _read_yaml_file)
  2. Load and merge (load_config, get_config)
  3. Precedence chain (resolve_setting)
  4. Template generation (generate_config_template)
  5. Agent session integration
  6. Capacity integration
  7. AgentCore integration
  8. Business value integration
  9. Pricing cache integration
  10. Model preferences
  11. Boundary conditions
  12. Error handling
  13. SKILL.md updates

Run: python3 tests/test_config.py
"""

import sys
import os
import tempfile
import shutil

# Load the script
sys.argv = ['bedrock_pricing.py']
_script_path = os.path.join(os.path.dirname(__file__), '..', 'skills', 'bedrock-pricing', 'scripts', 'bedrock_pricing.py')
_script_path = os.path.abspath(_script_path)
exec(open(_script_path).read())

# Test infrastructure
_pass_count = 0
_fail_count = 0
_current_group = ""


def _assert(condition, msg):
    global _pass_count, _fail_count
    if condition:
        _pass_count += 1
    else:
        _fail_count += 1
        print(f"  FAIL: {msg}")


def _run_group(name, fn):
    global _pass_count, _fail_count, _current_group
    _current_group = name
    before_pass = _pass_count
    before_fail = _fail_count
    try:
        fn()
    except Exception as e:
        _fail_count += 1
        print(f"  FAIL: {name} raised exception: {e}")
    group_pass = _pass_count - before_pass
    group_fail = _fail_count - before_fail
    status = "PASS" if group_fail == 0 else "FAIL"
    print(f"[{status}] {name} ({group_pass} passed, {group_fail} failed)")


# ═══════════════════════════════════════════════════════════════════════════════
# Group 1: Schema and Utilities
# ═══════════════════════════════════════════════════════════════════════════════
def test_schema_and_utilities():
    # _deep_merge tests
    r = _deep_merge({"a": 1, "b": {"x": 1}}, {"b": {"x": 2, "y": 3}})
    _assert(r == {"a": 1, "b": {"x": 2, "y": 3}}, "_deep_merge nested override")

    r = _deep_merge({}, {"a": 1})
    _assert(r == {"a": 1}, "_deep_merge empty base")

    r = _deep_merge({"a": 1}, {})
    _assert(r == {"a": 1}, "_deep_merge empty override")

    r = _deep_merge({"a": {"b": 1}}, {"a": None})
    _assert(r == {"a": None}, "_deep_merge override with None")

    # _validate_config tests
    _, w = _validate_config({"agent_defaults": {"input_tokens": "not_int"}}, "test.yaml")
    _assert(any("type" in x.lower() or "expected" in x.lower() for x in w), "_validate type error")

    _, w = _validate_config({"agent_defaults": {"input_tokens": -5}}, "test.yaml")
    _assert(any("below" in x.lower() or "min" in x.lower() for x in w), "_validate range error (negative)")

    _, w = _validate_config({"unknown_section": {"key": 1}}, "test.yaml")
    _assert(any("unrecognized" in x.lower() or "unknown" in x.lower() for x in w), "_validate unknown section")

    _, w = _validate_config({"defaults": {"history_mode": "invalid"}}, "test.yaml")
    _assert(any("not valid" in x.lower() or "options" in x.lower() for x in w), "_validate invalid choice")

    _, w = _validate_config({"capacity": {"peak_to_avg_ratio": 0.5}}, "test.yaml")
    _assert(any("below" in x.lower() for x in w), "_validate below min 1.0")

    _, w = _validate_config({"capacity": {"peak_to_avg_ratio": 101.0}}, "test.yaml")
    _assert(any("above" in x.lower() for x in w), "_validate above max 100.0")

    _, w = _validate_config({"capacity": {"active_hours_per_day": 25}}, "test.yaml")
    _assert(any("above" in x.lower() for x in w), "_validate above max 24")

    # _read_yaml_file tests
    r = _read_yaml_file("/nonexistent/path.yaml")
    _assert(r is None, "_read_yaml_file nonexistent returns None")

    # Empty file
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
    tmp.write("")
    tmp.close()
    r = _read_yaml_file(tmp.name)
    _assert(r is not None and r == {}, "_read_yaml_file empty returns {}")
    os.unlink(tmp.name)

    # CONFIG_SCHEMA structure
    _assert(len(CONFIG_SCHEMA) == 11, f"CONFIG_SCHEMA has 11 sections (got {len(CONFIG_SCHEMA)})")

    # Every key has type and default
    for section_name, section in CONFIG_SCHEMA.items():
        for key, spec in section.items():
            if key.startswith("_"):
                continue
            _assert("type" in spec and "default" in spec,
                    f"CONFIG_SCHEMA[{section_name}][{key}] has type and default")


# ═══════════════════════════════════════════════════════════════════════════════
# Group 2: Load and Merge
# ═══════════════════════════════════════════════════════════════════════════════
def test_load_and_merge():
    global _LOADED_CONFIG
    # No config files → empty
    _LOADED_CONFIG = None
    result = load_config(user_path="/nonexistent/user.yaml", project_path="/nonexistent/project.yaml")
    _assert(result == {}, "No config files → empty dict")

    # User config only
    tmp_dir = tempfile.mkdtemp()
    user_file = os.path.join(tmp_dir, "user.yaml")
    with open(user_file, 'w') as f:
        f.write("agent_defaults:\n  input_tokens: 200\n")
    _LOADED_CONFIG = None
    load_config(user_path=user_file, project_path="/nonexistent/project.yaml")
    _assert(get_config("agent_defaults", "input_tokens") == 200, "User config input_tokens=200")

    # Project config only
    proj_file = os.path.join(tmp_dir, "project.yaml")
    with open(proj_file, 'w') as f:
        f.write("capacity:\n  peak_to_avg_ratio: 5.0\n")
    _LOADED_CONFIG = None
    load_config(user_path="/nonexistent/user.yaml", project_path=proj_file)
    _assert(get_config("capacity", "peak_to_avg_ratio") == 5.0, "Project config peak_to_avg_ratio=5.0")

    # Both: project wins
    with open(user_file, 'w') as f:
        f.write("agent_defaults:\n  input_tokens: 200\n")
    with open(proj_file, 'w') as f:
        f.write("agent_defaults:\n  input_tokens: 300\n")
    _LOADED_CONFIG = None
    load_config(user_path=user_file, project_path=proj_file)
    _assert(get_config("agent_defaults", "input_tokens") == 300, "Project wins over user (300)")

    # Both: different sections preserved
    with open(user_file, 'w') as f:
        f.write("agent_defaults:\n  input_tokens: 200\n")
    with open(proj_file, 'w') as f:
        f.write("capacity:\n  peak_to_avg_ratio: 5.0\n")
    _LOADED_CONFIG = None
    load_config(user_path=user_file, project_path=proj_file)
    _assert(get_config("agent_defaults", "input_tokens") == 200, "User section preserved")
    _assert(get_config("capacity", "peak_to_avg_ratio") == 5.0, "Project section preserved")

    # get_config with no args
    full = get_config()
    _assert(isinstance(full, dict), "get_config() returns dict")

    # get_config nonexistent section
    _assert(get_config("nonexistent_section") is None or get_config("nonexistent_section") == {},
            "get_config nonexistent section")

    # get_config nonexistent key
    _assert(get_config("agent_defaults", "nonexistent_key") is None,
            "get_config nonexistent key returns None")

    shutil.rmtree(tmp_dir)
    _LOADED_CONFIG = None


# ═══════════════════════════════════════════════════════════════════════════════
# Group 3: Precedence Chain
# ═══════════════════════════════════════════════════════════════════════════════
def test_precedence_chain():
    global _LOADED_CONFIG
    _LOADED_CONFIG = {}

    # Explicit wins
    r = resolve_setting("agent_defaults", "input_tokens", explicit_value=500)
    _assert(r == 500, "Explicit value 500 wins")

    # Explicit 0 is not None
    r = resolve_setting("agent_defaults", "input_tokens", explicit_value=0)
    _assert(r == 0, "Explicit 0 wins (not None)")

    # Env var wins over config/default
    os.environ["BEDROCK_AGENT_DEFAULTS_INPUT_TOKENS"] = "300"
    _LOADED_CONFIG = {"agent_defaults": {"input_tokens": 200}}
    r = resolve_setting("agent_defaults", "input_tokens")
    _assert(r == 300, "Env var 300 wins over config 200")
    del os.environ["BEDROCK_AGENT_DEFAULTS_INPUT_TOKENS"]

    # Config wins over default
    _LOADED_CONFIG = {"agent_defaults": {"input_tokens": 200}}
    r = resolve_setting("agent_defaults", "input_tokens")
    _assert(r == 200, "Config 200 wins over default 100")

    # Schema default when nothing else
    _LOADED_CONFIG = {}
    r = resolve_setting("agent_defaults", "input_tokens")
    _assert(r == 100, "Schema default 100")

    # Explicit beats all
    os.environ["BEDROCK_AGENT_DEFAULTS_INPUT_TOKENS"] = "300"
    _LOADED_CONFIG = {"agent_defaults": {"input_tokens": 200}}
    r = resolve_setting("agent_defaults", "input_tokens", explicit_value=500)
    _assert(r == 500, "Explicit 500 beats env 300 and config 200")
    del os.environ["BEDROCK_AGENT_DEFAULTS_INPUT_TOKENS"]

    # Bad env var type → falls through
    os.environ["BEDROCK_AGENT_DEFAULTS_INPUT_TOKENS"] = "not_a_number"
    _LOADED_CONFIG = {"agent_defaults": {"input_tokens": 200}}
    r = resolve_setting("agent_defaults", "input_tokens")
    _assert(r == 200, "Bad env var falls through to config")
    del os.environ["BEDROCK_AGENT_DEFAULTS_INPUT_TOKENS"]

    # Bool conversion
    os.environ["BEDROCK_BEHAVIOR_SKIP_CONFIRMATION"] = "true"
    _LOADED_CONFIG = {}
    r = resolve_setting("behavior", "skip_confirmation")
    _assert(r == True, "Env 'true' → True")
    os.environ["BEDROCK_BEHAVIOR_SKIP_CONFIRMATION"] = "yes"
    r = resolve_setting("behavior", "skip_confirmation")
    _assert(r == True, "Env 'yes' → True")
    os.environ["BEDROCK_BEHAVIOR_SKIP_CONFIRMATION"] = "1"
    r = resolve_setting("behavior", "skip_confirmation")
    _assert(r == True, "Env '1' → True")
    os.environ["BEDROCK_BEHAVIOR_SKIP_CONFIRMATION"] = "false"
    r = resolve_setting("behavior", "skip_confirmation")
    _assert(r == False, "Env 'false' → False")
    del os.environ["BEDROCK_BEHAVIOR_SKIP_CONFIRMATION"]

    # Float conversion
    os.environ["BEDROCK_CAPACITY_PEAK_TO_AVG_RATIO"] = "2.5"
    _LOADED_CONFIG = {}
    r = resolve_setting("capacity", "peak_to_avg_ratio")
    _assert(r == 2.5, "Env '2.5' → 2.5 float")
    del os.environ["BEDROCK_CAPACITY_PEAK_TO_AVG_RATIO"]

    # Empty env var treated as not set
    os.environ["BEDROCK_DEFAULTS_REGION"] = ""
    _LOADED_CONFIG = {}
    r = resolve_setting("defaults", "region")
    _assert(r is None, "Empty env var falls through to default (None)")
    del os.environ["BEDROCK_DEFAULTS_REGION"]

    _LOADED_CONFIG = None


# ═══════════════════════════════════════════════════════════════════════════════
# Group 4: Template Generation
# ═══════════════════════════════════════════════════════════════════════════════
def test_template_generation():
    content = generate_config_template(output_path="/dev/null", force=True)

    # All 11 section headers present
    for section in ["reports:", "defaults:", "agent_defaults:", "rag_defaults:",
                    "research_defaults:", "agentcore_defaults:", "business_value_defaults:",
                    "capacity:", "pricing_cache:", "behavior:", "model_preferences:"]:
        _assert(section in content, f"Template contains '{section}'")

    # Model preferences defaults
    _assert("Claude Opus" in content, "Template contains 'Claude Opus' for router")
    _assert("latest" in content, "Template contains 'latest' for version")

    # All keys appear as commented entries
    for section_name, section_spec in CONFIG_SCHEMA.items():
        for key in section_spec:
            if key.startswith("_"):
                continue
            _assert(f"# {key}" in content or f"  # {key}" in content,
                    f"Template contains key '{key}'")


# ═══════════════════════════════════════════════════════════════════════════════
# Group 5: Agent Session Integration
# ═══════════════════════════════════════════════════════════════════════════════
def test_agent_session_integration():
    global _LOADED_CONFIG
    _LOADED_CONFIG = {}

    # RAG sub-agent with no args uses schema defaults
    rag = calculate_rag_subagent_tokens()
    _assert(rag["total_input"] > 0, "RAG defaults produce positive input")
    _assert(rag["assumptions"]["rag_n_chunks"] == 10, "RAG default rag_n_chunks=10")

    # RAG with explicit override
    rag2 = calculate_rag_subagent_tokens(rag_n_chunks=5)
    _assert(rag2["assumptions"]["rag_n_chunks"] == 5, "RAG explicit rag_n_chunks=5 wins")

    # RAG with config override
    _LOADED_CONFIG = {"rag_defaults": {"rag_n_chunks": 20}}
    rag3 = calculate_rag_subagent_tokens()
    _assert(rag3["assumptions"]["rag_n_chunks"] == 20, "RAG config rag_n_chunks=20 wins")

    # RAG explicit beats config
    rag4 = calculate_rag_subagent_tokens(rag_n_chunks=5)
    _assert(rag4["assumptions"]["rag_n_chunks"] == 5, "RAG explicit 5 beats config 20")

    # Research sub-agent defaults
    _LOADED_CONFIG = {}
    res = calculate_research_subagent_tokens()
    _assert(res["assumptions"]["n_research_iterations"] == 4, "Research default iterations=4")
    _assert(res["assumptions"]["fetch_probability"] == 0.5, "Research default fetch_prob=0.5")

    # Research with config
    _LOADED_CONFIG = {"research_defaults": {"fetch_probability": 0.8}}
    res2 = calculate_research_subagent_tokens()
    _assert(res2["assumptions"]["fetch_probability"] == 0.8, "Research config fetch_prob=0.8")

    # Research explicit beats config
    res3 = calculate_research_subagent_tokens(fetch_probability=0.3)
    _assert(res3["assumptions"]["fetch_probability"] == 0.3, "Research explicit 0.3 beats config 0.8")

    _LOADED_CONFIG = None


# ═══════════════════════════════════════════════════════════════════════════════
# Group 6: Capacity Integration
# ═══════════════════════════════════════════════════════════════════════════════
def test_capacity_integration():
    global _LOADED_CONFIG
    _LOADED_CONFIG = {}

    profile = {
        "llm_calls_per_question": 6,
        "avg_input_tokens_per_call": 5000,
        "avg_output_tokens_per_call": 200,
        "tokens_per_question": 31200,
        "questions_per_session": 5,
    }
    tier_limits = {"rpm_high": 10000, "tpm_high": 10000000}

    # Defaults match schema
    r = check_capacity_fit(profile, questions_per_month=100000, tier_limits=tier_limits)
    _assert(r["assumptions"]["peak_to_avg_ratio"] == 3.0, "Capacity default peak_ratio=3.0")
    _assert(r["assumptions"]["active_hours_per_day"] == 12, "Capacity default hours=12")
    _assert(r["assumptions"]["active_days_per_month"] == 22, "Capacity default days=22")
    _assert(r["assumptions"]["max_tokens_setting"] == 4096, "Capacity default max_tokens=4096")

    # Config override
    _LOADED_CONFIG = {"capacity": {"peak_to_avg_ratio": 5.0}}
    r2 = check_capacity_fit(profile, questions_per_month=100000, tier_limits=tier_limits)
    _assert(r2["assumptions"]["peak_to_avg_ratio"] == 5.0, "Capacity config peak_ratio=5.0")

    # Explicit beats config
    r3 = check_capacity_fit(profile, questions_per_month=100000,
                            peak_to_avg_ratio=2.0, tier_limits=tier_limits)
    _assert(r3["assumptions"]["peak_to_avg_ratio"] == 2.0, "Capacity explicit 2.0 beats config 5.0")

    _LOADED_CONFIG = None


# ═══════════════════════════════════════════════════════════════════════════════
# Group 7: AgentCore Integration
# ═══════════════════════════════════════════════════════════════════════════════
def test_agentcore_integration():
    global _LOADED_CONFIG
    _LOADED_CONFIG = {}

    # Call with defaults
    r = calculate_agentcore_cost(
        runtime_vcpu_price_hr=0.0895,
        runtime_mem_price_hr=0.00945,
        gateway_invocation_price=5e-6,
        gateway_search_price=2.5e-5,
        gateway_indexing_price=0.0002,
        stm_event_price=0.00025,
        ltm_storage_price=0.00075,
        ltm_retrieval_price=0.0005,
        questions_per_month=100000,
    )
    _assert(r["assumptions"]["num_vcpus"] == 2, "AgentCore default vcpus=2")
    _assert(r["assumptions"]["io_wait_pct"] == 0.70, "AgentCore default io_wait=0.70")

    # Config override
    _LOADED_CONFIG = {"agentcore_defaults": {"num_vcpus": 4, "io_wait_pct": 0.5}}
    r2 = calculate_agentcore_cost(
        runtime_vcpu_price_hr=0.0895,
        runtime_mem_price_hr=0.00945,
        gateway_invocation_price=5e-6,
        gateway_search_price=2.5e-5,
        gateway_indexing_price=0.0002,
        stm_event_price=0.00025,
        ltm_storage_price=0.00075,
        ltm_retrieval_price=0.0005,
        questions_per_month=100000,
    )
    _assert(r2["assumptions"]["num_vcpus"] == 4, "AgentCore config vcpus=4")
    _assert(r2["assumptions"]["io_wait_pct"] == 0.5, "AgentCore config io_wait=0.5")

    # Explicit beats config
    r3 = calculate_agentcore_cost(
        runtime_vcpu_price_hr=0.0895,
        runtime_mem_price_hr=0.00945,
        gateway_invocation_price=5e-6,
        gateway_search_price=2.5e-5,
        gateway_indexing_price=0.0002,
        stm_event_price=0.00025,
        ltm_storage_price=0.00075,
        ltm_retrieval_price=0.0005,
        questions_per_month=100000,
        num_vcpus=8,
    )
    _assert(r3["assumptions"]["num_vcpus"] == 8, "AgentCore explicit vcpus=8 beats config 4")

    _LOADED_CONFIG = None


# ═══════════════════════════════════════════════════════════════════════════════
# Group 8: Business Value Integration
# ═══════════════════════════════════════════════════════════════════════════════
def test_business_value_integration():
    global _LOADED_CONFIG
    _LOADED_CONFIG = {}

    # Defaults
    r = calculate_business_value(sessions_per_month=10000)
    _assert(r["assumptions"]["time_without_ai_min"] == 20.0, "BV default time_without=20")
    _assert(r["assumptions"]["human_cost_per_hour"] == 75.0, "BV default cost/hr=75")

    # Config override
    _LOADED_CONFIG = {"business_value_defaults": {"human_cost_per_hour": 100.0}}
    r2 = calculate_business_value(sessions_per_month=10000)
    _assert(r2["assumptions"]["human_cost_per_hour"] == 100.0, "BV config cost/hr=100")

    # Explicit beats config
    r3 = calculate_business_value(sessions_per_month=10000, human_cost_per_hour=50.0)
    _assert(r3["assumptions"]["human_cost_per_hour"] == 50.0, "BV explicit 50 beats config 100")

    _LOADED_CONFIG = None


# ═══════════════════════════════════════════════════════════════════════════════
# Group 9: Pricing Cache Integration
# ═══════════════════════════════════════════════════════════════════════════════
def test_pricing_cache_integration():
    global _LOADED_CONFIG
    _LOADED_CONFIG = {}

    # Default cache dir and max_age
    r = check_pricing_data_status()
    # Just verify it runs without error and returns expected structure
    _assert("status" in r, "check_pricing_data_status returns status")
    _assert("found" in r, "check_pricing_data_status returns found")

    # Config override for max_age_days
    _LOADED_CONFIG = {"pricing_cache": {"max_age_days": 14}}
    # Verify resolve_setting picks it up
    age = resolve_setting("pricing_cache", "max_age_days")
    _assert(age == 14, "Pricing cache config max_age_days=14")

    # Config override for dir
    _LOADED_CONFIG = {"pricing_cache": {"dir": "/tmp/test_cache_dir"}}
    d = resolve_setting("pricing_cache", "dir")
    _assert(d == "/tmp/test_cache_dir", "Pricing cache config dir override")

    # Explicit cache_dir overrides config
    _LOADED_CONFIG = {"pricing_cache": {"dir": "/tmp/config_cache"}}
    r2 = check_pricing_data_status(cache_dir="/tmp/explicit_cache")
    # The function should use /tmp/explicit_cache, not /tmp/config_cache
    # We can't easily verify the internal path, but it shouldn't crash
    _assert("status" in r2, "Explicit cache_dir doesn't crash")

    _LOADED_CONFIG = None


# ═══════════════════════════════════════════════════════════════════════════════
# Group 10: Model Preferences
# ═══════════════════════════════════════════════════════════════════════════════
def test_model_preferences():
    global _LOADED_CONFIG
    _LOADED_CONFIG = {}

    _assert(resolve_setting("model_preferences", "general") == "Claude Sonnet",
            "model_preferences.general default = Claude Sonnet")
    _assert(resolve_setting("model_preferences", "router") == "Claude Opus",
            "model_preferences.router default = Claude Opus")
    _assert(resolve_setting("model_preferences", "rag") == "Claude Haiku",
            "model_preferences.rag default = Claude Haiku")
    _assert(resolve_setting("model_preferences", "research") == "Nova Lite",
            "model_preferences.research default = Nova Lite")
    _assert(resolve_setting("model_preferences", "version") == "latest",
            "model_preferences.version default = latest")

    # Config override
    _LOADED_CONFIG = {"model_preferences": {"general": "Nova Pro"}}
    _assert(resolve_setting("model_preferences", "general") == "Nova Pro",
            "model_preferences.general config = Nova Pro")

    _LOADED_CONFIG = None


# ═══════════════════════════════════════════════════════════════════════════════
# Group 11: Boundary Conditions
# ═══════════════════════════════════════════════════════════════════════════════
def test_boundary_conditions():
    # Min/max accepted without warning
    v, w = _validate_config({"capacity": {"peak_to_avg_ratio": 1.0}}, "t.yaml")
    _assert(len(w) == 0 and v.get("capacity", {}).get("peak_to_avg_ratio") == 1.0,
            "peak_to_avg_ratio=1.0 (min) accepted")

    v, w = _validate_config({"capacity": {"peak_to_avg_ratio": 100.0}}, "t.yaml")
    _assert(len(w) == 0 and v.get("capacity", {}).get("peak_to_avg_ratio") == 100.0,
            "peak_to_avg_ratio=100.0 (max) accepted")

    v, w = _validate_config({"capacity": {"active_hours_per_day": 1}}, "t.yaml")
    _assert(len(w) == 0, "active_hours_per_day=1 (min) accepted")

    v, w = _validate_config({"capacity": {"active_hours_per_day": 24}}, "t.yaml")
    _assert(len(w) == 0, "active_hours_per_day=24 (max) accepted")

    v, w = _validate_config({"pricing_cache": {"max_age_days": 1}}, "t.yaml")
    _assert(len(w) == 0, "max_age_days=1 (min) accepted")

    v, w = _validate_config({"pricing_cache": {"max_age_days": 365}}, "t.yaml")
    _assert(len(w) == 0, "max_age_days=365 (max) accepted")

    v, w = _validate_config({"agentcore_defaults": {"io_wait_pct": 0.0}}, "t.yaml")
    _assert(len(w) == 0, "io_wait_pct=0.0 (min) accepted")

    v, w = _validate_config({"agentcore_defaults": {"io_wait_pct": 1.0}}, "t.yaml")
    _assert(len(w) == 0, "io_wait_pct=1.0 (max) accepted")

    v, w = _validate_config({"agent_defaults": {"input_tokens": 1}}, "t.yaml")
    _assert(len(w) == 0, "input_tokens=1 (min) accepted")

    v, w = _validate_config({"agent_defaults": {"tools_passed": 0}}, "t.yaml")
    _assert(len(w) == 0, "tools_passed=0 (min, zero allowed) accepted")

    # Max length
    v, w = _validate_config({"reports": {"naming_template": "x" * 128}}, "t.yaml")
    _assert(len(w) == 0, "naming_template 128 chars accepted")

    v, w = _validate_config({"reports": {"naming_template": "x" * 129}}, "t.yaml")
    _assert(len(w) > 0, "naming_template 129 chars rejected")


# ═══════════════════════════════════════════════════════════════════════════════
# Group 12: Error Handling
# ═══════════════════════════════════════════════════════════════════════════════
def test_error_handling():
    global _LOADED_CONFIG

    # Negative value
    v, w = _validate_config({"agent_defaults": {"input_tokens": -1}}, "t.yaml")
    _assert(len(w) > 0, "input_tokens=-1 produces warning")
    _assert("input_tokens" not in v.get("agent_defaults", {}), "input_tokens=-1 discarded")

    # Zero where min is 1
    v, w = _validate_config({"agent_defaults": {"input_tokens": 0}}, "t.yaml")
    _assert(len(w) > 0, "input_tokens=0 produces warning (min is 1)")

    # Invalid choice
    v, w = _validate_config({"reports": {"format": "xml"}}, "t.yaml")
    _assert(len(w) > 0, "format='xml' produces warning")

    v, w = _validate_config({"defaults": {"history_mode": "partial"}}, "t.yaml")
    _assert(len(w) > 0, "history_mode='partial' produces warning")

    # Type error
    v, w = _validate_config({"capacity": {"peak_to_avg_ratio": "fast"}}, "t.yaml")
    _assert(len(w) > 0, "peak_to_avg_ratio='fast' type error")

    # Above max
    v, w = _validate_config({"agentcore_defaults": {"io_wait_pct": 1.5}}, "t.yaml")
    _assert(len(w) > 0, "io_wait_pct=1.5 above max")

    # Below min
    v, w = _validate_config({"agentcore_defaults": {"io_wait_pct": -0.1}}, "t.yaml")
    _assert(len(w) > 0, "io_wait_pct=-0.1 below min")

    # Multiple errors all reported
    v, w = _validate_config({
        "agent_defaults": {"input_tokens": -1, "output_tokens": "bad"},
        "capacity": {"peak_to_avg_ratio": 999.0},
    }, "t.yaml")
    _assert(len(w) >= 3, f"Multiple errors: got {len(w)} warnings (expected >=3)")

    # Verify discarded values use defaults via resolve_setting
    _LOADED_CONFIG = {}
    tmp_dir = tempfile.mkdtemp()
    cfg_file = os.path.join(tmp_dir, "bad.yaml")
    with open(cfg_file, 'w') as f:
        f.write("agent_defaults:\n  input_tokens: -1\n")
    _LOADED_CONFIG = None
    load_config(user_path=cfg_file, project_path="/nonexistent.yaml")
    r = resolve_setting("agent_defaults", "input_tokens")
    _assert(r == 100, "Discarded value falls back to schema default 100")
    shutil.rmtree(tmp_dir)
    _LOADED_CONFIG = None


# ═══════════════════════════════════════════════════════════════════════════════
# Group 13: SKILL.md Updates
# ═══════════════════════════════════════════════════════════════════════════════
def test_skill_md_updates():
    skills_dir = os.path.join(os.path.dirname(__file__), '..', 'skills')
    skills_dir = os.path.abspath(skills_dir)

    # bedrock-pricing
    bp = open(os.path.join(skills_dir, "bedrock-pricing", "SKILL.md")).read()
    _assert("## Configuration" in bp, "bedrock-pricing has ## Configuration")
    _assert("Config values are defaults only" in bp, "bedrock-pricing has defaults-only callout")
    _assert("--init-config" in bp, "bedrock-pricing references --init-config")
    _assert("Precedence" in bp, "bedrock-pricing mentions Precedence")
    _assert("| Default |" not in bp and "| Default|" not in bp,
            "bedrock-pricing no Default column in tables")
    _assert("## Critical Rules" in bp, "bedrock-pricing still has Critical Rules")
    _assert("## Workflow" in bp, "bedrock-pricing still has Workflow")
    _assert("## Output Structure" in bp, "bedrock-pricing still has Output Structure")

    # bedrock-capacity
    bc = open(os.path.join(skills_dir, "bedrock-capacity", "SKILL.md")).read()
    _assert("## Configuration" in bc, "bedrock-capacity has ## Configuration")
    _assert("Config values are defaults only" in bc, "bedrock-capacity has defaults-only callout")
    _assert("| Default |" not in bc and "| Default|" not in bc,
            "bedrock-capacity no Default column")
    _assert("## Key Concepts" in bc, "bedrock-capacity still has Key Concepts")
    _assert("## When Workload Doesn" in bc, "bedrock-capacity still has When Workload Doesn't Fit")

    # agentcore-pricing
    ac = open(os.path.join(skills_dir, "agentcore-pricing", "SKILL.md")).read()
    _assert("## Configuration" in ac, "agentcore-pricing has ## Configuration")
    _assert("Config values are defaults only" in ac, "agentcore-pricing has defaults-only callout")
    _assert("| Default |" not in ac and "| Default|" not in ac,
            "agentcore-pricing no Default column")
    _assert("## Cache Key Reference" in ac, "agentcore-pricing still has Cache Key Reference")

    # agent-business-value
    bv = open(os.path.join(skills_dir, "agent-business-value", "SKILL.md")).read()
    _assert("## Configuration" in bv, "agent-business-value has ## Configuration")
    _assert("Config values are defaults only" in bv, "agent-business-value has defaults-only callout")
    _assert("BCG" in bv, "agent-business-value still has BCG citation")
    _assert("Harvard" in bv, "agent-business-value still has Harvard citation")
    _assert("Gartner" in bv, "agent-business-value still has Gartner citation")
    _assert("| Default |" not in bv or "| Dimension | Default |" in bv,
            "agent-business-value no parameter Default column (dimension menu is OK)")

    # bedrock-tier-advisor
    ta = open(os.path.join(skills_dir, "bedrock-tier-advisor", "SKILL.md")).read()
    _assert("## Configuration" in ta, "bedrock-tier-advisor has ## Configuration")
    _assert("model_preferences" in ta, "bedrock-tier-advisor references model_preferences")
    _assert("## Workflow" in ta, "bedrock-tier-advisor still has Workflow")
    _assert("## Lessons Learned" in ta, "bedrock-tier-advisor still has Lessons Learned")


# ═══════════════════════════════════════════════════════════════════════════════
# Main runner
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 70)
    print("YAML Config System — Unit Tests")
    print("=" * 70)
    print()

    _run_group("Group 1: Schema and Utilities", test_schema_and_utilities)
    _run_group("Group 2: Load and Merge", test_load_and_merge)
    _run_group("Group 3: Precedence Chain", test_precedence_chain)
    _run_group("Group 4: Template Generation", test_template_generation)
    _run_group("Group 5: Agent Session Integration", test_agent_session_integration)
    _run_group("Group 6: Capacity Integration", test_capacity_integration)
    _run_group("Group 7: AgentCore Integration", test_agentcore_integration)
    _run_group("Group 8: Business Value Integration", test_business_value_integration)
    _run_group("Group 9: Pricing Cache Integration", test_pricing_cache_integration)
    _run_group("Group 10: Model Preferences", test_model_preferences)
    _run_group("Group 11: Boundary Conditions", test_boundary_conditions)
    _run_group("Group 12: Error Handling", test_error_handling)
    _run_group("Group 13: SKILL.md Updates", test_skill_md_updates)

    print()
    print("=" * 70)
    total = _pass_count + _fail_count
    if _fail_count == 0:
        print(f"ALL PASSED: {_pass_count}/{total} assertions")
    else:
        print(f"FAILED: {_fail_count}/{total} assertions failed")
    print("=" * 70)
    sys.exit(0 if _fail_count == 0 else 1)
