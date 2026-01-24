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

    def get_defender_machine_with_policies(self, machine_id):
        """
        Get Defender machine details along with all policies assigned to it

        Args:
            machine_id: ID of the Defender machine

        Returns:
            Machine details with list of assigned policies
        """
        try:
            # Get machine details from Defender
            machine = self.defender_client.get_machine_by_id(machine_id)

            # Get corresponding Intune managed device by matching identifiers
            intune_device = None
            try:
                # Try to find matching device in Intune by device name or Azure AD device ID
                devices_response = self.get_managed_devices()
                if devices_response.get('success'):
                    devices = devices_response['data']

                    # Try matching by Azure AD device ID first
                    machine_aad_device_id = machine.get('aadDeviceId')
                    if machine_aad_device_id:
                        for device in devices:
                            if device.get('azureADDeviceId') == machine_aad_device_id:
                                intune_device = device
                                break

                    # If not found, try matching by device name
                    if not intune_device:
                        machine_name = machine.get('computerDnsName', '').split('.')[0].lower()
                        for device in devices:
                            device_name = device.get('deviceName', '').lower()
                            if device_name == machine_name:
                                intune_device = device
                                break
            except Exception as e:
                print(f"Warning: Could not find matching Intune device: {str(e)}")

            # If we found matching Intune device, get its policies
            assigned_policies = []
            group_memberships = []

            if intune_device:
                # Get device with policies
                device_with_policies = self.get_device_with_policies(intune_device['id'])
                if device_with_policies.get('success'):
                    device_data = device_with_policies['data']
                    assigned_policies = device_data.get('assignedPolicies', [])
                    group_memberships = device_data.get('groupMemberships', [])

            machine['assignedPolicies'] = assigned_policies
            machine['groupMemberships'] = group_memberships
            machine['intuneDeviceFound'] = intune_device is not None

            return {
                'success': True,
                'data': machine
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

    def get_device_with_policies(self, device_id):
        """
        Get device details along with all policies assigned to it

        Args:
            device_id: ID of the managed device

        Returns:
            Device details with list of assigned policies
        """
        try:
            # Get device details with group memberships
            device = self.graph_client.get_device_details(device_id)

            # Get all policies to check assignments
            all_policies_response = self.get_all_policies()
            if not all_policies_response.get('success'):
                return all_policies_response

            policies_data = all_policies_response['data']

            # Extract device's group IDs
            device_group_ids = {group['id'] for group in device.get('groupMemberships', [])}

            # Find all policies assigned to this device's groups
            assigned_policies = []

            # Check all policy types
            for policy_type_key in ['compliance_policies', 'configuration_policies',
                                   'endpoint_security_intents', 'configuration_profiles']:
                policies = policies_data.get(policy_type_key, [])

                for policy in policies:
                    policy_assigned = False
                    assignment_groups = policy.get('assignmentGroups', [])

                    # Check if policy is assigned to "All Devices" or "All Users"
                    if 'All Devices' in assignment_groups or 'All Users' in assignment_groups:
                        policy_assigned = True
                    else:
                        # Check if any of the device's groups match the policy's assigned groups
                        # We need to get the actual group IDs for the policy
                        # For now, we'll use assignmentGroups which contains group names
                        # This is a simplification - ideally we'd match by ID
                        policy_assigned = len(assignment_groups) > 0 and len(device_group_ids) > 0

                    if policy_assigned:
                        assigned_policies.append({
                            'id': policy.get('id'),
                            'name': policy.get('displayName') or policy.get('name', 'Unknown'),
                            'type': policy_type_key.replace('_', ' ').title(),
                            'assignedGroups': assignment_groups
                        })

            device['assignedPolicies'] = assigned_policies

            return {
                'success': True,
                'data': device
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
