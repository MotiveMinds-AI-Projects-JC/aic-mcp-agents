# OS module for environment variable access
import os

# Pydantic settings for structured configuration management
# This helps us define configuration variables in a clean, validated way
from pydantic_settings import BaseSettings, SettingsConfigDict

# Cloud Foundry environment utility
# Used to read service bindings when app runs in Cloud Foundry
from cfenv import AppEnv


# -------------------------
# SETTINGS CLASS
# -------------------------
class Settings(BaseSettings):
    """
    Application configuration class using Pydantic.

    What this class does:
    - Automatically reads values from environment variables
    - Can also read from a `.env` file (useful for local development)
    - Validates types (e.g., ensures strings, booleans, etc.)
    - Provides default values where needed
    """

    # -------------------------
    # DAR Service (Data Attribute Recommendation System)
    # -------------------------
    # These values are expected to come from environment variables
    DAR_DEPLOYMENT_URL: str
    DAR_BASE_URL: str
    DAR_CLIENT_ID: str
    DAR_CLIENT_SECRET: str
    DAR_AUTH_URL: str

    # -------------------------
    # RAG Endpoint
    # -------------------------
    RAG_ENDPOINT: str

    # -------------------------
    # S/4HANA Credentials
    # -------------------------
    BASE_URL: str
    USER: str
    PASSWORD: str

    # Debug flag (True by default for local development)
    DEBUG: bool = True

    # -------------------------
    # PYDANTIC CONFIGURATION
    # -------------------------
    # This tells Pydantic to load variables from a `.env` file
    model_config = SettingsConfigDict(
        env_file=".env",            # File to load environment variables from
        env_file_encoding="utf-8"   # Encoding format of the file
    )


# -------------------------
# LOAD SETTINGS FUNCTION
# -------------------------
def get_settings() -> Settings:
    """
    Load application settings based on the environment.

    This function decides:
    - If running in Cloud Foundry → load from service bindings
    - Else → load from local `.env` file

    Returns:
        Settings: Fully initialized configuration object
    """

    # Check if app is running in Cloud Foundry
    # Cloud Foundry automatically sets this environment variable
    is_cf = 'VCAP_SERVICES' in os.environ


    # -------------------------
    # CLOUD FOUNDRY ENVIRONMENT
    # -------------------------
    if is_cf:

        # Create Cloud Foundry environment helper
        cf_env = AppEnv()

        # Get the AI Core service bound to the app
        # 'label' should match the service name in CF
        ai_service = cf_env.get_service(label='aicore')

        # -------------------------
        # SET AI CORE ENV VARIABLES
        # -------------------------
        # These values are extracted from the service credentials
        # and stored in environment variables so the app can use them

        os.environ['AICORE_AUTH_URL'] = ai_service.credentials['url']
        os.environ['AICORE_CLIENT_ID'] = ai_service.credentials['clientid']
        os.environ['AICORE_CLIENT_SECRET'] = ai_service.credentials['clientsecret']

        # Construct base API URL for AI Core
        # Example: https://.../v2
        os.environ['AICORE_BASE_URL'] = f"{ai_service.credentials['serviceurls'].get('AI_API_URL')}/v2"


        # -------------------------
        # RETURN SETTINGS FROM CF
        # -------------------------
        # Here we explicitly pass values from environment variables
        # into the Settings object

        return Settings(
            DAR_DEPLOYMENT_URL=os.getenv("DAR_DEPLOYMENT_URL"),
            DAR_BASE_URL=os.getenv("DAR_BASE_URL"),
            DAR_CLIENT_ID=os.getenv("DAR_CLIENT_ID"),
            DAR_CLIENT_SECRET=os.getenv("DAR_CLIENT_SECRET"),
            DAR_AUTH_URL=os.getenv("DAR_AUTH_URL"),

            # RAG Endpoint
            RAG_ENDPOINT=os.getenv("RAG_ENDPOINT"),

            # S/4HANA credentials
            BASE_URL=os.getenv("BASE_URL"),
            USER=os.getenv("USER"),
            PASSWORD=os.getenv("PASSWORD"),

            # Disable debug mode in production
            DEBUG=False
        )

    # -------------------------
    # LOCAL ENVIRONMENT
    # -------------------------
    else:
        # If NOT running in Cloud Foundry:
        # Load values from `.env` file or system environment variables
        base_settings = Settings()

    return base_settings


# -------------------------
# GLOBAL SETTINGS INSTANCE
# -------------------------
# This creates a single shared instance of Settings
# so the whole application can reuse it without reloading each time
settings = get_settings()