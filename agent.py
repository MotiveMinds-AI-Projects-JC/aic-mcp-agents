# -------------------------
# IMPORTS
# -------------------------
# Import MRP-related tools for fetching data from SAP
from tools import get_mrp_plannedorder, get_mrp_purchaserequisition, get_pegged_requirements_for_mrp2

# Import utility to create a Deep Agent that orchestrates tools + LLM
from deepagents import create_deep_agent

# Import helper to initialize LLMs via Gen AI Hub
from gen_ai_hub.proxy.langchain.init_models import init_llm

# Import proxy client utilities (used to connect to Gen AI Hub)
from gen_ai_hub.proxy.core.proxy_clients import get_proxy_client, set_proxy_version


# -------------------------
# CONFIGURE GEN AI HUB PROXY
# -------------------------
# Set the proxy version for Gen AI Hub connection
set_proxy_version('gen-ai-hub')

# Get a proxy client instance to connect to Gen AI Hub
proxy_client = get_proxy_client('gen-ai-hub')


# -------------------------
# SYSTEM PROMPT / AGENT INSTRUCTION
# -------------------------
# This is the “brain instructions” for the deep agent
# It tells the AI how to handle SAP Pegged Requirements queries
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
# max_tokens=2000 ensures enough space for the model to output the table
llm = init_llm(
    'gpt-4o',
    proxy_client=proxy_client,
    max_tokens=2000
)


# -------------------------
# FUNCTION: AGENT ORCHESTRATOR
# -------------------------
def agent(query: str) -> str:
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

    Output:
        str - Markdown table with Pegged Requirements
    """

    # -------------------------
    # CREATE DEEP AGENT
    # -------------------------
    # Combines LLM + tools + system prompt
    # Tools list defines which functions LLM can call
    agent = create_deep_agent(
        model=llm,
        system_prompt=agent_instruction,
        tools=[get_mrp_plannedorder, get_mrp_purchaserequisition, get_pegged_requirements_for_mrp2]
    )

    # -------------------------
    # INVOKE AGENT
    # -------------------------
    # Send user query to the agent
    # Input format mimics a chat message structure
    result = agent.invoke({
        "messages": [{"role": "user", "content": f"{query}"}]
    })

    # -------------------------
    # EXTRACT FINAL RESPONSE
    # -------------------------
    # The response is stored in the last message returned by the agent
    return result["messages"][-1].content