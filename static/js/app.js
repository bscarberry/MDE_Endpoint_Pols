// Defender XDR Endpoint Policy Manager - Client-side JavaScript

// Global state
let allPoliciesData = null;

// Utility Functions
function showLoading() {
    document.getElementById('loadingSpinner').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingSpinner').style.display = 'none';
}

function showError(message) {
    alert('Error: ' + message);
}

function showModal(content) {
    const modal = document.getElementById('policyModal');
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = content;
    modal.style.display = 'block';
}

function closeModal() {
    document.getElementById('policyModal').style.display = 'none';
}

// View Management
function showDashboard() {
    // Show dashboard
    document.getElementById('dashboardSection').style.display = 'block';

    // Hide other sections
    hideQueryBuilder();
    document.getElementById('resultsSection').style.display = 'none';

    // Update nav
    updateActiveNav(0);
}

function showResultsSection() {
    // Hide dashboard
    document.getElementById('dashboardSection').style.display = 'none';

    // Hide query section
    hideQueryBuilder();

    // Show results section
    document.getElementById('resultsSection').style.display = 'block';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('policyModal');
    if (event.target == modal) {
        closeModal();
    }
}

// API Functions
async function fetchAPI(endpoint) {
    showLoading();
    try {
        const response = await fetch(endpoint);
        const data = await response.json();
        hideLoading();

        if (!data.success) {
            throw new Error(data.error || 'Request failed');
        }

        return data;
    } catch (error) {
        hideLoading();
        showError(error.message);
        throw error;
    }
}

async function postAPI(endpoint, payload) {
    showLoading();
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        hideLoading();

        if (!data.success) {
            throw new Error(data.error || 'Request failed');
        }

        return data;
    } catch (error) {
        hideLoading();
        showError(error.message);
        throw error;
    }
}

// Dashboard Functions
async function loadDashboard() {
    try {
        const data = await fetchAPI('/api/policies');
        allPoliciesData = data;

        // Update stats
        document.getElementById('compliancePolicyCount').textContent = data.counts.compliance_policies;
        document.getElementById('configPolicyCount').textContent = data.counts.configuration_policies;
        document.getElementById('securityPolicyCount').textContent = data.counts.endpoint_security_intents;

        // Load device count
        loadDeviceCount();

        // Display recent policies
        displayRecentPolicies(data.data);

    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

async function loadDeviceCount() {
    try {
        const data = await fetchAPI('/api/devices');
        document.getElementById('deviceCount').textContent = data.count || 0;
    } catch (error) {
        console.error('Failed to load device count:', error);
        document.getElementById('deviceCount').textContent = '-';
    }
}

function displayRecentPolicies(policies) {
    const container = document.getElementById('recentPolicies');
    let html = '';

    // Get first 9 policies from endpoint security (showing most relevant)
    const recentPolicies = [];

    if (policies.endpoint_security_intents && policies.endpoint_security_intents.length > 0) {
        recentPolicies.push(...policies.endpoint_security_intents.slice(0, 9));
    }

    if (recentPolicies.length === 0 && policies.compliance_policies && policies.compliance_policies.length > 0) {
        recentPolicies.push(...policies.compliance_policies.slice(0, 5));
    }

    if (recentPolicies.length === 0 && policies.configuration_policies && policies.configuration_policies.length > 0) {
        recentPolicies.push(...policies.configuration_policies.slice(0, 5));
    }

    if (recentPolicies.length === 0) {
        container.innerHTML = '<p class="text-muted">No policies found</p>';
        return;
    }

    recentPolicies.forEach(policy => {
        const displayName = getPolicyDisplayName(policy);
        const description = policy.description || 'No description available';
        const policyType = getPolicyType(policy);
        const category = categorizePolicyType(policy);

        const badgeClass = category.includes('Antivirus') || category.includes('EDR') ? 'badge-security' :
                          category.includes('Firewall') ? 'badge-compliance' :
                          category.includes('ASR') || category.includes('Attack Surface') ? 'badge-security' :
                          'badge-configuration';

        html += `
            <div class="policy-item" onclick="viewPolicyDetails('${policyType}', '${policy.id}')">
                <div class="policy-header">
                    <div class="policy-name">${displayName}</div>
                    <span class="policy-badge ${badgeClass}">${category}</span>
                </div>
                <div class="policy-description">${description}</div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// Policy Functions
async function loadPolicies() {
    try {
        const data = await fetchAPI('/api/policies');
        allPoliciesData = data;
        displayAllPolicies(data.data);
    } catch (error) {
        console.error('Failed to load policies:', error);
    }
}

function displayAllPolicies(policies) {
    showResultsSection();

    const resultsTitle = document.getElementById('resultsTitle');
    const resultsContent = document.getElementById('resultsContent');

    resultsTitle.textContent = 'All Endpoint Policies';
    updateActiveNav(1);

    let html = '<div class="policy-list">';

    // Compliance Policies
    if (policies.compliance_policies && policies.compliance_policies.length > 0) {
        html += '<h4>Compliance Policies</h4>';
        policies.compliance_policies.forEach(policy => {
            html += createPolicyCard(policy, 'compliance', 'badge-compliance');
        });
    }

    // Configuration Policies
    if (policies.configuration_policies && policies.configuration_policies.length > 0) {
        html += '<h4 class="mt-2">Configuration Policies</h4>';
        policies.configuration_policies.forEach(policy => {
            html += createPolicyCard(policy, 'configuration', 'badge-configuration');
        });
    }

    // Endpoint Security Intents
    if (policies.endpoint_security_intents && policies.endpoint_security_intents.length > 0) {
        html += '<h4 class="mt-2">Endpoint Security Policies</h4>';
        policies.endpoint_security_intents.forEach(policy => {
            html += createPolicyCard(policy, 'intent', 'badge-security');
        });
    }

    // Configuration Profiles
    if (policies.configuration_profiles && policies.configuration_profiles.length > 0) {
        html += '<h4 class="mt-2">Configuration Profiles (Settings Catalog)</h4>';
        policies.configuration_profiles.forEach(policy => {
            html += createPolicyCard(policy, 'configuration_profile', 'badge-configuration');
        });
    }

    html += '</div>';
    resultsContent.innerHTML = html;
}

function getPolicyDisplayName(policy) {
    return policy.displayName || policy.name || 'Unnamed Policy';
}

function getPolicyType(policy) {
    const name = getPolicyDisplayName(policy).toLowerCase();

    // Check policy source first
    if (policy.policySource) {
        if (policy.policySource === 'intents') return 'intent';
        if (policy.policySource === 'configurationPolicies') return 'configuration_profile';
        if (policy.policySource === 'windows10EndpointProtectionConfiguration') return 'configuration';
        if (policy.policySource === 'deviceConfigurations') return 'configuration';
    }

    // Fallback to checking @odata.type
    const odataType = policy['@odata.type'] || '';
    if (odataType.includes('windows10EndpointProtectionConfiguration')) return 'configuration';

    return 'configuration_profile';
}

function categorizePolicyType(policy) {
    const name = getPolicyDisplayName(policy).toLowerCase();

    // Categorize based on policy name
    if (name.includes('antivirus') || name.includes('defender') || name.includes('av -')) {
        return 'Antivirus';
    } else if (name.includes('firewall')) {
        return 'Firewall';
    } else if (name.includes('asr') || name.includes('attack surface')) {
        return 'Attack Surface Reduction';
    } else if (name.includes('edr') || name.includes('onboard')) {
        return 'EDR';
    } else if (name.includes('device control')) {
        return 'Device Control';
    } else if (name.includes('app control') || name.includes('wdac')) {
        return 'App Control';
    } else if (name.includes('bitlocker') || name.includes('encryption')) {
        return 'Encryption';
    }

    // Check template ID if available
    if (policy.templateId) {
        const templateId = policy.templateId.toLowerCase();
        if (templateId.includes('antivirus')) return 'Antivirus';
        if (templateId.includes('firewall')) return 'Firewall';
        if (templateId.includes('attacksurfacereduction')) return 'Attack Surface Reduction';
    }

    return 'Security Policy';
}

function createPolicyCard(policy, type, badgeClass) {
    const displayName = getPolicyDisplayName(policy);
    const description = policy.description || 'No description available';
    const policyType = getPolicyType(policy);
    const category = categorizePolicyType(policy);

    return `
        <div class="policy-item" onclick="viewPolicyDetails('${policyType}', '${policy.id}')">
            <div class="policy-header">
                <div class="policy-name">${displayName}</div>
                <div style="display: flex; gap: 8px;">
                    <span class="policy-badge ${badgeClass}">${category}</span>
                </div>
            </div>
            <div class="policy-description">${description}</div>
        </div>
    `;
}

async function viewPolicyDetails(policyType, policyId) {
    try {
        const data = await fetchAPI(`/api/policies/${policyType}/${policyId}`);
        const policy = data.data;

        const displayName = policy.displayName || policy.name || 'Policy Details';

        let html = `
            <h2>${displayName}</h2>
            <div style="margin-top: 20px;">
                <h3>Information</h3>
                <table class="data-table">
                    <tr>
                        <th>Property</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>ID</td>
                        <td>${policy.id}</td>
                    </tr>
                    <tr>
                        <td>Display Name</td>
                        <td>${displayName}</td>
                    </tr>
                    <tr>
                        <td>Description</td>
                        <td>${policy.description || 'N/A'}</td>
                    </tr>
                    <tr>
                        <td>Created</td>
                        <td>${policy.createdDateTime || 'N/A'}</td>
                    </tr>
                    <tr>
                        <td>Modified</td>
                        <td>${policy.lastModifiedDateTime || 'N/A'}</td>
                    </tr>
                </table>
        `;

        // Assignments
        if (policy.assignments && policy.assignments.length > 0) {
            html += '<h3 style="margin-top: 24px;">Assignments</h3>';
            html += '<table class="data-table"><tr><th>Group Name</th><th>Target Type</th></tr>';
            policy.assignments.forEach(assignment => {
                const groupName = assignment.groupName || assignment.target?.groupId || 'All Devices';
                const targetType = assignment.target?.['@odata.type'] || 'N/A';
                html += `<tr><td>${groupName}</td><td>${targetType}</td></tr>`;
            });
            html += '</table>';
        }

        // Settings (simplified JSON view)
        html += '<h3 style="margin-top: 24px;">Settings</h3>';
        html += '<pre style="background: var(--darker-bg); padding: 16px; border-radius: 8px; overflow-x: auto; max-height: 300px;">';
        html += JSON.stringify(policy, null, 2);
        html += '</pre>';

        html += '</div>';

        showModal(html);
    } catch (error) {
        console.error('Failed to load policy details:', error);
    }
}

// Device Functions
async function loadDevices() {
    try {
        const data = await fetchAPI('/api/devices');
        displayDevices(data.data);
    } catch (error) {
        console.error('Failed to load devices:', error);
    }
}

function displayDevices(devices) {
    showResultsSection();

    const resultsTitle = document.getElementById('resultsTitle');
    const resultsContent = document.getElementById('resultsContent');

    resultsTitle.textContent = `Managed Devices (${devices.length})`;
    updateActiveNav(2);

    let html = '<table class="data-table"><tr><th>Device Name</th><th>OS</th><th>Compliance</th><th>Last Sync</th></tr>';

    devices.forEach(device => {
        html += `
            <tr>
                <td>${device.deviceName || 'Unknown'}</td>
                <td>${device.operatingSystem || 'N/A'}</td>
                <td>${device.complianceState || 'Unknown'}</td>
                <td>${device.lastSyncDateTime || 'N/A'}</td>
            </tr>
        `;
    });

    html += '</table>';
    resultsContent.innerHTML = html;
}

// Defender Functions
async function loadMachines() {
    try {
        const data = await fetchAPI('/api/defender/machines');
        displayMachines(data.data);
    } catch (error) {
        console.error('Failed to load machines:', error);
    }
}

function displayMachines(machines) {
    showResultsSection();

    const resultsTitle = document.getElementById('resultsTitle');
    const resultsContent = document.getElementById('resultsContent');

    resultsTitle.textContent = `Defender Machines (${machines.length})`;
    updateActiveNav(3);

    let html = '<table class="data-table"><tr><th>Computer Name</th><th>OS Platform</th><th>Health Status</th><th>Risk Score</th></tr>';

    machines.forEach(machine => {
        html += `
            <tr>
                <td>${machine.computerDnsName || 'Unknown'}</td>
                <td>${machine.osPlatform || 'N/A'}</td>
                <td>${machine.healthStatus || 'Unknown'}</td>
                <td>${machine.riskScore || 'N/A'}</td>
            </tr>
        `;
    });

    html += '</table>';
    resultsContent.innerHTML = html;
}

async function loadAlerts() {
    try {
        const data = await fetchAPI('/api/defender/alerts');
        displayAlerts(data.data);
    } catch (error) {
        console.error('Failed to load alerts:', error);
    }
}

function displayAlerts(alerts) {
    showResultsSection();

    const resultsTitle = document.getElementById('resultsTitle');
    const resultsContent = document.getElementById('resultsContent');

    resultsTitle.textContent = `Security Alerts (${alerts.length})`;
    updateActiveNav(4);

    let html = '<table class="data-table"><tr><th>Title</th><th>Severity</th><th>Status</th><th>Created</th></tr>';

    alerts.forEach(alert => {
        html += `
            <tr>
                <td>${alert.title || 'Unknown'}</td>
                <td>${alert.severity || 'N/A'}</td>
                <td>${alert.status || 'Unknown'}</td>
                <td>${alert.createdDateTime || 'N/A'}</td>
            </tr>
        `;
    });

    html += '</table>';
    resultsContent.innerHTML = html;
}

// Query Functions
function showQueryBuilder() {
    // Hide dashboard
    document.getElementById('dashboardSection').style.display = 'none';

    // Hide results section
    document.getElementById('resultsSection').style.display = 'none';

    // Show query section
    document.getElementById('querySection').style.display = 'block';

    // Set active nav item
    updateActiveNav(5);
}

function hideQueryBuilder() {
    document.getElementById('querySection').style.display = 'none';
    document.getElementById('queryResults').innerHTML = '';
}

async function executeQuery() {
    const query = document.getElementById('queryInput').value.trim();

    if (!query) {
        showError('Please enter a query');
        return;
    }

    try {
        const data = await postAPI('/api/defender/query', { query });
        displayQueryResults(data);
    } catch (error) {
        console.error('Query failed:', error);
    }
}

function displayQueryResults(data) {
    const resultsDiv = document.getElementById('queryResults');

    if (!data.data || data.data.length === 0) {
        resultsDiv.innerHTML = '<p class="text-muted">No results found</p>';
        return;
    }

    // Create table from results
    const columns = Object.keys(data.data[0]);

    let html = `<h3 style="margin-top: 24px;">Results (${data.count})</h3>`;
    html += '<table class="data-table"><tr>';

    columns.forEach(col => {
        html += `<th>${col}</th>`;
    });
    html += '</tr>';

    data.data.forEach(row => {
        html += '<tr>';
        columns.forEach(col => {
            html += `<td>${row[col] !== null && row[col] !== undefined ? row[col] : 'N/A'}</td>`;
        });
        html += '</tr>';
    });

    html += '</table>';
    resultsDiv.innerHTML = html;
}

// Search Function
function handleSearch(event) {
    if (event.key === 'Enter') {
        const searchTerm = event.target.value.trim();
        if (searchTerm) {
            searchPolicies(searchTerm);
        }
    }
}

async function searchPolicies(searchTerm) {
    try {
        const data = await fetchAPI(`/api/search?q=${encodeURIComponent(searchTerm)}`);
        displaySearchResults(data, searchTerm);
    } catch (error) {
        console.error('Search failed:', error);
    }
}

function displaySearchResults(data, searchTerm) {
    hideQueryBuilder();

    const resultsSection = document.getElementById('resultsSection');
    const resultsTitle = document.getElementById('resultsTitle');
    const resultsContent = document.getElementById('resultsContent');

    resultsTitle.textContent = `Search Results for "${searchTerm}" (${data.count})`;
    resultsSection.style.display = 'block';

    if (data.count === 0) {
        resultsContent.innerHTML = '<p class="text-muted">No results found</p>';
        return;
    }

    let html = '<div class="policy-list">';

    data.data.forEach(policy => {
        const badgeClass = policy.type.includes('compliance') ? 'badge-compliance' :
                          policy.type.includes('configuration') ? 'badge-configuration' : 'badge-security';

        const policyType = policy.type.includes('intent') ? 'intent' :
                          policy.type.includes('configuration') ? 'configuration' : 'compliance';

        html += createPolicyCard({
            id: policy.id,
            displayName: policy.displayName,
            description: policy.description
        }, policyType, badgeClass);
    });

    html += '</div>';
    resultsContent.innerHTML = html;
}

// Navigation helper
function updateActiveNav(index) {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach((item, i) => {
        if (i === index) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}
