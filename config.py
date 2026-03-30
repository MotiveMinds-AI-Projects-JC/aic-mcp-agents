# OS module for environment variable access
import os

# Pydantic settings for structured configuration management
from pydantic_settings import BaseSettings, SettingsConfigDict

# Cloud Foundry environment utility
from cfenv import AppEnv

# -------------------------
# SETTINGS CLASS
# -------------------------
class Settings(BaseSettings):
    """
    Application configuration class using Pydantic.

    - Automatically reads values from environment variables or .env file
    - Provides type validation and default values
    """
    # DAR Service (Data Attribute Recommendation System)
    DAR_DEPLOYMENT_URL : str
    DAR_BASE_URL : str
    DAR_CLIENT_ID : str
    DAR_CLIENT_SECRET : str
    DAR_AUTH_URL : str
    # RAG Endpoint
    RAG_ENDPOINT : str
    #S/4HANA URL
    BASE_URL : str
    USER : str
    PASSWORD : str
    DEBUG: bool = True  # Default debug mode (True for local development)

    # -------------------------
    # PYDANTIC CONFIG
    # -------------------------
    # Configure Pydantic to load environment variables from .env file
    model_config = SettingsConfigDict(
        env_file=".env",           # Path to .env file
        env_file_encoding="utf-8" # Encoding format
    )


# -------------------------
# LOAD SETTINGS FUNCTION
# -------------------------
def get_settings() -> Settings:
    """
    Load application settings based on environment.

    - Detects if running in Cloud Foundry (CF)
    - If CF: fetch credentials from bound services
    - Else: load from local .env file

    Returns:
        Settings: Configured settings object
    """

    # Detect Cloud Foundry environment via VCAP_SERVICES variable
    is_cf = 'VCAP_SERVICES' in os.environ
    

    # -------------------------
    # CLOUD FOUNDRY ENVIRONMENT
    # -------------------------
    if is_cf:

        # Initialize Cloud Foundry environment helper
        cf_env = AppEnv()

        # Retrieve AI Core service binding
        ai_service = cf_env.get_service(label='aicore')

        # -------------------------
        # SET AI CORE ENV VARIABLES
        # -------------------------
        # These are required for Gen AI Hub / AI Core authentication
        os.environ['AICORE_AUTH_URL'] = ai_service.credentials['url']
        os.environ['AICORE_CLIENT_ID'] = ai_service.credentials['clientid']
        os.environ['AICORE_CLIENT_SECRET'] = ai_service.credentials['clientsecret']

        # Construct base API URL for AI Core
        os.environ['AICORE_BASE_URL'] = f'{ai_service.credentials['serviceurls'].get('AI_API_URL')}/v2'


        # -------------------------
        # RETURN SETTINGS FROM CF
        # -------------------------
        # Override only values that must come from CF services
        return Settings (
            DAR_DEPLOYMENT_URL = os.getenv("DAR_DEPLOYMENT_URL"),
            DAR_BASE_URL = os.getenv("DAR_BASE_URL"),
            DAR_CLIENT_ID = os.getenv("DAR_CLIENT_ID"),
            DAR_CLIENT_SECRET = os.getenv("DAR_CLIENT_SECRET"),
            DAR_AUTH_URL = os.getenv("DAR_AUTH_URL"),
            # RAG Endpoint
            RAG_ENDPOINT =os.getenv("RAG_ENDPOINT"),
            #S/4HANA URL,
            BASE_URL =os.getenv("BASE_URL"),
            USER =os.getenv("USER"),
            PASSWORD =os.getenv("PASSWORD"),
            # Disable debug in production
            DEBUG = False
        )
    # -------------------------
    # LOCAL ENVIRONMENT
    # -------------------------
    else:
        # Load settings from .env file and environment variables
        base_settings = Settings()

    return base_settings


# -------------------------
# GLOBAL SETTINGS INSTANCE
# -------------------------
# Initialize settings once and reuse across application
settings = get_settings()

