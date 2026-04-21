---
name: bedrock-cost-test-generator
display_name: Bedrock Cost Test Cases
description: "Library of 25 use case prompts and 25 negative test prompts for testing the Bedrock pricing, AgentCore, capacity, business value, and tier advisor skills. Use cases span industries and complexity levels. Negative tests target boundary conditions, invalid inputs, and error handling."
icon: "🧪"
trigger: generate bedrock cost test cases
depends-on: [bedrock-pricing, agentcore-pricing, bedrock-capacity, agent-business-value, bedrock-tier-advisor]
tools: []
---

## Overview

A prompt library for testing the 5-skill Bedrock pricing family. Contains two sets:

1. **25 Use Case Prompts** — ready-to-paste prompts that exercise the full skill chain across diverse industries and workload shapes
2. **25 Negative Test Prompts** — prompts designed to trigger boundary conditions, invalid inputs, missing data, and error handling paths

Copy any prompt into Quick Desktop or Kiro and observe the agent's behavior.

---

## Part 1: Use Case Prompts (25)

### Full-Chain Use Cases (pricing + AgentCore + capacity + business value)

**UC-01: Enterprise IT Helpdesk Agent**
> "Estimate the full cost for an IT helpdesk agent using Claude Sonnet 4.6 in us-east-1. 500K sessions/month, 3 questions per session, 5 tool calls per question (ticket lookup, KB search, status update, escalation check, resolution log). Include AgentCore Runtime, Gateway, and Memory. Then check capacity and calculate business value — currently each ticket takes 15 min manually, with AI it takes 4 min. Human cost is $65/hr."

**UC-02: Airline Booking & Disruption Agent (Multi-Agent)**
> "I'm building a multi-agent system for a major airline. Parent router on Nova Lite, three sub-agents on Claude Sonnet 4.6: (1) Booking agent — 45% traffic, 4 tools, (2) Flight status & rebooking agent — 35% traffic, 6 tools, (3) Loyalty & complaints agent — 20% traffic, 3 tools. 3M sessions/month, 5 questions per session, us-west-2. Include AgentCore. Calculate business value — manual handle time is 18 min, with AI 5 min, human cost $40/hr. The airline has 80M loyalty members, 2% monthly churn without AI, 1.5% with AI, $200 revenue per member per year."

**UC-03: Legal Document Review Agent**
> "Price an agent that reviews legal contracts. Claude Opus 4.6 in eu-west-1. 50K sessions/month, 1 question per session (upload doc, get analysis). No tools — pure document analysis. Large RAG: 20 chunks of 500 tokens each. System prompt is 3,000 tokens. Output is long — 1,000 tokens per response. Include capacity check and business value — lawyers spend 45 min per contract review, AI reduces to 10 min, cost is $250/hr."

**UC-04: E-Commerce Product Recommendation Chatbot**
> "Cost estimate for a product recommendation chatbot for an online retailer. Nova Pro in us-east-1. 2M sessions/month, 4 questions per session. 3 tools (product search, inventory check, cart add). RAG with 8 chunks of product catalog data. Calculate business value — the retailer has $5B annual revenue and expects 3% sales increase from better CX. Also check if this fits in Standard tier."

**UC-05: Healthcare Patient Triage Agent**
> "Estimate costs for a patient triage agent at a hospital network. Claude Sonnet 4.6 in us-east-1. 200K sessions/month, 6 questions per session. 4 tools (symptom checker, appointment scheduler, medical record lookup, insurance verifier). System prompt is 2,500 tokens (medical guidelines). RAG: 10 chunks. Business value: triage calls take 20 min without AI, 7 min with AI, nurse cost $55/hr. 500K patients, 3% monthly churn without AI, 2.2% with AI, $2,000 revenue per patient per year."

**UC-06: Financial Trading Research Agent**
> "Price a research agent for a hedge fund. Claude Opus 4.6 in us-east-1. 100K sessions/month, 8 questions per session. 10 tools (market data API, SEC filings search, earnings transcript search, sentiment analyzer, portfolio analyzer, risk calculator, news aggregator, peer comparison, valuation model, trade simulator). Heavy RAG: 15 chunks of 400 tokens. Output 500 tokens. Business value: analysts spend 30 min per research query, AI reduces to 8 min, analyst cost $150/hr, revenue per hour $500."

**UC-07: Government Benefits Eligibility Agent**
> "Cost for a citizen-facing benefits eligibility agent. Nova Pro in us-west-2. 1M sessions/month, 3 questions per session. 4 tools (eligibility rules engine, document validator, case status lookup, appointment scheduler). System prompt 2,000 tokens with policy rules. Business value: case workers spend 25 min per inquiry, AI reduces to 6 min, cost $45/hr."

**UC-08: Manufacturing Quality Control Agent**
> "Estimate costs for a quality control agent in a factory. Claude Sonnet 4.6 in eu-central-1. 300K sessions/month, 2 questions per session. 6 tools (defect image analyzer, production line status, parts inventory, maintenance scheduler, quality report generator, supplier lookup). Include BrowserTool for accessing the factory dashboard. Business value: QC inspections take 10 min manually, 3 min with AI, inspector cost $35/hr."

**UC-09: Real Estate Property Valuation Agent**
> "Price an agent that helps real estate agents with property valuations. Claude Sonnet 4.6 in us-east-1. 150K sessions/month, 5 questions per session. 7 tools (MLS search, comparable sales, tax records, neighborhood stats, mortgage calculator, market trends, property history). RAG: 12 chunks of property data. Business value: valuations take 40 min manually, 12 min with AI, agent cost $75/hr."

**UC-10: University Student Advisor Agent**
> "Cost estimate for a student advising chatbot at a large university. Nova Lite in us-east-1. 400K sessions/month, 4 questions per session. 2 tools (course catalog search, degree audit). Light RAG: 3 chunks. Small system prompt: 500 tokens. Business value: advising sessions take 20 min, AI reduces to 5 min, advisor cost $40/hr."

### Pricing-Only Use Cases (no AgentCore, no business value)

**UC-11: Simple Model Price Comparison**
> "Compare the pricing for Claude Sonnet 4.6, Nova Pro, and Llama 4 Maverick in us-east-1. Show all available tiers and variants for each. Which is cheapest for a standard on-demand workload?"

**UC-12: Batch vs On-Demand Comparison**
> "I have a content moderation pipeline that processes 10M documents per month. Each document is 1 question, no tools, 500 input tokens, 50 output tokens. Compare the cost of running this on Claude Haiku 4.5 in Batch mode vs Standard mode in us-west-2."

**UC-13: Caching Impact Analysis**
> "Show me the cost difference with and without prompt caching for Claude Sonnet 4.6 in us-east-1. 1M sessions, 5 questions per session, 10 tools invoked, system prompt 2,000 tokens, tool descriptions 4,000 tokens, 10 RAG chunks of 300 tokens each."

**UC-14: Multi-Region Pricing Comparison**
> "Compare Claude Sonnet 4.6 pricing across us-east-1, eu-west-1, and ap-northeast-1. Show Standard Global vs Standard Regional for each."

### Capacity-Focused Use Cases

**UC-15: High-Volume Capacity Check**
> "I have 20M questions per month on Claude Sonnet 4.6 in us-east-1. 5 tools per question, peak-to-average ratio of 4x, 16 active hours per day, 30 days per month. Does this fit in Standard tier? What about Priority? Use output burndown rate of 5."

**UC-16: Low-Volume Capacity Check**
> "Will 10K sessions per month with 2 questions per session fit in Flex tier for Nova Pro in us-west-2? 3 tools per question."

### Business Value Only

**UC-17: Cost Savings Framing**
> "Calculate business value for an agent that costs $50,000/month. It handles 500K sessions/month. Manual time is 12 min, AI time is 2 min. Human cost is $85/hr. Show me cost savings, not productivity increase."

**UC-18: All Three Dimensions**
> "Calculate business value for Marriott. 2M sessions/month, agent cost $320K/month. Time without AI 12 min, with AI 3 min, human cost $35/hr, revenue per hour $59. Also: 210M loyalty members, churn 1.5% without AI, 1.2% with AI, $120 revenue per member per year. Annual sales revenue $23.7B, expect 2% increase from better CX."

### Tier Advisor Use Cases

**UC-19: Tier Recommendation**
> "I'm building a customer service agent on Claude Sonnet 4.6 in us-east-1. It's production, customer-facing. Which tier and variant should I use?"

**UC-20: Dev/Test Tier**
> "I'm prototyping an agent and want the cheapest option. What tier should I use for Qwen3 235B in us-east-1?"

### Intentionally Vague Use Cases (test agent's ability to ask questions)

**UC-21: No Region Specified**
> "How much would it cost to run a Claude Sonnet agent with 1M sessions per month?"

**UC-22: No Model Specified**
> "I need to build a customer support agent in us-east-1. 500K sessions per month, 5 questions per session, 3 tools. How much will it cost?"

**UC-23: Minimal Information**
> "What's the cost of running an AI agent on Bedrock?"

**UC-24: Ambiguous Intent**
> "Tell me about Bedrock pricing."

**UC-25: Volume Without Context**
> "I have 10 million questions per month. How much will this cost on Bedrock?"

---

## Part 2: Negative Test Prompts (25)

### Invalid Inputs

**NEG-01: Negative Sessions**
> "Calculate the cost for an agent with -1000 sessions per month using Claude Sonnet 4.6 in us-east-1."

**NEG-02: Zero Sessions**
> "Estimate costs for an agent with 0 sessions per month on Claude Sonnet 4.6 in us-east-1, 5 questions per session, 3 tools."

**NEG-03: Zero Questions Per Session**
> "Price an agent with 100K sessions per month but 0 questions per session on Claude Sonnet 4.6 in us-east-1."

**NEG-04: Negative Tools**
> "Calculate cost for an agent with -5 tools invoked per question. Claude Sonnet 4.6, us-east-1, 100K sessions, 3 questions per session."

**NEG-05: AI Takes Longer Than Manual**
> "Calculate business value for an agent that costs $10,000/month. 100K sessions. Manual time is 5 minutes, AI time is 20 minutes. Human cost $50/hr."

**NEG-06: Zero Agent Cost with Business Value**
> "Calculate business value for an agent with $0 monthly cost. 1M sessions, manual time 15 min, AI time 5 min, human cost $75/hr. What's the ROI?"

**NEG-07: Extremely Large Volume**
> "Estimate costs for 1 billion sessions per month on Claude Sonnet 4.6 in us-east-1. 10 questions per session, 20 tools per question."

### Boundary Conditions

**NEG-08: Single Session, Single Question, No Tools**
> "Calculate the cost for exactly 1 session per month, 1 question per session, 0 tools, on Claude Sonnet 4.6 in us-east-1. System prompt 500 tokens, no RAG."

**NEG-09: Fractional Questions Per Session**
> "Price an agent with 100K sessions per month and 1.7 questions per session on Claude Sonnet 4.6 in us-east-1 with 3 tools."

**NEG-10: Zero RAG, Zero System Prompt, Zero Tool Descriptions**
> "Calculate cost for an agent with 0 system prompt tokens, 0 tool description tokens, 0 RAG chunks, but 5 tools invoked. Claude Sonnet 4.6, us-east-1, 100K sessions, 3 questions per session."

**NEG-11: max_tokens Smaller Than Output**
> "Check capacity for Claude Sonnet 4.6 in us-east-1. 1M questions/month, 5 tools, output_tokens=500, but max_tokens_setting=100. Output burndown rate 5."

**NEG-12: Zero Output Tokens**
> "Calculate cost for an agent that produces 0 output tokens per question. Claude Sonnet 4.6, us-east-1, 100K sessions, 3 questions, 5 tools."

**NEG-13: One Tool Invoked**
> "Price an agent with exactly 1 tool invocation per question. Claude Sonnet 4.6, us-east-1, 500K sessions, 4 questions per session."

**NEG-14: 100 Tools Invoked Per Question**
> "Estimate cost for an agent that invokes 100 tools per question. Claude Sonnet 4.6, us-east-1, 50K sessions, 2 questions per session."

### Model/Region Errors

**NEG-15: Non-Existent Model**
> "Get pricing for Claude Sonnet 9.0 in us-east-1."

**NEG-16: Misspelled Model**
> "Get pricing for Claud Sonet 4.6 in us-east-1."

**NEG-17: Non-Existent Region**
> "Get pricing for Claude Sonnet 4.6 in us-north-3."

**NEG-18: Model Not Available in Region**
> "Get pricing for Llama 4 Maverick in ap-southeast-6."

### Missing Data / Cache Issues

**NEG-19: Request Without Cache Files**
> "Get pricing for Claude Sonnet 4.6 in us-east-1. Assume the cache files don't exist — what should happen?"

**NEG-20: Model Without Caching Support**
> "Calculate the cost with prompt caching enabled for Llama 4 Maverick in us-east-1. 500K sessions, 5 questions, 3 tools. What happens to the cache split math when cache_read and cache_write prices are null?"

### Conflicting Parameters

**NEG-21: Batch Tier for Real-Time Agent**
> "I need a real-time customer-facing agent with sub-second latency. Use Batch tier for Claude Sonnet 4.6 in us-east-1. 1M sessions/month."

**NEG-22: Flex Tier for Mission-Critical**
> "I'm building a mission-critical trading agent that cannot tolerate any downtime. Recommend Flex tier for cost savings. Claude Sonnet 4.6, us-east-1."

**NEG-23: Business Value Without Sessions**
> "Calculate business value. Manual time 20 min, AI time 5 min, human cost $75/hr. Agent cost $10,000/month. But I forgot to mention sessions per month."

### Stress Tests

**NEG-24: All Parameters at Maximum**
> "Calculate cost for an agent with 100M sessions/month, 20 questions per session, 50 tools invoked, system prompt 10,000 tokens, tool descriptions 20,000 tokens, 30 RAG chunks of 1,000 tokens each, output 2,000 tokens. Claude Opus 4.6 in us-east-1. Include AgentCore, capacity check, and business value — manual time 60 min, AI time 5 min, human cost $200/hr."

**NEG-25: All Parameters at Minimum**
> "Calculate cost for an agent with 1 session/month, 1 question per session, 0 tools, 0 system prompt tokens, 0 tool descriptions, 0 RAG chunks, 1 input token, 1 output token. Nova Micro in us-east-1. Include business value — manual time 1 min, AI time 0 min, human cost $1/hr."

---

## How to Use

### Running Use Cases
1. Copy any `UC-XX` prompt into Quick Desktop or Kiro
2. Observe: Does the agent activate the right skills? Ask clarifying questions when needed? Produce reasonable numbers?
3. For vague prompts (UC-21 through UC-25): verify the agent asks for missing information before calculating

### Running Negative Tests
1. Copy any `NEG-XX` prompt into Quick Desktop or Kiro
2. Observe: Does the agent handle the error gracefully? Does it crash? Does it produce nonsensical numbers silently?
3. Expected behaviors:
   - Invalid inputs → agent should warn or reject, not crash
   - Boundary conditions → agent should produce valid (if extreme) numbers
   - Missing models/regions → agent should suggest alternatives
   - Conflicting parameters → agent should flag the conflict and advise

### Tracking Results
For each test, record:
- **Prompt ID** (e.g., UC-01, NEG-15)
- **Skills activated** (which skills did the agent load?)
- **Behavior** (asked questions? used defaults? crashed? warned?)
- **Output quality** (reasonable numbers? correct tier? proper error message?)
- **Pass/Fail** and notes
