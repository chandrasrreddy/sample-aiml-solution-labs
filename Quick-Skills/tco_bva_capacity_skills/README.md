# Bedrock Agent Pricing & Business Value Skills

A 5-skill toolkit that estimates costs, plans capacity, recommends tiers, and calculates business value for Amazon Bedrock agent workloads. Works with **Amazon Quick Desktop** and **Kiro / Claude Code**. All pricing data comes from the AWS Pricing API — never from model training data.

---

## Skill Family Overview

| Skill | What it does |
|-------|-------------|
| **bedrock-pricing** | Model inference costs — per-token pricing, prompt caching, multi-turn sessions |
| **agentcore-pricing** | AgentCore infrastructure costs — Runtime, Gateway, Memory, BrowserTool, CodeInterpreter, Evaluations |
| **bedrock-capacity** | RPM/TPM capacity planning — checks if your workload fits within quota limits |
| **agent-business-value** | ROI calculation — time savings, cost reduction, churn reduction, sales uplift |
| **bedrock-tier-advisor** | Tier & variant recommendation — Flex, Standard, Priority, Batch, Global vs Regional |

All five skills share a single Python script (`bedrock_pricing.py`) and local JSON cache files.

---

## Prerequisites

1. **Amazon Quick Desktop** or **Kiro / Claude Code** — any AI coding assistant that supports skill files
2. **AWS CLI credentials** — required *only* for the one-time cache refresh step. You need:
   - `aws configure` or AWS SSO configured (`aws sso login`)
   - IAM permissions: `pricing:GetProducts`, `service-quotas:ListServiceQuotas`
3. **Python 3.10+** — for running the cache refresh from the command line

> **Note:** Once the cache files are created, the skills work without AWS credentials. You can refresh the cache once and distribute the JSON files to colleagues who don't have AWS CLI access.

---

## Installation

### Quick Desktop

#### Step 1: Copy the Skill Folders

Copy the five folders from `skills/` into your Quick Desktop skills directory:

```
~/.quickwork/skills/
├── bedrock-pricing/
│   ├── SKILL.md
│   └── scripts/
│       └── bedrock_pricing.py
├── agentcore-pricing/
│   └── SKILL.md
├── bedrock-capacity/
│   └── SKILL.md
├── agent-business-value/
│   └── SKILL.md
└── bedrock-tier-advisor/
    ├── SKILL.md
    └── bedrock-tier-guidance.md
```

Quick Desktop scans `~/.quickwork/skills/` automatically — the skills appear in your next new conversation. No restart required.

```bash
# Quick copy from this repo
cp -R skills/bedrock-pricing ~/.quickwork/skills/
cp -R skills/agentcore-pricing ~/.quickwork/skills/
cp -R skills/bedrock-capacity ~/.quickwork/skills/
cp -R skills/agent-business-value ~/.quickwork/skills/
cp -R skills/bedrock-tier-advisor ~/.quickwork/skills/
```

#### Step 2: Create the Pricing Cache

The skills read pricing data from local JSON cache files. Generate them before first use:

```bash
python3 ~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh
```

This creates 5 files in your home directory (`~/`):

| File | Contents |
|------|----------|
| `bedrock_pricing.json` | 1P Amazon models + newer 3P models |
| `bedrock_pricing_3p.json` | 3P Marketplace models (Anthropic, Meta, Mistral, etc.) |
| `bedrock_pricing_service.json` | Very new models (latest additions) |
| `bedrock_pricing_agentcore.json` | AgentCore component pricing |
| `bedrock_quotas.json` | RPM/TPM default quotas per model/region |

**Optional flags:**

```bash
# Pricing only, skip quotas (~2 min)
python3 ~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh --skip-quotas

# Specific regions for quotas
python3 ~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh --quota-regions "us-west-2,us-east-1"

# All Bedrock regions (~15 min, comprehensive)
python3 ~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh --all-regions
```

#### Step 3: Verify

Open a new Quick Desktop conversation and type:

> *"Get Bedrock pricing for Claude Sonnet 4.6 in us-east-1"*

If the skill activates and returns pricing from the cache, you're set.

### Kiro / Claude Code

The skills work from the workspace root. Open this repo in Kiro or Claude Code — the agent will find the skill files under `skills/` and the Python script via the dual-path loader:

```python
_p = os.path.join(os.getcwd(), "skills/bedrock-pricing/scripts/bedrock_pricing.py")
if not os.path.exists(_p):
    _p = os.path.expanduser("~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py")
```

You still need the cache files in `~/`. Run the same `--refresh` command above using the workspace path:

```bash
python3 skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh
```

---

## Usage Examples

### Compare Model Costs

> *"Compare Claude Sonnet 4.6 vs Nova Pro in us-east-1 for 500K sessions/month, 3 questions per session."*

Returns a side-by-side table: monthly cost, per-session cost, caching savings %, and annual totals.

### Full Agent Cost + Capacity Check

> *"Estimate the full cost for an agent on AgentCore using Claude Sonnet 4.6 in us-east-1. 1M sessions/month, 5 questions per session, 5 tool calls per question. Include Runtime, Gateway, and Memory. Then check if it fits within default RPM/TPM quotas."*

Returns combined cost breakdown (model + AgentCore) and capacity fit analysis with optimization recommendations if it doesn't fit.

### Business Value & ROI

> *"Calculate business value. 500K sessions/month, agent cost $80K/month. Manual time 15 min, AI time 4 min, human cost $65/hr."*

Returns tiered savings (conservative/moderate/optimistic), net ROI %, payback period, and FTE equivalents.

### Tier Recommendation

> *"I'm building a production customer-facing agent on Claude Sonnet 4.6 in us-east-1. Which tier and variant should I use?"*

Returns a recommendation (e.g., Standard Global with prompt caching) with alternatives and trade-offs.

### Multi-Agent Architecture

> *"Price a multi-agent system: parent router on Nova Lite, 3 sub-agents on Claude Sonnet 4.6 with 45%/35%/20% traffic split. 3M sessions/month, 5 Q/session, us-west-2. Include AgentCore."*

Returns per-agent cost breakdown, shared AgentCore infrastructure cost, and combined total.

### All Three Business Value Dimensions

> *"Calculate business value for Marriott. 2M sessions/month, agent cost $320K/month. Time without AI 12 min, with AI 3 min, human cost $35/hr, revenue per hour $59. 210M loyalty members, churn 1.5% without AI, 1.2% with AI, $120 revenue per member per year. Annual sales revenue $23.7B, expect 2% increase from better CX."*

Returns Dim 1 (time savings), Dim 2 (churn reduction), Dim 3 (sales uplift), grand total, and ROI.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│          Quick Desktop / Kiro / Claude Code               │
│                                                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐            │
│  │  bedrock-   │ │ agentcore- │ │  bedrock-  │            │
│  │  pricing    │ │  pricing   │ │  capacity  │            │
│  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘            │
│        │              │              │                    │
│  ┌─────┴──┐     ┌─────┴──────┐                           │
│  │ agent-  │     │  bedrock-  │                           │
│  │ business│     │  tier-     │                           │
│  │ -value  │     │  advisor   │                           │
│  └─────┬──┘     └─────┬──────┘                           │
│        │              │                                   │
│  ┌─────┴──────────────┴──────────────────────────────┐   │
│  │           bedrock_pricing.py (shared)              │   │
│  │                                                    │   │
│  │  query_model_pricing()          query_quotas()     │   │
│  │  query_agentcore_pricing()      check_capacity_fit()│  │
│  │  extract_bedrock_model_prices()                    │   │
│  │  calculate_agent_cost_with_incremental_caching()   │   │
│  │  calculate_agentcore_cost()                        │   │
│  │  calculate_business_value()                        │   │
│  │  calculate_evaluation_cost()                       │   │
│  └───────────────────────┬───────────────────────────┘   │
│                          │                                │
│  ┌───────────────────────┴───────────────────────────┐   │
│  │            Local JSON Cache (~/*)                  │   │
│  │  bedrock_pricing.json      bedrock_quotas.json     │   │
│  │  bedrock_pricing_3p.json                           │   │
│  │  bedrock_pricing_service.json                      │   │
│  │  bedrock_pricing_agentcore.json                    │   │
│  └───────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
                           ▲
                           │ --refresh (one-time setup)
                 ┌─────────┴──────────┐
                 │  AWS Pricing API   │
                 │  AWS Service Quotas│
                 └────────────────────┘
```

---

## Key Defaults

These defaults are used when you don't specify values. Override any of them in your prompt.

| Parameter | Default | Notes |
|-----------|---------|-------|
| Service tier | Standard (On-Demand) | Also supports Priority, Flex, Batch |
| Inference variant | Global (cross-region) | Also supports Regional |
| Prompt caching | Enabled | Auto-enabled for supported models |
| Questions per session | 5 | Multi-turn conversation |
| Input tokens per question | 100 | User's question text |
| Output tokens per question | 100 | Model's response |
| System prompt tokens | 1,000 | Sent every LLM call |
| Tool description tokens | 4,000 | All tool schemas combined |
| RAG chunks per question | 10 | Retrieved context |
| Tokens per RAG chunk | 300 | Chunk size |
| Tools invoked per question | 10 | Tool-use turns |
| Tool call tokens (output) | 100 | JSON per tool call |
| Tool result tokens (input) | 500 | Response per tool result |
| Output burndown rate | 5× for Claude 3.7+ | Each output token = 5 TPM quota |
| Peak-to-average ratio | 3× | For capacity planning |
| Active hours/day | 12 | Business hours + buffer |
| Active days/month | 22 | Business days |

---

## Refreshing the Cache

Re-run periodically to pick up new models and price changes:

```bash
# Full refresh — pricing + quotas (~5 min)
python3 ~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh

# Quick refresh — pricing only (~2 min)
python3 ~/.quickwork/skills/bedrock-pricing/scripts/bedrock_pricing.py --refresh --skip-quotas
```

> **⚠️ The skills automatically warn when cache files are older than 7 days.** Re-run `--refresh` when you see the warning.

Share the JSON files with teammates who don't have AWS CLI access — just copy the 5 files to their `~/` directory.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Cache file not found" | Run `--refresh` to generate cache files |
| Skill doesn't activate | Verify folder is at `~/.quickwork/skills/bedrock-pricing/` (not nested deeper) |
| "No results for model X" | Try a broader search (e.g., "Sonnet" instead of "Sonnet 4.6") or refresh cache |
| AWS credentials error on `--refresh` | Run `aws configure` or `aws sso login` first |
| Quotas file empty | Re-run with `--quota-regions "us-west-2,us-east-1"` |
| Stale pricing data | Re-run `--refresh` |

---

## Limitations

- **Pricing only, not billing** — estimates use published list prices. Actual bills may differ due to EDPs or negotiated rates.
- **No Reserved pricing** — covers On-Demand (Standard/Priority/Flex) and Batch tiers only.
- **Quota defaults** — capacity checks use default service quotas. Your account may have custom limits.
- **Business value is illustrative** — ROI calculations use research-backed assumptions (BCG, Harvard, Gartner) but are estimates. Validate with your specific data.
- **Costs depend on your assumptions** — always ask to *"list assumptions"* and *"show the step-by-step explanation"* before sharing results.

---

## Testing (for contributors)

The `tests/` folder contains a QA framework for validating the skills using **Kiro** or **Claude Code**. It is not used by Quick Desktop.

| File | Purpose |
|------|---------|
| `tests/pricing_spec_v1.2.md` | Single source of truth for all formulas — used to independently verify skill output |
| `tests/use_cases.md` | 25 test case prompts spanning industries, complexity levels, and edge cases |
| `tests/execute_test_cases.md` | Instructions for running all 25 test cases with automated verification |

The `responses/` folder contains the results of the most recent QA run: 25 response files + 25 verification files. All 1,222 verified fields pass.

To re-run the tests, open this repo in Kiro and follow the instructions in `tests/execute_test_cases.md`.
