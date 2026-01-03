"""
Microsoft Defender XDR API Client
"""
import requests
from config import Config
from modules.auth import AuthenticationManager


class DefenderClient:
    """Client for interacting with Microsoft Defender XDR API"""

    def __init__(self, auth_manager: AuthenticationManager):
        """
        Initialize the Defender API client

        Args:
            auth_manager: AuthenticationManager instance
        """
        self.auth_manager = auth_manager
        self.base_url = Config.DEFENDER_API_ENDPOINT
        self.headers = None
        self._update_headers()

    def _update_headers(self):
        """Update request headers with fresh access token"""
        token = self.auth_manager.get_defender_token()
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def _make_request(self, method, endpoint, **kwargs):
        """
        Make HTTP request to Defender API

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response data or raises exception
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json() if response.content else {}

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                # Token might be expired, refresh and retry
                self._update_headers()
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    **kwargs
                )
                response.raise_for_status()
                return response.json() if response.content else {}
            else:
                raise Exception(f"API request failed: {e.response.status_code} - {e.response.text}")

    def get_machines(self):
        """Get all machines from Defender"""
        return self._make_request('GET', '/api/machines')

    def get_machine_by_id(self, machine_id):
        """Get specific machine details"""
        return self._make_request('GET', f'/api/machines/{machine_id}')

    def get_security_recommendations(self):
        """Get security recommendations"""
        return self._make_request('GET', '/api/recommendations')

    def get_vulnerabilities(self):
        """Get discovered vulnerabilities"""
        return self._make_request('GET', '/api/vulnerabilities')

    def get_alerts(self, filters=None):
        """
        Get security alerts

        Args:
            filters: Optional OData filter string
        """
        endpoint = '/api/alerts'
        if filters:
            endpoint += f'?$filter={filters}'
        return self._make_request('GET', endpoint)

    def get_incidents(self):
        """Get security incidents"""
        return self._make_request('GET', '/api/incidents')

    def run_query(self, query):
        """
        Run advanced hunting query

        Args:
            query: KQL query string

        Returns:
            Query results
        """
        payload = {'Query': query}
        return self._make_request('POST', '/api/advancedqueries/run', json=payload)
