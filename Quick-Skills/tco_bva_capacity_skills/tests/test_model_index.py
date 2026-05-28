#!/usr/bin/env python3
"""
test_model_index.py — Unit tests for list_models(), _generate_model_index(), and _classify_model_family().

Covers 4 test groups:
  1. _classify_model_family() — family classification from model names
  2. _generate_model_index() — index generation from real cache files
  3. list_models() — query-time lookup from generated index
  4. Integration — list_models() → get_model_prices() end-to-end

Run: python3 tests/test_model_index.py
"""

import sys
import os
import tempfile
import shutil
import json

# Load the script
sys.argv = ['bedrock_pricing.py']
os.environ['USE_IN_CLAUDE_CODE'] = '1'
_script_path = os.path.join(os.path.dirname(__file__), '..', 'skills', 'bedrock-pricing', 'scripts', 'bedrock_pricing.py')
_script_path = os.path.abspath(_script_path)
exec(open(_script_path).read())

# Test infrastructure
_pass_count = 0
_fail_count = 0


def _assert(condition, msg):
    global _pass_count, _fail_count
    if condition:
        _pass_count += 1
    else:
        _fail_count += 1
        print(f"  FAIL: {msg}")


def _run_group(name, fn):
    global _pass_count, _fail_count
    before_pass = _pass_count
    before_fail = _fail_count
    try:
        fn()
    except Exception as e:
        _fail_count += 1
        print(f"  FAIL: {name} raised exception: {e}")
        import traceback
        traceback.print_exc()
    group_pass = _pass_count - before_pass
    group_fail = _fail_count - before_fail
    status = "PASS" if group_fail == 0 else "FAIL"
    print(f"[{status}] {name} ({group_pass} passed, {group_fail} failed)")


# ═══════════════════════════════════════════════════════════════════════════════
# Group 1: _classify_model_family()
# ═══════════════════════════════════════════════════════════════════════════════
def test_classify_model_family():
    # Claude families
    _assert(_classify_model_family("Claude Sonnet 4.6") == "Sonnet",
            "Claude Sonnet 4.6 → Sonnet")
    _assert(_classify_model_family("Claude 3.5 Sonnet v2") == "Sonnet",
            "Claude 3.5 Sonnet v2 → Sonnet")
    _assert(_classify_model_family("Claude 3 Sonnet") == "Sonnet",
            "Claude 3 Sonnet → Sonnet")
    _assert(_classify_model_family("Claude Opus 4.7") == "Opus",
            "Claude Opus 4.7 → Opus")
    _assert(_classify_model_family("Claude 3 Opus") == "Opus",
            "Claude 3 Opus → Opus")
    _assert(_classify_model_family("Claude Haiku 4.5") == "Haiku",
            "Claude Haiku 4.5 → Haiku")
    _assert(_classify_model_family("Claude 3 Haiku") == "Haiku",
            "Claude 3 Haiku → Haiku")
    _assert(_classify_model_family("Claude Instant") == "Claude Instant",
            "Claude Instant → Claude Instant")
    _assert(_classify_model_family("Claude Instant (100K)") == "Claude Instant",
            "Claude Instant (100K) → Claude Instant")
    _assert(_classify_model_family("Claude 2.0") == "Claude",
            "Claude 2.0 → Claude")
    _assert(_classify_model_family("Claude") == "Claude",
            "Claude → Claude")

    # Non-Claude families
    _assert(_classify_model_family("Nova Pro") == "Nova Pro",
            "Nova Pro → Nova Pro")
    _assert(_classify_model_family("Nova Pro Latency Optimized") == "Nova Pro",
            "Nova Pro Latency Optimized → Nova Pro")
    _assert(_classify_model_family("Nova Lite") == "Nova Lite",
            "Nova Lite → Nova Lite")
    _assert(_classify_model_family("Nova 2.0 Omni") == "Nova Omni",
            "Nova 2.0 Omni → Nova Omni")
    _assert(_classify_model_family("Nova Sonic 2.0") == "Nova Sonic",
            "Nova Sonic 2.0 → Nova Sonic")
    _assert(_classify_model_family("Llama 3.1 70B") == "Llama 3.1",
            "Llama 3.1 70B → Llama 3.1")
    _assert(_classify_model_family("Llama 4 Maverick 17B") == "Llama 4",
            "Llama 4 Maverick 17B → Llama 4")
    _assert(_classify_model_family("Mistral Large 3") == "Mistral Large",
            "Mistral Large 3 → Mistral Large")
    _assert(_classify_model_family("Mixtral 8x7B") == "Mixtral",
            "Mixtral 8x7B → Mixtral")
    _assert(_classify_model_family("DeepSeek V3.1") == "DeepSeek",
            "DeepSeek V3.1 → DeepSeek")
    _assert(_classify_model_family("Qwen3 32B") == "Qwen",
            "Qwen3 32B → Qwen")
    _assert(_classify_model_family("GLM 4.7") == "GLM",
            "GLM 4.7 → GLM")
    _assert(_classify_model_family("Gemma 3 27B") == "Gemma",
            "Gemma 3 27B → Gemma")

    # Unknown model → Other
    _assert(_classify_model_family("SomeNewModel v99") == "Other",
            "Unknown model → Other")
    _assert(_classify_model_family("") == "Other",
            "Empty string → Other")


# ═══════════════════════════════════════════════════════════════════════════════
# Group 2: _generate_model_index()
# ═══════════════════════════════════════════════════════════════════════════════
def test_generate_model_index():
    cache_dir = os.path.expanduser("~/bedrock_cache")

    # Generate into a temp dir (copy cache files there first)
    tmp_dir = tempfile.mkdtemp(prefix="test_index_")
    try:
        # Copy cache files to temp dir
        for fname in ["bedrock_pricing.json", "bedrock_pricing_3p.json", "bedrock_pricing_service.json"]:
            src = os.path.join(cache_dir, fname)
            if os.path.exists(src):
                os.symlink(src, os.path.join(tmp_dir, fname))

        # Generate index
        _generate_model_index(tmp_dir)

        index_path = os.path.join(tmp_dir, MODEL_INDEX_FILE)
        _assert(os.path.exists(index_path),
                "index file was created")

        with open(index_path) as f:
            index = json.load(f)

        # Structure checks
        _assert(isinstance(index, dict),
                "index is a dict")
        _assert(len(index) >= 30,
                f"index has >= 30 regions (got {len(index)})")

        # us-west-2 must exist
        _assert("us-west-2" in index,
                "us-west-2 is in the index")

        usw2 = index["us-west-2"]
        _assert(isinstance(usw2, dict),
                "us-west-2 value is a dict of families")

        # Known families exist
        _assert("Sonnet" in usw2,
                "Sonnet family exists in us-west-2")
        _assert("Opus" in usw2,
                "Opus family exists in us-west-2")
        _assert("Haiku" in usw2,
                "Haiku family exists in us-west-2")

        # Known models in correct families
        _assert("Claude Sonnet 4.6" in usw2.get("Sonnet", []),
                "Claude Sonnet 4.6 is in Sonnet family")
        _assert("Claude Opus 4.7" in usw2.get("Opus", []),
                "Claude Opus 4.7 is in Opus family")
        _assert("Claude Haiku 4.5" in usw2.get("Haiku", []),
                "Claude Haiku 4.5 is in Haiku family")

        # No empty families
        for region, families in index.items():
            for family, models in families.items():
                _assert(len(models) > 0,
                        f"No empty family: {region}/{family}")
                if len(models) == 0:
                    break
            else:
                continue
            break

        # All values in families are lists of strings
        for model in usw2.get("Sonnet", []):
            _assert(isinstance(model, str),
                    f"Model name is a string: {model}")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Group 3: list_models()
# ═══════════════════════════════════════════════════════════════════════════════
def test_list_models():
    cache_dir = os.path.expanduser("~/bedrock_cache")

    # Ensure index exists
    index_path = os.path.join(cache_dir, MODEL_INDEX_FILE)
    if not os.path.exists(index_path):
        _generate_model_index(cache_dir)

    # Basic lookup
    sonnet_models = list_models(cache_dir, "us-west-2", "Sonnet")
    _assert(isinstance(sonnet_models, list),
            "list_models returns a list")
    _assert(len(sonnet_models) >= 5,
            f"Sonnet has >= 5 versions in us-west-2 (got {len(sonnet_models)})")
    _assert("Claude Sonnet 4.6" in sonnet_models,
            "Claude Sonnet 4.6 is in Sonnet list")
    _assert("Claude 3 Sonnet" in sonnet_models,
            "Claude 3 Sonnet is in Sonnet list")

    # Case-insensitive
    sonnet_lower = list_models(cache_dir, "us-west-2", "sonnet")
    _assert(sonnet_lower == sonnet_models,
            "list_models is case-insensitive for family")

    opus_upper = list_models(cache_dir, "us-west-2", "OPUS")
    _assert(len(opus_upper) >= 4,
            "OPUS (uppercase) returns Opus models")

    # Non-existent family
    empty = list_models(cache_dir, "us-west-2", "GPT-5")
    _assert(empty == [],
            "Non-existent family returns empty list")

    # Non-existent region
    empty_region = list_models(cache_dir, "xx-nowhere-99", "Sonnet")
    _assert(empty_region == [],
            "Non-existent region returns empty list")

    # All returned values are strings
    for model in sonnet_models:
        _assert(isinstance(model, str),
                f"list_models returns strings: {model}")

    # FileNotFoundError when NO cache files exist at all
    tmp_dir = tempfile.mkdtemp(prefix="test_no_cache_")
    try:
        raised = False
        try:
            list_models(tmp_dir, "us-west-2", "Sonnet")
        except FileNotFoundError:
            raised = True
        _assert(raised,
                "list_models raises FileNotFoundError when no cache files exist")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # Auto-generates index when cache files exist but index doesn't
    tmp_dir2 = tempfile.mkdtemp(prefix="test_auto_index_")
    try:
        cache_dir = os.path.expanduser("~/bedrock_cache")
        for fname in ["bedrock_pricing.json", "bedrock_pricing_3p.json", "bedrock_pricing_service.json"]:
            src = os.path.join(cache_dir, fname)
            if os.path.exists(src):
                os.symlink(src, os.path.join(tmp_dir2, fname))
        # No index file yet — list_models should auto-generate it
        result = list_models(tmp_dir2, "us-west-2", "Sonnet")
        _assert(len(result) >= 5,
                "list_models auto-generates index when cache exists but index doesn't")
        _assert(os.path.exists(os.path.join(tmp_dir2, MODEL_INDEX_FILE)),
                "auto-generated index file exists after list_models call")
    finally:
        shutil.rmtree(tmp_dir2, ignore_errors=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Group 4: Integration (list_models → get_model_prices)
# ═══════════════════════════════════════════════════════════════════════════════
def test_integration():
    cache_dir = os.path.expanduser("~/bedrock_cache")

    # list_models → pick model → get_model_prices
    models = list_models(cache_dir, "us-west-2", "Sonnet")
    _assert(len(models) > 0,
            "integration: list_models returns non-empty for Sonnet")

    # Pick the latest (last in sorted list)
    picked = models[-1]
    _assert("Sonnet" in picked or "sonnet" in picked.lower(),
            f"integration: picked model contains 'Sonnet': {picked}")

    # get_model_prices should succeed with the exact name from list_models
    prices = get_model_prices(cache_dir, "us-west-2", picked)
    _assert(isinstance(prices, dict),
            "integration: get_model_prices returns dict")
    _assert("input_price" in prices,
            "integration: result has input_price")
    _assert("output_price" in prices,
            "integration: result has output_price")
    _assert("cache_read_price" in prices,
            "integration: result has cache_read_price")
    _assert("cache_write_price" in prices,
            "integration: result has cache_write_price")
    _assert("model_name" in prices,
            "integration: result has model_name")
    _assert(prices["model_name"] == picked,
            f"integration: model_name matches picked ({picked})")

    # Prices are positive numbers
    _assert(prices["input_price"] > 0,
            "integration: input_price > 0")
    _assert(prices["output_price"] > 0,
            "integration: output_price > 0")

    # Test with Opus family too
    opus_models = list_models(cache_dir, "us-west-2", "Opus")
    if opus_models:
        opus_prices = get_model_prices(cache_dir, "us-west-2", opus_models[-1])
        _assert(opus_prices["input_price"] > 0,
                f"integration: Opus ({opus_models[-1]}) has valid input_price")

    # Test with Haiku family
    haiku_models = list_models(cache_dir, "us-east-1", "Haiku")
    if haiku_models:
        haiku_prices = get_model_prices(cache_dir, "us-east-1", haiku_models[-1])
        _assert(haiku_prices["input_price"] > 0,
                f"integration: Haiku ({haiku_models[-1]}) has valid input_price")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 70)
    print("test_model_index.py — Model Index & list_models() Tests")
    print("=" * 70)
    print()

    _run_group("Group 1: _classify_model_family()", test_classify_model_family)
    _run_group("Group 2: _generate_model_index()", test_generate_model_index)
    _run_group("Group 3: list_models()", test_list_models)
    _run_group("Group 4: Integration", test_integration)

    print()
    print("=" * 70)
    total = _pass_count + _fail_count
    print(f"TOTAL: {_pass_count}/{total} passed, {_fail_count} failed")
    print("=" * 70)

    sys.exit(0 if _fail_count == 0 else 1)
