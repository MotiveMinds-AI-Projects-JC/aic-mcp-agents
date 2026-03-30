import requests
from dotenv import load_dotenv
import json
from config import settings

mrp_dict = {
    "Material" : "",
    "Area" : "",
    "Plant" : "",
    "Planned_Order" : "",
    "Purchase_Requisition" : ""
}

BASE_URL = settings.BASE_URL
USER = settings.USER
PASSWORD = settings.PASSWORD

def get_mrp_plannedorder(planned_order:str) ->dict:
    """Get Pegged Requirements PlannedOrder"""
    URL = BASE_URL + f"api_plannedorder/srvd_a2x/sap/plannedorder/0001/PlannedOrderHeader/{planned_order}"
    response  = requests.get(url=URL, auth=(USER,PASSWORD))
    # Decode bytes to string
    data_str = response.content.decode("utf-8")

    # Convert JSON string to dictionary
    data = json.loads(data_str)

    mrp_dict = {
    "Material" : data.get("Material"),
    "Area" : data.get("MRPArea"),
    "Plant" : data.get("MRPPlant"),
    "PO/PR" : planned_order,
    }

    return get_pegged_requirements_for_mrp2(mrp_dict['Material'],mrp_dict['Plant'],mrp_dict['Area'],mrp_dict['PO/PR'])

def get_mrp_purchaserequisition(purchase_req: str)-> dict:
    """Get Pegged Requirements for Purchase Requisition"""
    URL = BASE_URL + f"api_purchaserequisition_2/srvd_a2x/sap/purchaserequisition/0001/PurchaseReqn/{purchase_req}/_PurchaseRequisitionItem"
    response  = requests.get(url=URL, auth=(USER,PASSWORD))
    # Decode bytes to string
    data_str = response.content.decode("utf-8")

    # Convert JSON string to dictionary
    data = json.loads(data_str)
    print(data)

    mrp_dict = {
    "Material" : data.get("Material"),
    "Area" : data.get("CompanyCode"),
    "Plant" : data.get("Plant"),
    "PO/PR" : purchase_req,
    }

    return get_pegged_requirements_for_mrp2(mrp_dict['Material'],mrp_dict['Plant'],mrp_dict['Area'],mrp_dict['PO/PR'])

    # return mrp_dict
    # Getinng Pegged Requirements

def get_pegged_requirements_for_mrp2(Material: str, Plant: str, Area: str, PR: str = 'XXXXXXXXXX'):
    """Get Pegged Requirements for MRP (Material , Area , Plant)"""
    URL = BASE_URL + f"zmm_sb_joule_pegged/srvd_a2x/sap/zmm_sd_joule_pegged/0001/ZMM_C_PEGGED_USE_CASE/SAP__self.getpeggedrequirements(Material=%27{Material}%27,MRPArea=%27{Area}%27,MRPPlant=%27{Plant}%27,PlannedOrder=%27{PR}%27)"
    response  = requests.get(url=URL, auth=(USER,PASSWORD))

    data_str = response.content.decode("utf-8")
    print(response.status_code)

    # Convert JSON string to dictionary
    data = json.loads(data_str)
    data = data["value"]

    return(data)

def get_pegged_requirements_for_mrp(Material: str, Plant: str, Area: str):
    """Get Pegged Requirements for MRP (Material , Area , Plant)"""
    URL = BASE_URL + f"zmm_sb_joule_pegged/srvd_a2x/sap/zmm_sd_joule_pegged/0001/ZMM_C_PEGGED_USE_CASE/SAP__self.getpeggedrequirements(Material=%27{Material}%27,MRPArea=%27{Area}%27,MRPPlant=%27{Plant}%27,PlannedOrder=%27XXXXXXXXXX%27)"
    response  = requests.get(url=URL, auth=(USER,PASSWORD))

    data_str = response.content.decode("utf-8")

    # Convert JSON string to dictionary
    data = json.loads(data_str)
    data = data["value"]

    return(data)

# print(get_mrp_plannedorder("400000285"))
# print(get_mrp_purchaserequisition("3000001516"))
# print(get_pegged_requirements_for_mrp2("KKR001", '1810',"1810"))

from sap.aibus.dar.client.inference_client import InferenceClient

def predict_gl(Company_Code:str,Document_Number: str, Fiscal_Year:str, LineItem:str, AccountType:str, Amount:str, Vendor:str,DocumentType:str,PostingDate:str,TaxCode:str ):
    # Replace the deployment URL with your model's URL
    DEPLOYMENT_URL = settings.DAR_DEPLOYMENT_URL

    # Extract the credentials
    url = settings.DAR_BASE_URL
    client_id = settings.DAR_CLIENT_ID
    client_secret = settings.DAR_CLIENT_SECRET
    auth_url = settings.DAR_AUTH_URL

    inference_client = InferenceClient.construct_from_credentials(
        dar_url=url,
        clientid=client_id,
        clientsecret=client_secret,
        uaa_url=auth_url,
    )

    objects_to_be_classified = [
    {
        "objectId": "optional-identifier-1",
        "features": [
            {"name": "BUKRS", "value": Company_Code},
            {"name": "BELNR", "value": Document_Number},
            {"name": "GJAHR", "value": Fiscal_Year},
            {"name": "BUZEI", "value": LineItem},
            {"name": "KOART" , "value": AccountType},
            {"name":"WRBTR","value":Amount},
            {"name":"LIFNR","value":Vendor},
            {"name":"BLART","value":DocumentType},
            {"name":"BUDAT","value":PostingDate},
            {"name":"MWSKZ","value":TaxCode}
         ]
    }
    ]

    inference_response = inference_client.create_inference_request_with_url(
    url=DEPLOYMENT_URL,
    objects=objects_to_be_classified,
    top_n=3
)

    if inference_response.get('predictions'):
        labels = inference_response['predictions'][0].get('labels', [])
    if labels:
        results = labels[0].get('results', [])

    return(results)





    