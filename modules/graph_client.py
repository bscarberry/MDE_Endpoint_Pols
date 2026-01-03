"""
Microsoft Graph API Client for Endpoint Policies
"""
import requests
from config import Config
from modules.auth import AuthenticationManager


class GraphClient:
    """Client for interacting with Microsoft Graph API for endpoint management"""

    def __init__(self, auth_manager: AuthenticationManager):
        """
        Initialize the Graph API client

        Args:
            auth_manager: AuthenticationManager instance
        """
        self.auth_manager = auth_manager
        self.base_url = Config.GRAPH_API_ENDPOINT
        self.headers = None
        self._update_headers()

    def _update_headers(self):
        """Update request headers with fresh access token"""
        token = self.auth_manager.get_graph_token()
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def _make_request(self, method, endpoint, **kwargs):
        """
        Make HTTP request to Graph API

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

    def _get_all_pages(self, endpoint):
        """
        Get all pages of results from paginated endpoint

        Args:
            endpoint: API endpoint

        Returns:
            List of all items from all pages
        """
        all_items = []
        next_link = endpoint

        while next_link:
            if next_link.startswith('http'):
                # It's a full URL from @odata.nextLink
                response = requests.get(next_link, headers=self.headers)
                response.raise_for_status()
                data = response.json()
            else:
                # It's a relative path
                data = self._make_request('GET', next_link)

            all_items.extend(data.get('value', []))
            next_link = data.get('@odata.nextLink')

        return all_items

    # Device Compliance Policies
    def get_device_compliance_policies(self):
        """Get all device compliance policies"""
        return self._get_all_pages('/deviceManagement/deviceCompliancePolicies')

    def get_compliance_policy_by_id(self, policy_id):
        """Get specific compliance policy with assignments"""
        policy = self._make_request('GET', f'/deviceManagement/deviceCompliancePolicies/{policy_id}')
        assignments = self._make_request('GET', f'/deviceManagement/deviceCompliancePolicies/{policy_id}/assignments')
        policy['assignments'] = assignments.get('value', [])
        return policy

    # Device Configuration Policies
    def get_device_configurations(self):
        """Get all device configuration policies"""
        return self._get_all_pages('/deviceManagement/deviceConfigurations')

    def get_device_configuration_by_id(self, config_id):
        """Get specific device configuration with assignments"""
        config = self._make_request('GET', f'/deviceManagement/deviceConfigurations/{config_id}')
        assignments = self._make_request('GET', f'/deviceManagement/deviceConfigurations/{config_id}/assignments')
        config['assignments'] = assignments.get('value', [])
        return config

    # Endpoint Security Policies
    def get_intents(self):
        """Get all endpoint security intents (policies)"""
        return self._get_all_pages('/deviceManagement/intents')

    def get_intent_by_id(self, intent_id):
        """Get specific security intent with settings and assignments"""
        intent = self._make_request('GET', f'/deviceManagement/intents/{intent_id}')
        assignments = self._make_request('GET', f'/deviceManagement/intents/{intent_id}/assignments')
        categories = self._make_request('GET', f'/deviceManagement/intents/{intent_id}/categories')

        intent['assignments'] = assignments.get('value', [])
        intent['categories'] = categories.get('value', [])

        return intent

    # Antivirus Policies
    def get_antivirus_policies(self):
        """Get antivirus policies from endpoint security"""
        intents = self.get_intents()
        return [intent for intent in intents if 'antivirus' in intent.get('templateId', '').lower()]

    # Firewall Policies
    def get_firewall_policies(self):
        """Get firewall policies from endpoint security"""
        intents = self.get_intents()
        return [intent for intent in intents if 'firewall' in intent.get('templateId', '').lower()]

    # Attack Surface Reduction Policies
    def get_asr_policies(self):
        """Get Attack Surface Reduction policies"""
        intents = self.get_intents()
        return [intent for intent in intents if 'attacksurfacereduction' in intent.get('templateId', '').lower()]

    # Device Health Scripts
    def get_device_health_scripts(self):
        """Get all device health monitoring scripts"""
        return self._get_all_pages('/deviceManagement/deviceHealthScripts')

    # Windows Update Policies
    def get_windows_update_policies(self):
        """Get Windows Update for Business policies"""
        return self._get_all_pages('/deviceManagement/deviceConfigurations?$filter=isof(%27microsoft.graph.windowsUpdateForBusinessConfiguration%27)')

    # Configuration Profiles (Settings Catalog)
    def get_configuration_policies(self):
        """Get configuration policies (Settings Catalog)"""
        return self._get_all_pages('/deviceManagement/configurationPolicies')

    def get_configuration_policy_by_id(self, policy_id):
        """Get specific configuration policy with settings and assignments"""
        policy = self._make_request('GET', f'/deviceManagement/configurationPolicies/{policy_id}')
        settings = self._make_request('GET', f'/deviceManagement/configurationPolicies/{policy_id}/settings')
        assignments = self._make_request('GET', f'/deviceManagement/configurationPolicies/{policy_id}/assignments')

        policy['settings'] = settings.get('value', [])
        policy['assignments'] = assignments.get('value', [])
        return policy

    # Scripts
    def get_device_management_scripts(self):
        """Get all PowerShell scripts"""
        return self._get_all_pages('/deviceManagement/deviceManagementScripts')

    # Managed Devices
    def get_managed_devices(self):
        """Get all managed devices"""
        return self._get_all_pages('/deviceManagement/managedDevices')

    # Groups (for assignments)
    def get_groups(self):
        """Get all Azure AD groups"""
        return self._get_all_pages('/groups')

    def get_group_by_id(self, group_id):
        """Get specific group details"""
        return self._make_request('GET', f'/groups/{group_id}')

    # All Policies Summary
    def get_all_policies_summary(self):
        """Get summary of all endpoint policies"""
        try:
            policies = {
                'compliance_policies': self.get_device_compliance_policies(),
                'configuration_policies': self.get_device_configurations(),
                'endpoint_security_intents': self.get_intents(),
                'configuration_profiles': self.get_configuration_policies(),
                'device_scripts': self.get_device_management_scripts(),
                'health_scripts': self.get_device_health_scripts(),
            }
            return policies
        except Exception as e:
            raise Exception(f"Failed to retrieve policies: {str(e)}")
