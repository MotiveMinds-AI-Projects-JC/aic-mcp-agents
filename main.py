# Import FastMCP framework
# FastMCP helps you expose functions ("tools") that can be called by AI agents
from fastmcp import FastMCP

# OS module to access environment variables (like PORT)
import os

# Import your custom agent logic
# This is likely where your core business logic or orchestration happens
from agent import agent

# Import function that calls RAG (Retrieval-Augmented Generation) system
from resource import get_answers

# Import function that performs GL (General Ledger) prediction using ML model
from tools import predict_gl


# -------------------------
# INITIALIZE MCP SERVER
# -------------------------
# Create an MCP server instance
# Name "Pegged-Requirements-Tool" identifies this service
mcp = FastMCP("Pegged-Requirements-Tool")


# -------------------------
# TOOL 1: ECHO / MAIN AGENT TOOL
# -------------------------
@mcp.tool()
def echo(query: str) -> str:
    """
    Tool exposed via MCP.

    Purpose:
    - Takes a user query
    - Passes it to your custom agent
    - Returns processed result

    Likely use case:
    - Handles queries like:
        * Planned Order lookup
        * Purchase Requisition lookup
        * MRP-related queries
    """

    # Call your agent function with user query
    result = agent(query)

    # Return formatted result
    return f"Result: {result}"


# -------------------------
# TOOL 2: COMPANY POLICIES (RAG)
# -------------------------
@mcp.tool()
def get_company_policies(query: str) -> str:
    """
    Tool to query company policies using RAG system.

    RAG = Retrieval-Augmented Generation
    (combines knowledge base + AI model)

    What happens:
    1. Sends query to external RAG API
    2. Retrieves context-aware answer
    3. Returns full response
    """

    # Call RAG API function
    result = get_answers(query)

    # Return response from RAG system
    return result


# -------------------------
# TOOL 3: GL PREDICTION
# -------------------------
@mcp.tool()
def get_gl_prediction(
    Company_Code: str,
    Document_Number: str,
    Fiscal_Year: str,
    LineItem: str,
    AccountType: str,
    Amount: str,
    Vendor: str,
    DocumentType: str,
    PostingDate: str,
    TaxCode: str
):
    """
    Tool to predict General Ledger (GL) account.

    This uses a machine learning model (DAR service).

    Inputs:
    - Financial document details (SAP fields)

    Output:
    - Predicted GL account(s)
    """

    # Call prediction function with all required inputs
    results = predict_gl(
        Company_Code,
        Document_Number,
        Fiscal_Year,
        LineItem,
        AccountType,
        Amount,
        Vendor,
        DocumentType,
        PostingDate,
        TaxCode
    )

    # Return prediction results
    return results


# -------------------------
# SERVER CONFIGURATION
# -------------------------
# Get port number from environment variable
# If not set, default to 8000
port = int(os.getenv("PORT", 8000))


# -------------------------
# APPLICATION ENTRY POINT
# -------------------------
# This block runs only when you execute this file directly
# (not when imported as a module)
if __name__ == "__main__":

    # Start the MCP server
    # transport="http" → exposes tools over HTTP
    # host="0.0.0.0" → makes server accessible from any network interface
    # port=port → uses configured port
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port
    )