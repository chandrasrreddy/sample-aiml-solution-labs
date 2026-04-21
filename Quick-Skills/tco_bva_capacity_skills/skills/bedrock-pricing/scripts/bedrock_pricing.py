#!/usr/bin/env python3
"""
bedrock_pricing.py — Query AWS Pricing API for Bedrock model and AgentCore pricing.

Bundled with the 'bedrock-pricing' Amazon Quick skill.

This script has TWO modes:
  1. REFRESH MODE (run from Terminal): Fetches fresh pricing data from the AWS Pricing API
     and saves it to ~/bedrock_pricing.json (or specified output paths).
     Requires: boto3, valid AWS credentials.
     
     Usage:
       python3 bedrock_pricing.py --refresh
       python3 bedrock_pricing.py --refresh --output-dir /path/to/dir

  2. QUERY MODE (called by the skill inside the sandbox): Reads cached JSON files,
     applies filters, and outputs Markdown.
     
     Usage:
       python3 bedrock_pricing.py --cache-dir ~ [--region REGION] [--provider PROVIDER] [--model MODEL] [--include-agentcore]

Output: Markdown to stdout with structured pricing data.
"""

import json
import sys
import argparse
import os
import time
from collections import defaultdict


def _fmt(n):
    """Format a number with commas for display in explanations."""
    return f"{n:,.0f}" if isinstance(n, (int, float)) else str(n)

SERVICE_CODES = {
    "AmazonBedrockFoundationModels": "3P Marketplace models",
    "AmazonBedrock": "1P Amazon models + newer 3P models",
    "AmazonBedrockService": "Very new models",
    "AmazonBedrockAgentCore": "AgentCore components",
}

MODEL_SERVICE_CODES = [
    "AmazonBedrockFoundationModels",
    "AmazonBedrock",
    "AmazonBedrockService",
]

AGENTCORE_SERVICE_CODE = "AmazonBedrockAgentCore"

CACHE_FILES = {
    "AmazonBedrock": "bedrock_pricing.json",
    "AmazonBedrockFoundationModels": "bedrock_pricing_3p.json",
    "AmazonBedrockService": "bedrock_pricing_service.json",
    "AmazonBedrockAgentCore": "bedrock_pricing_agentcore.json",
}

QUOTAS_CACHE_FILE = "bedrock_quotas.json"

PROVIDER_RULES = [
    (["Claude", "Anthropic"], "Anthropic"),
    (["Llama", "Meta"], "Meta (Llama)"),
    (["Nova", "Titan"], "Amazon"),
    (["Mistral", "Mixtral", "Pixtral", "Ministral", "Magistral", "Devstral", "Voxtral"], "Mistral AI"),
    (["Cohere", "Command", "Embed"], "Cohere"),
    (["Stable", "Stability", "SDXL"], "Stability AI"),
    (["DeepSeek"], "DeepSeek"),
    (["Qwen"], "Alibaba (Qwen)"),
    (["Gemma"], "Google (Gemma)"),
    (["GPT", "gpt"], "OpenAI (GPT-OSS)"),
    (["Nemotron", "NVIDIA", "Nvidia"], "NVIDIA"),
    (["Writer", "Palmyra"], "Writer"),
    (["Kimi"], "Moonshot (Kimi)"),
    (["GLM"], "Zhipu (GLM)"),
    (["MiniMax", "Minimax"], "MiniMax"),
    (["AI21", "Jamba", "Jurassic"], "AI21 Labs"),
    (["Ray"], "Ray"),
]


def classify_provider(name: str) -> str:
    for keywords, provider in PROVIDER_RULES:
        for kw in keywords:
            if kw.lower() in name.lower():
                return provider
    return "Other"


def fuzzy_match(query: str, text: str) -> bool:
    q = query.lower().strip()
    t = text.lower()
    if q in t:
        return True
    words = q.split()
    if len(words) > 1 and all(w in t for w in words):
        return True
    if len(words) == 1 and len(q) >= 4:
        for i in range(len(q)):
            if (q[:i] + q[i+1:]) in t:
                return True
    return False


def parse_price_dimensions(terms: dict) -> list:
    dimensions = []
    for term_type in ["OnDemand", "Reserved"]:
        term_data = terms.get(term_type, {})
        for sku_val in term_data.values():
            for dim_val in sku_val.get("priceDimensions", {}).values():
                price_usd = dim_val.get("pricePerUnit", {}).get("USD", "0")
                try:
                    if price_usd and float(price_usd) > 0:
                        dimensions.append({
                            "term_type": term_type,
                            "description": dim_val.get("description", ""),
                            "unit": dim_val.get("unit", ""),
                            "price_usd": price_usd,
                        })
                except (ValueError, TypeError):
                    pass
    return dimensions


def get_model_name(attrs: dict) -> str:
    name = attrs.get("model", "")
    if not name:
        name = attrs.get("servicename", attrs.get("group", "Unknown"))
        name = name.replace(" (Amazon Bedrock Edition)", "").strip()
    if not name:
        name = attrs.get("titanModel", attrs.get("titanModelUnit", "Unknown"))
    return name


def detect_tier(attrs: dict) -> str:
    usage_type = attrs.get("usagetype", "").lower()
    inference_type = attrs.get("inferenceType", "").lower()
    feature = attrs.get("feature", "").lower()
    if "priority" in usage_type or "priority" in inference_type:
        return "Priority"
    elif "flex" in usage_type or "flex" in inference_type:
        return "Flex"
    elif "provisioned" in usage_type or "provisioned" in feature:
        return "Provisioned"
    elif "batch" in usage_type or "batch" in feature:
        return "Batch"
    elif "cache" in usage_type or "cache" in inference_type:
        return "Prompt Caching"
    elif "custom-model" in usage_type or "customization" in feature:
        return "Custom Model"
    return "Standard"


def detect_variant(attrs: dict) -> str:
    usage_type = attrs.get("usagetype", "").lower()
    if "cross-region-global" in usage_type:
        return "Cross-Region (Global)"
    elif "cross-region" in usage_type:
        return "Cross-Region"
    return "Standard"


def load_cache_file(cache_dir: str, service_code: str) -> list:
    """Load a pricing cache JSON file. Warns if file is older than 7 days."""
    filename = CACHE_FILES.get(service_code, "")
    if not filename:
        return []
    paths_to_try = [
        os.path.join(cache_dir, filename),
        os.path.expanduser(f"~/{filename}"),
        os.path.join(cache_dir, "My Strands Examples", filename),
        os.path.expanduser(f"~/My Strands Examples/{filename}"),
    ]
    for filepath in paths_to_try:
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    # Check cache age — warn if older than 7 days
                    file_age_days = (time.time() - os.path.getmtime(filepath)) / 86400
                    if file_age_days > 7:
                        print(f"⚠️  Cache file '{filename}' is {int(file_age_days)} days old. "
                              f"Run: python3 ~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh", file=sys.stderr)
                    data = json.load(f)
                items = data.get("PriceList", [])
                parsed = []
                for item in items:
                    if isinstance(item, str):
                        parsed.append(json.loads(item))
                    else:
                        parsed.append(item)
                return parsed
            except Exception as e:
                print(f"Warning: Failed to load {filepath}: {e}", file=sys.stderr)
    return []


def query_model_pricing(cache_dir, region_filter=None, provider_filter=None, model_filter=None):
    results = []
    for sc in MODEL_SERVICE_CODES:
        products = load_cache_file(cache_dir, sc)
        for prod in products:
            attrs = prod.get("product", {}).get("attributes", {})
            region_code = attrs.get("regionCode", "")
            if region_filter and region_code != region_filter:
                continue
            model_name = get_model_name(attrs)
            provider = attrs.get("provider", "")
            provider = classify_provider(provider if provider else model_name)
            if provider_filter and not fuzzy_match(provider_filter, provider):
                continue
            if model_filter and not fuzzy_match(model_filter, model_name):
                continue
            dimensions = parse_price_dimensions(prod.get("terms", {}))
            if not dimensions:
                continue
            tier = detect_tier(attrs)
            variant = detect_variant(attrs)
            results.append({
                "provider": provider,
                "model": model_name,
                "region": region_code,
                "tier": tier,
                "variant": variant,
                "dimensions": dimensions,
            })
    return results


def extract_bedrock_model_prices(results, tier="Standard", variant="Global", all_tiers=False, include_multimodal=False):
    """Extract standardized per-1M-token prices from query_model_pricing() results.

    Handles differences in pricing format across model families:
    - Most models: prices stored per 1M tokens with "Million Input Tokens" descriptions.
    - Amazon Nova models: prices stored per 1K tokens — auto-detected and converted to per-1M.
    - Models with "Response Tokens" instead of "Output Tokens" (e.g., Haiku 4.5).

    Args:
        results: List of dicts from query_model_pricing().
        tier: Target tier: "Standard", "Priority", "Flex", "Batch". Default: "Standard".
             Prompt Caching prices are always included alongside the selected tier.
        variant: Target variant: "Global" (cross-region) or "Regional" (in-region).
                 Matched against the description field, not the variant field. Default: "Global".
        all_tiers: If True, return nested dict keyed by "{tier} {variant}" with all
                   available tier/variant combos. Default: False (returns flat dict for
                   the specified tier+variant).
        include_multimodal: If True, include image_input, audio_input, video_input keys.
                           Default: False (text tokens only).

    Returns:
        If all_tiers=False: Dict with keys: input, output, cache_read, cache_write
            (and optionally image_input, audio_input, video_input). Values are float
            ($/M tokens) or None if not found.
        If all_tiers=True: Dict of "{Tier} {Variant}" → price dict. Only tiers with
            at least one non-None price are included.
    """

    def _classify_variant(desc):
        """Determine if a description is Global or Regional."""
        d = desc.lower()
        if "cross-region-global" in d or ("global" in d and "regional" not in d):
            return "Global"
        elif "regional" in d or "cris" in d:
            return "Regional"
        # For per-1K Nova format: "USW2-" prefix = Regional, "cross-region" = Global
        if "cross-region" in d:
            return "Global"
        # Default: if no variant indicator, treat as Regional (in-region)
        return "Regional"

    def _classify_dim(desc):
        """Classify a price dimension into a price key."""
        d = desc.lower()
        # Skip reserved throughput and grounding
        if "per hour" in d or "reserved" in d or "grounding" in d:
            return None
        # Cache read
        if ("cache" in d and "read" in d) or "cacheread" in d.replace(" ", ""):
            return "cache_read"
        # Cache write — skip 1-hour TTL (prefer standard 5-min)
        if ("cache" in d and "write" in d) or "cachewrite" in d.replace(" ", ""):
            if "1h" in d or "1 hour" in d or "1-hr" in d:
                return None  # Skip 1-hour TTL
            return "cache_write"
        # Text output (some models use "response" instead of "output")
        # Must come BEFORE multimodal checks — "output-image-token" should be "output", not "image_input"
        if "output" in d or "response" in d:
            return "output"
        # Multimodal inputs (checked AFTER output to avoid misclassifying multimodal outputs)
        if "image" in d and ("input" in d or "image-token" in d):
            return "image_input"
        if "audio" in d and ("input" in d or "audio-token" in d):
            return "audio_input"
        if "video" in d and ("input" in d or "video-token" in d):
            return "video_input"
        # Text input (must come after cache/multimodal checks)
        if "input" in d:
            return "input"
        return None

    def _extract_for_tier_variant(results, target_tier, target_variant, include_mm=False):
        """Extract prices for a specific tier+variant combo."""
        keys = ["input", "output", "cache_read", "cache_write"]
        if include_mm:
            keys += ["image_input", "audio_input", "video_input"]
        prices = {k: None for k in keys}

        # For Standard/Priority/Flex/Batch, also pull in Prompt Caching tier
        tier_match = [target_tier.lower()]
        if target_tier.lower() in ("standard", "priority", "flex"):
            tier_match.append("prompt caching")

        filtered = [r for r in results if r.get("tier", "").lower() in tier_match]

        for r in filtered:
            for dim in r.get("dimensions", []):
                desc = dim.get("description", "")
                price = float(dim.get("price_usd", 0))
                if price == 0:
                    continue

                # Detect per-1K vs per-1M
                desc_lower = desc.lower()
                is_per_1k = ("per 1k" in desc_lower or "/1k" in desc_lower) and "million" not in desc_lower
                multiplier = 1000.0 if is_per_1k else 1.0

                # Check variant match
                dim_variant = _classify_variant(desc)
                if dim_variant.lower() != target_variant.lower():
                    continue

                # Classify the dimension
                key = _classify_dim(desc)
                if key is None:
                    continue
                if key not in prices:
                    continue  # e.g., multimodal key when include_mm=False

                # First match wins — iteration order determines which price is kept
                if prices[key] is None:
                    prices[key] = price * multiplier

        return prices

    if all_tiers:
        # Return nested dict with all available tier × variant combos
        all_results = {}
        tier_names = set(r.get("tier", "") for r in results)

        # Map detected tiers to canonical names
        canonical_tiers = set()
        for t in tier_names:
            if t.lower() in ("standard", "prompt caching"):
                canonical_tiers.add("Standard")
            elif t.lower() == "priority":
                canonical_tiers.add("Priority")
            elif t.lower() == "flex":
                canonical_tiers.add("Flex")
            elif t.lower() == "batch":
                canonical_tiers.add("Batch")
            elif t.lower() == "provisioned":
                canonical_tiers.add("Provisioned")
            elif t.lower() == "custom model":
                canonical_tiers.add("Custom Model")

        for t in sorted(canonical_tiers):
            for v in ["Global", "Regional"]:
                prices = _extract_for_tier_variant(results, t, v, include_multimodal)
                # Only include if at least one price was found
                if any(val is not None for val in prices.values()):
                    label = f"{t} {v}"
                    all_results[label] = prices

        return all_results

    else:
        # Single tier+variant extraction (backward compatible)
        return _extract_for_tier_variant(results, tier, variant, include_multimodal)



def query_agentcore_pricing(cache_dir, region_filter=None):
    results = []
    products = load_cache_file(cache_dir, AGENTCORE_SERVICE_CODE)
    for prod in products:
        attrs = prod.get("product", {}).get("attributes", {})
        region_code = attrs.get("regionCode", "")
        if region_filter and region_code != region_filter:
            continue
        service_name = attrs.get("servicename", attrs.get("group", "AgentCore"))
        component = attrs.get("group", attrs.get("usagetype", "Unknown"))
        dimensions = parse_price_dimensions(prod.get("terms", {}))
        if not dimensions:
            continue
        results.append({
            "component": service_name,
            "sub_component": component,
            "region": region_code,
            "dimensions": dimensions,
        })
    return results


def calculate_agent_cost_with_incremental_caching(
    input_price,
    output_price,
    cache_read_price,
    cache_write_price,
    sessions_per_month,
    questions_per_session=5,
    input_tokens=100,
    output_tokens=100,
    system_prompt_tokens=1000,
    tool_desc_tokens=4000,
    rag_chunks=10,
    rag_tokens_per_chunk=300,
    tools_invoked=10,
    tool_call_tokens=100,
    tool_result_tokens=500,
):
    """Calculate agent monthly cost using incremental prefix caching.

    Uses incremental caching: each LLM turn's prompt extends the prior turn's.
    The unchanged prefix is a cache read; only the new delta is new.

    Args:
        input_price (float): Input token price, $/M tokens.
        output_price (float): Output token price, $/M tokens.
        cache_read_price (float | None): Cache read price, $/M. None → 0.0.
        cache_write_price (float | None): Cache write price, $/M. None → 0.0.
        sessions_per_month (int): Total sessions per month.
        questions_per_session (float): Questions/session (default 5). Fractional
            values are supported and represent a weighted average across sessions
            with varying question counts.
        input_tokens (int): User question tokens (default 100).
        output_tokens (int): Final turn output tokens (default 100).
        system_prompt_tokens (int): System prompt tokens (default 1000).
        tool_desc_tokens (int): Tool description tokens (default 4000).
        rag_chunks (int): RAG chunks per question (default 10).
        rag_tokens_per_chunk (int): Tokens per RAG chunk (default 300).
        tools_invoked (int): Tool calls per question (default 10).
        tool_call_tokens (int): Tokens per tool call JSON (default 100).
        tool_result_tokens (int): Tokens per tool result (default 500).

    Returns:
        dict: assumptions, per_question, per_session, monthly_tokens,
        with_cache (dict with total_monthly, total_annual),
        no_cache (dict with total_monthly, total_annual),
        savings_monthly, savings_annual, savings_pct (float),
        explanation (dict): token_profile, turn_by_turn_q1,
            cross_question_caching, cache_math, no_cache_baseline,
            monthly_rollup, prices_used.
    """
    # Input validation
    if sessions_per_month <= 0:
        raise ValueError(f"sessions_per_month must be > 0, got {sessions_per_month}")
    if questions_per_session <= 0:
        raise ValueError(f"questions_per_session must be > 0, got {questions_per_session}")

    # Guard against None cache prices (models without caching support)
    cache_read_price = cache_read_price if cache_read_price is not None else 0.0
    cache_write_price = cache_write_price if cache_write_price is not None else 0.0
    N = tools_invoked
    turns_per_question = N + 1
    rag_tokens = rag_chunks * rag_tokens_per_chunk
    delta = tool_call_tokens + tool_result_tokens
    questions_per_month = sessions_per_month * questions_per_session

    if questions_per_month == 0 or sessions_per_month == 0:
        return {
            "assumptions": {"sessions_per_month": sessions_per_month, "questions_per_session": questions_per_session},
            "per_question": {}, "per_session": {}, "monthly_tokens": {},
            "with_cache": {"total_monthly": 0, "total_annual": 0},
            "no_cache": {"total_monthly": 0, "total_annual": 0},
            "savings_monthly": 0, "savings_annual": 0, "savings_pct": 0,
            "explanation": {"note": "Zero sessions or questions - no cost."},
        }

    # Base prompt on turn 0 of any question
    cacheable_base = system_prompt_tokens + tool_desc_tokens  # 5,000
    base_prompt = cacheable_base + input_tokens + rag_tokens  # 8,100

    # --- First question in session ---
    if N == 0:
        # Single turn, no tools: entire base_prompt is cache_write (for cross-Q caching)
        q1_cache_write = base_prompt
        q1_cache_read = 0
        q1_regular = 0
    else:
        # Turn 0: all new → cache write (will be re-read on turn 1)
        # Turns 1..N-1: prefix = cache read, delta = cache write (will be re-read)
        # Turn N (last): prefix = cache read, delta = regular input (not re-read)
        q1_cache_write = base_prompt + (N - 1) * delta
        q1_cache_read = 0
        for k in range(1, turns_per_question):
            q1_cache_read += base_prompt + (k - 1) * delta
        q1_regular = delta  # last turn only

    # --- Subsequent questions (2nd..last) in session ---
    if N == 0:
        # Single turn, no tools: system+tools cached from prior Q, user+RAG is new
        q2_cache_write = input_tokens + rag_tokens
        q2_cache_read = cacheable_base
        q2_regular = 0
    else:
        # Turn 0: system+tools = cache read (from prior Q), user+RAG = cache write (new)
        # Turns 1..N-1: full prefix = cache read, delta = cache write
        # Turn N (last): full prefix = cache read, delta = regular input
        q2_cache_write = (input_tokens + rag_tokens) + (N - 1) * delta
        q2_cache_read = cacheable_base  # turn 0: system+tools cached
        for k in range(1, turns_per_question):
            q2_cache_read += base_prompt + (k - 1) * delta
        q2_regular = delta

    # --- Per session ---
    n_subsequent = questions_per_session - 1
    session_cw = q1_cache_write + n_subsequent * q2_cache_write
    session_cr = q1_cache_read + n_subsequent * q2_cache_read
    session_reg = q1_regular + n_subsequent * q2_regular
    output_per_question = output_tokens + tools_invoked * tool_call_tokens
    session_out = questions_per_session * output_per_question

    # --- Monthly costs ---
    monthly_cw = sessions_per_month * (session_cw / 1e6) * cache_write_price
    monthly_cr = sessions_per_month * (session_cr / 1e6) * cache_read_price
    monthly_reg = sessions_per_month * (session_reg / 1e6) * input_price
    monthly_out = sessions_per_month * (session_out / 1e6) * output_price
    total_cached = monthly_cw + monthly_cr + monthly_reg + monthly_out

    # --- No-cache baseline ---
    # Every turn sends full prompt at regular input price
    total_input_per_question = 0
    for t in range(turns_per_question):
        total_input_per_question += base_prompt + t * delta
    total_no_cache_input = questions_per_month * (total_input_per_question / 1e6) * input_price
    total_no_cache_output = questions_per_month * (output_per_question / 1e6) * output_price
    total_no_cache = total_no_cache_input + total_no_cache_output

    savings = total_no_cache - total_cached
    savings_pct = (savings / total_no_cache) * 100 if total_no_cache > 0 else 0

    # ── Build step-by-step explanation ──
    # Section 1: Token profile
    token_profile = {
        "base_context": f"{_fmt(base_prompt)} = {_fmt(system_prompt_tokens)} (system) + {_fmt(tool_desc_tokens)} (tools) + {_fmt(input_tokens)} (user) + {_fmt(rag_tokens)} (RAG)",
        "cacheable_prefix": f"{_fmt(cacheable_base)} = {_fmt(system_prompt_tokens)} (system) + {_fmt(tool_desc_tokens)} (tools)",
        "delta_per_turn": f"{_fmt(delta)} = {_fmt(tool_call_tokens)} (tool call) + {_fmt(tool_result_tokens)} (tool result)",
        "turns_per_question": f"{turns_per_question} = {N} tool invocations + 1",
        "output_per_question": f"{_fmt(output_per_question)} = {_fmt(output_tokens)} (response) + {N} × {_fmt(tool_call_tokens)} (tool calls)",
    }

    # Section 2: Turn-by-turn breakdown for Q1
    turn_details = []
    for t in range(turns_per_question):
        tokens_in = base_prompt + t * delta
        if t == 0:
            cache_action = f"WRITE {_fmt(tokens_in)} (entire prompt — first turn of session)"
        elif t < turns_per_question - 1:
            prefix = base_prompt + (t - 1) * delta
            cache_action = f"READ {_fmt(prefix)} (cached prefix) + WRITE {_fmt(delta)} (new tool delta)"
        else:
            prefix = base_prompt + (t - 1) * delta
            cache_action = f"READ {_fmt(prefix)} (cached prefix) + REG {_fmt(delta)} (last turn — won't be re-read)"
        turn_details.append(f"Turn {t}: {_fmt(tokens_in)} input tokens → {cache_action}")
    total_input_q1 = sum(base_prompt + t * delta for t in range(turns_per_question))
    turn_details.append(f"Total Q1 input: {_fmt(total_input_q1)} tokens across {turns_per_question} turns")

    # Section 3: Cross-question caching
    cross_question = {
        "q2_turn0": f"READ {_fmt(cacheable_base)} (system+tools still cached from Q1) + WRITE {_fmt(input_tokens + rag_tokens)} (new user question + RAG)",
        "savings": f"Cross-Q caching saves re-writing {_fmt(cacheable_base)} tokens at ${cache_write_price}/M on each subsequent question",
    }

    # Section 4: Cache math (monthly)
    cache_math = {
        "cache_write": f"{_fmt(sessions_per_month * session_cw)} tokens × ${cache_write_price}/M = ${monthly_cw:,.2f}",
        "cache_read": f"{_fmt(sessions_per_month * session_cr)} tokens × ${cache_read_price}/M = ${monthly_cr:,.2f}",
        "regular_input": f"{_fmt(sessions_per_month * session_reg)} tokens × ${input_price}/M = ${monthly_reg:,.2f}",
        "output": f"{_fmt(sessions_per_month * session_out)} tokens × ${output_price}/M = ${monthly_out:,.2f}",
        "total_cached": f"${monthly_cw:,.2f} + ${monthly_cr:,.2f} + ${monthly_reg:,.2f} + ${monthly_out:,.2f} = ${total_cached:,.2f}",
    }

    # Section 5: No-cache baseline
    no_cache_math = {
        "total_input_per_q": f"{_fmt(total_input_per_question)} tokens/question × {_fmt(questions_per_month)} questions × ${input_price}/M = ${total_no_cache_input:,.2f}",
        "total_output": f"{_fmt(output_per_question)} tokens/question × {_fmt(questions_per_month)} questions × ${output_price}/M = ${total_no_cache_output:,.2f}",
        "total_no_cache": f"${total_no_cache_input:,.2f} + ${total_no_cache_output:,.2f} = ${total_no_cache:,.2f}",
    }

    # Section 6: Monthly rollup
    monthly_rollup = {
        "questions_per_month": _fmt(questions_per_month),
        "with_caching": f"${total_cached:,.2f}/mo (${total_cached / sessions_per_month:.4f}/session, ${total_cached / questions_per_month:.4f}/question)",
        "without_caching": f"${total_no_cache:,.2f}/mo (${total_no_cache / sessions_per_month:.4f}/session)",
        "savings": f"${savings:,.2f}/mo ({savings_pct:.1f}%)",
    }

    # Section 7: Prices used
    prices_used = {
        "input": f"${input_price}/M tokens",
        "output": f"${output_price}/M tokens",
        "cache_read": f"${cache_read_price}/M tokens ({cache_read_price/input_price*100:.0f}% of input)" if input_price > 0 else f"${cache_read_price}/M tokens",
        "cache_write": f"${cache_write_price}/M tokens ({cache_write_price/input_price*100:.0f}% of input)" if input_price > 0 else f"${cache_write_price}/M tokens",
    }

    explanation = {
        "token_profile": token_profile,
        "turn_by_turn_q1": turn_details,
        "cross_question_caching": cross_question,
        "cache_math": cache_math,
        "no_cache_baseline": no_cache_math,
        "monthly_rollup": monthly_rollup,
        "prices_used": prices_used,
    }

    return {
        "assumptions": {
            "sessions_per_month": sessions_per_month,
            "questions_per_session": questions_per_session,
            "questions_per_month": questions_per_month,
            "tools_invoked": N,
            "turns_per_question": turns_per_question,
            "system_prompt_tokens": system_prompt_tokens,
            "tool_desc_tokens": tool_desc_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "rag_chunks": rag_chunks,
            "rag_tokens_per_chunk": rag_tokens_per_chunk,
            "rag_tokens": rag_tokens,
            "tool_call_tokens": tool_call_tokens,
            "tool_result_tokens": tool_result_tokens,
            "delta_per_tool_turn": delta,
            "base_prompt": base_prompt,
            "cacheable_base": cacheable_base,
        },
        "per_question": {
            "q1_cache_write": q1_cache_write,
            "q1_cache_read": q1_cache_read,
            "q1_regular": q1_regular,
            "q2_cache_write": q2_cache_write,
            "q2_cache_read": q2_cache_read,
            "q2_regular": q2_regular,
        },
        "per_session": {
            "cache_write": session_cw,
            "cache_read": session_cr,
            "regular_input": session_reg,
            "output": session_out,
        },
        "monthly_tokens": {
            "cache_write": sessions_per_month * session_cw,
            "cache_read": sessions_per_month * session_cr,
            "regular_input": sessions_per_month * session_reg,
            "output": sessions_per_month * session_out,
        },
        "with_cache": {
            "cache_write_cost": monthly_cw,
            "cache_read_cost": monthly_cr,
            "regular_input_cost": monthly_reg,
            "output_cost": monthly_out,
            "total_monthly": total_cached,
            "total_annual": total_cached * 12,
        },
        "no_cache": {
            "input_cost": total_no_cache_input,
            "output_cost": total_no_cache_output,
            "total_monthly": total_no_cache,
            "total_annual": total_no_cache * 12,
        },
        "savings_monthly": savings,
        "savings_annual": savings * 12,
        "savings_pct": savings_pct,
        "explanation": explanation,
    }


def format_price(p):
    try:
        v = float(p)
        if v == 0: return "$0.00"
        elif v < 0.0001: return f"${v:.8f}"
        elif v < 0.01: return f"${v:.6f}"
        elif v < 1: return f"${v:.4f}"
        else: return f"${v:.2f}"
    except: return p


def generate_model_markdown(results):
    if not results:
        return "No pricing data found matching the specified filters.\n"
    tree = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
    for r in results:
        key = r["tier"]
        if r.get("variant", "Standard") != "Standard":
            key = f"{r['tier']} ({r['variant']})"
        tree[r["region"]][r["provider"]][r["model"]][key].extend(r["dimensions"])
    lines = ["## Bedrock Model Pricing\n"]
    region_count = len(tree)
    model_set = set()
    for rd in tree.values():
        for pd in rd.values():
            for mn in pd:
                model_set.add(mn)
    lines.append(f"**{len(model_set)} models** across **{region_count} regions**\n")
    for region in sorted(tree.keys()):
        lines.append(f"\n### Region: `{region}`\n")
        for provider in sorted(tree[region].keys()):
            lines.append(f"\n#### {provider}\n")
            for model in sorted(tree[region][provider].keys()):
                lines.append(f"\n**{model}**\n")
                lines.append("| Tier | Description | Unit | Price |")
                lines.append("|------|-------------|------|-------|")
                for tier in sorted(tree[region][provider][model].keys()):
                    for d in tree[region][provider][model][tier]:
                        desc = d["description"][:80] if d["description"] else "-"
                        lines.append(f"| {tier} | {desc} | {d['unit']} | {format_price(d['price_usd'])} |")
    return "\n".join(lines)


def generate_agentcore_markdown(results):
    if not results:
        return ""
    tree = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in results:
        tree[r["region"]][r["component"]][r["sub_component"]].extend(r["dimensions"])
    lines = ["\n## AgentCore Pricing\n"]
    for region in sorted(tree.keys()):
        lines.append(f"\n### Region: `{region}`\n")
        for component in sorted(tree[region].keys()):
            lines.append(f"\n#### {component}\n")
            lines.append("| Resource | Description | Unit | Price |")
            lines.append("|----------|-------------|------|-------|")
            for sub in sorted(tree[region][component].keys()):
                for d in tree[region][component][sub]:
                    desc = d["description"][:80] if d["description"] else "-"
                    lines.append(f"| {sub} | {desc} | {d['unit']} | {format_price(d['price_usd'])} |")
    return "\n".join(lines)


def refresh_cache(output_dir):
    try:
        import boto3
    except ImportError:
        print("ERROR: boto3 is required for refresh mode. Install with: pip install boto3", file=sys.stderr)
        sys.exit(1)
    client = boto3.client("pricing", region_name="us-east-1")
    for sc, filename in CACHE_FILES.items():
        filepath = os.path.join(output_dir, filename)
        print(f"Fetching {sc}...", file=sys.stderr)
        all_items = []
        paginator = client.get_paginator("get_products")
        for page in paginator.paginate(ServiceCode=sc):
            all_items.extend(page["PriceList"])
        data = {"PriceList": all_items, "FormatVersion": "aws_v1"}
        with open(filepath, "w") as f:
            json.dump(data, f)
        print(f"  Saved {len(all_items)} entries to {filepath}", file=sys.stderr)
    print("\nCache refresh complete!", file=sys.stderr)
    print("\n💡 Tier advisory may be outdated. To refresh, open Quick Desktop and ask:", file=sys.stderr)
    print("   \"Read the current guidance file at ~/.quickwork/skills/bedrock-tier-advisor/bedrock-tier-guidance.md.", file=sys.stderr)
    print("   Query AWS documentation using the aws-documentation-mcp-server to extract the latest tier", file=sys.stderr)
    print("   and variant guidance from these pages:", file=sys.stderr)
    print("   - https://docs.aws.amazon.com/bedrock/latest/userguide/service-tiers-inference.html", file=sys.stderr)
    print("   - https://docs.aws.amazon.com/bedrock/latest/userguide/capacity-limits-cost-optimization.html", file=sys.stderr)
    print("   - https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html", file=sys.stderr)
    print("   Update bedrock-tier-guidance.md with any changes. Preserve the file structure and source citations.\"", file=sys.stderr)


def refresh_quotas(output_dir, regions=None):
    """Fetch default RPM/TPM quotas for Bedrock models using Service Quotas API.

    Uses list-service-quotas (not get-aws-default-service-quota) to get all quotas,
    then filters to RPM/TPM entries. Results are universal defaults regardless of
    which AWS account calls the API.

    Args:
        output_dir: Directory to save bedrock_quotas.json
        regions: List of region codes to query. Default: major Bedrock regions.
    """
    try:
        import boto3
    except ImportError:
        print("ERROR: boto3 is required for quota refresh. Install with: pip install boto3", file=sys.stderr)
        return

    if regions is None:
        regions = [
            "us-east-1",
            "us-west-2",
            "eu-west-1",
            "eu-central-1",
            "ap-northeast-1",
            "ap-southeast-1",
            "ap-southeast-2",
            "ap-south-1",
            "ca-central-1",
            "sa-east-1",
        ]  # Major Bedrock regions; override with --quota-regions for others

    # Keywords to filter relevant quota names
    RPM_KEYWORDS = ["requests per minute", "invocations per minute"]
    TPM_KEYWORDS = ["tokens per minute"]
    TPD_KEYWORDS = ["tokens per day"]

    all_quotas = []
    errors = []

    for region in regions:
        print(f"Fetching quotas for {region}...", file=sys.stderr)
        try:
            client = boto3.client("service-quotas", region_name=region)
            paginator = client.get_paginator("list_service_quotas")
            region_count = 0

            for page in paginator.paginate(ServiceCode="bedrock"):
                for quota in page.get("Quotas", []):
                    name = quota.get("QuotaName", "")
                    name_lower = name.lower()

                    # Determine quota type
                    quota_type = None
                    if any(kw in name_lower for kw in RPM_KEYWORDS):
                        quota_type = "RPM"
                    elif any(kw in name_lower for kw in TPM_KEYWORDS):
                        quota_type = "TPM"
                    elif any(kw in name_lower for kw in TPD_KEYWORDS):
                        quota_type = "TPD"

                    if quota_type is None:
                        continue

                    # Determine inference type from name
                    inference_type = "On-demand"
                    if "global cross-region" in name_lower:
                        inference_type = "Global"
                    elif "cross-region" in name_lower:
                        inference_type = "Cross-region"
                    elif "latency-optimized" in name_lower:
                        inference_type = "Latency-optimized"
                    elif "custom model" in name_lower or "model customization" in name_lower:
                        inference_type = "Custom-model"

                    entry = {
                        "region": region,
                        "quota_name": name,
                        "quota_code": quota.get("QuotaCode", ""),
                        "value": quota.get("Value", 0),
                        "unit": quota.get("Unit", ""),
                        "adjustable": quota.get("Adjustable", False),
                        "quota_type": quota_type,
                        "inference_type": inference_type,
                        "service_code": quota.get("ServiceCode", "bedrock"),
                    }
                    all_quotas.append(entry)
                    region_count += 1

            print(f"  Found {region_count} RPM/TPM/TPD quotas in {region}", file=sys.stderr)

        except Exception as e:
            err_msg = f"Error fetching quotas for {region}: {str(e)}"
            print(f"  WARNING: {err_msg}", file=sys.stderr)
            errors.append(err_msg)
            continue

    if not all_quotas:
        print("WARNING: No quotas found. Check AWS credentials and region availability.", file=sys.stderr)
        return

    # Save to cache
    filepath = os.path.join(output_dir, QUOTAS_CACHE_FILE)
    import time
    cache_data = {
        "quotas": all_quotas,
        "regions_queried": regions,
        "total_entries": len(all_quotas),
        "refresh_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "errors": errors,
    }
    with open(filepath, "w") as f:
        json.dump(cache_data, f, indent=2, default=str)
    print(f"  Saved {len(all_quotas)} quota entries to {filepath}", file=sys.stderr)
    if errors:
        print(f"  ({len(errors)} region(s) had errors — see file for details)", file=sys.stderr)


def query_quotas(cache_dir, region_filter=None, model_filter=None, quota_type_filter=None,
                 inference_type_filter=None):
    """Query cached quota data. Works in sandbox (no boto3 needed).

    Args:
        cache_dir: Directory containing bedrock_quotas.json
        region_filter: Filter by region code (e.g. 'us-west-2')
        model_filter: Fuzzy match against quota_name (e.g. 'Claude Sonnet 4.6', 'Nova')
        quota_type_filter: Filter by type: 'RPM', 'TPM', or 'TPD'
        inference_type_filter: Filter by inference type: 'On-demand', 'Cross-region', 'Global'

    Returns:
        List of quota dicts, or empty list if cache file not found.
    """
    filepath = os.path.join(cache_dir, QUOTAS_CACHE_FILE)
    if not os.path.exists(filepath):
        filepath = os.path.expanduser(f"~/{QUOTAS_CACHE_FILE}")
    if not os.path.exists(filepath):
        return []

    with open(filepath, "r") as f:
        data = json.load(f)

    results = data.get("quotas", [])

    if region_filter:
        results = [q for q in results if q.get("region") == region_filter]
    if model_filter:
        results = [q for q in results if fuzzy_match(model_filter, q.get("quota_name", ""))]
    if quota_type_filter:
        results = [q for q in results if q.get("quota_type") == quota_type_filter]
    if inference_type_filter:
        results = [q for q in results if q.get("inference_type") == inference_type_filter]

    return results


def main():
    parser = argparse.ArgumentParser(description="Fetch Bedrock & AgentCore pricing")
    parser.add_argument("--refresh", action="store_true", help="Refresh cache from AWS Pricing API")
    parser.add_argument("--output-dir", type=str, default=os.path.expanduser("~"), help="Dir to save cache files")
    parser.add_argument("--cache-dir", type=str, default=os.path.expanduser("~"), help="Dir to read cache files")
    parser.add_argument("--quota-regions", type=str,
                        default="us-east-1,us-west-2,eu-west-1,eu-central-1,ap-northeast-1,ap-southeast-1,ap-southeast-2,ap-south-1,ca-central-1,sa-east-1",
                        help="Comma-separated regions for quota refresh (default: 10 major Bedrock regions)")
    parser.add_argument("--all-regions", action="store_true", default=False, help="Fetch quotas for ALL 35 Bedrock regions (slow)")
    parser.add_argument("--region", type=str, default=None, help="AWS region code")
    parser.add_argument("--provider", type=str, default=None, help="Provider/model family")
    parser.add_argument("--model", type=str, default=None, help="Model name")
    parser.add_argument("--include-agentcore", action="store_true", default=False, help="Include AgentCore")
    parser.add_argument("--json", action="store_true", default=False, help="Output raw JSON")
    parser.add_argument("--skip-quotas", action="store_true", default=False, help="Skip quota refresh (pricing only)")
    args = parser.parse_args()
    if args.refresh:
        refresh_cache(args.output_dir)
        if not args.skip_quotas:
            if args.all_regions:
                # Fetch quotas for all known Bedrock regions
                quota_regions = [
                    "af-south-1", "ap-east-2", "ap-northeast-1", "ap-northeast-2", "ap-northeast-3",
                    "ap-south-1", "ap-south-2", "ap-southeast-1", "ap-southeast-2", "ap-southeast-3",
                    "ap-southeast-4", "ap-southeast-5", "ap-southeast-6", "ap-southeast-7",
                    "ca-central-1", "ca-west-1", "eu-central-1", "eu-central-2", "eu-north-1",
                    "eu-south-1", "eu-south-2", "eu-west-1", "eu-west-2", "eu-west-3",
                    "il-central-1", "me-central-1", "me-south-1", "mx-central-1",
                    "sa-east-1", "us-east-1", "us-east-2", "us-west-1", "us-west-2",
                ]
                print(f"Fetching quotas for ALL {len(quota_regions)} regions...", file=sys.stderr)
            else:
                quota_regions = [r.strip() for r in args.quota_regions.split(",") if r.strip()]
            refresh_quotas(args.output_dir, regions=quota_regions)
        return
    model_results = query_model_pricing(args.cache_dir, args.region, args.provider, args.model)
    agentcore_results = []
    if args.include_agentcore:
        agentcore_results = query_agentcore_pricing(args.cache_dir, args.region)
    if args.json:
        output = {"model_pricing": model_results}
        if agentcore_results:
            output["agentcore_pricing"] = agentcore_results
        print(json.dumps(output, indent=2))
    else:
        md = generate_model_markdown(model_results)
        if args.include_agentcore:
            md += generate_agentcore_markdown(agentcore_results)
        print(md)
    print(f"\nTotal model price entries: {len(model_results)}", file=sys.stderr)
    if agentcore_results:
        print(f"Total AgentCore price entries: {len(agentcore_results)}", file=sys.stderr)


def calculate_evaluation_cost(
    questions_per_month,
    sessions_per_month,
    # Sampling
    sampling_rate=0.10,                    # 10% of sessions evaluated
    # Built-in evaluators (fixed-price LLM judge, model chosen by AWS)
    num_builtin_evaluators=3,              # e.g. Helpfulness, Correctness, Safety
    builtin_input_price=2.40,              # per 1M tokens (from AC cache)
    builtin_output_price=12.00,            # per 1M tokens (from AC cache)
    # Custom LLM-as-a-Judge evaluators (you pick the model)
    num_custom_llm_evaluators=0,
    custom_eval_invocation_price=0.0015,   # per evaluation (from AC cache)
    custom_judge_model_input_price=0.0,    # per 1M tokens (the judge model's own Bedrock price)
    custom_judge_model_output_price=0.0,   # per 1M tokens
    # Custom code-based evaluators (Lambda)
    num_code_evaluators=0,
    code_eval_invocation_price=0.0015,     # per evaluation (from AC cache)
    # Trace size — what the judge sees per question
    agent_input_tokens_per_q=100,
    agent_output_tokens_per_q=100,
    system_prompt_tokens=1000,
    tool_desc_tokens=4000,
    tools_invoked=10,
    tool_call_tokens=100,
    tool_result_tokens=500,
    rag_chunks=10,
    rag_tokens_per_chunk=300,
    # Judge output
    judge_output_tokens_per_eval=300,      # score + reasoning per evaluator
    questions_per_session=10,
):
    """Calculate AgentCore Evaluations cost (LLM-as-a-Judge).

    Args:
        questions_per_month (int): Total questions/month.
        sessions_per_month (int): Total sessions/month.
        sampling_rate (float): Fraction of sessions evaluated (default 0.10).
        num_builtin_evaluators (int): Built-in evaluators/question (default 3).
        builtin_input_price (float): Judge input $/M tokens (default 2.40).
        builtin_output_price (float): Judge output $/M tokens (default 12.00).
        num_custom_llm_evaluators (int): Custom LLM evaluators (default 0).
        num_code_evaluators (int): Code evaluators (default 0).
        agent_input/output_tokens_per_q, system_prompt_tokens, tool_desc_tokens,
            tools_invoked, tool_call/result_tokens, rag_chunks/tokens_per_chunk:
            Agent trace profile for judge input sizing.
        judge_output_tokens_per_eval (int): Judge output/eval (default 300).

    Returns:
        dict: evaluated_sessions, evaluated_questions, trace_tokens_per_q,
        builtin/custom_llm/custom_code (dicts with cost breakdowns),
        total_monthly, total_annual, warnings (list[str]),
        explanation (dict): sampling, trace_size, builtin_evaluators,
            custom_llm_evaluators, custom_code_evaluators, grand_total.
    """
    # Derive evaluated volume
    evaluated_sessions = sessions_per_month * sampling_rate
    evaluated_questions = evaluated_sessions * questions_per_session

    # Trace size per question (what the judge sees)
    rag_tokens = rag_chunks * rag_tokens_per_chunk
    tool_trace_tokens = tools_invoked * (tool_call_tokens + tool_result_tokens)
    trace_tokens_per_q = (
        system_prompt_tokens
        + tool_desc_tokens
        + agent_input_tokens_per_q
        + rag_tokens
        + tool_trace_tokens
        + agent_output_tokens_per_q
    )

    # ── Built-in evaluators ──
    builtin_judge_calls = evaluated_questions * num_builtin_evaluators
    builtin_input_cost = builtin_judge_calls * (trace_tokens_per_q / 1_000_000) * builtin_input_price
    builtin_output_cost = builtin_judge_calls * (judge_output_tokens_per_eval / 1_000_000) * builtin_output_price
    builtin_total = builtin_input_cost + builtin_output_cost

    # ── Custom LLM-as-a-Judge evaluators ──
    custom_llm_judge_calls = evaluated_questions * num_custom_llm_evaluators
    custom_llm_invocation_cost = custom_llm_judge_calls * custom_eval_invocation_price
    custom_llm_input_cost = custom_llm_judge_calls * (trace_tokens_per_q / 1_000_000) * custom_judge_model_input_price
    custom_llm_output_cost = custom_llm_judge_calls * (judge_output_tokens_per_eval / 1_000_000) * custom_judge_model_output_price
    custom_llm_total = custom_llm_invocation_cost + custom_llm_input_cost + custom_llm_output_cost

    # ── Custom code-based evaluators ──
    code_eval_calls = evaluated_questions * num_code_evaluators
    code_eval_total = code_eval_calls * code_eval_invocation_price

    total_monthly = builtin_total + custom_llm_total + code_eval_total

    # Warnings
    warnings = []
    if custom_judge_model_input_price > 0 and custom_judge_model_input_price == builtin_input_price:
        warnings.append(
            "Custom judge model price matches the agent's inference model price. "
            "If using the same model for both agent inference and evaluation judging, "
            "consider a cheaper model (e.g. Nova Lite) as the judge to reduce costs."
        )

    # ── Build step-by-step explanation ──
    explanation = {
        "sampling": {
            "total_sessions": _fmt(sessions_per_month),
            "sampling_rate": f"{sampling_rate*100:.0f}%",
            "evaluated_sessions": _fmt(evaluated_sessions),
            "questions_per_session": _fmt(questions_per_session),
            "evaluated_questions": _fmt(evaluated_questions),
        },
        "trace_size": {
            "components": f"{_fmt(system_prompt_tokens)} (sys) + {_fmt(tool_desc_tokens)} (tools) + {_fmt(agent_input_tokens_per_q)} (input) + {_fmt(rag_tokens)} (RAG) + {_fmt(tool_trace_tokens)} (tool traces) + {_fmt(agent_output_tokens_per_q)} (output)",
            "total_per_question": f"{_fmt(trace_tokens_per_q)} tokens",
        },
        "builtin_evaluators": {
            "count": _fmt(num_builtin_evaluators),
            "judge_calls": f"{_fmt(evaluated_questions)} questions × {num_builtin_evaluators} evaluators = {_fmt(builtin_judge_calls)}",
            "input_cost": f"{_fmt(builtin_judge_calls)} calls × {_fmt(trace_tokens_per_q)} tokens × ${builtin_input_price}/M = ${builtin_input_cost:,.2f}",
            "output_cost": f"{_fmt(builtin_judge_calls)} calls × {_fmt(judge_output_tokens_per_eval)} tokens × ${builtin_output_price}/M = ${builtin_output_cost:,.2f}",
            "total": f"${builtin_total:,.2f}",
        },
        "custom_llm_evaluators": {
            "count": _fmt(num_custom_llm_evaluators),
            "total": f"${custom_llm_total:,.2f}",
        },
        "custom_code_evaluators": {
            "count": _fmt(num_code_evaluators),
            "total": f"${code_eval_total:,.2f}",
        },
        "grand_total": f"${builtin_total:,.2f} + ${custom_llm_total:,.2f} + ${code_eval_total:,.2f} = ${total_monthly:,.2f}/mo",
    }

    return {
        "evaluated_sessions": evaluated_sessions,
        "evaluated_questions": evaluated_questions,
        "trace_tokens_per_q": trace_tokens_per_q,
        "builtin": {
            "judge_calls": builtin_judge_calls,
            "input_cost": builtin_input_cost,
            "output_cost": builtin_output_cost,
            "total": builtin_total,
        },
        "custom_llm": {
            "judge_calls": custom_llm_judge_calls,
            "invocation_cost": custom_llm_invocation_cost,
            "model_input_cost": custom_llm_input_cost,
            "model_output_cost": custom_llm_output_cost,
            "total": custom_llm_total,
        },
        "custom_code": {
            "eval_calls": code_eval_calls,
            "total": code_eval_total,
        },
        "total_monthly": total_monthly,
        "total_annual": total_monthly * 12,
        "warnings": warnings,
        "explanation": explanation,
    }


def check_capacity_fit(
    questions_per_month,
    sessions_per_month,
    rpm_limit,
    tpm_limit,
    # Traffic profile
    peak_to_avg_ratio=3.0,             # peak RPM = avg RPM × this factor
    active_hours_per_day=12,           # hours with traffic (rest = 0)
    active_days_per_month=22,          # business days
    # Agent config (same defaults as pricing)
    tools_invoked=10,
    input_tokens=100,
    output_tokens=100,
    system_prompt_tokens=1000,
    tool_desc_tokens=4000,
    rag_chunks=10,
    rag_tokens_per_chunk=300,
    tool_call_tokens=100,
    tool_result_tokens=500,
    questions_per_session=5,
    max_tokens_setting=4096,           # what max_tokens is set to in the API call
    # Model characteristics
    output_burndown_rate=1,            # 5 for Claude 3.7+, 1 for all others
    # Optional: pass token profile from calculate_agent_cost_with_incremental_caching result
    token_profile=None,                # If provided, overrides individual token params above
):
    """Check if a workload fits within Bedrock RPM/TPM quota limits.

    IMPORTANT: rpm_limit and tpm_limit are REQUIRED. Get them from query_quotas()
    for the specific model and region. Do NOT use hardcoded approximations.

    RECOMMENDED: Pass token_profile=model_result['assumptions'] from
    calculate_agent_cost_with_incremental_caching() to ensure the capacity check
    uses the exact same token parameters as the cost estimate.

    Args:
        questions_per_month, sessions_per_month (int): Workload volume.
        rpm_limit (int): Actual RPM quota limit from query_quotas().
        tpm_limit (int): Actual TPM quota limit from query_quotas().
        peak_to_avg_ratio (float): Peak multiplier (default 3.0).
        active_hours_per_day (int): Traffic hours (default 12).
        active_days_per_month (int): Business days (default 22).
        tools_invoked, input/output_tokens, system_prompt_tokens,
            tool_desc_tokens, rag_chunks, rag_tokens_per_chunk,
            tool_call/result_tokens: Token profile (overridden by token_profile if provided).
        max_tokens_setting (int): API max_tokens (default 4096).
        output_burndown_rate (int): Output TPM multiplier. 5 for Claude, 1 others.
        token_profile (dict | None): If provided, extracts token params from this dict
            (e.g., model_result['assumptions']). Overrides individual token params.

    Returns:
        dict: avg/peak_rpm, avg/peak/effective_peak_tpm (float),
        fits (bool), rpm/tpm_fits (bool), rpm/tpm_utilization_pct (float),
        recommendations (list[str]), optimization_checklist (list[dict]),
        explanation (dict): rpm_calculation, tpm_calculation, quota_comparison.
    """
    # If token_profile provided, extract values from it (overrides individual params)
    if token_profile is not None:
        tools_invoked = token_profile.get("tools_invoked", tools_invoked)
        input_tokens = token_profile.get("input_tokens", input_tokens)
        output_tokens = token_profile.get("output_tokens", output_tokens)
        system_prompt_tokens = token_profile.get("system_prompt_tokens", system_prompt_tokens)
        tool_desc_tokens = token_profile.get("tool_desc_tokens", tool_desc_tokens)
        rag_chunks = token_profile.get("rag_chunks", rag_chunks)
        rag_tokens_per_chunk = token_profile.get("rag_tokens_per_chunk", rag_tokens_per_chunk)
        tool_call_tokens = token_profile.get("tool_call_tokens", tool_call_tokens)
        tool_result_tokens = token_profile.get("tool_result_tokens", tool_result_tokens)
        questions_per_session = token_profile.get("questions_per_session", questions_per_session)
    # Input validation
    if questions_per_month <= 0:
        raise ValueError(f"questions_per_month must be > 0, got {questions_per_month}")
    if active_hours_per_day <= 0:
        raise ValueError(f"active_hours_per_day must be > 0, got {active_hours_per_day}")
    if active_days_per_month <= 0:
        raise ValueError(f"active_days_per_month must be > 0, got {active_days_per_month}")
    if rpm_limit <= 0:
        raise ValueError(f"rpm_limit must be > 0, got {rpm_limit}")
    if tpm_limit <= 0:
        raise ValueError(f"tpm_limit must be > 0, got {tpm_limit}")

    N = tools_invoked

    # ── Compute average RPM ──
    active_minutes_per_month = active_hours_per_day * 60 * active_days_per_month
    avg_questions_per_min = questions_per_month / active_minutes_per_month
    # Each question = N+1 LLM requests (1 initial + N tool calls)
    avg_rpm = avg_questions_per_min * (N + 1)
    peak_rpm = avg_rpm * peak_to_avg_ratio

    # ── Compute TPM ──
    base_context = input_tokens + system_prompt_tokens + tool_desc_tokens + rag_chunks * rag_tokens_per_chunk
    # Average input tokens across all N+1 turns of a question:
    # Sum = (N+1) × base_context + delta × N × (N+1) / 2
    # Per-turn average = base_context + delta × N / 2
    delta = (tool_call_tokens + tool_result_tokens)
    avg_input_per_turn = base_context + (delta / 2) * N
    # Average output per turn: tool call turns produce tool_call_tokens (JSON),
    # final turn produces the full output_tokens. Weighted average across N+1 turns.
    avg_output_per_turn = (N * tool_call_tokens + output_tokens) // (N + 1) if N > 0 else output_tokens

    # TPM at average load
    avg_tpm_input = avg_rpm * avg_input_per_turn
    avg_tpm_output = avg_rpm * avg_output_per_turn * output_burndown_rate
    avg_tpm = avg_tpm_input + avg_tpm_output

    # TPM at peak
    peak_tpm = avg_tpm * peak_to_avg_ratio

    # max_tokens overhead: at request start, max_tokens is reserved
    # This inflates effective TPM by (max_tokens - actual_output) per request
    max_tokens_overhead_per_req = max(0, max_tokens_setting - avg_output_per_turn)
    effective_peak_tpm = peak_tpm + (peak_rpm * max_tokens_overhead_per_req)

    # ── Compare against quota limits ──
    rpm_fits = peak_rpm <= rpm_limit
    tpm_fits = peak_tpm <= tpm_limit
    effective_tpm_fits = effective_peak_tpm <= tpm_limit
    fits = rpm_fits and effective_tpm_fits

    rpm_util = (peak_rpm / rpm_limit) * 100
    tpm_util = (effective_peak_tpm / tpm_limit) * 100

    # ── Recommendations ──
    recommendations = []
    if not rpm_fits:
        recommendations.append(f"Peak RPM ({peak_rpm:,.0f}) exceeds quota limit ({rpm_limit:,}). Consider a quota increase or cross-region inference.")
    if not effective_tpm_fits and tpm_fits:
        recommendations.append(f"Peak TPM fits ({peak_tpm:,.0f}) but effective TPM with max_tokens overhead ({effective_peak_tpm:,.0f}) exceeds limit ({tpm_limit:,}). Reduce max_tokens from {max_tokens_setting:,} to ~{avg_output_per_turn * 2}.")
    if not tpm_fits:
        recommendations.append(f"Peak TPM ({peak_tpm:,.0f}) exceeds quota limit ({tpm_limit:,}). Consider a quota increase or cross-region inference.")
    if output_burndown_rate > 1:
        recommendations.append(f"Output burndown rate is {output_burndown_rate}× — each output token consumes {output_burndown_rate} TPM quota. Reducing output length has {output_burndown_rate}× impact.")
    if fits:
        recommendations.append(f"Workload fits within quota limits. RPM utilization: {rpm_util:.0f}%, TPM utilization: {tpm_util:.0f}%.")

    # ── Optimization checklist (always returned) ──
    optimization_checklist = [
        {"area": "RAG chunks", "current": f"{rag_chunks} chunks × {rag_tokens_per_chunk} = {rag_chunks * rag_tokens_per_chunk:,} tokens", "action": "Reduce chunks retrieved or tokens per chunk without quality loss"},
        {"area": "System prompt", "current": f"{system_prompt_tokens:,} tokens", "action": "Shorten instructions, remove redundancy"},
        {"area": "Prompt caching", "current": "Check if enabled", "action": "Cache reads do NOT count toward TPM — enable caching to free quota"},
        {"area": "max_tokens", "current": f"{max_tokens_setting:,} (actual output ~{avg_output_per_turn})", "action": f"Reduce to ~{avg_output_per_turn * 3} to free {max_tokens_overhead_per_req:,} TPM/request"},
        {"area": "Conversation history", "current": "Included in context", "action": "Limit past Q&A turns packed as context"},
        {"area": "Tool count", "current": f"{tool_desc_tokens // 200} tools × 200 = {tool_desc_tokens:,} tokens", "action": "Use AC Gateway dynamic tool selection to reduce tool descriptions per request"},
        {"area": "Agent architecture", "current": f"Single agent, {N} tools", "action": "Split into parent + sub-agents to reduce per-agent tool count and compounding"},
        {"area": "Output length", "current": f"~{avg_output_per_turn} tokens" + (f" (×{output_burndown_rate} burndown)" if output_burndown_rate > 1 else ""), "action": "Constrain output with max_tokens and prompt instructions"},
    ]

    # ── Build step-by-step explanation ──
    explanation = {
        "rpm_calculation": {
            "active_minutes_per_month": f"{active_hours_per_day}h × 60 × {active_days_per_month}d = {_fmt(active_minutes_per_month)} min",
            "avg_questions_per_min": f"{_fmt(questions_per_month)} questions ÷ {_fmt(active_minutes_per_month)} min = {avg_questions_per_min:.2f} Q/min",
            "llm_calls_per_question": f"{N} tools + 1 = {N+1} LLM calls/question",
            "avg_rpm": f"{avg_questions_per_min:.2f} Q/min × {N+1} calls = {avg_rpm:.1f} RPM",
            "peak_rpm": f"{avg_rpm:.1f} × {peak_to_avg_ratio}× peak ratio = {peak_rpm:.0f} RPM",
        },
        "tpm_calculation": {
            "base_context": f"{_fmt(input_tokens)} (user) + {_fmt(system_prompt_tokens)} (sys) + {_fmt(tool_desc_tokens)} (tools) + {_fmt(rag_chunks * rag_tokens_per_chunk)} (RAG) = {_fmt(base_context)}",
            "avg_input_per_turn": f"{_fmt(base_context)} + ({_fmt(delta)}/2) × {N} = {_fmt(avg_input_per_turn)} tokens",
            "avg_tpm": f"{avg_rpm:.1f} RPM × ({_fmt(avg_input_per_turn)} in + {_fmt(avg_output_per_turn)}{'×' + str(output_burndown_rate) if output_burndown_rate > 1 else ''} out) = {_fmt(avg_tpm)} TPM",
            "peak_tpm": f"{_fmt(avg_tpm)} × {peak_to_avg_ratio}× = {_fmt(peak_tpm)} TPM",
            "max_tokens_overhead": f"max_tokens={_fmt(max_tokens_setting)} − actual_output={_fmt(avg_output_per_turn)} = {_fmt(max_tokens_overhead_per_req)} reserved/req",
            "effective_peak_tpm": f"{_fmt(peak_tpm)} + ({peak_rpm:.0f} RPM × {_fmt(max_tokens_overhead_per_req)}) = {_fmt(effective_peak_tpm)} TPM",
        },
        "quota_comparison": {
            "rpm_limit": f"{_fmt(rpm_limit)} (peak: {peak_rpm:.0f} → {'✅ fits' if rpm_fits else '❌ exceeds'})",
            "tpm_limit": f"{_fmt(tpm_limit)} (effective peak: {_fmt(effective_peak_tpm)} → {'✅ fits' if effective_tpm_fits else '❌ exceeds'})",
            "rpm_utilization": f"{rpm_util:.0f}%",
            "tpm_utilization": f"{tpm_util:.0f}%",
        },
    }

    return {
        "avg_rpm": avg_rpm,
        "peak_rpm": peak_rpm,
        "avg_tpm": avg_tpm,
        "peak_tpm": peak_tpm,
        "effective_peak_tpm": effective_peak_tpm,
        "max_tokens_overhead_per_req": max_tokens_overhead_per_req,
        "rpm_limit": rpm_limit,
        "tpm_limit": tpm_limit,
        "rpm_utilization_pct": rpm_util,
        "tpm_utilization_pct": tpm_util,
        "fits": fits,
        "rpm_fits": rpm_fits,
        "tpm_fits": tpm_fits,
        "recommendations": recommendations,
        "optimization_checklist": optimization_checklist,
        "assumptions": {
            "peak_to_avg_ratio": peak_to_avg_ratio,
            "active_hours_per_day": active_hours_per_day,
            "active_days_per_month": active_days_per_month,
            "active_minutes_per_month": active_minutes_per_month,
            "output_burndown_rate": output_burndown_rate,
        },
        "explanation": explanation,
    }




# ============================================================
# BUSINESS VALUE TIERS
# ============================================================
BUSINESS_VALUE_TIERS = {
    "Conservative": {"effectiveness": 0.50, "efficiency": 0.50},
    "Moderate":     {"effectiveness": 0.65, "efficiency": 0.60},
    "Optimistic":   {"effectiveness": 0.80, "efficiency": 0.70},
}


def calculate_agentcore_cost(
    # Prices (from cache — caller passes these in)
    runtime_vcpu_price_hr,
    runtime_mem_price_hr,
    gateway_invocation_price,
    gateway_search_price,
    gateway_indexing_price,
    stm_event_price,
    ltm_storage_price,
    ltm_retrieval_price,
    # Optional component prices (None = not included)
    browser_vcpu_price_hr=None,
    browser_mem_price_hr=None,
    ci_vcpu_price_hr=None,
    ci_mem_price_hr=None,
    # Workload params
    questions_per_month=1_000_000,
    questions_per_session=5,
    tools_invoked=10,
    tools_indexed=50,
    # Runtime params
    num_vcpus=2,
    peak_memory_gb=4,
    io_wait_pct=0.70,
    idle_time_between_questions_s=30,
    time_per_llm_turn_s=4.0,
    # Memory params
    stm_events_per_question=2,
    ltm_records_per_session=3,
    ltm_retrievals_per_question=1,
    # BrowserTool params
    browser_usage_pct=1.0,
    browser_vcpus=2,
    browser_memory_gb=4,
    # CodeInterpreter params
    ci_usage_pct=1.0,
    ci_vcpus=2,
    ci_memory_gb=4,
):
    """Calculate AgentCore component costs (Runtime, Gateway, Memory, BrowserTool, CodeInterpreter).

    Does NOT include Evaluations — use calculate_evaluation_cost() separately.

    Args:
        runtime_vcpu_price_hr, runtime_mem_price_hr (float): Runtime prices.
        gateway_invocation/search/indexing_price (float): Gateway prices.
        stm_event_price, ltm_storage/retrieval_price (float): Memory prices.
        browser_vcpu/mem_price_hr (float | None): BrowserTool prices. None = skip.
        ci_vcpu/mem_price_hr (float | None): CodeInterpreter prices. None = skip.
        questions_per_month (int): Total questions (default 1M).
        questions_per_session (int): Qs/session (default 5). Sessions derived.
        tools_invoked (int): Tool calls/question (default 10).
        num_vcpus (int): vCPUs per microVM (default 2).
        peak_memory_gb (int): Memory per microVM (default 4).
        io_wait_pct (float): I/O wait fraction, vCPU FREE during wait (default 0.70).
        time_per_llm_turn_s (float): Seconds per LLM turn (default 4.0).

    Returns:
        dict: assumptions, runtime/gateway/memory (dicts with cost breakdowns),
        total_monthly, total_annual (float),
        explanation (dict): session_profile, runtime, gateway, memory,
            grand_total, cost_composition.
    """
    # Input validation
    if questions_per_month <= 0:
        raise ValueError(f"questions_per_month must be > 0, got {questions_per_month}")
    if questions_per_session <= 0:
        raise ValueError(f"questions_per_session must be > 0, got {questions_per_session}")

    sessions_per_month = questions_per_month / questions_per_session

    # --- Runtime ---
    time_per_question_s = (1 + tools_invoked) * time_per_llm_turn_s
    active_cpu_per_question_s = time_per_question_s * (1 - io_wait_pct)
    total_active_cpu_per_session_s = active_cpu_per_question_s * questions_per_session

    idle_gaps_s = (questions_per_session - 1) * idle_time_between_questions_s
    total_session_duration_s = (time_per_question_s * questions_per_session) + idle_gaps_s

    runtime_cpu_cost = (total_active_cpu_per_session_s * num_vcpus
                        * (runtime_vcpu_price_hr / 3600) * sessions_per_month)
    runtime_mem_cost = (total_session_duration_s * peak_memory_gb
                        * (runtime_mem_price_hr / 3600) * sessions_per_month)
    runtime_total = runtime_cpu_cost + runtime_mem_cost

    # --- Gateway ---
    gateway_inv_count = (1 + tools_invoked) * questions_per_month
    gateway_search_count = questions_per_month
    gateway_inv_cost = gateway_inv_count * gateway_invocation_price
    gateway_search_cost = gateway_search_count * gateway_search_price
    gateway_index_cost = tools_indexed * gateway_indexing_price
    gateway_total = gateway_inv_cost + gateway_search_cost + gateway_index_cost

    # --- Memory ---
    stm_events = stm_events_per_question * questions_per_month
    ltm_records = ltm_records_per_session * sessions_per_month
    ltm_retrievals = ltm_retrievals_per_question * questions_per_month

    stm_cost = stm_events * stm_event_price
    ltm_storage_cost = ltm_records * ltm_storage_price
    ltm_retrieval_cost = ltm_retrievals * ltm_retrieval_price
    memory_total = stm_cost + ltm_storage_cost + ltm_retrieval_cost

    # --- BrowserTool (optional) ---
    browser_total = 0
    browser_cpu_cost = 0
    browser_mem_cost = 0
    if browser_vcpu_price_hr is not None and browser_mem_price_hr is not None:
        browser_questions = questions_per_month * browser_usage_pct
        # 100% duration — no I/O wait discount
        browser_cpu_cost = (time_per_question_s * browser_questions * browser_vcpus
                            * (browser_vcpu_price_hr / 3600))
        browser_mem_cost = (time_per_question_s * browser_questions * browser_memory_gb
                            * (browser_mem_price_hr / 3600))
        browser_total = browser_cpu_cost + browser_mem_cost

    # --- CodeInterpreter (optional) ---
    ci_total = 0
    ci_cpu_cost = 0
    ci_mem_cost = 0
    if ci_vcpu_price_hr is not None and ci_mem_price_hr is not None:
        ci_questions = questions_per_month * ci_usage_pct
        ci_cpu_cost = (time_per_question_s * ci_questions * ci_vcpus
                       * (ci_vcpu_price_hr / 3600))
        ci_mem_cost = (time_per_question_s * ci_questions * ci_memory_gb
                       * (ci_mem_price_hr / 3600))
        ci_total = ci_cpu_cost + ci_mem_cost

    # --- Totals ---
    total_monthly = runtime_total + gateway_total + memory_total + browser_total + ci_total
    total_annual = total_monthly * 12

    # ── Build step-by-step explanation ──
    explanation = {
        "session_profile": {
            "sessions_per_month": _fmt(sessions_per_month),
            "questions_per_session": _fmt(questions_per_session),
            "questions_per_month": _fmt(questions_per_month),
            "time_per_question": f"({tools_invoked} tools + 1) × 4s = {time_per_question_s}s",
            "session_duration": f"{questions_per_session} Qs × {time_per_question_s}s + {questions_per_session - 1} × {idle_time_between_questions_s}s idle = {total_session_duration_s}s ({total_session_duration_s/60:.1f} min)",
        },
        "runtime": {
            "vcpu_billing": f"Active processing only: {time_per_question_s}s × {1 - io_wait_pct:.0%} active × {questions_per_session} Qs = {total_active_cpu_per_session_s:.1f}s/session",
            "vcpu_cost": f"{total_active_cpu_per_session_s:.1f}s × {num_vcpus} vCPU × ${runtime_vcpu_price_hr}/hr ÷ 3600 × {_fmt(sessions_per_month)} sessions = ${runtime_cpu_cost:,.2f}",
            "memory_billing": f"Full session duration: {total_session_duration_s}s/session (I/O wait still billed for memory)",
            "memory_cost": f"{total_session_duration_s}s × {peak_memory_gb} GB × ${runtime_mem_price_hr}/hr ÷ 3600 × {_fmt(sessions_per_month)} sessions = ${runtime_mem_cost:,.2f}",
            "total": f"${runtime_cpu_cost:,.2f} + ${runtime_mem_cost:,.2f} = ${runtime_total:,.2f}",
            "key_insight": f"vCPU is FREE during I/O wait ({io_wait_pct:.0%} of time). Memory is billed for full duration.",
        },
        "gateway": {
            "invocations": f"({tools_invoked} + 1) × {_fmt(questions_per_month)} Qs = {_fmt(gateway_inv_count)} calls × ${gateway_invocation_price} = ${gateway_inv_cost:,.2f}",
            "search": f"{_fmt(questions_per_month)} Qs × ${gateway_search_price} = ${gateway_search_cost:,.2f}",
            "indexing": f"{tools_indexed} tools × ${gateway_indexing_price}/tool-month = ${gateway_index_cost:,.2f}",
            "total": f"${gateway_total:,.2f}",
        },
        "memory": {
            "stm": f"{stm_events_per_question} events/Q × {_fmt(questions_per_month)} Qs × ${stm_event_price}/event = ${stm_cost:,.2f} (reads are FREE)",
            "ltm_storage": f"{ltm_records_per_session} records/session × {_fmt(sessions_per_month)} sessions × ${ltm_storage_price}/record = ${ltm_storage_cost:,.2f}",
            "ltm_retrieval": f"{ltm_retrievals_per_question}/Q × {_fmt(questions_per_month)} Qs × ${ltm_retrieval_price}/retrieval = ${ltm_retrieval_cost:,.2f}",
            "total": f"${memory_total:,.2f}",
        },
        "grand_total": f"${runtime_total:,.2f} (runtime) + ${gateway_total:,.2f} (gateway) + ${memory_total:,.2f} (memory)"
                       + (f" + ${browser_total:,.2f} (browser)" if browser_total > 0 else "")
                       + (f" + ${ci_total:,.2f} (code interpreter)" if ci_total > 0 else "")
                       + f" = ${total_monthly:,.2f}/mo",
        "cost_composition": {
            "runtime_pct": f"{runtime_total / total_monthly * 100:.0f}%" if total_monthly > 0 else "0%",
            "gateway_pct": f"{gateway_total / total_monthly * 100:.0f}%" if total_monthly > 0 else "0%",
            "memory_pct": f"{memory_total / total_monthly * 100:.0f}%" if total_monthly > 0 else "0%",
        },
    }

    return {
        "assumptions": {
            "questions_per_month": questions_per_month,
            "questions_per_session": questions_per_session,
            "sessions_per_month": sessions_per_month,
            "tools_invoked": tools_invoked,
            "tools_indexed": tools_indexed,
            "num_vcpus": num_vcpus,
            "peak_memory_gb": peak_memory_gb,
            "io_wait_pct": io_wait_pct,
            "idle_time_between_questions_s": idle_time_between_questions_s,
            "time_per_question_s": time_per_question_s,
            "total_session_duration_s": total_session_duration_s,
        },
        "runtime": {
            "cpu_cost": runtime_cpu_cost,
            "mem_cost": runtime_mem_cost,
            "total": runtime_total,
        },
        "gateway": {
            "invocation_cost": gateway_inv_cost,
            "search_cost": gateway_search_cost,
            "indexing_cost": gateway_index_cost,
            "total": gateway_total,
        },
        "memory": {
            "stm_cost": stm_cost,
            "ltm_storage_cost": ltm_storage_cost,
            "ltm_retrieval_cost": ltm_retrieval_cost,
            "total": memory_total,
        },
        "browser": {
            "cpu_cost": browser_cpu_cost,
            "mem_cost": browser_mem_cost,
            "total": browser_total,
            "included": browser_vcpu_price_hr is not None,
        },
        "code_interpreter": {
            "cpu_cost": ci_cpu_cost,
            "mem_cost": ci_mem_cost,
            "total": ci_total,
            "included": ci_vcpu_price_hr is not None,
        },
        "total_monthly": total_monthly,
        "total_annual": total_annual,
        "explanation": explanation,
    }


def calculate_business_value(
    sessions_per_month,
    agent_cost_monthly=0,
    # Dim 1: Time savings
    time_without_ai_min=20,
    time_with_ai_min=10,
    human_cost_per_hour=75,
    revenue_per_hour=300,
    # Dim 2: Churn reduction (set total_customers=0 to skip)
    total_customers=0,
    churn_without_ai_pct=2.0,
    churn_with_ai_pct=1.0,
    revenue_per_customer_year=1000,
    # Dim 3: Sales increase (set annual_sales_revenue=0 to skip)
    annual_sales_revenue=0,
    sales_increase_pct=10.0,
    # Optional: override default business value tiers
    value_tiers=None,
):
    """Calculate business value of an AI agent across up to three dimensions.

    Dim 1 (always): Time savings → productivity or cost savings (3 tiers).
    Dim 2 (if total_customers > 0): Customer churn reduction.
    Dim 3 (if annual_sales_revenue > 0): Sales increase from better CX.

    Args:
        sessions_per_month (int): Agent sessions/month.
        agent_cost_monthly (float): Total agent cost (model + infra) $/month.
        time_without/with_ai_min (int): Minutes per task (default 20/10).
        human_cost_per_hour (float): Fully loaded cost (default $75).
        revenue_per_hour (float): Revenue per productive hour (default $300).
        total_customers (int): Customer base (default 0 = skip Dim 2).
        churn_without/with_ai_pct (float): Monthly churn rates (default 3.0/2.5%).
        revenue_per_customer_year (float): Annual revenue/customer (default $5000).
        annual_sales_revenue (float): Annual sales (default 0 = skip Dim 3).
        sales_increase_pct (float): AI sales uplift (default 2.0%).
        value_tiers (dict | None): Override default tiers. Each tier key maps to
            {effectiveness: float, efficiency: float}.

    Returns:
        dict: assumptions, dim1_cost_savings, dim1_productivity (per-tier dicts),
        dim2/dim3 (conditional dicts), summary (grand_total_annual, net_value,
        roi_pct, payback_days),
        explanation (dict): dim1_time_savings, dim2_churn_reduction (conditional),
            dim3_sales_increase (conditional), summary.
    """
    time_saved_min = time_without_ai_min - time_with_ai_min
    if time_saved_min < 0:
        import warnings
        warnings.warn("Negative time savings: AI takes longer than manual (rare scenario).")

    # --- Dimension 1: Time Savings (all 3 tiers) ---
    dim1_cost_savings = {}
    dim1_productivity = {}

    # Allow caller to override default tiers
    tiers = value_tiers if value_tiers is not None else BUSINESS_VALUE_TIERS

    for tier_name, params in tiers.items():
        eff = params["effectiveness"]
        effi = params["efficiency"]

        effective_sessions = sessions_per_month * eff
        time_saved_hrs = effective_sessions * time_saved_min / 60
        productive_hrs = time_saved_hrs * effi

        cost_savings_monthly = productive_hrs * human_cost_per_hour
        cost_savings_annual = cost_savings_monthly * 12

        revenue_uplift_monthly = productive_hrs * revenue_per_hour
        revenue_uplift_annual = revenue_uplift_monthly * 12

        dim1_cost_savings[tier_name] = {
            "monthly": cost_savings_monthly,
            "annual": cost_savings_annual,
            "productive_hrs_monthly": productive_hrs,
            "effectiveness": eff,
            "efficiency": effi,
        }
        dim1_productivity[tier_name] = {
            "monthly": revenue_uplift_monthly,
            "annual": revenue_uplift_annual,
            "productive_hrs_monthly": productive_hrs,
            "effectiveness": eff,
            "efficiency": effi,
        }

    # --- Dimension 2: Churn Reduction ---
    dim2_annual = 0
    dim2_details = {}
    if total_customers > 0:
        churn_reduction_pp = churn_without_ai_pct - churn_with_ai_pct
        customers_retained = total_customers * (churn_reduction_pp / 100)
        dim2_annual = customers_retained * revenue_per_customer_year
        dim2_details = {
            "churn_reduction_pp": churn_reduction_pp,
            "customers_retained": customers_retained,
            "annual": dim2_annual,
        }

    # --- Dimension 3: Sales Increase ---
    dim3_annual = 0
    dim3_details = {}
    if annual_sales_revenue > 0:
        dim3_annual = annual_sales_revenue * (sales_increase_pct / 100)
        dim3_details = {
            "sales_increase_pct": sales_increase_pct,
            "annual": dim3_annual,
        }

    # --- Summary (Moderate tier for Dim 1a) ---
    moderate_1a = dim1_productivity["Moderate"]["annual"]
    grand_total = moderate_1a + dim2_annual + dim3_annual
    agent_cost_annual = agent_cost_monthly * 12
    net_value = grand_total - agent_cost_annual
    roi_pct = (net_value / agent_cost_annual * 100) if agent_cost_annual > 0 else float("inf")
    payback_days = (agent_cost_annual / grand_total * 365) if grand_total > 0 else float("inf")

    # ── Build step-by-step explanation ──
    mod = tiers["Moderate"]
    mod_eff = mod["effectiveness"]
    mod_effi = mod["efficiency"]
    mod_effective_sessions = sessions_per_month * mod_eff
    mod_time_saved_hrs = mod_effective_sessions * time_saved_min / 60
    mod_productive_hrs = mod_time_saved_hrs * mod_effi

    explanation = {
        "dim1_time_savings": {
            "time_saved": f"{time_without_ai_min} min (without AI) − {time_with_ai_min} min (with AI) = {time_saved_min} min saved/session",
            "moderate_scenario": f"{_fmt(sessions_per_month)} sessions × {mod_eff:.0%} effectiveness = {_fmt(mod_effective_sessions)} effective sessions",
            "productive_hours": f"{_fmt(mod_effective_sessions)} × {time_saved_min} min ÷ 60 × {mod_effi:.0%} efficiency = {_fmt(mod_productive_hrs)} hrs/month",
            "cost_savings": f"{_fmt(mod_productive_hrs)} hrs × ${human_cost_per_hour}/hr = ${dim1_cost_savings['Moderate']['monthly']:,.2f}/mo",
            "productivity_uplift": f"{_fmt(mod_productive_hrs)} hrs × ${revenue_per_hour}/hr = ${dim1_productivity['Moderate']['monthly']:,.2f}/mo",
            "tiers_note": "Conservative (50%/50%), Moderate (65%/60%), Optimistic (80%/70%) — effectiveness/efficiency",
        },
    }

    if total_customers > 0:
        explanation["dim2_churn_reduction"] = {
            "churn_delta": f"{churn_without_ai_pct}% − {churn_with_ai_pct}% = {dim2_details['churn_reduction_pp']:.1f}pp reduction",
            "customers_retained": f"{_fmt(total_customers)} × {dim2_details['churn_reduction_pp']:.1f}% = {_fmt(dim2_details['customers_retained'])} customers",
            "annual_value": f"{_fmt(dim2_details['customers_retained'])} × ${_fmt(revenue_per_customer_year)}/yr = ${dim2_annual:,.2f}/yr",
        }

    if annual_sales_revenue > 0:
        explanation["dim3_sales_increase"] = {
            "uplift": f"${_fmt(annual_sales_revenue)}/yr × {sales_increase_pct}% = ${dim3_annual:,.2f}/yr",
        }

    explanation["summary"] = {
        "grand_total_annual": f"${moderate_1a:,.2f} (Dim1)" + (f" + ${dim2_annual:,.2f} (Dim2)" if dim2_annual > 0 else "") + (f" + ${dim3_annual:,.2f} (Dim3)" if dim3_annual > 0 else "") + f" = ${grand_total:,.2f}/yr",
        "agent_cost_annual": f"${agent_cost_monthly:,.2f}/mo × 12 = ${agent_cost_annual:,.2f}/yr",
        "net_value": f"${grand_total:,.2f} − ${agent_cost_annual:,.2f} = ${net_value:,.2f}/yr",
        "roi": f"{roi_pct:,.0f}%" if roi_pct != float("inf") else "∞ (no agent cost)",
        "payback": f"{payback_days:.0f} days" if payback_days != float("inf") else "N/A",
    }

    return {
        "assumptions": {
            "sessions_per_month": sessions_per_month,
            "time_without_ai_min": time_without_ai_min,
            "time_with_ai_min": time_with_ai_min,
            "time_saved_min": time_saved_min,
            "human_cost_per_hour": human_cost_per_hour,
            "revenue_per_hour": revenue_per_hour,
            "agent_cost_monthly": agent_cost_monthly,
        },
        "dim1_cost_savings": dim1_cost_savings,
        "dim1_productivity": dim1_productivity,
        "dim2": dim2_details,
        "dim3": dim3_details,
        "summary": {
            "dim1_moderate_productivity_annual": moderate_1a,
            "dim1_moderate_cost_savings_annual": dim1_cost_savings["Moderate"]["annual"],
            "dim2_annual": dim2_annual,
            "dim3_annual": dim3_annual,
            "grand_total": grand_total,
            "agent_cost_annual": agent_cost_annual,
            "net_value": net_value,
            "roi_pct": roi_pct,
            "payback_days": payback_days,
        },
        "explanation": explanation,
    }


if __name__ == "__main__":
    main()
