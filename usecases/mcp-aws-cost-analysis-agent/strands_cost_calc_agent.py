import time
from datetime import timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from mcp.server.fastmcp import FastMCP
from strands import Agent, tool
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

import os

app = BedrockAgentCoreApp()

# Set up environment for tools
os.environ["BYPASS_TOOL_CONSENT"] = "true"
os.environ["PYTHON_REPL_INTERACTIVE"] = "false"

# Create FastMCP application
mcp = FastMCP(host="0.0.0.0", stateless_http=True)

# Import the tools (now with mocked strands)
from pricing_util import get_bedrock_pricing, get_agentcore_pricing, get_aws_pricing, get_attribute_values
from use_bedrock_calculator import use_bedrock_calculator, bedrock_what_if_analysis
from use_agentcore_calculator import use_agentcore_calculator, agentcore_what_if_analysis
from bva_calculator import bva_calculator, bva_what_if_analysis
from use_emr_calculator import use_emr_calculator, emr_what_if_analysis

# Pydantic models for response validation

class BedrockCosts(BaseModel):
    """
    Bedrock cost analysis response structure.
    Uses flexible Dict types to allow calculator evolution without schema updates.
    """
    questions_per_month_all_models: int = Field(
        description="Total questions processed monthly across all models"
    )
    assumptions: Dict[str, Any] = Field(
        description="Global assumptions (system_prompt_tokens, history_qa_pairs)"
    )
    warnings: Optional[List[str]] = Field(
        default=None,
        description="Warning messages if model percentages don't sum to 100%"
    )
    total_cost_for_all_models: float = Field(
        description="Total monthly cost across all models"
    )
    
    class Config:
        extra = "allow"  # Allows dynamic model keys (model1, model2, etc.)

class AgentCoreCosts(BaseModel):
    """
    AgentCore cost analysis response structure.
    Uses flexible Dict types to allow calculator evolution without schema updates.
    """
    runtime: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Runtime component costs (if used)"
    )
    browser: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Browser tool component costs (if used)"
    )
    code_interpreter: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Code interpreter component costs (if used)"
    )
    gateway: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Gateway component costs (if used)"
    )
    memory: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Memory component costs (if used)"
    )
    total_all_components: float = Field(
        description="Total monthly cost for all AgentCore components used"
    )
    
    class Config:
        extra = "allow"  # Allow additional components in the future

class BusinessValue(BaseModel):
    """
    Business Value Analysis response structure.
    Uses flexible Dict types to allow calculator evolution without schema updates.
    """
    assumptions: Dict[str, Any] = Field(
        description="Global assumptions and parameters used in the analysis"
    )
    business_value_summary: Dict[str, Any] = Field(
        description="Comprehensive ROI analysis with benefits, costs, net results, and ongoing metrics"
    )
    cost_savings: Optional[Dict[str, Any]] = Field(
        None,
        description="Cost savings analysis (if calculated)"
    )
    revenue_growth: Optional[Dict[str, Any]] = Field(
        None,
        description="Revenue growth analysis (if calculated)"
    )
    customer_churn_reduction: Optional[Dict[str, Any]] = Field(
        None,
        description="Customer churn reduction analysis (if calculated)"
    )
    implementation_costs: Optional[Dict[str, Any]] = Field(
        None,
        description="Implementation costs (if provided)"
    )
    
    class Config:
        extra = "allow"  # Allow additional fields for future calculator enhancements    

# Create an Agent that can use both Bedrock and AgentCore tool.

agent_system_prompt = f"""
You are an expert AWS cost analyst specializing in helping sales teams with Amazon Bedrock, Amazon Bedrock AgentCore, and Amazon ElasticMapReduce (EMR) pricing calculations. Your mission is to deliver precise, data-driven cost analysis that enables informed business decisions.

PRICING DATA REQUIREMENTS:
- Use ONLY pricing retrieved from get_bedrock_pricing for Bedrock and get_agentcore_pricing tools for AgentCore; Use get_aws_pricing with service code ElasticMapReduce for EMR pricing. Never rely on pre-trained knowledge or assumptions.
- Default to us-west-2 region unless explicitly specified otherwise.
- If pricing data is unavailable for any component, clearly state this limitation and say "I am sorry I can't help you."

QUERY ANALYSIS:
- Identify whether the user is asking for Bedrock Model costs, AgentCore costs, EMR costs, or a combination
- Determine if the user is requesting business value analysis (ROI, cost savings, revenue impact)
- Follow the appropriate workflow based on the identified query type

CALCULATOR TOOL USAGE:
- For Bedrock costs: Use use_bedrock_calculator with proper parameter structure
  * Model percentages should sum to 100% or less (warnings will be generated if not)
  * Vector database is optional per model - configure within each model that uses it
  * Tools are optional per model - only include if the model uses agentic workflows
- For AgentCore costs: Use use_agentcore_calculator with proper parameter structure
  * All components (runtime, browser, code_interpreter, gateway, memory) are optional and independent
  * Only include components that are actually used in the architecture
  * Percentages can overlap (e.g., 100% use runtime + 80% use tools is valid)
- Always review calculator output for 'warnings' field and communicate warnings to users

RESPONSE STRUCTURE - CRITICAL:
- Return the COMPLETE, UNMODIFIED output from all calculator tools
- NEVER filter, omit, or exclude ANY fields from calculator outputs
- Preserve the ENTIRE nested structure
- When returning Bedrock costs, model keys (e.g., 'model1', 'model2') should be descriptive

RESTRICTIONS: 
- Don't create any files as you can't store them locally since the local storage is ephemeral.
- If the user asks any questions that are not related to Amazon Bedrock, AgentCore, and EMR, Just say - "I am sorry I can't answer the question. I am an agent specialized to respond to questions related to Bedrock, AgentCore, and EMR."

REMEMBER: 
Your analysis directly influences budget planning, architecture decisions, and business strategy. Precision and transparency are non-negotiable.

INTERACTIONS:
When you need more information to provide accurate cost analysis, follow these guidelines:

CRITICAL DEFAULT VALUE HANDLING:
- ALWAYS read tool docstrings to get current default values and present them to users
- NEVER use hardcoded defaults from examples below. Examples show interaction PATTERN only, not actual values

1. MISSING CRITICAL INFORMATION (Direct Cost Calculation Queries): When the user asks for cost calculations but doesn't provide essential parameters,
   - Read the tool's docstring to understand parameters and their current defaults
   - Ask targeted questions in a single response
   - For each question, provide: the parameter name, why it matters, and the default value from the tool
   - Always end with: "If you're ok with these defaults, just type 'Go'"
   
   Example:
   User: "Calculate Bedrock costs"
   
   Agent: "I need a few details to calculate accurate costs:
   
   1. Which model? Choice impacts latency, costs, and accuracy. (default: <reads from tool>)
   2. Input tokens per question? Impacts costs and latency. (default: <reads from tool>)
   3. Output tokens per question? Impacts costs. (default: <reads from tool>)
   4. Questions per month? Determines monthly volume. (default: <reads from tool>)
   
   If you're ok with these defaults, just type 'Go'"

2. USE CASE EXPLORATION (User Describes a Scenario): When the user shares a business context, application, or use case,
   - Ask probing questions that uncover cost-driving factors specific to their scenario
   - Focus on: volume, frequency, data size, concurrency, user behavior patterns
   - Read tool docstrings for current defaults and provide them based on use case context
   - Always end with: "If you're ok with these defaults, just type 'Go'"
   
   Example:
   User: "I have 100K customers with 80% failure rate of at least 1 backup job. I want to use Agents to process backup failures."
   
   Agent: "Let me understand the cost drivers:
   
   1. Backup failures per day? Determines agent invocations. (calculated: 80,000/day from your 80% rate)
   2. Log size per failure? Affects input tokens. (default: <reads from tool>)
   3. Agent response size? (diagnose only vs. diagnose + fixes) Impacts output tokens. (default: <reads from tool>)
   4. Need conversation history for follow-ups? Adds memory costs. (default: <reads from tool>)
   
   If you're ok with these defaults, just type 'Ok. Go.'"

3. BUSINESS VALUE ANALYSIS (ROI/Savings Queries):  When the user asks about ROI, cost savings, or business value,
   - First gather cost calculation parameters (follow rules 1 or 2 above)
   - Then ask business impact questions
   - Focus on: time savings, labor costs, revenue impact, and churn reduction
   - Always end with: "If you're ok with these defaults, just type 'Go'"
   
   Example:
   User: "What's the ROI of this AI agent?"
   
   Agent: "To calculate ROI, I need costs and benefits:
   
   [First ask cost questions from scenario 1 or 2]
   
   Business Impact:
   1. Time taken to triage without AI? (default: <reads from tool>)
   2. Time taken to triage with AI? (default: <reads from tool>)
   3. Support engineer hourly cost? (default: <reads from tool>)
   
   If you're ok with these defaults, just type 'Ok. Go.'"

GENERAL RULES:
- Batch related questions together in a single response
- Prioritize questions with biggest impact on cost accuracy
- Use the user's context when suggesting defaults
- Make it easy to proceed quickly with default values: "Ok. Go."
"""

agent_system_prompt += f"""

CRITICAL: You MUST respond with ONLY valid JSON. No explanatory text before or after the JSON.

Your response must be a valid JSON object that can include one or more of these schemas as top-level keys:

1. "bedrock_costs" - Use this schema:
{BedrockCosts.model_json_schema()}

2. "agentcore_costs" - Use this schema:
{AgentCoreCosts.model_json_schema()}

3. "business_value" - Use this schema:
{BusinessValue.model_json_schema()}

Example structure:
{{
  "bedrock_costs": {{ ... }},
  "agentcore_costs": {{ ... }},
  "business_value": {{ ... }}
}}

RULES:
- Output ONLY the JSON object, nothing else
- No markdown code blocks (no ```json), no explanations, no additional text
- Include only the relevant schemas based on the query
- Ensure all required fields are present for each schema you include
- Use proper JSON syntax with double quotes
- Numbers must be numeric types, not strings
- Start your response with {{ and end with }}
"""

model_id = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
agent = Agent(
    system_prompt=agent_system_prompt,
    model=BedrockModel(model_id=model_id, temperature = 0.1),
    tools=[get_bedrock_pricing, get_agentcore_pricing, use_bedrock_calculator, bedrock_what_if_analysis, use_agentcore_calculator, agentcore_what_if_analysis, bva_calculator, bva_what_if_analysis, use_emr_calculator, emr_what_if_analysis, get_aws_pricing, get_attribute_values]
)

# A helper function to retry agent calls with exponential backoff
def invoke_strands_agent(agent, prompt, max_retries=3, base_delay=1):
    """Retry agent calls with exponential backoff"""
    
    for attempt in range(max_retries + 1):
        try:
            return agent(prompt)
        except Exception as e:
            error_str = str(e).lower()
            if ("serviceunavailableexception" in error_str or "modelthrottledexception" in error_str or "throttling" in error_str) and attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                print(f"Retry {attempt + 1}/{max_retries} after {delay}s due to: {type(e).__name__}")
                time.sleep(delay)
                continue
            else:
                raise e

@mcp.tool()
def invoke_cost_analysis_agent_read_only(query: str):
    """
    Invoke specialized agent for AWS cost calculation and analysis
    Args:
        - query (str): A user query describing use case that the user want to know about its estimated AWS cost and financial impact.
    """
    response = invoke_strands_agent(agent, query)
    return response.message['content'][0]['text']


if __name__ == "__main__":
    mcp.run(transport="streamable-http")    