# API Documentation

This document describes the REST API endpoints available in the Defender XDR Endpoint Policy Manager application.

## Base URL

```
http://localhost:5000
```

## Response Format

All API responses follow this standard format:

### Success Response
```json
{
    "success": true,
    "data": { ... },
    "count": 0  // Optional, for list endpoints
}
```

### Error Response
```json
{
    "success": false,
    "error": "Error message description"
}
```

## Endpoints

### Health Check

Check the health and configuration status of the application.

**Endpoint:** `GET /api/health`

**Response:**
```json
{
    "status": "healthy",
    "configured": true
}
```

**Status Codes:**
- `200 OK` - Application is healthy and configured
- `500 Internal Server Error` - Configuration error

---

### Get All Policies

Retrieve all endpoint policies from Microsoft Graph API.

**Endpoint:** `GET /api/policies`

**Response:**
```json
{
    "success": true,
    "data": {
        "compliance_policies": [...],
        "configuration_policies": [...],
        "endpoint_security_intents": [...],
        "configuration_profiles": [...],
        "device_scripts": [...],
        "health_scripts": [...]
    },
    "counts": {
        "compliance_policies": 5,
        "configuration_policies": 10,
        "endpoint_security_intents": 8,
        "configuration_profiles": 3,
        "device_scripts": 2,
        "health_scripts": 1
    }
}
```

**Policy Types:**

- **compliance_policies**: Device compliance policies that define requirements devices must meet
- **configuration_policies**: Device configuration profiles
- **endpoint_security_intents**: Security policies (antivirus, firewall, ASR, etc.)
- **configuration_profiles**: Settings catalog configuration profiles
- **device_scripts**: PowerShell scripts for device management
- **health_scripts**: Device health monitoring scripts

**Status Codes:**
- `200 OK` - Successfully retrieved policies
- `500 Internal Server Error` - Failed to retrieve policies

---

### Get Policy Details

Retrieve detailed information about a specific policy including settings and assignments.

**Endpoint:** `GET /api/policies/<policy_type>/<policy_id>`

**Parameters:**
- `policy_type` - Type of policy (compliance, configuration, intent, configuration_profile)
- `policy_id` - UUID of the policy

**Example:**
```
GET /api/policies/compliance/12345678-1234-1234-1234-123456789abc
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": "12345678-1234-1234-1234-123456789abc",
        "displayName": "Windows 10 Compliance Policy",
        "description": "Compliance requirements for Windows 10 devices",
        "createdDateTime": "2024-01-15T10:30:00Z",
        "lastModifiedDateTime": "2024-01-20T14:45:00Z",
        "assignments": [
            {
                "id": "...",
                "target": {
                    "@odata.type": "#microsoft.graph.groupAssignmentTarget",
                    "groupId": "..."
                },
                "groupName": "All Windows Devices"
            }
        ],
        // Additional policy-specific settings
    }
}
```

**Status Codes:**
- `200 OK` - Successfully retrieved policy details
- `400 Bad Request` - Invalid policy type
- `500 Internal Server Error` - Failed to retrieve policy

---

### Search Policies

Search for policies by name or description.

**Endpoint:** `GET /api/search?q=<search_term>`

**Parameters:**
- `q` - Search term (query parameter)

**Example:**
```
GET /api/search?q=antivirus
```

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "type": "endpoint_security_intents",
            "id": "...",
            "displayName": "Antivirus Policy - Windows",
            "description": "Microsoft Defender Antivirus configuration"
        }
    ],
    "count": 1
}
```

**Status Codes:**
- `200 OK` - Search completed successfully
- `400 Bad Request` - Missing search term
- `500 Internal Server Error` - Search failed

---

### Get Managed Devices

Retrieve all Intune-managed devices.

**Endpoint:** `GET /api/devices`

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": "...",
            "deviceName": "DESKTOP-ABC123",
            "operatingSystem": "Windows",
            "osVersion": "10.0.19045",
            "complianceState": "compliant",
            "lastSyncDateTime": "2024-01-20T15:30:00Z",
            "emailAddress": "user@example.com",
            "userPrincipalName": "user@example.com"
        }
    ],
    "count": 150
}
```

**Status Codes:**
- `200 OK` - Successfully retrieved devices
- `500 Internal Server Error` - Failed to retrieve devices

---

### Get Defender Machines

Retrieve machine inventory from Microsoft Defender XDR.

**Endpoint:** `GET /api/defender/machines`

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": "...",
            "computerDnsName": "desktop-abc123.contoso.com",
            "osPlatform": "Windows10",
            "osVersion": "10.0.19045.3803",
            "healthStatus": "Active",
            "riskScore": "Medium",
            "exposureLevel": "Medium",
            "lastSeen": "2024-01-20T16:00:00Z"
        }
    ],
    "count": 145
}
```

**Status Codes:**
- `200 OK` - Successfully retrieved machines
- `500 Internal Server Error` - Failed to retrieve machines

---

### Get Security Alerts

Retrieve security alerts from Microsoft Defender XDR.

**Endpoint:** `GET /api/defender/alerts?filter=<odata_filter>`

**Parameters:**
- `filter` - Optional OData filter string

**Example:**
```
GET /api/defender/alerts?filter=severity eq 'High'
```

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": "...",
            "title": "Suspicious PowerShell activity detected",
            "description": "PowerShell executed with encoded command",
            "severity": "High",
            "status": "New",
            "category": "Execution",
            "createdDateTime": "2024-01-20T14:20:00Z",
            "machineId": "..."
        }
    ],
    "count": 25
}
```

**Status Codes:**
- `200 OK` - Successfully retrieved alerts
- `500 Internal Server Error` - Failed to retrieve alerts

---

### Run Advanced Hunting Query

Execute a KQL (Kusto Query Language) query for advanced threat hunting.

**Endpoint:** `POST /api/defender/query`

**Request Body:**
```json
{
    "query": "DeviceInfo | where OSPlatform == 'Windows10' | limit 10"
}
```

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "DeviceId": "...",
            "DeviceName": "DESKTOP-ABC123",
            "OSPlatform": "Windows10",
            "OSVersion": "10.0.19045.3803",
            "Timestamp": "2024-01-20T16:00:00Z"
        }
    ],
    "count": 10,
    "schema": [
        {
            "Name": "DeviceId",
            "Type": "String"
        },
        {
            "Name": "DeviceName",
            "Type": "String"
        }
    ]
}
```

**Supported Tables:**
Common tables available for querying:
- `DeviceInfo` - Device inventory and configuration
- `DeviceProcessEvents` - Process creation events
- `DeviceNetworkEvents` - Network connections
- `DeviceFileEvents` - File operations
- `DeviceRegistryEvents` - Registry modifications
- `DeviceLogonEvents` - Logon events
- `AlertInfo` - Alert information
- `AlertEvidence` - Evidence related to alerts

**Status Codes:**
- `200 OK` - Query executed successfully
- `400 Bad Request` - Missing or invalid query
- `500 Internal Server Error` - Query execution failed

---

### Clear Cache

Clear all cached API responses to force fresh data retrieval.

**Endpoint:** `POST /api/cache/clear`

**Description:**
The application caches policy and device data for improved performance. Use this endpoint to manually clear the cache when you need to see the most recent data immediately instead of waiting for the automatic cache expiry.

**Cache Durations:**
- Policy data (`/api/policies`): 10 minutes
- Device data (`/api/devices`): 5 minutes

**Response:**
```json
{
    "success": true,
    "message": "Cache cleared successfully"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/cache/clear
```

**Status Codes:**
- `200 OK` - Cache cleared successfully
- `500 Internal Server Error` - Failed to clear cache

---

## Authentication

The application uses Azure AD application credentials (Client ID and Secret) for authentication. All API calls to Microsoft services are authenticated using these credentials through the MSAL library.

Authentication tokens are:
- Automatically acquired on first request
- Cached for subsequent requests
- Automatically refreshed when expired

## Rate Limiting

Be aware of Microsoft API rate limits:

- **Microsoft Graph API**: 10,000 requests per 10 minutes per app per tenant
- **Microsoft Defender API**: Varies by endpoint, typically 45 requests per minute

The application implements **in-memory caching** to reduce API calls and improve performance:
- Most API responses are cached for 5-10 minutes
- Subsequent requests within the cache period are served from memory
- This dramatically reduces the number of API calls to Microsoft services
- Manual cache clearing is available via `POST /api/cache/clear`

## Error Codes

| HTTP Status | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Authentication failed |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error - Server-side error |

## Common Error Messages

### "Missing required environment variables"
The `.env` file is not configured correctly. Ensure `TENANT_ID`, `CLIENT_ID`, and `CLIENT_SECRET` are set.

### "Authentication failed"
- Check that your Azure AD credentials are correct
- Verify the client secret hasn't expired
- Ensure admin consent has been granted for API permissions

### "API request failed: 403"
The Azure AD application doesn't have sufficient permissions. Review and grant the required API permissions in Azure Portal.

### "API request failed: 404"
The requested resource (policy, device, etc.) doesn't exist or the ID is incorrect.

## Example Usage

### Using cURL

**Get all policies:**
```bash
curl http://localhost:5000/api/policies
```

**Search for policies:**
```bash
curl "http://localhost:5000/api/search?q=firewall"
```

**Run advanced hunting query:**
```bash
curl -X POST http://localhost:5000/api/defender/query \
  -H "Content-Type: application/json" \
  -d '{"query": "DeviceInfo | limit 5"}'
```

### Using Python

```python
import requests

# Get all policies
response = requests.get('http://localhost:5000/api/policies')
data = response.json()

if data['success']:
    print(f"Found {data['counts']['compliance_policies']} compliance policies")

# Run advanced hunting query
query_payload = {
    "query": "DeviceInfo | where OSPlatform == 'Windows10' | limit 10"
}
response = requests.post(
    'http://localhost:5000/api/defender/query',
    json=query_payload
)
results = response.json()

if results['success']:
    print(f"Query returned {results['count']} results")
```

### Using JavaScript (Fetch API)

```javascript
// Get all policies
fetch('/api/policies')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Policies:', data.data);
        }
    });

// Run advanced hunting query
fetch('/api/defender/query', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        query: 'DeviceInfo | limit 10'
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('Query results:', data.data);
    }
});
```

## Microsoft Graph API Resources

For more information about the underlying Microsoft APIs:

- [Microsoft Graph Device Management](https://docs.microsoft.com/en-us/graph/api/resources/intune-graph-overview)
- [Device Compliance Policies](https://docs.microsoft.com/en-us/graph/api/resources/intune-deviceconfig-devicecompliancepolicy)
- [Device Configurations](https://docs.microsoft.com/en-us/graph/api/resources/intune-deviceconfig-deviceconfiguration)
- [Microsoft Defender API](https://docs.microsoft.com/en-us/microsoft-365/security/defender-endpoint/api/apis-intro)
- [Advanced Hunting KQL Reference](https://docs.microsoft.com/en-us/microsoft-365/security/defender/advanced-hunting-query-language)
