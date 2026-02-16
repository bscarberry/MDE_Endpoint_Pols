"""
Microsoft Defender XDR API Client
"""
import re
import logging
import requests
from urllib.parse import quote
from config import Config
from modules.auth import AuthenticationManager

logger = logging.getLogger(__name__)

# Allowed OData filter fields for the alerts endpoint
ALLOWED_ALERT_FILTER_FIELDS = {
    'severity', 'status', 'category', 'createdDateTime',
    'lastUpdatedDateTime', 'assignedTo', 'classification',
    'determination', 'detectionSource', 'threatFamilyName',
    'title', 'machineId',
}

# Maximum KQL query length to prevent abuse
MAX_KQL_QUERY_LENGTH = 10000


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

    @staticmethod
    def _validate_odata_filter(filter_string):
        """Validate OData filter to prevent injection attacks."""
        if not filter_string:
            return None
        # Strip whitespace
        filter_string = filter_string.strip()
        # Reject excessively long filters
        if len(filter_string) > 500:
            raise ValueError("Filter string too long")
        # Ensure only allowed field names are used
        # Extract field names (words before operators like eq, ne, gt, lt, ge, le, contains)
        field_pattern = re.compile(r'\b(\w+)\s+(?:eq|ne|gt|lt|ge|le)\b', re.IGNORECASE)
        contains_pattern = re.compile(r'\bcontains\(\s*(\w+)', re.IGNORECASE)
        fields = set(field_pattern.findall(filter_string))
        fields.update(contains_pattern.findall(filter_string))
        disallowed = fields - ALLOWED_ALERT_FILTER_FIELDS
        if disallowed:
            raise ValueError(f"Disallowed filter fields: {', '.join(disallowed)}")
        return filter_string

    def get_alerts(self, filters=None):
        """
        Get security alerts

        Args:
            filters: Optional OData filter string (validated against allowlist)
        """
        endpoint = '/api/alerts'
        if filters:
            validated = self._validate_odata_filter(filters)
            if validated:
                endpoint += f'?$filter={quote(validated, safe="()\'/ ")}'
        return self._make_request('GET', endpoint)

    def get_incidents(self):
        """Get security incidents"""
        return self._make_request('GET', '/api/incidents')

    def run_query(self, query):
        """
        Run advanced hunting query

        Args:
            query: KQL query string (validated for length and basic safety)

        Returns:
            Query results
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if len(query) > MAX_KQL_QUERY_LENGTH:
            raise ValueError(f"Query exceeds maximum length of {MAX_KQL_QUERY_LENGTH} characters")
        logger.info("Executing advanced hunting query (%d chars)", len(query))
        payload = {'Query': query}
        return self._make_request('POST', '/api/advancedqueries/run', json=payload)
