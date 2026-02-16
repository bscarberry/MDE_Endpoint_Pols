"""
Microsoft Graph API Client for Endpoint Policies
"""
import logging
import requests
from config import Config
from modules.auth import AuthenticationManager

logger = logging.getLogger(__name__)


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

    def _batch_request(self, requests_data):
        """
        Make batch request to Graph API to fetch multiple resources in a single call

        Args:
            requests_data: List of request dictionaries with 'id', 'method', and 'url'

        Returns:
            Dictionary mapping request IDs to response bodies
        """
        if not requests_data:
            return {}

        # Microsoft Graph batch API supports up to 20 requests per batch
        # Split into chunks if needed
        batch_size = 20
        all_responses = {}

        for i in range(0, len(requests_data), batch_size):
            batch = requests_data[i:i+batch_size]

            batch_payload = {
                "requests": batch
            }

            try:
                url = f"{self.base_url}/$batch"
                response = requests.post(
                    url=url,
                    headers=self.headers,
                    json=batch_payload
                )
                response.raise_for_status()
                batch_response = response.json()

                # Map responses by ID
                for resp in batch_response.get('responses', []):
                    req_id = resp.get('id')
                    if resp.get('status') == 200:
                        all_responses[req_id] = resp.get('body')
                    else:
                        # Request failed, set to None
                        all_responses[req_id] = None

            except Exception as e:
                logger.warning("Batch request failed: %s", str(e))
                # Set all requests in this batch to None
                for req in batch:
                    all_responses[req['id']] = None

        return all_responses

    def _batch_request_beta(self, requests_data):
        """
        Make batch request to Graph API beta endpoint

        Args:
            requests_data: List of request dictionaries with 'id', 'method', and 'url'

        Returns:
            Dictionary mapping request IDs to response bodies
        """
        if not requests_data:
            return {}

        # Microsoft Graph batch API supports up to 20 requests per batch
        batch_size = 20
        all_responses = {}

        for i in range(0, len(requests_data), batch_size):
            batch = requests_data[i:i+batch_size]

            batch_payload = {
                "requests": batch
            }

            try:
                url = f"{self.base_url_beta}/$batch"
                response = requests.post(
                    url=url,
                    headers=self.headers,
                    json=batch_payload
                )
                response.raise_for_status()
                batch_response = response.json()

                # Map responses by ID
                for resp in batch_response.get('responses', []):
                    req_id = resp.get('id')
                    if resp.get('status') == 200:
                        all_responses[req_id] = resp.get('body')
                    else:
                        all_responses[req_id] = None

            except Exception as e:
                logger.warning("Beta batch request failed: %s", str(e))
                for req in batch:
                    all_responses[req['id']] = None

        return all_responses

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
            logger.debug("Retrieving endpoint security policies from deviceConfigurations...")
            all_configs = self._get_all_pages('/deviceManagement/deviceConfigurations')
            logger.debug("Found %d total device configurations", len(all_configs))

            # Look for endpoint protection configurations
            security_configs = []
            for config in all_configs:
                config_type = config.get('@odata.type', '')
                display_name = config.get('displayName', '')

                logger.debug("Checking config '%s' with type '%s'", display_name, config_type)

                # Check for windows10EndpointProtectionConfiguration (the main type for endpoint security)
                if config_type == '#microsoft.graph.windows10EndpointProtectionConfiguration':
                    config['policySource'] = 'windows10EndpointProtectionConfiguration'
                    security_configs.append(config)
                    logger.debug("Found endpoint protection config: %s", display_name)
                # Also check for other endpoint security related types
                elif any(keyword in config_type.lower() for keyword in
                        ['endpointprotection', 'firewall', 'defender', 'antivirus', 'security']):
                    config['policySource'] = 'deviceConfigurations'
                    security_configs.append(config)
                    logger.debug("Found security config: %s (%s)", display_name, config_type)

            logger.debug("Retrieved %d endpoint security policies from deviceConfigurations", len(security_configs))
            all_policies.extend(security_configs)

        except Exception as e:
            logger.error("Error retrieving from deviceConfigurations: %s", str(e))

        # Method 2: Get from intents endpoint (beta) - newer style policies
        try:
            logger.debug("Retrieving from intents (beta)...")
            intents = self._get_all_pages('/deviceManagement/intents', use_beta=True)
            logger.debug("Found %d intents", len(intents))

            # Get detailed info for each intent
            for idx, intent in enumerate(intents):
                try:
                    logger.debug("Processing intent %d/%d: %s", idx + 1, len(intents), intent.get('displayName', 'Unknown'))
                    detailed_intent = self.get_intent_by_id(intent['id'])
                    detailed_intent['policySource'] = 'intents'
                    all_policies.append(detailed_intent)
                except Exception as e:
                    logger.warning("Could not get details for intent %s: %s", intent.get('id'), str(e))
                    intent['policySource'] = 'intents'
                    all_policies.append(intent)

            logger.debug("Retrieved %d policies from intents", len(intents))

        except Exception as e:
            logger.warning("Intents endpoint failed: %s", str(e))

        # Method 3: Try configuration policies from beta (Settings Catalog)
        try:
            logger.debug("Retrieving from configurationPolicies (beta)...")
            config_policies = self._get_all_pages('/deviceManagement/configurationPolicies', use_beta=True)
            logger.debug("Found %d configuration policies", len(config_policies))

            # Add all configuration policies (Settings Catalog)
            for policy in config_policies:
                policy['policySource'] = 'configurationPolicies'
                all_policies.append(policy)
                logger.debug("Found Settings Catalog policy: %s", policy.get('name', 'Unknown'))

            logger.debug("Retrieved %d policies from configurationPolicies", len(config_policies))

        except Exception as e:
            logger.warning("Configuration policies (beta) failed: %s", str(e))

        logger.info("Retrieved %d endpoint security policies from all sources", len(all_policies))

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
                        logger.warning("Could not get settings for category %s: %s", category.get('id'), str(e))

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

    def get_device_details(self, device_id):
        """Get device details including group memberships"""
        try:
            # Get device details
            device = self._make_request('GET', f'/deviceManagement/managedDevices/{device_id}')

            # Get Azure AD device object to fetch group memberships
            azure_ad_device_id = device.get('azureADDeviceId')
            if azure_ad_device_id:
                try:
                    # Get group memberships for the device
                    memberships = self._get_all_pages(f'/devices(deviceId=\'{azure_ad_device_id}\')/memberOf')
                    device['groupMemberships'] = [
                        {
                            'id': group.get('id'),
                            'displayName': group.get('displayName', 'Unknown Group')
                        }
                        for group in memberships
                        if group.get('@odata.type') == '#microsoft.graph.group'
                    ]
                except Exception as e:
                    logger.warning("Could not fetch group memberships: %s", str(e))
                    device['groupMemberships'] = []
            else:
                device['groupMemberships'] = []

            return device
        except Exception as e:
            raise Exception(f"Failed to get device details: {str(e)}")

    # Groups (for assignments)
    def get_groups(self):
        """Get all Azure AD groups"""
        return self._get_all_pages('/groups')

    def get_group_by_id(self, group_id):
        """Get specific group details"""
        return self._make_request('GET', f'/groups/{group_id}')

    # All Policies Summary
    def _add_assignment_counts(self, policies, policy_type=None):
        """Add assignment counts and group names to policies using batch requests for maximum performance"""
        if not policies:
            return policies

        # Build batch requests for ALL policy assignments
        assignment_batch_requests = []
        policy_metadata = {}  # Store policy type info for later

        for idx, policy in enumerate(policies):
            policy_id = policy.get('id')
            if not policy_id:
                policy['assignmentCount'] = 0
                policy['assignmentGroups'] = []
                continue

            # Determine the actual policy type
            actual_type = policy_type
            if policy.get('policySource'):
                if policy['policySource'] == 'intents':
                    actual_type = 'intent'
                elif policy['policySource'] == 'configurationPolicies':
                    actual_type = 'configuration_profile'
                elif policy['policySource'] in ['windows10EndpointProtectionConfiguration', 'deviceConfigurations']:
                    actual_type = 'configuration'

            # Build assignment endpoint URL
            assignment_url = None
            if actual_type == 'compliance':
                assignment_url = f'/deviceManagement/deviceCompliancePolicies/{policy_id}/assignments'
            elif actual_type == 'configuration':
                assignment_url = f'/deviceManagement/deviceConfigurations/{policy_id}/assignments'
            elif actual_type == 'intent':
                assignment_url = f'/deviceManagement/intents/{policy_id}/assignments'
            elif actual_type == 'configuration_profile':
                assignment_url = f'/deviceManagement/configurationPolicies/{policy_id}/assignments'

            if assignment_url:
                assignment_batch_requests.append({
                    'id': str(idx),
                    'method': 'GET',
                    'url': assignment_url
                })
                policy_metadata[str(idx)] = {
                    'policy_id': policy_id,
                    'policy_index': idx,
                    'needs_beta': actual_type in ['intent', 'configuration_profile']
                }

        # Split into v1.0 and beta batches since batch endpoint doesn't support mixing
        v1_requests = [r for r in assignment_batch_requests if not policy_metadata[r['id']]['needs_beta']]
        beta_requests = [r for r in assignment_batch_requests if policy_metadata[r['id']]['needs_beta']]

        # Execute batch requests for assignments
        all_group_ids = set()
        policy_assignments = {}

        # Process v1.0 batch
        if v1_requests:
            v1_responses = self._batch_request(v1_requests)
            for req_id, response_data in v1_responses.items():
                if response_data and isinstance(response_data, dict):
                    meta = policy_metadata[req_id]
                    policy_id = meta['policy_id']
                    policy_idx = meta['policy_index']
                    assignment_list = response_data.get('value', [])

                    policies[policy_idx]['assignmentCount'] = len(assignment_list)
                    policy_assignments[policy_id] = assignment_list

                    # Collect group IDs
                    for assignment in assignment_list:
                        target = assignment.get('target', {})
                        group_id = target.get('groupId')
                        if group_id:
                            all_group_ids.add(group_id)
                else:
                    meta = policy_metadata[req_id]
                    policy_idx = meta['policy_index']
                    policies[policy_idx]['assignmentCount'] = 0
                    policies[policy_idx]['assignmentGroups'] = []

        # Process beta batch
        if beta_requests:
            beta_responses = self._batch_request_beta(beta_requests)
            for req_id, response_data in beta_responses.items():
                if response_data and isinstance(response_data, dict):
                    meta = policy_metadata[req_id]
                    policy_id = meta['policy_id']
                    policy_idx = meta['policy_index']
                    assignment_list = response_data.get('value', [])

                    policies[policy_idx]['assignmentCount'] = len(assignment_list)
                    policy_assignments[policy_id] = assignment_list

                    # Collect group IDs
                    for assignment in assignment_list:
                        target = assignment.get('target', {})
                        group_id = target.get('groupId')
                        if group_id:
                            all_group_ids.add(group_id)
                else:
                    meta = policy_metadata[req_id]
                    policy_idx = meta['policy_index']
                    policies[policy_idx]['assignmentCount'] = 0
                    policies[policy_idx]['assignmentGroups'] = []

        # Batch fetch all group names
        group_name_cache = {}
        if all_group_ids:
            batch_requests = []
            for idx, group_id in enumerate(all_group_ids):
                batch_requests.append({
                    'id': str(idx),
                    'method': 'GET',
                    'url': f'/groups/{group_id}?$select=id,displayName'
                })

            batch_responses = self._batch_request(batch_requests)

            # Build group name cache
            id_to_idx = {gid: str(idx) for idx, gid in enumerate(all_group_ids)}
            for group_id in all_group_ids:
                idx = id_to_idx[group_id]
                group_data = batch_responses.get(idx)
                if group_data and isinstance(group_data, dict):
                    group_name_cache[group_id] = group_data.get('displayName', group_id)
                else:
                    group_name_cache[group_id] = group_id

        # Final pass: Assign group names to policies
        for policy in policies:
            policy_id = policy.get('id')
            if policy_id not in policy_assignments:
                if 'assignmentCount' not in policy:
                    policy['assignmentCount'] = 0
                if 'assignmentGroups' not in policy:
                    policy['assignmentGroups'] = []
                continue

            group_names = []
            for assignment in policy_assignments[policy_id]:
                target = assignment.get('target', {})
                group_id = target.get('groupId')
                if group_id:
                    group_names.append(group_name_cache.get(group_id, group_id))
                elif target.get('@odata.type') == '#microsoft.graph.allDevicesAssignmentTarget':
                    group_names.append('All Devices')
                elif target.get('@odata.type') == '#microsoft.graph.allLicensedUsersAssignmentTarget':
                    group_names.append('All Users')

            policy['assignmentGroups'] = group_names

        return policies

    def get_all_policies_summary(self):
        """Get summary of all endpoint policies - each endpoint is optional"""
        policies = {}

        # Try each endpoint individually - if one fails, continue with others
        try:
            compliance_policies = self.get_device_compliance_policies()
            policies['compliance_policies'] = self._add_assignment_counts(compliance_policies, 'compliance')
        except Exception as e:
            logger.warning("Could not retrieve compliance policies: %s", str(e))
            policies['compliance_policies'] = []

        try:
            config_policies = self.get_device_configurations()
            policies['configuration_policies'] = self._add_assignment_counts(config_policies, 'configuration')
        except Exception as e:
            logger.warning("Could not retrieve configuration policies: %s", str(e))
            policies['configuration_policies'] = []

        try:
            # get_intents() calls get_endpoint_security_policies() which returns mixed policy types
            # Each policy has policySource set, so _add_assignment_counts will route correctly
            intents = self.get_intents()
            policies['endpoint_security_intents'] = self._add_assignment_counts(intents)
        except Exception as e:
            logger.warning("Could not retrieve endpoint security intents: %s", str(e))
            policies['endpoint_security_intents'] = []

        try:
            config_profiles = self.get_configuration_policies()
            policies['configuration_profiles'] = self._add_assignment_counts(config_profiles, 'configuration_profile')
        except Exception as e:
            logger.warning("Could not retrieve configuration profiles: %s", str(e))
            policies['configuration_profiles'] = []

        try:
            policies['device_scripts'] = self.get_device_management_scripts()
        except Exception as e:
            logger.warning("Could not retrieve device scripts: %s", str(e))
            policies['device_scripts'] = []

        try:
            policies['health_scripts'] = self.get_device_health_scripts()
        except Exception as e:
            logger.warning("Could not retrieve health scripts: %s", str(e))
            policies['health_scripts'] = []

        return policies
