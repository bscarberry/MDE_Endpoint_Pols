"""
User Authentication module using MSAL for interactive login
"""
import msal
from flask import session, url_for
from config import Config


class UserAuthManager:
    """Handles user authentication using OAuth 2.0 authorization code flow"""

    def __init__(self, redirect_uri=None):
        """Initialize the user authentication manager"""
        self.client_id = Config.CLIENT_ID
        self.client_secret = Config.CLIENT_SECRET
        self.authority = Config.AUTHORITY
        self.redirect_uri = redirect_uri or Config.REDIRECT_URI
        self.scope = Config.USER_SCOPE

    def _build_msal_app(self, cache=None):
        """Build MSAL confidential client application"""
        return msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority,
            token_cache=cache
        )

    def _build_auth_url(self, authority=None, scopes=None, state=None):
        """Build authorization URL for user login"""
        return self._build_msal_app().get_authorization_request_url(
            scopes=scopes or [],
            state=state or "",
            redirect_uri=self.redirect_uri
        )

    def get_login_url(self, state=None):
        """
        Get the login URL for user authentication

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            str: Authorization URL for user login
        """
        return self._build_auth_url(
            scopes=self.scope,
            state=state
        )

    def get_token_from_code(self, auth_code, scopes=None):
        """
        Exchange authorization code for access token

        Args:
            auth_code: Authorization code from callback
            scopes: List of scopes to request

        Returns:
            dict: Token response with access_token, id_token, etc.
        """
        result = self._build_msal_app().acquire_token_by_authorization_code(
            code=auth_code,
            scopes=scopes or self.scope,
            redirect_uri=self.redirect_uri
        )
        return result

    def get_user_from_session(self):
        """
        Get user information from session

        Returns:
            dict: User information or None if not authenticated
        """
        return session.get('user')

    def is_authenticated(self):
        """
        Check if user is authenticated

        Returns:
            bool: True if user is authenticated
        """
        return 'user' in session

    def logout(self):
        """Clear user session"""
        session.clear()

    def get_logout_url(self, post_logout_redirect_uri):
        """
        Get the logout URL for Azure AD

        Args:
            post_logout_redirect_uri: URL to redirect after logout

        Returns:
            str: Azure AD logout URL
        """
        return (
            f"{self.authority}/oauth2/v2.0/logout"
            f"?post_logout_redirect_uri={post_logout_redirect_uri}"
        )
