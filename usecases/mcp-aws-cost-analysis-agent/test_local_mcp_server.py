#!/usr/bin/env python3
"""
Local MCP Server Test Client for Strands Cost Calculator Agent

This script tests a locally running MCP server (assumes server is already running).
It connects to the server and runs test queries against the agent.

Prerequisites:
    1. Start the MCP server first:
       python strands_cost_calc_agent.py
    
    2. Then run this test script:
       python test_local_mcp_server.py

Usage:
    python test_local_mcp_server.py
    python test_local_mcp_server.py --port 8080
    python test_local_mcp_server.py --query "Calculate Bedrock costs"
    python test_local_mcp_server.py --verbose
"""

import asyncio
import json
import sys
import argparse
from datetime import timedelta

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client, streamable_http_client
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient


async def test_mcp_server(mcp_url: str, verbose: bool = False):
    """
    Test the local MCP server with various queries.
    
    Args:
        mcp_url: URL of the local MCP server
        verbose: Show detailed output
    """
    headers = {"Content-Type": "application/json"}
    
    print(f"\n{'='*80}")
    print(f"🔗 Connecting to Local MCP Server")
    print(f"{'='*80}")
    print(f"URL: {mcp_url}")
    print(f"\n💡 Make sure the server is running:")
    print(f"   python strands_cost_calc_agent.py")
    
    try:
        print(f"\n🔄 Establishing connection...")
        async with streamablehttp_client(
            mcp_url,
            headers,
            timeout=timedelta(seconds=30)
        ) as (read_stream, write_stream, _):
            print("✓ HTTP connection established")
            
            async with ClientSession(read_stream, write_stream) as session:
                print("✓ MCP session created")
                
                print("🔄 Initializing MCP session...")
                await session.initialize()
                print("✓ MCP session initialized")
                
                # List available tools
                print("\n🔄 Discovering available tools...")
                tool_result = await session.list_tools()
                
                print("\n" + "="*80)
                print("📋 Available MCP Tools")
                print("="*80)
                for tool in tool_result.tools:
                    print(f"\n🔧 {tool.name}")
                    print(f"   {tool.description[:100]}...")
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        properties = tool.inputSchema.get('properties', {})
                        if properties:
                            print(f"   Parameters: {', '.join(properties.keys())}")
                
                print("\n" + "="*80)
                print(f"✅ Found {len(tool_result.tools)} tools available")
                print("="*80)
                
                # Run test queries
                await run_test_queries(session, verbose)
                
    except ConnectionRefusedError:
        print(f"\n❌ Connection refused!")
        print(f"\n💡 The server is not running. Start it first:")
        print(f"   python strands_cost_calc_agent.py")
        print(f"\n   Then run this test script again.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error connecting to MCP server: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        if "Connection refused" in str(e):
            print("\n💡 Connection refused:")
            print("   - Server is not running on the specified port")
            print("   - Start server: python strands_cost_calc_agent.py")
        elif "timeout" in str(e).lower():
            print("\n💡 Timeout:")
            print("   - Server may be overloaded or not responding")
            print("   - Check server logs for errors")
        
        import traceback
        print("\n📋 Full traceback:")
        traceback.print_exc()
        sys.exit(1)


async def run_test_queries(session, verbose: bool = False):
    """Run comprehensive test queries against the agent"""
    
    test_queries = [
        {
            "query": "What is the pricing for Claude Haiku in us-west-2?",
            "description": "Simple pricing lookup",
            "category": "Pricing Query"
        },
        {
            "query": "Calculate Bedrock costs for 10,000 questions per month using Claude Haiku with 1000 input tokens and 500 output tokens per question",
            "description": "Basic Bedrock cost calculation",
            "category": "Bedrock Costs"
        },
        {
            "query": "I have an AI agent that processes 50,000 questions per month. Each question uses Claude Sonnet with 2000 input tokens and 800 output tokens. I also use a vector database that retrieves 5 chunks of 400 tokens each. Calculate the total monthly cost.",
            "description": "Bedrock with vector database",
            "category": "Bedrock Costs"
        },
        {
            "query": "Calculate costs for an agentic workflow: 30,000 questions/month, Claude Haiku, 10 tools available, agent uses 3 tools per question, 80% of questions invoke tools, 50 tokens per tool description, 75 tokens per tool output",
            "description": "Agentic workflow with tools",
            "category": "Bedrock Costs"
        },
        {
            "query": "What are the AgentCore pricing components for us-west-2?",
            "description": "AgentCore pricing lookup",
            "category": "AgentCore Pricing"
        },
        {
            "query": "Calculate AgentCore costs for an agent that runs 100 hours per month with 2GB memory, handles 10,000 requests, uses browser tool 500 times, code interpreter 200 times, and stores 1000 memory records",
            "description": "Complete AgentCore cost calculation",
            "category": "AgentCore Costs"
        },
        {
            "query": "Size an EMR cluster for processing 5TB of data using Spark on EC2 for batch processing",
            "description": "EMR EC2 cluster sizing",
            "category": "EMR Sizing"
        },
        {
            "query": "Calculate EMR Serverless costs for a streaming job with 20 workers, 4 vCPUs and 16GB per worker",
            "description": "EMR Serverless sizing",
            "category": "EMR Sizing"
        },
        {
            "query": "Size an EMR on EKS cluster for 10TB data processing with Trino, 20 workers, 8 cores and 32GB per worker",
            "description": "EMR on EKS sizing",
            "category": "EMR Sizing"
        },
        {
            "query": "What's the ROI if I process 10,000 questions per month, save 10 minutes per question, and my labor cost is $50/hour? The AI agent costs $500/month.",
            "description": "Basic ROI calculation",
            "category": "Business Value"
        },
        {
            "query": "Calculate business value: 50,000 questions/month, save 15 minutes per question without AI vs 3 minutes with AI, 90% of questions save time, $60/hour labor cost, AI costs $2000/month, analyze over 12 months",
            "description": "Comprehensive business value analysis",
            "category": "Business Value"
        },
        {
            "query": "Compare costs: Claude Haiku vs Claude Sonnet for 20,000 questions with 1500 input and 600 output tokens each",
            "description": "Model comparison",
            "category": "What-If Analysis"
        }
    ]
    
    print("\n" + "="*80)
    print("🧪 Running Test Queries")
    print("="*80)
    
    passed = 0
    failed = 0
    results_by_category = {}
    
    for i, test in enumerate(test_queries, 1):
        category = test['category']
        if category not in results_by_category:
            results_by_category[category] = {'passed': 0, 'failed': 0}
        
        print(f"\n{'─'*80}")
        print(f"📝 Test {i}/{len(test_queries)}: {test['description']}")
        print(f"   Category: {category}")
        print(f"   Query: {test['query'][:80]}...")
        
        try:
            print(f"   ⏳ Processing...")
            result = await session.call_tool(
                name="invoke_cost_analysis_agent_read_only",
                arguments={"query": test['query']}
            )
            result_text = result.content[0].text
            
            # Try to parse as JSON
            try:
                result_data = json.loads(result_text)
                
                # Check for errors
                if isinstance(result_data, dict) and 'error' in result_data:
                    print(f"   ⚠️  Agent returned error: {result_data['error'][:100]}")
                    failed += 1
                    results_by_category[category]['failed'] += 1
                else:
                    # Success
                    print(f"   ✅ Success")
                    
                    # Show summary based on response type
                    if verbose:
                        print(f"\n   📊 Response Summary:")
                        if 'BEDROCK_COSTS' in result_data:
                            bedrock = result_data['BEDROCK_COSTS']
                            total = bedrock.get('total_monthly_cost', 0)
                            print(f"      Bedrock Total: ${total:,.2f}/month")
                        if 'AGENTCORE_COSTS' in result_data:
                            agentcore = result_data['AGENTCORE_COSTS']
                            total = agentcore.get('total_monthly_cost', 0)
                            print(f"      AgentCore Total: ${total:,.2f}/month")
                        if 'EMR_COSTS' in result_data:
                            emr = result_data['EMR_COSTS']
                            if 'cluster_totals' in emr:
                                nodes = emr['cluster_totals'].get('total_nodes', 0)
                                print(f"      EMR Nodes: {nodes}")
                        if 'BUSINESS_VALUE' in result_data:
                            bva = result_data['BUSINESS_VALUE']
                            roi = bva.get('roi_percent', 0)
                            print(f"      ROI: {roi:.1f}%")
                    
                    passed += 1
                    results_by_category[category]['passed'] += 1
                    
            except json.JSONDecodeError:
                # Not JSON, but still success
                print(f"   ✅ Success (non-JSON response)")
                if verbose:
                    print(f"   Response: {result_text[:200]}...")
                passed += 1
                results_by_category[category]['passed'] += 1
                
        except Exception as e:
            print(f"   ❌ Failed: {str(e)[:100]}")
            if verbose:
                import traceback
                traceback.print_exc()
            failed += 1
            results_by_category[category]['failed'] += 1
        
        # Small delay between tests
        if i < len(test_queries):
            await asyncio.sleep(1)
    
    # Print summary
    print("\n" + "="*80)
    print("📊 Test Summary")
    print("="*80)
    print(f"\n🎯 Overall Results:")
    print(f"   Total Tests: {passed + failed}")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    if passed + failed > 0:
        print(f"   Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    print(f"\n📂 Results by Category:")
    for category, results in results_by_category.items():
        total = results['passed'] + results['failed']
        rate = (results['passed'] / total * 100) if total > 0 else 0
        print(f"   {category}:")
        print(f"      ✅ {results['passed']}/{total} passed ({rate:.0f}%)")
    
    print("\n" + "="*80)
    print("✅ Local MCP Server Testing Complete!")
    print("="*80)


async def test_single_query(mcp_url: str, query: str, verbose: bool = False):
    """Test a single query against the MCP server"""
    
    headers = {"Content-Type": "application/json"}
    
    print(f"\n{'='*80}")
    print(f"🤖 Testing Single Query")
    print(f"{'='*80}")
    print(f"Query: {query}")
    
    try:
        async with streamablehttp_client(
            mcp_url,
            headers,
            timeout=timedelta(seconds=30)
        ) as (read_stream, write_stream, _):
            
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                print(f"\n⏳ Processing query...")
                result = await session.call_tool(
                    name="invoke_cost_analysis_agent_read_only",
                    arguments={"query": query}
                )
                result_text = result.content[0].text
                
                print(f"\n✅ Agent Response:")
                print(f"{'='*80}")
                
                # Try to parse and pretty print JSON
                try:
                    result_data = json.loads(result_text)
                    print(json.dumps(result_data, indent=2))
                except json.JSONDecodeError:
                    print(result_text)
                
                print(f"{'='*80}")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def format_human_readable(result_data):
    """Format JSON response in human-readable format"""
    output = []
    
    # Check for Bedrock costs
    if 'bedrock_costs' in result_data:
        bedrock = result_data['bedrock_costs']
        output.append("\n" + "="*80)
        output.append("💰 BEDROCK COSTS")
        output.append("="*80)
        
        # Global info
        questions = bedrock.get('questions_per_month_all_models', 0)
        output.append(f"\n📊 Total Questions: {questions:,} per month")
        
        # Global assumptions
        if 'assumptions' in bedrock and 'global' in bedrock['assumptions']:
            global_assumptions = bedrock['assumptions']['global']
            output.append(f"\n🔧 Global Settings:")
            output.append(f"   • System prompt tokens: {global_assumptions.get('system_prompt_tokens', 0):,}")
            output.append(f"   • History Q&A pairs: {global_assumptions.get('history_qa_pairs', 0)}")
        
        # Warnings
        if 'warnings' in bedrock and bedrock['warnings']:
            output.append(f"\n⚠️  Warnings:")
            for warning in bedrock['warnings']:
                output.append(f"   {warning}")
        
        # Individual models
        output.append(f"\n🤖 Model Costs:")
        for key, value in bedrock.items():
            if key not in ['questions_per_month_all_models', 'assumptions', 
                          'warnings', 'total_cost_for_all_models'] and isinstance(value, dict):
                model = value
                output.append(f"\n   📦 {key.upper()}: {model.get('model_name', 'Unknown')}")
                
                costs = model.get('costs', {})
                output.append(f"      💵 Input tokens:  ${costs.get('input_token_cost', 0):,.2f}")
                output.append(f"      💵 Output tokens: ${costs.get('output_token_cost', 0):,.2f}")
                output.append(f"      💵 Total:         ${costs.get('total_token_cost', 0):,.2f}")
                
                assumptions = model.get('assumptions', {})
                output.append(f"      📊 Questions allocated: {assumptions.get('calculated_questions_for_this_model', 0):,.0f} ({assumptions.get('percent_questions_for_model', 0):.0f}%)")
                output.append(f"      📊 Input tokens/question: {assumptions.get('input_tokens_per_question', 0):,}")
                output.append(f"      📊 Output tokens/question: {assumptions.get('output_tokens_per_question', 0):,}")
                
                # Vector database info if present for this model
                if 'vector_database' in assumptions:
                    vdb = assumptions['vector_database']
                    output.append(f"      🗄️  Vector Database:")
                    output.append(f"         • Chunks per call: {vdb.get('chunks_per_call', 0)}")
                    output.append(f"         • Tokens per chunk: {vdb.get('tokens_per_chunk', 0)}")
                    output.append(f"         • % questions using: {vdb.get('percent_questions_using_vector_db', 0):.0f}%")
                
                # Tool info if present
                if assumptions.get('number_of_tools'):
                    output.append(f"      🔧 Tools: {assumptions.get('number_of_tools', 0)} total, {assumptions.get('tools_passed_to_model', 0)} passed to model")
                    output.append(f"      🔧 Tool invocations/question: {assumptions.get('tool_invocations_per_question', 0)}")
                    output.append(f"      🔧 Questions using tools: {assumptions.get('percent_questions_that_invoke_tools', 0):.0f}%")
                
                # Token breakdown
                breakdown = model.get('token_breakdown', {})
                output.append(f"      📈 Total input tokens: {breakdown.get('total_input_tokens', 0):,.0f}")
                output.append(f"      📈 Total output tokens: {breakdown.get('total_output_tokens', 0):,.0f}")
        
        # Total
        total = bedrock.get('total_cost_for_all_models', 0)
        output.append(f"\n{'─'*80}")
        output.append(f"💰 TOTAL BEDROCK COST: ${total:,.2f} per month")
        output.append(f"{'─'*80}")
    
    # Check for AgentCore costs
    if 'agentcore_costs' in result_data:
        agentcore = result_data['agentcore_costs']
        output.append("\n" + "="*80)
        output.append("🏗️  AGENTCORE COSTS")
        output.append("="*80)
        
        # Runtime
        if 'runtime' in agentcore:
            runtime = agentcore['runtime']
            output.append(f"\n⚙️  Runtime:")
            output.append(f"   💵 CPU cost:    ${runtime.get('cpu_cost', 0):,.2f}")
            output.append(f"   💵 Memory cost: ${runtime.get('memory_cost', 0):,.2f}")
            output.append(f"   💵 Total:       ${runtime.get('total_cost', 0):,.2f}")
            output.append(f"   📊 vCPU hours:  {runtime.get('vcpu_hours', 0):,.2f}")
            output.append(f"   📊 GB hours:    {runtime.get('gb_hours', 0):,.2f}")
            output.append(f"   📊 Questions:   {runtime.get('total_questions_per_month', 0):,.0f} ({runtime.get('percent_questions_using_runtime', 0):.0f}%)")
        
        # Browser
        if 'browser' in agentcore:
            browser = agentcore['browser']
            output.append(f"\n🌐 Browser Tool:")
            output.append(f"   💵 CPU cost:    ${browser.get('cpu_cost', 0):,.2f}")
            output.append(f"   💵 Memory cost: ${browser.get('memory_cost', 0):,.2f}")
            output.append(f"   💵 Total:       ${browser.get('total_cost', 0):,.2f}")
            output.append(f"   📊 Questions:   {browser.get('total_questions_per_month', 0):,.0f} ({browser.get('percent_questions_using_browser', 0):.0f}%)")
        
        # Code Interpreter
        if 'code_interpreter' in agentcore:
            code = agentcore['code_interpreter']
            output.append(f"\n💻 Code Interpreter:")
            output.append(f"   💵 CPU cost:    ${code.get('cpu_cost', 0):,.2f}")
            output.append(f"   💵 Memory cost: ${code.get('memory_cost', 0):,.2f}")
            output.append(f"   💵 Total:       ${code.get('total_cost', 0):,.2f}")
            output.append(f"   📊 Questions:   {code.get('total_questions_per_month', 0):,.0f} ({code.get('percent_questions_using_code_interpreter', 0):.0f}%)")
        
        # Gateway
        if 'gateway' in agentcore:
            gateway = agentcore['gateway']
            output.append(f"\n🚪 Gateway:")
            output.append(f"   💵 Invoke tool cost: ${gateway.get('invoke_tool_cost', 0):,.2f}")
            output.append(f"   💵 Search API cost:  ${gateway.get('search_api_cost', 0):,.2f}")
            output.append(f"   💵 Indexing cost:    ${gateway.get('indexing_cost', 0):,.2f}")
            output.append(f"   💵 Total:            ${gateway.get('total_cost', 0):,.2f}")
            output.append(f"   📊 Tool invocations: {gateway.get('total_invoke_tool_calls', 0):,.0f}")
            output.append(f"   📊 Search API calls: {gateway.get('total_search_api_calls', 0):,.0f}")
            output.append(f"   📊 Questions using tools: {gateway.get('questions_using_tools_per_month', 0):,.0f} ({gateway.get('percent_questions_using_tools', 0):.0f}%)")
        
        # Memory
        if 'memory' in agentcore:
            memory = agentcore['memory']
            output.append(f"\n🧠 Memory:")
            output.append(f"   💵 Short-term cost:  ${memory.get('short_term_cost', 0):,.2f}")
            output.append(f"   💵 Long-term storage: ${memory.get('long_term_storage_cost', 0):,.2f}")
            output.append(f"   💵 Long-term retrieval: ${memory.get('long_term_retrieval_cost', 0):,.2f}")
            output.append(f"   💵 Total:            ${memory.get('total_cost', 0):,.2f}")
            output.append(f"   📊 Events/month:     {memory.get('total_events_per_month', 0):,.0f}")
            output.append(f"   📊 Records stored:   {memory.get('records_stored_per_month', 0):,.0f}")
            output.append(f"   📊 Retrievals:       {memory.get('total_retrievals_per_month', 0):,.0f}")
        
        # Total
        total = agentcore.get('total_all_components', 0)
        output.append(f"\n{'─'*80}")
        output.append(f"💰 TOTAL AGENTCORE COST: ${total:,.2f} per month")
        output.append(f"{'─'*80}")
    
    # Check for Business Value
    if 'business_value' in result_data:
        bva = result_data['business_value']
        output.append("\n" + "="*80)
        output.append("📈 BUSINESS VALUE ANALYSIS")
        output.append("="*80)
        
        output.append(f"\n💰 Financial Summary:")
        output.append(f"   Initial investment: ${bva.get('initial_investment', 0):,.2f}")
        output.append(f"   Total benefits:     ${bva.get('total_benefits', 0):,.2f}")
        output.append(f"   Total costs:        ${bva.get('total_costs', 0):,.2f}")
        output.append(f"   Net value:          ${bva.get('net_value', 0):,.2f}")
        output.append(f"   ROI:                {bva.get('roi_percent', 0):.1f}%")
        
        if 'cost_savings' in bva and bva['cost_savings']:
            savings = bva['cost_savings']
            output.append(f"\n💵 Cost Savings:")
            output.append(f"   Hours saved/month:  {savings.get('hours_saved_per_month', 0):,.1f}")
            output.append(f"   Costs saved/month:  ${savings.get('costs_saved_per_month', 0):,.2f}")
        
        if 'revenue_growth' in bva and bva['revenue_growth']:
            revenue = bva['revenue_growth']
            output.append(f"\n📊 Revenue Growth:")
            output.append(f"   Time to new projects: {revenue.get('percent_time_to_new_projects', 0):.0f}%")
            output.append(f"   Revenue/month:        ${revenue.get('revenue_generated_per_month', 0):,.2f}")
        
        if 'customer_churn_reduction' in bva and bva['customer_churn_reduction']:
            churn = bva['customer_churn_reduction']
            output.append(f"\n👥 Churn Reduction:")
            output.append(f"   Churn before AI: {churn.get('customer_churn_before_ai', 0):.2f}%")
            output.append(f"   Churn after AI:  {churn.get('customer_churn_after_ai', 0):.2f}%")
            output.append(f"   Monthly value:   ${churn.get('monthly_total_churn_value', 0):,.2f}")
    
    return "\n".join(output)


async def interactive_mode(mcp_url: str):
    """Interactive mode - ask questions in a loop until user types quit/exit"""
    
    headers = {"Content-Type": "application/json"}
    
    print(f"\n{'='*80}")
    print(f"💬 INTERACTIVE MODE")
    print(f"{'='*80}")
    print(f"Server: {mcp_url}")
    print(f"\n💡 Tips:")
    print(f"   • Ask questions about AWS costs (Bedrock, AgentCore, EMR)")
    print(f"   • Type 'quit' or 'exit' to stop")
    print(f"   • Type 'help' for example questions")
    print(f"{'='*80}\n")
    
    try:
        async with streamablehttp_client(
            mcp_url,
            headers,
            timeout=timedelta(seconds=60)
        ) as (read_stream, write_stream, _):
            
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                print("✅ Connected to MCP server\n")
                
                while True:
                    try:
                        # Get user input
                        query = input("🤔 Your question: ").strip()
                        
                        # Check for exit commands
                        if query.lower() in ['quit', 'exit', 'q']:
                            print("\n👋 Goodbye!")
                            break
                        
                        # Check for help
                        if query.lower() == 'help':
                            print("\n📚 Example Questions:")
                            print("   • What is the pricing for Claude Haiku in us-west-2?")
                            print("   • Calculate Bedrock costs for 10,000 questions per month using Claude Haiku")
                            print("   • Calculate AgentCore costs for 100 hours per month with 2GB memory")
                            print("   • What's the ROI if I save 10 minutes per question with 10k questions/month?")
                            print("   • Size an EMR cluster for processing 5TB of data\n")
                            continue
                        
                        # Skip empty queries
                        if not query:
                            continue
                        
                        # Process query
                        print(f"\n⏳ Processing...\n")
                        result = await session.call_tool(
                            name="invoke_cost_analysis_agent_read_only",
                            arguments={"query": query}
                        )
                        result_text = result.content[0].text
                        print(f"{result_text}")
                        
                        # # Try to parse as JSON and format
                        # try:
                        #     result_data = json.loads(result_text)
                            
                        #     # Check for errors
                        #     if isinstance(result_data, dict) and 'error' in result_data:
                        #         print(f"❌ Error: {result_data['error']}\n")
                        #     else:
                        #         # Format and display
                        #         formatted = format_human_readable(result_data)
                        #         print(formatted)
                        #         print()
                        
                        # except json.JSONDecodeError:
                        #     # Not JSON, display as-is
                        #     print(f"📄 Response:\n{result_text}\n")
                    
                    except KeyboardInterrupt:
                        print("\n\n👋 Interrupted. Type 'quit' to exit or continue asking questions.")
                        continue
                    except Exception as e:
                        print(f"\n❌ Error processing query: {e}\n")
                        continue
    
    except ConnectionRefusedError:
        print(f"\n❌ Connection refused!")
        print(f"\n💡 The server is not running. Start it first:")
        print(f"   python strands_cost_calc_agent.py")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error connecting to MCP server: {e}")
        sys.exit(1)


def agent_mode(mcp_url: str):
    """Agent mode - use Strands agent with MCP tools in an interactive loop"""
    
    print(f"\n{'='*80}")
    print(f"🤖 AGENT MODE")
    print(f"{'='*80}")
    print(f"Server: {mcp_url}")
    print(f"\n💡 Tips:")
    print(f"   • Ask questions about AWS costs (Bedrock, AgentCore, EMR)")
    print(f"   • The Strands agent will use MCP tools to answer your questions")
    print(f"   • Type 'quit' or 'exit' to stop")
    print(f"   • Type 'help' for example questions")
    print(f"{'='*80}\n")
    
    try:
        # Create MCP client for the running server
        print("🔄 Connecting to MCP server...")
        mcp_client = MCPClient(
            lambda: streamable_http_client(mcp_url)
        )
        
        # Use context manager to establish connection
        with mcp_client:
            print("✅ Connected to MCP server")
            
            # Get available tools from MCP server
            print("🔄 Discovering MCP tools...")
            mcp_tools = mcp_client.list_tools_sync()
            print(f"✅ Found {len(mcp_tools)} MCP tools")
            
            # Display tool names
            for i, tool in enumerate(mcp_tools, 1):
                print(f"   Tool #{i}: {tool.tool_name}")
            print()
            
            # Create Strands agent with MCP tools
            print("🔄 Creating Strands agent with MCP tools...")
            
            agent_system_prompt = """
You are an AWS cost analysis and business value assistant. You have access to MCP tools that can help answer questions about AWS costs and business value. You are just just a pass-through mechanism to the MCP tool that sends questions to the MCP tool and presents responses from the MCP tool as-is.

When a user asks a question:
1. ALWAYS pass the question as-is to the MCP tool.
2. ALWAYS present the tool's response exactly as received - do not modify, summarize, or interpret the JSON output
3. CRITICAL: When the tool requests additional information and shows default values, even in a multi-turn conversation, display those defaults exactly as provided without paraphrasing or interpretation. Allow the user to either accept defaults or specify different values.
4. CRITICAL OUTPUT FORMAT: When you receive the final JSON response from the tool:
   - First, print the complete JSON dictionary exactly as received
   - Use a code block or clear formatting to display it
   - Do NOT summarize, interpret, or extract specific values
   - After showing the complete JSON, you may add a brief summary if helpful
   - Example interaction:
User: "Calculate costs for 10k questions"
Tool returns: {"key": "value"}
Your response should be:

Here's the complete cost analysis:

```json
{
  "key": "value"
}
Summary: The costs are $xxx
"""
            
            model_id = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
            agent = Agent(
                system_prompt=agent_system_prompt,
                model=BedrockModel(model_id=model_id, temperature=0.1),
                tools=mcp_tools
            )
            
            print("✅ Agent created and ready\n")
            
            # Interactive loop
            while True:
                try:
                    # Get user input
                    query = input("🤔 Your question: ").strip()
                    
                    # Check for exit commands
                    if query.lower() in ['quit', 'exit', 'q']:
                        print("\n👋 Goodbye!")
                        break
                    
                    # Check for help
                    if query.lower() == 'help':
                        print("\n� Example Questions:")
                        print("   • What is the pricing for Claude Haiku in us-west-2?")
                        print("   • Calculate Bedrock costs for 10,000 questions per month using Claude Haiku")
                        print("   • Calculate AgentCore costs for 100 hours per month with 2GB memory")
                        print("   • What's the ROI if I save 10 minutes per question with 10k questions/month?")
                        print("   • Size an EMR cluster for processing 5TB of data\n")
                        continue
                    
                    # Skip empty queries
                    if not query:
                        continue
                    
                    # Process query with agent
                    print(f"\n⏳ Agent processing...\n")
                    response = agent(query)
                    
                    # Display agent response
                    print(f"🤖 Agent: {response.message['content'][0]['text']}\n")
                
                except KeyboardInterrupt:
                    print("\n\n👋 Interrupted by Ctrl+C. Exiting...")
                    break
                except Exception as e:
                    print(f"\n❌ Error processing query: {e}\n")
                    import traceback
                    traceback.print_exc()
                    continue
    
    except ConnectionRefusedError:
        print(f"\n❌ Connection refused!")
        print(f"\n💡 The server is not running. Start it first:")
        print(f"   python strands_cost_calc_agent.py")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error connecting to MCP server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        sys.exit(1)


async def main():
    parser = argparse.ArgumentParser(
        description='Test Local MCP Server for Strands Cost Calculator Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Prerequisites:
  Start the MCP server first:
    python strands_cost_calc_agent.py

Examples:
  # Agent mode (Strands agent uses MCP tools)
  python test_local_mcp_server.py --agent
  
  # Interactive mode (direct MCP tool calls)
  python test_local_mcp_server.py --interactive
  
  # Run full test suite
  python test_local_mcp_server.py
  
  # Test with custom port
  python test_local_mcp_server.py --port 8080
  
  # Test single query
  python test_local_mcp_server.py --query "Calculate Bedrock costs for 10k questions"
  
  # Verbose output
  python test_local_mcp_server.py --verbose
        """
    )
    parser.add_argument('--port', type=int, default=8000,
                        help='Port where MCP server is running (default: 8000)')
    parser.add_argument('--host', type=str, default='localhost',
                        help='Host where MCP server is running (default: localhost)')
    parser.add_argument('--query', type=str,
                        help='Test a single query instead of running full suite')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Interactive mode - ask questions in a loop')
    parser.add_argument('--agent', '-a', action='store_true',
                        help='Agent mode - use Strands agent with MCP tools')
    parser.add_argument('--verbose', action='store_true',
                        help='Show detailed output including response summaries')
    
    args = parser.parse_args()
    
    mcp_url = f"http://{args.host}:{args.port}/mcp"
    
    print(f"{'='*80}")
    print(f"🚀 Local MCP Server Test Client")
    print(f"{'='*80}")
    print(f"Server: {mcp_url}")
    
    try:
        if args.agent:
            # Agent mode - use Strands agent with MCP tools
            agent_mode(mcp_url)
        elif args.interactive:
            # Interactive mode
            await interactive_mode(mcp_url)
        elif args.query:
            # Test single query
            await test_single_query(mcp_url, args.query, args.verbose)
        else:
            # Run full test suite
            await test_mcp_server(mcp_url, args.verbose)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
