from fastmcp import FastMCP
import os
from agent import agent
from resource import get_answers
from tools import predict_gl

mcp = FastMCP("Pegged-Requirements-Tool")

@mcp.tool()
def echo(query: str) -> str:
    """Get Pegged Requirements for Planned Order, Purchase Order or MRPDetails(Material, Area and Plant)"""
    result = agent(query)
    return f"Result: {result}"

@mcp.tool()
def get_company_policies(query: str) -> str:
    """Calls external RAG chat endpoint and returns full response"""

    result = get_answers(query)

    return result

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
    """Predict G/L Ledger to use"""

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


    return results

port = int(os.getenv("PORT", 8000))

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=port)
