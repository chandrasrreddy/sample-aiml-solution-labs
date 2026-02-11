#!/usr/bin/env python3
"""
Vector Search Test Script with LLM-as-a-Judge Evaluation

Enhanced test script for the vector retrieval Lambda function with relevance scoring
using Claude 4.5 Sonnet as a judge to evaluate search result quality.

Arguments:
--query: The text to search for
--mode: The retrieval strategy (content_similarity, metadata_similarity, hybrid_similarity, filter_and_search)
--metadata: Metadata JSON for metadata-based searches or filter parameters
--judge: Enable LLM-as-a-judge scoring (default: False)
--judge-model: Claude model to use for judging (default: anthropic.claude-sonnet-4-5-20250929-v1:0)

Usage:
    # Basic search without judging
    python validation/scripts/test_vector_search.py --query "machine learning" --mode content_similarity --metadata "{}"
    
    # Search with LLM-as-a-judge evaluation
    python validation/scripts/test_vector_search.py --query "machine learning on AWS" --mode content_similarity --metadata "{}" --judge
    
    # Hybrid search with custom judge model
    python validation/scripts/test_vector_search.py --query "neural networks" --mode hybrid_similarity --metadata '{"query": "research paper", "content_weight": 0.7, "metadata_weight": 0.3}' --judge --judge-model us.anthropic.claude-sonnet-4-5-20250929-v1:0
"""

import json
import boto3
import sys
import argparse
from typing import Dict, Any, List, Tuple
from datetime import datetime


def get_lambda_function_name(region: str = 'us-west-2') -> str:
    """Get the retrieval Lambda function name from CDK stack outputs."""
    try:
        cf_client = boto3.client('cloudformation', region_name=region)
        response = cf_client.describe_stacks(StackName='AuroraVectorKbStack')
        
        for stack in response['Stacks']:
            for output in stack.get('Outputs', []):
                if output['OutputKey'] == 'RetrievalLambdaFunctionName':
                    return output['OutputValue']
        
        raise ValueError("RetrievalLambdaFunctionName output not found in stack")
        
    except Exception as e:
        print(f"Error getting Lambda function name: {str(e)}")
        sys.exit(1)


def create_payload(query: str, mode: str, metadata: Dict[str, Any], k: int = 3) -> Dict[str, Any]:
    """
    Create the Lambda payload based on query mode and parameters.
    
    Args:
        query: Query string
        mode: Query mode (search type)
        metadata: Metadata dictionary with additional parameters
        k: Number of results to return
        
    Returns:
        Lambda payload dictionary
    """
    # Base payload - use explicit k parameter, fallback to metadata, then default
    payload = {
        "search_type": mode,
        "k": k if k is not None else metadata.get("k", 3)
    }
    
    # Add parameters based on search type
    if mode == "content_similarity":
        payload["query"] = query
        
    elif mode == "metadata_similarity":
        payload["metadata_query"] = str(metadata.get("query")),
        
    elif mode == "hybrid_similarity":
        payload.update({
            "query": query,
            "metadata_query": str(metadata.get("query")),
            "content_weight": metadata.get("content_weight", 0.5),
            "metadata_weight": metadata.get("metadata_weight", 0.5)
        })
        
    elif mode == "filter_and_search":
        payload.update({
            "query": query,
            "filter_type": metadata["filter_type"],
            "filter_value": metadata["filter_value"]
        })
    else:
        raise ValueError(f"Invalid query mode: {mode}. Must be one of: content_similarity, metadata_similarity, hybrid_similarity, filter_and_search")
    
    return payload


def invoke_lambda(function_name: str, payload: Dict[str, Any], region: str = 'us-west-2') -> Dict[str, Any]:
    """Invoke the retrieval Lambda function."""
    lambda_client = boto3.client('lambda', region_name=region)
    
    try:
        print(f"🔍 Invoking Lambda: {function_name}")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        print("-" * 60)
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse response
        result = json.loads(response['Payload'].read())
        return result
        
    except Exception as e:
        print(f"❌ Error invoking Lambda: {str(e)}")
        sys.exit(1)


def judge_relevance_with_llm(
    query: str,
    document: str,
    metadata: Dict[str, Any],
    model_id: str = "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    region: str = "us-west-2"
) -> Tuple[float, str, Dict[str, Any]]:
    """
    Use Claude 4.5 Sonnet to judge the relevance of a search result.
    
    Args:
        query: The original search query
        document: The retrieved document content
        metadata: Document metadata (category, industry, etc.)
        model_id: Bedrock model ID for Claude
        region: AWS region
        
    Returns:
        Tuple of (relevance_score, explanation, detailed_scores)
        - relevance_score: 0.0 to 1.0 score
        - explanation: Text explanation of the score
        - detailed_scores: Dict with breakdown of scoring criteria
    """
    bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
    
    # Construct the judging prompt
    judge_prompt = f"""You are an expert evaluator assessing the relevance of search results. 

Your task is to evaluate how well a retrieved document matches a user's search query.

SEARCH QUERY:
{query}

RETRIEVED DOCUMENT:
{document[:2000]}  # Limit to first 2000 chars

DOCUMENT METADATA:
{json.dumps(metadata, indent=2)}

Please evaluate the relevance on these criteria:

1. CONTENT RELEVANCE (0-10): Does the document content directly address the query topic?
2. SEMANTIC MATCH (0-10): Are the concepts and terminology aligned with the query?
3. METADATA ALIGNMENT (0-10): Do the category/industry tags match the query intent?
4. COMPLETENESS (0-10): Does the document provide comprehensive information on the query topic?
5. SPECIFICITY (0-10): Is the information specific and actionable, or too general?

Provide your evaluation in this EXACT JSON format (no additional text):
{{
  "content_relevance": <score 0-10>,
  "semantic_match": <score 0-10>,
  "metadata_alignment": <score 0-10>,
  "completeness": <score 0-10>,
  "specificity": <score 0-10>,
  "overall_score": <average of above, 0-10>,
  "explanation": "<2-3 sentence explanation of the overall score>",
  "key_strengths": ["<strength 1>", "<strength 2>"],
  "key_weaknesses": ["<weakness 1>", "<weakness 2>"]
}}

Respond ONLY with the JSON object, no other text."""

    try:
        # Call Claude via Bedrock
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0.0,  # Deterministic for consistent judging
            "messages": [
                {
                    "role": "user",
                    "content": judge_prompt
                }
            ]
        }
        
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        content = response_body['content'][0]['text']
        
        # Extract JSON from response
        # Handle cases where Claude might add markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        judgment = json.loads(content)
        
        # Normalize overall score to 0-1 range
        relevance_score = judgment['overall_score'] / 10.0
        explanation = judgment['explanation']
        
        return relevance_score, explanation, judgment
        
    except Exception as e:
        print(f"⚠️  Warning: LLM judging failed: {str(e)}")
        # Return neutral score on error
        return 0.5, f"Judging failed: {str(e)}", {}


def calculate_aggregate_metrics(results_with_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate aggregate metrics across all judged results.
    
    Args:
        results_with_scores: List of results with LLM judge scores
        
    Returns:
        Dictionary with aggregate metrics
    """
    if not results_with_scores:
        return {}
    
    # Extract scores
    relevance_scores = [r['llm_relevance_score'] for r in results_with_scores]
    similarity_scores = [r['similarity_score'] for r in results_with_scores]
    
    # Calculate metrics
    metrics = {
        "mean_relevance_score": sum(relevance_scores) / len(relevance_scores),
        "mean_similarity_score": sum(similarity_scores) / len(similarity_scores),
        "max_relevance_score": max(relevance_scores),
        "min_relevance_score": min(relevance_scores),
        "relevance_score_std": calculate_std(relevance_scores),
        "highly_relevant_count": sum(1 for s in relevance_scores if s >= 0.8),
        "moderately_relevant_count": sum(1 for s in relevance_scores if 0.5 <= s < 0.8),
        "low_relevant_count": sum(1 for s in relevance_scores if s < 0.5),
        "score_correlation": calculate_correlation(similarity_scores, relevance_scores)
    }
    
    return metrics


def calculate_std(values: List[float]) -> float:
    """Calculate standard deviation."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance ** 0.5


def calculate_correlation(x: List[float], y: List[float]) -> float:
    """Calculate Pearson correlation coefficient."""
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n)) ** 0.5
    denominator_y = sum((y[i] - mean_y) ** 2 for i in range(n)) ** 0.5
    
    if denominator_x == 0 or denominator_y == 0:
        return 0.0
    
    return numerator / (denominator_x * denominator_y)


def print_results(response: Dict[str, Any], enable_judging: bool = False, query: str = None, judge_model: str = None, region: str = 'us-west-2'):
    """Print the search results in a formatted way, optionally with LLM judging."""
    if response.get('status') == 'success':
        print(f"✅ Status: {response['status']}")
        print(f"🔍 Search Type: {response['search_type']}")
        print(f"📊 Total Results: {response['total_results']}")
        print(f"⏱️  Execution Time: {response['execution_time_ms']}ms")
        
        results = response.get('results', [])
        if results:
            # Optionally judge results with LLM
            if enable_judging and query:
                print(f"\n🤖 Evaluating results with LLM Judge ({judge_model})...")
                print("=" * 80)
                
                results_with_scores = []
                for i, result in enumerate(results, 1):
                    print(f"\n⚖️  Judging Result {i}/{len(results)}...")
                    
                    relevance_score, explanation, detailed_scores = judge_relevance_with_llm(
                        query=query,
                        document=result['document'],
                        metadata=result.get('metadata', {}),
                        model_id=judge_model,
                        region=region
                    )
                    
                    # Add scores to result
                    result['llm_relevance_score'] = relevance_score
                    result['llm_explanation'] = explanation
                    result['llm_detailed_scores'] = detailed_scores
                    results_with_scores.append(result)
                
                # Calculate aggregate metrics
                aggregate_metrics = calculate_aggregate_metrics(results_with_scores)
                
                # Print aggregate metrics
                print("\n" + "=" * 80)
                print("📈 AGGREGATE EVALUATION METRICS")
                print("=" * 80)
                print(f"Mean LLM Relevance Score: {aggregate_metrics['mean_relevance_score']:.3f}")
                print(f"Mean Vector Similarity Score: {aggregate_metrics['mean_similarity_score']:.3f}")
                print(f"Score Correlation: {aggregate_metrics['score_correlation']:.3f}")
                print(f"Relevance Score Std Dev: {aggregate_metrics['relevance_score_std']:.3f}")
                print(f"\nRelevance Distribution:")
                print(f"  🟢 Highly Relevant (≥0.8): {aggregate_metrics['highly_relevant_count']}")
                print(f"  🟡 Moderately Relevant (0.5-0.8): {aggregate_metrics['moderately_relevant_count']}")
                print(f"  🔴 Low Relevance (<0.5): {aggregate_metrics['low_relevant_count']}")
                
                # Update results for display
                results = results_with_scores
            
            print(f"\n{'=' * 80}")
            print(f"📋 SEARCH RESULTS")
            print(f"{'=' * 80}")
            
            for i, result in enumerate(results, 1):
                print(f"\n{'─' * 80}")
                print(f"🔸 Result {i}")
                print(f"{'─' * 80}")
                print(f"ID: {result['id']}")
                print(f"Source: {result['source_s3_uri']}")
                print(f"\nContent Preview:")
                print(f"{result['document'][:300]}...")
                
                # Print vector similarity scores
                print(f"\n📊 Vector Similarity Scores:")
                print(f"  Overall Similarity: {result['similarity_score']:.4f}")
                if 'content_score' in result:
                    print(f"  Content Score: {result['content_score']:.4f}")
                if 'metadata_score' in result:
                    print(f"  Metadata Score: {result['metadata_score']:.4f}")
                if 'filter_score' in result:
                    print(f"  Filter Score: {result['filter_score']:.4f}")
                
                # Print LLM judge scores if available
                if 'llm_relevance_score' in result:
                    print(f"\n🤖 LLM Judge Evaluation:")
                    print(f"  Overall Relevance: {result['llm_relevance_score']:.3f} ({result['llm_relevance_score']*100:.1f}%)")
                    
                    if result.get('llm_detailed_scores'):
                        scores = result['llm_detailed_scores']
                        print(f"  Detailed Scores:")
                        print(f"    • Content Relevance: {scores.get('content_relevance', 0)}/10")
                        print(f"    • Semantic Match: {scores.get('semantic_match', 0)}/10")
                        print(f"    • Metadata Alignment: {scores.get('metadata_alignment', 0)}/10")
                        print(f"    • Completeness: {scores.get('completeness', 0)}/10")
                        print(f"    • Specificity: {scores.get('specificity', 0)}/10")
                        
                        if scores.get('key_strengths'):
                            print(f"  Strengths:")
                            for strength in scores['key_strengths']:
                                print(f"    ✓ {strength}")
                        
                        if scores.get('key_weaknesses'):
                            print(f"  Weaknesses:")
                            for weakness in scores['key_weaknesses']:
                                print(f"    ✗ {weakness}")
                    
                    print(f"\n  Explanation: {result['llm_explanation']}")
                
                # Print metadata
                if result.get('metadata'):
                    metadata = result['metadata']
                    print(f"\n📝 Metadata:")
                    print(f"  Category: {metadata.get('category', 'N/A')}")
                    print(f"  Industry: {metadata.get('industry', 'N/A')}")
            
            if len(results) > 10:
                print(f"\n... showing first 10 of {len(results)} results")
        else:
            print("\n📭 No results found")
            
    else:
        print(f"❌ Status: {response['status']}")
        print(f"🚫 Error Type: {response.get('error_type', 'unknown')}")
        print(f"💬 Message: {response.get('message', 'No error message')}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Test the vector retrieval Lambda function with optional LLM-as-a-judge evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic content similarity search
  python test_vector_search.py --query "machine learning" --mode content_similarity --metadata "{}"
  
  # Content similarity search with LLM judging
  python test_vector_search.py --query "machine learning on AWS" --mode content_similarity --metadata "{}" --judge
  
  # Hybrid search with custom k and judging
  python test_vector_search.py --query "neural networks" --mode hybrid_similarity --metadata '{"query": "research paper", "content_weight": 0.7, "metadata_weight": 0.3}' --k 5 --judge
  
  # Filter and search with custom judge model
  python test_vector_search.py --query "deep learning" --mode filter_and_search --metadata '{"filter_type": "category", "filter_value": "machine learning"}' --judge 
        """
    )
    
    parser.add_argument(
        '--query',
        required=False,
        help='The text to search for'
    )
    
    parser.add_argument(
        '--mode',
        required=True,
        choices=['content_similarity', 'metadata_similarity', 'hybrid_similarity', 'filter_and_search'],
        help='The retrieval strategy to use'
    )
    
    parser.add_argument(
        '--metadata',
        required=False,
        help='Metadata JSON string with additional parameters'
    )
    
    parser.add_argument(
        '--k',
        type=int,
        default=3,
        help='Number of results to return (default: 3)'
    )
    
    parser.add_argument(
        '--region',
        default='us-west-2',
        help='AWS region (default: us-west-2)'
    )
    
    parser.add_argument(
        '--judge',
        action='store_true',
        help='Enable LLM-as-a-judge evaluation of search results'
    )
    
    parser.add_argument(
        '--judge-model',
        default='us.anthropic.claude-sonnet-4-5-20250929-v1:0',
        help='Bedrock model ID for LLM judge (default: us.anthropic.claude-sonnet-4-5-20250929-v1:0)'
    )
    
    args = parser.parse_args()
    
    query = args.query
    mode = args.mode
    metadata_json = args.metadata
    
    # Parse metadata JSON
    try:
        metadata = json.loads(metadata_json)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in metadata parameter: {str(e)}")
        sys.exit(1)
    
    print(f"🚀 Starting Vector Search Test")
    print(f"🔤 Query: {query}")
    print(f"🎯 Mode: {mode}")
    print(f"📝 Metadata: {json.dumps(metadata, indent=2)}")
    if args.judge:
        print(f"🤖 LLM Judge: Enabled ({args.judge_model})")
    print("=" * 80)
    
    try:
        # Get Lambda function name
        function_name = get_lambda_function_name(args.region)
        
        # Create payload
        payload = create_payload(query, mode, metadata, args.k)
        
        # Invoke Lambda
        response = invoke_lambda(function_name, payload, args.region)
        
        # Print results (with optional judging)
        print_results(
            response, 
            enable_judging=args.judge,
            query=query,
            judge_model=args.judge_model,
            region=args.region
        )
        
        # Exit with appropriate code
        if response.get('status') == 'success':
            print(f"\n{'=' * 80}")
            print(f"🎉 Search completed successfully!")
            print(f"{'=' * 80}")
            sys.exit(0)
        else:
            print(f"\n{'=' * 80}")
            print(f"💥 Search failed!")
            print(f"{'=' * 80}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()