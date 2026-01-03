"""
Configuration module for Defender XDR Endpoint Policy Manager
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class"""

    # Azure AD Configuration
    TENANT_ID = os.getenv('TENANT_ID')
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')

    # Microsoft Graph API Configuration
    GRAPH_API_ENDPOINT = os.getenv('GRAPH_API_ENDPOINT', 'https://graph.microsoft.com/v1.0')
    GRAPH_API_SCOPE = ['https://graph.microsoft.com/.default']

    # Defender API Configuration
    DEFENDER_API_ENDPOINT = os.getenv('DEFENDER_API_ENDPOINT', 'https://api.securitycenter.microsoft.com')
    DEFENDER_API_SCOPE = ['https://api.securitycenter.microsoft.com/.default']

    # Flask Configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))

    # Authority URL for MSAL
    AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

    @staticmethod
    def validate():
        """Validate required configuration"""
        required_vars = ['TENANT_ID', 'CLIENT_ID', 'CLIENT_SECRET']
        missing = [var for var in required_vars if not os.getenv(var)]

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        return True
