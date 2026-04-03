# Import the requests library to make HTTP API calls
# This is used for direct REST/OData calls to SAP S/4HANA or custom services
# Note: In SAP BTP production setups, you may prefer a destination-based HTTP client instead
import requests

# Load environment variables from a .env file (used in local development)
# Typically used outside Cloud Foundry (CF), since CF provides env vars via VCAP_SERVICES
from dotenv import load_dotenv

# JSON module to convert between JSON strings and Python dictionaries
# Required because SAP APIs return JSON payloads as strings
import json

# Import application settings (configured in your config.py)
# This wraps environment variables and CF service bindings
from config import settings

# This is SAP AI Core / DAR SDK for inference
# DAR = Data Attribute Recommendation (used for classification/prediction scenarios)
# This is required for GL Prediction Tool
from sap.aibus.dar.client.inference_client import InferenceClient


# -------------------------
# DEFAULT MRP DICTIONARY TEMPLATE
# -------------------------
# This is just a sample structure (not actively used later in code)
# Acts as a reference schema for expected MRP fields
# Could be useful for validation or type hinting in a stricter design
mrp_dict = {
    "Material": "",
    "Area": "",
    "Plant": "",
    "Planned_Order": "",
    "Purchase_Requisition": "",
}


# -------------------------
# LOAD BASE CONFIG VALUES
# -------------------------
# These values come from your Settings class (env variables or CF)
# In SAP BTP:
# - BASE_URL likely points to an API endpoint exposed via API Management or CAP service
# - USER/PASSWORD suggests Basic Auth (less preferred vs OAuth in enterprise setups)
BASE_URL = settings.BASE_URL
USER = settings.USER
PASSWORD = settings.PASSWORD


# -------------------------
# TOOL: GET MRP DATA FOR PLANNED ORDER
# -------------------------
def get_mrp_plannedorder(planned_order: str) -> dict:
    """
    Fetch MRP (Material Requirements Planning) details
    for a given Planned Order.

    Steps:
    1. Call SAP API for planned order
    2. Extract Material, Plant, Area
    3. Pass values to pegged requirements API
    """

    # Construct API URL dynamically using planned order
    # This follows SAP A2X service pattern (srvd_a2x)
    # Endpoint suggests a standard S/4HANA Cloud API for Planned Orders
    URL = (
        BASE_URL
        + f"api_plannedorder/srvd_a2x/sap/plannedorder/0001/PlannedOrderHeader/{planned_order}"
    )

    # Send GET request with basic authentication
    # In production:
    # - Consider retry logic
    # - Add timeout
    # - Use destination service instead of raw credentials
    response = requests.get(url=URL, auth=(USER, PASSWORD))

    # Convert response from bytes → string
    # SAP APIs typically return UTF-8 encoded JSON
    data_str = response.content.decode("utf-8")

    # Convert JSON string → Python dictionary
    # No validation here → assumes response is always valid JSON
    data = json.loads(data_str)

    # Extract relevant fields into dictionary
    # Using .get() avoids KeyError but silently returns None if field missing
    mrp_dict = {
        "Material": data.get("Material"),
        "Area": data.get("MRPArea"),
        "Plant": data.get("MRPPlant"),
        "PO/PR": planned_order,
    }

    # Call another function to get pegged requirements
    # This creates a chained API call pattern:
    # Planned Order → derive MRP context → fetch pegged requirements
    return get_pegged_requirements_for_mrp2(
        mrp_dict["Material"], mrp_dict["Plant"], mrp_dict["Area"], mrp_dict["PO/PR"]
    )


# -------------------------
# TOOL: GET MRP DATA FOR PURCHASE REQUISITION
# -------------------------
def get_mrp_purchaserequisition(purchase_req: str) -> dict:
    """
    Fetch MRP data for a Purchase Requisition.

    Steps:
    1. Call SAP API for purchase requisition
    2. Extract relevant fields
    3. Call pegged requirements API
    """

    # Construct API URL
    # Note: This endpoint fetches Purchase Requisition items (not header)
    # "_PurchaseRequisitionItem" indicates navigation to item-level entity
    URL = (
        BASE_URL
        + f"api_purchaserequisition_2/srvd_a2x/sap/purchaserequisition/0001/PurchaseReqn/{purchase_req}/_PurchaseRequisitionItem"
    )

    # Send API request
    response = requests.get(url=URL, auth=(USER, PASSWORD))

    # Decode response
    data_str = response.content.decode("utf-8")

    # Convert JSON → dictionary
    data = json.loads(data_str)

    # Print full response (useful for debugging)
    # Not suitable for production (may expose sensitive data in logs)
    print(data)

    # Extract required values
    # POTENTIAL ISSUE:
    # API likely returns a list of items, but code assumes a flat structure
    mrp_dict = {
        "Material": data.get("Material"),
        "Area": data.get("CompanyCode"),  # Using CompanyCode as MRP Area surrogate
        "Plant": data.get("Plant"),
        "PO/PR": purchase_req,
    }

    # Call pegged requirements function
    return get_pegged_requirements_for_mrp2(
        mrp_dict["Material"], mrp_dict["Plant"], mrp_dict["Area"], mrp_dict["PO/PR"]
    )


# -------------------------
# TOOL: GET PEGGED REQUIREMENTS (WITH PR/PO)
# -------------------------
def get_pegged_requirements_for_mrp2(
    Material: str, Plant: str, Area: str, PR: str = "XXXXXXXXXX"
):
    """
    Fetch pegged requirements for a material.

    Pegged requirements = dependencies between supply and demand.

    Inputs:
    - Material
    - Plant
    - Area (MRP Area)
    - PR (Planned Order or Purchase Req)
    """

    # Construct API URL with query parameters
    # This uses SAP function import style (GET with parameters encoded in URL)
    # %27 represents URL-encoded single quote (')
    URL = (
        BASE_URL
        + f"zmm_sb_joule_pegged/srvd_a2x/sap/zmm_sd_joule_pegged/0001/ZMM_C_PEGGED_USE_CASE/SAP__self.getpeggedrequirements(Material=%27{Material}%27,MRPArea=%27{Area}%27,MRPPlant=%27{Plant}%27,PlannedOrder=%27{PR}%27)"
    )

    # Send request
    response = requests.get(url=URL, auth=(USER, PASSWORD))

    # Decode response
    data_str = response.content.decode("utf-8")

    # Print HTTP status code (debugging)
    # Useful during development but should be replaced with structured logging
    print(response.status_code)

    # Convert JSON → dictionary
    data = json.loads(data_str)

    # Extract only the "value" field from response
    # SAP OData responses typically wrap actual data under "value"
    data = data["value"]

    return data


# -------------------------
# TOOL: GET PEGGED REQUIREMENTS (WITHOUT PR/PO)
# -------------------------
def get_pegged_requirements_for_mrp(Material: str, Plant: str, Area: str):
    """
    Same as above function but without passing a Planned Order / PR.
    Uses a dummy placeholder value.
    """

    # Same API as above, but PlannedOrder parameter is hardcoded
    # This allows querying pegged requirements purely by MRP context
    URL = (
        BASE_URL
        + f"zmm_sb_joule_pegged/srvd_a2x/sap/zmm_sd_joule_pegged/0001/ZMM_C_PEGGED_USE_CASE/SAP__self.getpeggedrequirements(Material=%27{Material}%27,MRPArea=%27{Area}%27,MRPPlant=%27{Plant}%27,PlannedOrder=%27XXXXXXXXXX%27)"
    )

    response = requests.get(url=URL, auth=(USER, PASSWORD))

    data_str = response.content.decode("utf-8")

    data = json.loads(data_str)

    data = data["value"]

    return data


# -------------------------
# SAMPLE TEST CALLS (COMMENTED)
# -------------------------
# These are quick manual tests for local debugging
# In real projects, replace with unit tests or Postman collections
# print(get_mrp_plannedorder("400000285"))
# print(get_mrp_purchaserequisition("3000001516"))
# print(get_pegged_requirements_for_mrp2("KKR001", '1810',"1810"))


# -------------------------
# TOOL: PREDICT GL ACCOUNT
# -------------------------
def predict_gl(
    Company_Code: str,
    Document_Number: str,
    Fiscal_Year: str,
    LineItem: str,
    AccountType: str,
    Amount: str,
    Vendor: str,
    DocumentType: str,
    PostingDate: str,
    TaxCode: str,
):
    """
    Calls SAP DAR (Data Attribute Recommendation) model
    to predict GL account.

    Input:
    - Financial document fields

    Output:
    - Predicted GL account(s)
    """

    # Deployment URL of ML model
    # This is typically obtained from SAP AI Core deployment
    DEPLOYMENT_URL = settings.DAR_DEPLOYMENT_URL

    # Authentication credentials
    # These are used to fetch OAuth token from SAP AI Core / XSUAA
    url = settings.DAR_BASE_URL
    client_id = settings.DAR_CLIENT_ID
    client_secret = settings.DAR_CLIENT_SECRET
    auth_url = settings.DAR_AUTH_URL

    # Create inference client using credentials
    # This abstracts:
    # - Token retrieval
    # - Request signing
    # - Endpoint communication
    inference_client = InferenceClient.construct_from_credentials(
        dar_url=url,
        clientid=client_id,
        clientsecret=client_secret,
        uaa_url=auth_url,
    )

    # Prepare input data in required format
    # DAR expects:
    # - objectId (identifier)
    # - features (name-value pairs)
    #
    # Mapping SAP fields (BUKRS, BELNR, etc.) aligns with FI document structure
    objects_to_be_classified = [
        {
            "objectId": "optional-identifier-1",
            "features": [
                {"name": "BUKRS", "value": Company_Code},  # Company Code
                {"name": "BELNR", "value": Document_Number},  # Document Number
                {"name": "GJAHR", "value": Fiscal_Year},  # Fiscal Year
                {"name": "BUZEI", "value": LineItem},  # Line Item
                {"name": "KOART", "value": AccountType},  # Account Type
                {"name": "WRBTR", "value": Amount},  # Amount
                {"name": "LIFNR", "value": Vendor},  # Vendor
                {"name": "BLART", "value": DocumentType},  # Document Type
                {"name": "BUDAT", "value": PostingDate},  # Posting Date
                {"name": "MWSKZ", "value": TaxCode},  # Tax Code
            ],
        }
    ]

    # Send inference request to model
    # top_n=3 returns top 3 predicted GL accounts with confidence scores
    inference_response = inference_client.create_inference_request_with_url(
        url=DEPLOYMENT_URL, objects=objects_to_be_classified, top_n=3
    )

    # Extract predictions safely
    # Defensive pattern but incomplete (see note below)
    if inference_response.get("predictions"):
        labels = inference_response["predictions"][0].get("labels", [])

    if labels:
        results = labels[0].get("results", [])

    # Returns list of predicted GL accounts
    return results
