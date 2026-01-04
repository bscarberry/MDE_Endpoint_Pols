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
        self.base_url_beta = 'https://graph.microsoft.com/beta'
        self.headers = None
        self._update_headers()

    def _update_headers(self):
        """Update request headers with fresh access token"""
        token = self.auth_manager.get_graph_token()
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def _make_request(self, method, endpoint, use_beta=False, **kwargs):
        """
        Make HTTP request to Graph API

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            use_beta: Use beta API instead of v1.0
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response data or raises exception
        """
        base = self.base_url_beta if use_beta else self.base_url
        url = f"{base}{endpoint}"

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

    def _get_all_pages(self, endpoint, use_beta=False):
        """
        Get all pages of results from paginated endpoint

        Args:
            endpoint: API endpoint
            use_beta: Use beta API instead of v1.0

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
                data = self._make_request('GET', next_link, use_beta=use_beta)

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
    def get_endpoint_security_policies(self):
        """
        Get all endpoint security policies from multiple sources
        Combines results from intents, configurationPolicies, and deviceConfigurations
        """
        all_policies = []

        # Method 1: Get from deviceConfigurations (PRIMARY SOURCE - Graph REST 1.0)
        # This is where windows10EndpointProtectionConfiguration objects live
        try:
            print("Attempting to retrieve endpoint security policies from deviceConfigurations...")
            all_configs = self._get_all_pages('/deviceManagement/deviceConfigurations')
            print(f"DEBUG: Found {len(all_configs)} total device configurations")

            # Look for endpoint protection configurations
            security_configs = []
            for config in all_configs:
                config_type = config.get('@odata.type', '')
                display_name = config.get('displayName', '')

                print(f"DEBUG: Checking config '{display_name}' with type '{config_type}'")

                # Check for windows10EndpointProtectionConfiguration (the main type for endpoint security)
                if config_type == '#microsoft.graph.windows10EndpointProtectionConfiguration':
                    config['policySource'] = 'windows10EndpointProtectionConfiguration'
                    security_configs.append(config)
                    print(f"  ✓ Found endpoint protection config: {display_name}")
                # Also check for other endpoint security related types
                elif any(keyword in config_type.lower() for keyword in
                        ['endpointprotection', 'firewall', 'defender', 'antivirus', 'security']):
                    config['policySource'] = 'deviceConfigurations'
                    security_configs.append(config)
                    print(f"  ✓ Found security config: {display_name} ({config_type})")

            print(f"Retrieved {len(security_configs)} endpoint security policies from deviceConfigurations")
            all_policies.extend(security_configs)

        except Exception as e:
            print(f"ERROR retrieving from deviceConfigurations: {str(e)}")

        # Method 2: Get from intents endpoint (beta) - newer style policies
        try:
            print("\nAttempting to retrieve from intents (beta)...")
            intents = self._get_all_pages('/deviceManagement/intents', use_beta=True)
            print(f"DEBUG: Found {len(intents)} intents")

            # Get detailed info for each intent
            for idx, intent in enumerate(intents):
                try:
                    print(f"DEBUG: Processing intent {idx + 1}/{len(intents)}: {intent.get('displayName', 'Unknown')}")
                    detailed_intent = self.get_intent_by_id(intent['id'])
                    detailed_intent['policySource'] = 'intents'
                    all_policies.append(detailed_intent)
                except Exception as e:
                    print(f"Warning: Could not get details for intent {intent.get('id')}: {str(e)}")
                    intent['policySource'] = 'intents'
                    all_policies.append(intent)

            print(f"Retrieved {len(intents)} policies from intents")

        except Exception as e:
            print(f"Intents endpoint failed: {str(e)}")

        # Method 3: Try configuration policies from beta (Settings Catalog)
        try:
            print("\nAttempting to retrieve from configurationPolicies (beta)...")
            config_policies = self._get_all_pages('/deviceManagement/configurationPolicies', use_beta=True)
            print(f"DEBUG: Found {len(config_policies)} configuration policies")

            # Add all configuration policies (Settings Catalog)
            for policy in config_policies:
                policy['policySource'] = 'configurationPolicies'
                all_policies.append(policy)
                print(f"  ✓ Found Settings Catalog policy: {policy.get('name', 'Unknown')}")

            print(f"Retrieved {len(config_policies)} policies from configurationPolicies")

        except Exception as e:
            print(f"Configuration policies (beta) failed: {str(e)}")

        print(f"\n{'='*60}")
        print(f"TOTAL: Retrieved {len(all_policies)} endpoint security policies from all sources")
        print(f"{'='*60}\n")

        return all_policies

    def get_intent_by_id(self, intent_id):
        """Get specific security intent with full settings and assignments"""
        try:
            # Get base intent info
            intent = self._make_request('GET', f'/deviceManagement/intents/{intent_id}', use_beta=True)

            # Get assignments
            try:
                assignments = self._make_request('GET', f'/deviceManagement/intents/{intent_id}/assignments', use_beta=True)
                intent['assignments'] = assignments.get('value', [])
            except:
                intent['assignments'] = []

            # Get categories (settings groups)
            try:
                categories = self._make_request('GET', f'/deviceManagement/intents/{intent_id}/categories', use_beta=True)
                intent['categories'] = categories.get('value', [])

                # Get settings for each category
                intent['settingsByCategory'] = []
                for category in intent['categories']:
                    try:
                        settings = self._make_request('GET',
                            f'/deviceManagement/intents/{intent_id}/categories/{category["id"]}/settings',
                            use_beta=True)
                        intent['settingsByCategory'].append({
                            'categoryId': category['id'],
                            'categoryName': category.get('displayName'),
                            'settings': settings.get('value', [])
                        })
                    except Exception as e:
                        print(f"Could not get settings for category {category.get('id')}: {str(e)}")

            except:
                intent['categories'] = []
                intent['settingsByCategory'] = []

            return intent

        except Exception as e:
            raise Exception(f"Failed to get intent details: {str(e)}")

    # Legacy methods for backward compatibility
    def get_intents(self):
        """Get all endpoint security intents (policies) - uses new method"""
        return self.get_endpoint_security_policies()

    def get_antivirus_policies(self):
        """Get antivirus policies from endpoint security"""
        policies = self.get_endpoint_security_policies()
        return [p for p in policies if 'antivirus' in p.get('templateId', '').lower() or
                'antivirus' in p.get('displayName', '').lower() or
                'defender' in p.get('displayName', '').lower()]

    def get_firewall_policies(self):
        """Get firewall policies from endpoint security"""
        policies = self.get_endpoint_security_policies()
        return [p for p in policies if 'firewall' in p.get('templateId', '').lower() or
                'firewall' in p.get('displayName', '').lower()]

    def get_asr_policies(self):
        """Get Attack Surface Reduction policies"""
        policies = self.get_endpoint_security_policies()
        return [p for p in policies if 'attacksurfacereduction' in p.get('templateId', '').lower() or
                'asr' in p.get('displayName', '').lower() or
                'attack surface' in p.get('displayName', '').lower()]

    # Device Health Scripts
    def get_device_health_scripts(self):
        """Get all device health monitoring scripts"""
        return self._get_all_pages('/deviceManagement/deviceHealthScripts', use_beta=True)

    # Windows Update Policies
    def get_windows_update_policies(self):
        """Get Windows Update for Business policies"""
        return self._get_all_pages('/deviceManagement/deviceConfigurations?$filter=isof(%27microsoft.graph.windowsUpdateForBusinessConfiguration%27)', use_beta=True)

    # Configuration Profiles (Settings Catalog)
    def get_configuration_policies(self):
        """Get configuration policies (Settings Catalog)"""
        return self._get_all_pages('/deviceManagement/configurationPolicies', use_beta=True)

    def get_configuration_policy_by_id(self, policy_id):
        """Get specific configuration policy with settings and assignments"""
        policy = self._make_request('GET', f'/deviceManagement/configurationPolicies/{policy_id}', use_beta=True)
        settings = self._make_request('GET', f'/deviceManagement/configurationPolicies/{policy_id}/settings', use_beta=True)
        assignments = self._make_request('GET', f'/deviceManagement/configurationPolicies/{policy_id}/assignments', use_beta=True)

        policy['settings'] = settings.get('value', [])
        policy['assignments'] = assignments.get('value', [])
        return policy

    # Scripts
    def get_device_management_scripts(self):
        """Get all PowerShell scripts"""
        return self._get_all_pages('/deviceManagement/deviceManagementScripts', use_beta=True)

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
        """Get summary of all endpoint policies - each endpoint is optional"""
        policies = {}

        # Try each endpoint individually - if one fails, continue with others
        try:
            policies['compliance_policies'] = self.get_device_compliance_policies()
        except Exception as e:
            print(f"Warning: Could not retrieve compliance policies: {str(e)}")
            policies['compliance_policies'] = []

        try:
            policies['configuration_policies'] = self.get_device_configurations()
        except Exception as e:
            print(f"Warning: Could not retrieve configuration policies: {str(e)}")
            policies['configuration_policies'] = []

        try:
            policies['endpoint_security_intents'] = self.get_intents()
        except Exception as e:
            print(f"Warning: Could not retrieve endpoint security intents: {str(e)}")
            policies['endpoint_security_intents'] = []

        try:
            policies['configuration_profiles'] = self.get_configuration_policies()
        except Exception as e:
            print(f"Warning: Could not retrieve configuration profiles: {str(e)}")
            policies['configuration_profiles'] = []

        try:
            policies['device_scripts'] = self.get_device_management_scripts()
        except Exception as e:
            print(f"Warning: Could not retrieve device scripts: {str(e)}")
            policies['device_scripts'] = []

        try:
            policies['health_scripts'] = self.get_device_health_scripts()
        except Exception as e:
            print(f"Warning: Could not retrieve health scripts: {str(e)}")
            policies['health_scripts'] = []

        return policies
