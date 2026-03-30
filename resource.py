import requests
from config import settings
def get_answers(query:str)->str:
    url = settings.RAG_ENDPOINT
    params = {
    "message": query
    # "session_id": "optional-existing-session-id"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        print("Session ID:", data["session_id"])
        return data["response"]
    else:
        return ("Error:", response.status_code, response.text)
        