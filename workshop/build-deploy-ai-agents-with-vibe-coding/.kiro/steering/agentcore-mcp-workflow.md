---
inclusion: always
---

# AgentCore MCP Workflow Guidelines

This steering file contains critical instructions that apply to ALL AgentCore MCP workflow prompts.

## CRITICAL WORKFLOW RULES

### ⚠️ CRITICAL: ALWAYS REFERENCE MCP SERVER CODE FOR API METHODS

**BEFORE creating ANY script that uses boto3 AWS APIs (Gateway, Runtime, Memory, etc.):**

1. **CHECK THE MCP SERVER HANDLERS FIRST** - The MCP server code at `agentcore-mcp-server/handlers/` contains the CORRECT boto3 API methods
2. **USE THE SAME API METHODS** - Copy the exact client names and method calls from the MCP handlers
3. **DO NOT GUESS** - Never assume API method names without checking the MCP server code first

**Why this matters**: The MCP server handlers are based on the reference notebook and use the correct boto3 API methods. If you guess or assume API methods, you will create broken code that fails at runtime.

**Example - Gateway API Methods**:
- ✅ CORRECT (from MCP server): `bedrock-agentcore-control` client with `list_gateway_targets()`, `delete_gateway_target(targetId=...)`
- ❌ WRONG (guessing): `bedrock-agentcore` client with `list_targets()`, `delete_target(targetIdentifier=...)`

**Example - Runtime API Methods**:
- ✅ CORRECT (from MCP server): `bedrock-agentcore-control` client with `delete_agent_runtime(agentRuntimeId=...)`
- ❌ WRONG (guessing): `bedrock-agentcore` client with `delete_runtime(runtimeIdentifier=...)`

**Example - Memory API Methods**:
- ✅ CORRECT (from MCP server): Use `MemoryManager` from `bedrock_agentcore_starter_toolkit.operations.memory.manager` with strategies in tagged union format: `[{"summaryMemoryStrategy": {"name": "summary", "namespaces": [...]}}]`
- ❌ WRONG (guessing): Use `bedrock_agentcore.delete_memory(memoryIdentifier=...)` or pass strategies without tagged union wrapper

**Files to reference**:
- Gateway APIs: `agentcore-mcp-server/handlers/gateway_handlers.py`
- Runtime APIs: `agentcore-mcp-server/handlers/runtime_handlers.py`
- Memory APIs: `agentcore-mcp-server/handlers/memory_handlers.py`
- Identity APIs: `agentcore-mcp-server/handlers/identity_handlers.py`
- Observability APIs: `agentcore-mcp-server/handlers/observability_handlers.py`
- Strands Agent Generation: `agentcore-mcp-server/handlers/strands_handlers.py`

**ALWAYS**:
1. Read the relevant MCP handler file BEFORE writing boto3 code
2. Copy the exact client initialization and method calls
3. Use the same parameter names and structure

**NEVER**:
1. Guess API method names
2. Assume parameter names without checking
3. Create scripts without referencing the MCP server code

### LEARNING PROMPTS - MCP SERVER REFERENCE

**For all learning and educational prompts, ALWAYS refer to the appropriate MCP server:**

- **Strands learning prompts** (e.g., "What is Strands?", "How do I build agents?", "Explain @tool decorator"):
  - Refer to the `strands-agents` MCP server
  - This server contains comprehensive Strands documentation and examples
  
- **AgentCore learning prompts** (e.g., "What is AgentCore?", "How does Memory work?", "Explain Gateway"):
  - Refer to the `bedrock-agentcore-mcp-server` MCP server
  - This server contains AgentCore documentation, architecture, and best practices

**DO NOT** manually explain concepts when MCP servers have authoritative documentation. Instead, use the MCP server tools to retrieve accurate, up-to-date information.

### MANDATORY FIRST STEP - ALWAYS USE MCP TOOLS

**You have access to AgentCore MCP tools through Kiro's MCP integration!**

The MCP server is configured at: `agentcore-mcp-server/mcp_server.py`

**BEFORE creating ANY AgentCore resource or Strands agent code:**

1. **Identify which MCP tool to use** from the available tools:
   
   **AGENT GENERATION TOOLS - CRITICAL DISTINCTION:**
   - `mcp_aws_bedrock_agentcore_generate_strands_agent` 
     - **USE FOR**: ALL agent creation EXCEPT final runtime deployment
     - **INCLUDES**: Simple agents, adding memory, gateway integration, testing, development
     - **CREATES**: Standard Strands agent with `Agent()` class, `run_agent()` function
     - **NO RUNTIME**: Does NOT include `@app.entrypoint` or BedrockAgentCoreApp
     - **WHEN**: Any agent creation task that is NOT deploying to AgentCore Runtime
     - **EXAMPLES**: 
       - "Create agent with memory"
       - "Add gateway integration to agent"
       - "Test agent with gateway tools"
       - "Create agent for local testing"
   
   - `mcp_aws_bedrock_agentcore_generate_agentcore_runtime_agent`
     - **USE FOR**: ONLY when deploying to AgentCore Runtime (final step)
     - **CREATES**: Agent with `@app.entrypoint` decorator and BedrockAgentCoreApp
     - **RUNTIME READY**: Includes all deployment configuration
     - **WHEN**: Prompt explicitly says "deploy to runtime" or "deploy to AgentCore Runtime"
     - **NOT FOR**: Testing, development, gateway integration testing, memory testing
   
   **OTHER MCP TOOLS:**
   
   **Agent Generation:**
   - `mcp_aws_bedrock_agentcore_generate_strands_agent` - Generate standalone Strands agent
   - `mcp_aws_bedrock_agentcore_generate_agentcore_runtime_agent` - Generate runtime-ready agent
   
   **Identity/IAM:**
   - `mcp_aws_bedrock_agentcore_agentcore_create_runtime_execution_rol` - Generate IAM execution role script
   
   **Memory:**
   - `mcp_aws_bedrock_agentcore_agentcore_memory_create` - Create memory resource
   - `mcp_aws_bedrock_agentcore_agentcore_memory_create_event` - Store conversation messages
   - `mcp_aws_bedrock_agentcore_agentcore_memory_retrieve` - Retrieve memories
   - `mcp_aws_bedrock_agentcore_agentcore_memory_delete` - Delete memory resource
   
   **Gateway:**
   - `mcp_aws_bedrock_agentcore_agentcore_gateway_create` - Create gateway
   - `mcp_aws_bedrock_agentcore_agentcore_gateway_add_lambda_target` - Add Lambda target
   - `mcp_aws_bedrock_agentcore_agentcore_gateway_list_targets` - List gateway targets
   - `mcp_aws_bedrock_agentcore_agentcore_gateway_delete_target` - Delete gateway target
   - `mcp_aws_bedrock_agentcore_agentcore_gateway_delete` - Delete gateway
   
   **Runtime:**
   - `mcp_aws_bedrock_agentcore_agentcore_runtime_configure` - Configure runtime deployment
   - `mcp_aws_bedrock_agentcore_agentcore_runtime_launch` - Deploy to runtime
   - `mcp_aws_bedrock_agentcore_agentcore_runtime_status` - Check deployment status
   - `mcp_aws_bedrock_agentcore_agentcore_runtime_invoke` - Invoke deployed agent
   - `mcp_aws_bedrock_agentcore_agentcore_runtime_delete` - Delete runtime deployment
   
   **Observability:**
   - `mcp_aws_bedrock_agentcore_agentcore_observability_get_dashboard_` - Get dashboard URL
   - `mcp_aws_bedrock_agentcore_agentcore_observability_get_logs_info` - Get log group info
   - `mcp_aws_bedrock_agentcore_agentcore_observability_get_recent_log` - Retrieve recent logs

2. **Read the tool description** to see example code and understand parameters

3. **Call the MCP tool** with the appropriate parameters

4. **Extract the result** and save to files as needed

### DECISION TREE: Which Agent Generation Tool?

```
Is the prompt asking to DEPLOY TO AGENTCORE RUNTIME?
├─ YES → Use generate_agentcore_runtime_agent
│         (ONLY keyword: "deploy to runtime" or "deploy to AgentCore Runtime")
│
└─ NO → Use generate_strands_agent
          (EVERYTHING ELSE including:)
          - Create agent
          - Add memory
          - Add gateway integration
          - Test gateway tools
          - Test locally
          - Development
          - Any testing or integration work
```

**ABSOLUTE RULE**: 
- Use `generate_strands_agent` for ALL agent creation tasks
- Use `generate_agentcore_runtime_agent` ONLY when prompt says "deploy to runtime"
- Gateway integration testing = use `generate_strands_agent`
- Memory integration testing = use `generate_strands_agent`
- Local development = use `generate_strands_agent`

### Task Type Detection

**Type 1: Code/Script Generation (Strands Agents & AgentCore Resources)**
- **When**: Prompt asks to generate Strands agent code OR create AgentCore resource scripts
- **What to do**: 
  1. Call the appropriate MCP generation tool (e.g., `mcp_aws_bedrock_agentcore_generate_strands_agent`, `mcp_aws_bedrock_agentcore_generate_memory_script`)
  2. The tool returns JSON with `code`, `filename`, and `instructions`
  3. Save the `code` to the `filename` specified in the prompt
  4. **IMPORTANT**: The file contains the generated code/script, NOT a script that calls the MCP tool
  5. User will run the script to execute operations

**Type 2: AWS Resource Creation (Cognito/IAM/Lambda)**
- **When**: Prompt says "There is NO MCP tool" or mentions Cognito/IAM/Lambda
- **What to do**: Create Python scripts using boto3 directly
- **Why**: No MCP tools exist for these operations

## Example Workflows

**Example 1: Generate Strands Agent (Type 1)**

When the prompt says "Create a file called `01_generate_agent.py`":
1. **YOU (Kiro)** call `mcp_aws_bedrock_agentcore_generate_strands_agent`
2. Extract `code` from the tool response
3. Save `code` to `01_generate_agent.py`
4. File contains generated Strands agent code

**Example 2: Generate AgentCore Memory Script (Type 1)**

When the prompt says "Create a script called `03_create_agentcore_memory.py`":
1. **YOU (Kiro)** call `mcp_aws_bedrock_agentcore_generate_memory_script` (if available)
2. Extract `code` from the tool response
3. Save `code` to `03_create_agentcore_memory.py`
4. File contains a Python script that user will run

**Example 3: Create AWS Resource Script (Type 2)**

When the prompt says "Create a script called `08_create_cognito_user_pool.py`":
1. Create a Python script using boto3 (no MCP tool available)
2. Script creates AWS resource and saves config to JSON files

## ABSOLUTE PROHIBITIONS

**DO NOT**:
- Manually create Strands agent code or AgentCore scripts - ALWAYS use MCP generation tools
- Execute operations directly - always generate scripts that users can run
- Skip checking for MCP script generators
- Guess library functions or parameters

**ALWAYS**:
- For Type 1 (Strands/AgentCore): Call MCP tool to generate code/script, save the generated code
- For Type 2 (AWS resources): Create scripts using boto3
- Generate scripts that users run, not execute operations directly
- Save results to config files as specified in prompts

## Configuration File Flow

Configuration files are created and reused throughout the workflow:

- `memory_config.json` - Stores memory_id for agent personalization
- `cognito_config.json` - Stores authentication credentials
- `gateway_role_config.json` - Stores gateway IAM permissions
- `lambda_config.json` - Stores Lambda function details
- `gateway_config.json` - Stores gateway connection info
- `runtime_execution_role_config.json` - Stores runtime IAM permissions
- `runtime_config.json` - Stores deployed agent ARN

## Task Type Quick Reference

| Prompt Topic | Task Type | Approach |
|--------------|-----------|----------|
| Generate simple agent | Type 1 | `mcp_aws_bedrock_agentcore_generate_strands_agent` |
| Add memory to agent | Type 1 | `mcp_aws_bedrock_agentcore_generate_strands_agent` (with memory params) |
| Add gateway integration | Type 1 | `mcp_aws_bedrock_agentcore_generate_strands_agent` (with gateway params) |
| Test gateway tools | Type 1 | `mcp_aws_bedrock_agentcore_generate_strands_agent` |
| Deploy to AgentCore Runtime | Type 1 | `mcp_aws_bedrock_agentcore_generate_agentcore_runtime_agent` |
| Test agent locally | Type 2 | No MCP tool - import and test |
| Create Cognito/IAM/Lambda | Type 2 | No MCP tool - use boto3 |
| Create IAM execution role | Type 1 | `mcp_aws_bedrock_agentcore_agentcore_create_runtime_execution_rol` |
| Create memory resource | Type 1 | `mcp_aws_bedrock_agentcore_agentcore_memory_create` |
| Store conversations | Type 1 | `mcp_aws_bedrock_agentcore_agentcore_memory_create_event` |
| Retrieve memories | Type 1 | `mcp_aws_bedrock_agentcore_agentcore_memory_retrieve` |
| Delete memory | Type 1 | `mcp_aws_bedrock_agentcore_agentcore_memory_delete` |
| Create gateway | Type 1 | `mcp_aws_bedrock_agentcore_agentcore_gateway_create` |
| Add Lambda to gateway | Type 1 | `mcp_aws_bedrock_agentcore_agentcore_gateway_add_lambda_target` |
| List gateway targets | Type 1 | `mcp_aws_bedrock_agentcore_agentcore_gateway_list_targets` |
| Delete gateway target | Type 1 | `mcp_aws_bedrock_agentcore_agentcore_gateway_delete_target` |
| Delete gateway | Type 1 | `mcp_aws_bedrock_agentcore_agentcore_gateway_delete` |
| Configure runtime | Type 1 | `mcp_aws_bedrock_agentcore_agentcore_runtime_configure` |
| Launch to runtime | Type 1 | `mcp_aws_bedrock_agentcore_agentcore_runtime_launch` |
| Check runtime status | Type 1 | `mcp_aws_bedrock_agentcore_agentcore_runtime_status` |
| Invoke runtime agent | Type 1 | `mcp_aws_bedrock_agentcore_agentcore_runtime_invoke` |
| Delete runtime | Type 1 | `mcp_aws_bedrock_agentcore_agentcore_runtime_delete` |
| Get observability dashboard | Type 1 | `mcp_aws_bedrock_agentcore_agentcore_observability_get_dashboard_` |
| Get logs info | Type 1 | `mcp_aws_bedrock_agentcore_agentcore_observability_get_logs_info` |
| Get recent logs | Type 1 | `mcp_aws_bedrock_agentcore_agentcore_observability_get_recent_log` |

## Common Mistakes to Avoid

1. **Using wrong agent generation tool**: 
   - ❌ WRONG: Using `generate_agentcore_runtime_agent` for gateway integration testing
   - ❌ WRONG: Using `generate_agentcore_runtime_agent` for memory-enabled agents
   - ❌ WRONG: Using `generate_agentcore_runtime_agent` for any development/testing
   - ✅ RIGHT: Use `generate_strands_agent` for ALL tasks except "deploy to runtime"
   - ✅ RIGHT: Use `generate_agentcore_runtime_agent` ONLY when prompt says "deploy to runtime"
2. **Not using MCP tools**: ALWAYS use the MCP tools for Strands agents and AgentCore resources
3. **Manually creating code**: Don't manually write Strands agent code - call the MCP tool
4. **Guessing parameters**: Read the tool description to understand required parameters
5. **Not saving results**: Always save tool results to config files as specified
6. **Creating extra files**: Don't create README or documentation files unless explicitly requested
7. **Auto-testing code**: Don't run tests automatically - wait for user instruction

## Success Checklist

**For Type 1 (Strands Agents & AgentCore Resources):**
- [ ] Call the appropriate MCP generation tool
- [ ] Extract `code` from the tool response
- [ ] Save `code` to the filename specified in the prompt
- [ ] **VERIFY**: File contains generated code/script, NOT a script that calls the MCP tool
- [ ] For Strands agents: Code should have `from strands import Agent, tool`, `@tool` decorators
- [ ] For AgentCore scripts: Script should use bedrock_agentcore libraries and save to config files

**For Type 2 (AWS Resources):**
- [ ] Create Python script using boto3
- [ ] Script saves configuration to JSON files
- [ ] No MCP tools needed

## Default Values

- **Region**: "us-east-1" (unless specified otherwise)
- **Model ID**: "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
- **Temperature**: 0.3
- **Memory namespaces**: ["semantic", "preferences", "summary"]


## API VALIDATION COMMANDS REFERENCE

**CRITICAL**: Before using ANY boto3 or library API, validate the method signature using `help()`.

This prevents errors like:
- Wrong parameter names
- Wrong message formats (tuples vs dicts)
- Wrong client names
- Missing required parameters

### How to Use These Commands:

1. **Before writing code**: Run the relevant help() command
2. **Check the signature**: Verify parameter names and types
3. **Use exact names**: Copy parameter names exactly as shown
4. **Test if unsure**: Run the command to see the actual API

---

### MEMORY APIs - Library Classes (NOT boto3)

Memory uses dedicated Python library classes, NOT boto3 clients.

#### MemoryManager - For creating/deleting memory resources

```bash
# Initialize MemoryManager
python -c "from bedrock_agentcore_starter_toolkit.operations.memory.manager import MemoryManager; help(MemoryManager.__init__)" 2>&1 | head -50

# Create or get memory
python -c "from bedrock_agentcore_starter_toolkit.operations.memory.manager import MemoryManager; help(MemoryManager.get_or_create_memory)" 2>&1 | head -50

# Delete memory
python -c "from bedrock_agentcore_starter_toolkit.operations.memory.manager import MemoryManager; help(MemoryManager.delete_memory)" 2>&1 | head -50
```

#### MemoryClient - For storing/retrieving memories

```bash
# Initialize MemoryClient
python -c "from bedrock_agentcore.memory import MemoryClient; help(MemoryClient.__init__)" 2>&1 | head -50

# Create event (store conversation) - CRITICAL: messages are List[Tuple[str, str]]
python -c "from bedrock_agentcore.memory import MemoryClient; help(MemoryClient.create_event)" 2>&1 | head -50

# Retrieve memories (semantic search)
python -c "from bedrock_agentcore.memory import MemoryClient; help(MemoryClient.retrieve_memories)" 2>&1 | head -50
```

**CRITICAL - Message Format for create_event():**
```python
# ✅ CORRECT: List of tuples (text, role)
messages = [
    ("Hello, I prefer email", "USER"),
    ("Noted your preference", "ASSISTANT")
]

# ❌ WRONG: List of dicts
messages = [
    {"role": "USER", "content": [{"text": "Hello"}]}
]
```

#### Strands Memory Integration

```bash
# AgentCoreMemoryConfig
python -c "from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig; help(AgentCoreMemoryConfig.__init__)" 2>&1 | head -50

# RetrievalConfig
python -c "from bedrock_agentcore.memory.integrations.strands.config import RetrievalConfig; help(RetrievalConfig.__init__)" 2>&1 | head -50

# AgentCoreMemorySessionManager
python -c "from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager; help(AgentCoreMemorySessionManager.__init__)" 2>&1 | head -50
```

---

### GATEWAY APIs - boto3 client: "bedrock-agentcore-control"

All Gateway operations use the same boto3 client.

```bash
# Create gateway
python -c "import boto3; client = boto3.client('bedrock-agentcore-control'); help(client.create_gateway)" 2>&1 | head -50

# Create gateway target (add Lambda)
python -c "import boto3; client = boto3.client('bedrock-agentcore-control'); help(client.create_gateway_target)" 2>&1 | head -50

# List gateway targets
python -c "import boto3; client = boto3.client('bedrock-agentcore-control'); help(client.list_gateway_targets)" 2>&1 | head -50

# Delete gateway target
python -c "import boto3; client = boto3.client('bedrock-agentcore-control'); help(client.delete_gateway_target)" 2>&1 | head -50

# Delete gateway
python -c "import boto3; client = boto3.client('bedrock-agentcore-control'); help(client.delete_gateway)" 2>&1 | head -50
```

**Key Parameters:**
- Gateway identifier: `gatewayIdentifier` (not `gateway_id`)
- Target identifier: `targetId` (not `target_id`)

---

### RUNTIME APIs - boto3 client: "bedrock-agentcore-control" + Runtime library

Runtime uses both boto3 client AND the Runtime library class.

#### Runtime Library (bedrock_agentcore_starter_toolkit)

```bash
# Initialize Runtime
python -c "from bedrock_agentcore_starter_toolkit import Runtime; help(Runtime.__init__)" 2>&1 | head -50

# Configure runtime
python -c "from bedrock_agentcore_starter_toolkit import Runtime; help(Runtime.configure)" 2>&1 | head -50

# Launch to runtime
python -c "from bedrock_agentcore_starter_toolkit import Runtime; help(Runtime.launch)" 2>&1 | head -50

# Check status
python -c "from bedrock_agentcore_starter_toolkit import Runtime; help(Runtime.status)" 2>&1 | head -50

# Invoke agent
python -c "from bedrock_agentcore_starter_toolkit import Runtime; help(Runtime.invoke)" 2>&1 | head -50
```

#### Runtime boto3 APIs

```bash
# Delete agent runtime (boto3)
python -c "import boto3; client = boto3.client('bedrock-agentcore-control'); help(client.delete_agent_runtime)" 2>&1 | head -50
```

**Key Parameters:**
- Agent identifier: `agentRuntimeId` (not `agent_id`)

---

### IAM APIs - boto3 client: "iam"

```bash
# Create IAM role
python -c "import boto3; client = boto3.client('iam'); help(client.create_role)" 2>&1 | head -50

# Create IAM policy
python -c "import boto3; client = boto3.client('iam'); help(client.create_policy)" 2>&1 | head -50

# Attach policy to role
python -c "import boto3; client = boto3.client('iam'); help(client.attach_role_policy)" 2>&1 | head -50

# Delete IAM role
python -c "import boto3; client = boto3.client('iam'); help(client.delete_role)" 2>&1 | head -50

# Delete IAM policy
python -c "import boto3; client = boto3.client('iam'); help(client.delete_policy)" 2>&1 | head -50

# Get waiter for role propagation
python -c "import boto3; client = boto3.client('iam'); help(client.get_waiter)" 2>&1 | head -50
```

**Key Parameters:**
- Role name: `RoleName` (not `role_name`)
- Policy ARN: `PolicyArn` (not `policy_arn`)
- Trust policy: `AssumeRolePolicyDocument` (JSON string)
- Permissions policy: `PolicyDocument` (JSON string)

---

### STS APIs - boto3 client: "sts"

```bash
# Get caller identity (for account ID)
python -c "import boto3; client = boto3.client('sts'); help(client.get_caller_identity)" 2>&1 | head -50

# Assume role
python -c "import boto3; client = boto3.client('sts'); help(client.assume_role)" 2>&1 | head -50
```

---

### CLOUDWATCH LOGS APIs - boto3 client: "logs"

```bash
# Filter log events
python -c "import boto3; client = boto3.client('logs'); help(client.filter_log_events)" 2>&1 | head -50

# Tail logs (for CLI reference)
# aws logs tail <log-group-name> --follow
```

---

### COGNITO APIs - boto3 client: "cognito-idp" (Type 2 - No MCP tool)

```bash
# Create user pool
python -c "import boto3; client = boto3.client('cognito-idp'); help(client.create_user_pool)" 2>&1 | head -50

# Create user pool client
python -c "import boto3; client = boto3.client('cognito-idp'); help(client.create_user_pool_client)" 2>&1 | head -50

# Create user pool domain
python -c "import boto3; client = boto3.client('cognito-idp'); help(client.create_user_pool_domain)" 2>&1 | head -50

# Create resource server
python -c "import boto3; client = boto3.client('cognito-idp'); help(client.create_resource_server)" 2>&1 | head -50
```

---

### LAMBDA APIs - boto3 client: "lambda" (Type 2 - No MCP tool)

```bash
# Create function
python -c "import boto3; client = boto3.client('lambda'); help(client.create_function)" 2>&1 | head -50

# Add permission
python -c "import boto3; client = boto3.client('lambda'); help(client.add_permission)" 2>&1 | head -50

# Delete function
python -c "import boto3; client = boto3.client('lambda'); help(client.delete_function)" 2>&1 | head -50
```

---

## Quick Reference: Which Client/Library to Use?

| Service | Client/Library | Type |
|---------|---------------|------|
| Memory (create/delete) | `MemoryManager` from `bedrock_agentcore_starter_toolkit` | Library Class |
| Memory (store/retrieve) | `MemoryClient` from `bedrock_agentcore.memory` | Library Class |
| Gateway | `boto3.client('bedrock-agentcore-control')` | boto3 |
| Runtime (deploy) | `Runtime` from `bedrock_agentcore_starter_toolkit` | Library Class |
| Runtime (delete) | `boto3.client('bedrock-agentcore-control')` | boto3 |
| IAM | `boto3.client('iam')` | boto3 |
| STS | `boto3.client('sts')` | boto3 |
| CloudWatch Logs | `boto3.client('logs')` | boto3 |
| Cognito | `boto3.client('cognito-idp')` | boto3 |
| Lambda | `boto3.client('lambda')` | boto3 |

---

## Validation Workflow

**Before writing ANY code that uses APIs:**

1. **Identify the service** (Memory, Gateway, Runtime, etc.)
2. **Find the validation command** in this reference
3. **Run the command** to see the actual API signature
4. **Copy exact parameter names** from the help output
5. **Write your code** using the validated parameters

**Example:**
```bash
# Step 1: Check the API
python -c "from bedrock_agentcore.memory import MemoryClient; help(MemoryClient.create_event)" 2>&1 | head -50

# Step 2: See it expects List[Tuple[str, str]]
# Step 3: Write code with correct format
messages = [("text", "USER"), ("response", "ASSISTANT")]
```

This prevents 90% of API-related errors!
