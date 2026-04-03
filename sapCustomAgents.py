# Import MRP-related tools for fetching data from SAP
# These are custom wrappers around SAP APIs (e.g., OData, RFC, or RAP services)
# Each function encapsulates a specific business object retrieval logic
from tools import (
    get_mrp_plannedorder,
    get_mrp_purchaserequisition,
    get_pegged_requirements_for_mrp2,
)

# Import utility to create a Deep Agent that orchestrates tools + LLM
# This abstraction handles tool-calling, reasoning, and execution loop internally
# Think of this as a lightweight agent framework similar to LangGraph / ReAct pattern
from deepagents import create_deep_agent

# Import helper to initialize LLMs via Gen AI Hub
# This abstracts away authentication, endpoint configuration, and model selection
from gen_ai_hub.proxy.langchain.init_models import init_llm

# Import proxy client utilities (used to connect to Gen AI Hub)
# These handle routing requests via SAP Gen AI Hub instead of direct OpenAI endpoints
from gen_ai_hub.proxy.core.proxy_clients import get_proxy_client, set_proxy_version


# -------------------------
# CONFIGURE GEN AI HUB PROXY
# -------------------------
# Set the proxy version for Gen AI Hub connection
# This ensures compatibility with the expected API contract/version exposed by SAP BTP
# Important in enterprise setups where multiple proxy versions may coexist
set_proxy_version("gen-ai-hub")

# Get a proxy client instance to connect to Gen AI Hub
# This client acts as the gateway for all LLM calls, handling:
# - Authentication (OAuth/service bindings)
# - Routing via SAP BTP
# - Logging/monitoring hooks (if enabled)
proxy_client = get_proxy_client("gen-ai-hub")


# -------------------------
# SYSTEM PROMPT / AGENT INSTRUCTION
# -------------------------
# This is the “brain instructions” for the deep agent
# It defines:
# - Intent classification logic (PO vs PR vs MRP input)
# - Tool selection strategy
# - Output formatting contract (strict Markdown table)
#
# In agent design terms, this is effectively:
# - Policy definition
# - Output schema enforcement (soft constraint via prompt)
#
# Note: Any ambiguity here directly impacts tool selection accuracy
agent_instruction = """\
You are an SAP Pegged Requirements Assistant.

## Objective

Retrieve Pegged Requirements based on user input and return the result strictly in the required Markdown table format.

## Instructions

### Step 1: Analyze User Input

Determine the type of input provided by the user:

* If the input is a **Planned Order (PO)** number
* If the input is a **Purchase Requisition (PR)** number
* If the input contains **MRP Details** (Material, Area, and Plant)

### Step 2: Select the Appropriate Tool

* If a **Planned Order (PO)** is provided, use:
  `get_mrp_plannedorder`

* If a **Purchase Requisition (PR)** is provided, use:
  `get_mrp_purchaserequisition`

* If **MRP Details (Material, Area, and Plant)** are provided, use:
  `get_pegged_requirements_for_mrp`

### Step 3: Process Tool Output

Convert the tool response into the following Markdown table format.

## Required Output Format

| Material | PR_PlannedOrder | Assembly | AssemblyPR_PlannedOrder |
| -------- | --------------- | -------- | ----------------------- |
|    |         |     |             |

## Important Rules

* Always return the final answer in Markdown table format.
* Do not include explanations.
* Do not modify column names.
* Ensure accurate mapping of tool output fields to the table columns.
* If multiple records are returned, include all records in the table.
"""


# -------------------------
# INITIALIZE LARGE LANGUAGE MODEL
# -------------------------
# Initialize GPT-4o model via Gen AI Hub proxy
# Key considerations:
# - Model is accessed via SAP BTP Gen AI Hub (not direct OpenAI)
# - Ensures enterprise compliance, auditability, and governance
#
# max_tokens=2000 ensures enough space for the model to output the table
# especially important when multiple pegged requirement records are returned
llm = init_llm("gpt-4o", proxy_client=proxy_client, max_tokens=2000)


# -------------------------
# FUNCTION: AGENT ORCHESTRATOR
# -------------------------
def sap_pegged_requirement_agent(query: str) -> str:
    """
    Deep agent orchestrator for SAP Pegged Requirements.

    Steps performed:
    1. Creates a deep agent connecting the LLM and the MRP tools
    2. Uses system_prompt to instruct LLM on how to handle queries
    3. Chooses the correct tool based on input (PO, PR, or MRP details)
    4. Invokes the agent with the user query
    5. Returns the final answer (Markdown table format) as string

    Input:
        query (str) - User question or SAP reference
        # Example:
        #   "Show pegged requirements for PO 123456"
        #   "Get details for PR 987654"
        #   "Material=MAT1, Plant=1000, Area=A1"

    Output:
        str - Markdown table with Pegged Requirements
        # Strictly formatted as per system prompt contract
    """

    # -------------------------
    # CREATE DEEP AGENT
    # -------------------------
    # Combines LLM + tools + system prompt
    #
    # Internally, this likely sets up:
    # - Tool schema exposure (function signatures → JSON schema)
    # - Reasoning loop (LLM decides → tool call → result → LLM refinement)
    # - Message state management
    #
    # Tools list defines which functions LLM can call
    # IMPORTANT OBSERVATION:
    # The prompt refers to `get_pegged_requirements_for_mrp`
    # but the actual tool registered is `get_pegged_requirements_for_mrp2`
    # This mismatch may cause:
    # - Incorrect tool selection
    # - Hallucinated tool calls
    agent = create_deep_agent(
        model=llm,
        system_prompt=agent_instruction,
        tools=[
            get_mrp_plannedorder,
            get_mrp_purchaserequisition,
            get_pegged_requirements_for_mrp2,
        ],
    )

    # -------------------------
    # INVOKE AGENT
    # -------------------------
    # Send user query to the agent
    #
    # Input format mimics a chat message structure:
    # - "messages" is a conversation history array
    # - Each message has role (user/system/assistant) and content
    #
    # This design aligns with:
    # - OpenAI ChatCompletion schema
    # - LangChain message abstraction
    #
    # f-string ensures query is safely embedded as string
    result = agent.invoke({"messages": [{"role": "user", "content": f"{query}"}]})

    # -------------------------
    # EXTRACT FINAL RESPONSE
    # -------------------------
    # The agent returns a structured response containing full message history
    #
    # result["messages"] typically looks like:
    # [
    #   {role: "user", content: "..."},
    #   {role: "assistant", content: "...", tool_calls: [...]},
    #   {role: "tool", content: "..."},
    #   {role: "assistant", content: "FINAL ANSWER"}
    # ]
    #
    # We extract the last message assuming:
    # - The final assistant message contains the formatted Markdown table
    #
    # Potential risk:
    # - If agent fails or stops early, last message may not be final answer
    return result["messages"][-1].content
