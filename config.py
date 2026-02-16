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

    # User Authentication Configuration
    REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:5000/auth/callback')
    USER_SCOPE = ['User.Read']  # Minimal scope for user authentication

    # Microsoft Graph API Configuration
    GRAPH_API_ENDPOINT = os.getenv('GRAPH_API_ENDPOINT', 'https://graph.microsoft.com/v1.0')
    GRAPH_API_SCOPE = ['https://graph.microsoft.com/.default']

    # Defender API Configuration
    DEFENDER_API_ENDPOINT = os.getenv('DEFENDER_API_ENDPOINT', 'https://api.securitycenter.microsoft.com')
    DEFENDER_API_SCOPE = ['https://api.securitycenter.microsoft.com/.default']

    # Flask Configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))

    # Session Configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

    # Authority URL for MSAL
    AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

    @staticmethod
    def validate():
        """Validate required configuration"""
        required_vars = ['TENANT_ID', 'CLIENT_ID', 'CLIENT_SECRET', 'FLASK_SECRET_KEY']
        missing = [var for var in required_vars if not os.getenv(var)]

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        return True
