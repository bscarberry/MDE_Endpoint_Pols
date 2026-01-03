"""
Authentication module for Azure AD using MSAL
"""
import msal
from config import Config


class AuthenticationManager:
    """Handles authentication to Azure AD and token management"""

    def __init__(self):
        """Initialize the authentication manager"""
        self.tenant_id = Config.TENANT_ID
        self.client_id = Config.CLIENT_ID
        self.client_secret = Config.CLIENT_SECRET
        self.authority = Config.AUTHORITY

        # Create MSAL confidential client application
        self.app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )

    def get_access_token(self, scope):
        """
        Acquire access token for the specified scope

        Args:
            scope (list): List of scopes to request

        Returns:
            str: Access token or None if authentication fails
        """
        try:
            # Try to get token from cache first
            result = self.app.acquire_token_silent(scope, account=None)

            if not result:
                # If no cached token, acquire new token
                result = self.app.acquire_token_for_client(scopes=scope)

            if "access_token" in result:
                return result["access_token"]
            else:
                error = result.get("error")
                error_description = result.get("error_description")
                raise Exception(f"Authentication failed: {error} - {error_description}")

        except Exception as e:
            raise Exception(f"Failed to acquire token: {str(e)}")

    def get_graph_token(self):
        """Get access token for Microsoft Graph API"""
        return self.get_access_token(Config.GRAPH_API_SCOPE)

    def get_defender_token(self):
        """Get access token for Defender API"""
        return self.get_access_token(Config.DEFENDER_API_SCOPE)
