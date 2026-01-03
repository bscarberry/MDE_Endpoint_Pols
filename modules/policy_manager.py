"""
Policy Manager - Coordinates policy retrieval and formatting
"""
from modules.auth import AuthenticationManager
from modules.graph_client import GraphClient
from modules.defender_client import DefenderClient


class PolicyManager:
    """Manages endpoint policies and provides unified interface"""

    def __init__(self):
        """Initialize policy manager with API clients"""
        self.auth_manager = AuthenticationManager()
        self.graph_client = GraphClient(self.auth_manager)
        self.defender_client = DefenderClient(self.auth_manager)

    def get_all_policies(self):
        """
        Retrieve all endpoint policies from Graph API

        Returns:
            Dictionary containing all policy types
        """
        try:
            policies = self.graph_client.get_all_policies_summary()
            return {
                'success': True,
                'data': policies,
                'counts': {
                    'compliance_policies': len(policies.get('compliance_policies', [])),
                    'configuration_policies': len(policies.get('configuration_policies', [])),
                    'endpoint_security_intents': len(policies.get('endpoint_security_intents', [])),
                    'configuration_profiles': len(policies.get('configuration_profiles', [])),
                    'device_scripts': len(policies.get('device_scripts', [])),
                    'health_scripts': len(policies.get('health_scripts', [])),
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_policy_details(self, policy_type, policy_id):
        """
        Get detailed information about a specific policy

        Args:
            policy_type: Type of policy (compliance, configuration, etc.)
            policy_id: ID of the policy

        Returns:
            Policy details including settings and assignments
        """
        try:
            if policy_type == 'compliance':
                data = self.graph_client.get_compliance_policy_by_id(policy_id)
            elif policy_type == 'configuration':
                data = self.graph_client.get_device_configuration_by_id(policy_id)
            elif policy_type == 'intent':
                data = self.graph_client.get_intent_by_id(policy_id)
            elif policy_type == 'configuration_profile':
                data = self.graph_client.get_configuration_policy_by_id(policy_id)
            else:
                return {'success': False, 'error': 'Invalid policy type'}

            # Enrich assignments with group names
            if 'assignments' in data:
                for assignment in data['assignments']:
                    target = assignment.get('target', {})
                    group_id = target.get('groupId')
                    if group_id:
                        try:
                            group = self.graph_client.get_group_by_id(group_id)
                            assignment['groupName'] = group.get('displayName', 'Unknown')
                        except:
                            assignment['groupName'] = 'Unknown Group'

            return {
                'success': True,
                'data': data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def search_policies(self, search_term):
        """
        Search for policies by name or description

        Args:
            search_term: Term to search for

        Returns:
            List of matching policies
        """
        try:
            all_policies = self.graph_client.get_all_policies_summary()
            results = []

            search_lower = search_term.lower()

            # Search in each policy type
            for policy_type, policies in all_policies.items():
                for policy in policies:
                    name = policy.get('displayName', '').lower()
                    description = policy.get('description', '').lower()

                    if search_lower in name or search_lower in description:
                        results.append({
                            'type': policy_type,
                            'id': policy.get('id'),
                            'displayName': policy.get('displayName'),
                            'description': policy.get('description'),
                        })

            return {
                'success': True,
                'data': results,
                'count': len(results)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_defender_machines(self):
        """Get all machines from Defender XDR"""
        try:
            data = self.defender_client.get_machines()
            return {
                'success': True,
                'data': data.get('value', []),
                'count': len(data.get('value', []))
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_defender_alerts(self, filters=None):
        """Get security alerts from Defender XDR"""
        try:
            data = self.defender_client.get_alerts(filters)
            return {
                'success': True,
                'data': data.get('value', []),
                'count': len(data.get('value', []))
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def run_advanced_query(self, query):
        """
        Run advanced hunting query in Defender XDR

        Args:
            query: KQL query string

        Returns:
            Query results
        """
        try:
            data = self.defender_client.run_query(query)
            results = data.get('Results', [])
            return {
                'success': True,
                'data': results,
                'count': len(results),
                'schema': data.get('Schema', [])
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_managed_devices(self):
        """Get all managed devices from Intune"""
        try:
            devices = self.graph_client.get_managed_devices()
            return {
                'success': True,
                'data': devices,
                'count': len(devices)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
