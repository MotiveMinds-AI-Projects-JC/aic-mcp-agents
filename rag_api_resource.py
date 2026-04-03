# Import requests library to make HTTP calls (API requests)
import requests

# Import application settings (contains RAG endpoint URL and other configs)
from config import settings


# -------------------------
# FUNCTION: GET ANSWERS FROM RAG SYSTEM
# -------------------------
def get_answers_using_rag(query: str) -> str:
    """
    Send a user query to a RAG (Retrieval-Augmented Generation) API
    and return the generated response.

    What this function does:
    1. Sends the user's question to the RAG endpoint
    2. Receives a response (usually from an LLM + knowledge base)
    3. Extracts and returns the answer

    Input:
        query (str): User's question or message

    Output:
        str: Response from the RAG system OR error message
    """

    # Get the RAG API endpoint URL from settings
    url = settings.RAG_ENDPOINT

    # -------------------------
    # QUERY PARAMETERS
    # -------------------------
    # These parameters are sent in the URL as:
    # ?message=your_query
    params = {
        "message": query
        # Optional: session_id can be used to maintain conversation context
        # "session_id": "optional-existing-session-id"
    }

    # -------------------------
    # SEND API REQUEST
    # -------------------------
    # This makes a GET request to the RAG API
    # Example: GET /endpoint?message=Hello
    response = requests.get(url, params=params)

    # -------------------------
    # HANDLE SUCCESS RESPONSE
    # -------------------------
    # HTTP status code 200 means "OK"
    if response.status_code == 200:

        # Convert JSON response into Python dictionary
        data = response.json()

        # Print session ID (useful for tracking conversations/debugging)
        print("Session ID:", data["session_id"])

        # Return only the generated response text
        return data["response"]

    # -------------------------
    # HANDLE ERROR RESPONSE
    # -------------------------
    else:
        # If request failed, return error details
        # Includes:
        # - status code (e.g., 404, 500)
        # - error message from server
        return ("Error:", response.status_code, response.text)
