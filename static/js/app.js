// Defender XDR Endpoint Policy Manager - Client-side JavaScript

// Global state
let allPoliciesData = null;

// HTML Escaping - prevents XSS when inserting API data into the DOM
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    console.log('Initializing theme:', savedTheme);
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);

    // Recreate charts with new theme colors
    if (allPoliciesData && allPoliciesData.data) {
        createDashboardCharts(allPoliciesData.data);
    }
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('themeIcon');
    console.log('Updating theme icon:', theme, 'Icon element:', icon);
    if (icon) {
        icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        console.log('Icon class set to:', icon.className);
    } else {
        console.error('Theme icon element not found!');
    }
}

// Mobile Menu Management
function toggleMobileMenu() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.mobile-overlay');
    const toggle = document.querySelector('.mobile-menu-toggle');

    sidebar.classList.toggle('active');
    overlay.classList.toggle('active');
    toggle.classList.toggle('active');
}

function closeMobileMenu() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.mobile-overlay');
    const toggle = document.querySelector('.mobile-menu-toggle');

    sidebar.classList.remove('active');
    overlay.classList.remove('active');
    toggle.classList.remove('active');
}

// Initialize theme and dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    initTheme();

    // Load dashboard if we're on the home page
    const dashboardSection = document.getElementById('dashboardSection');
    if (dashboardSection) {
        loadDashboard();
    }
});

// Utility Functions
function showLoading() {
    document.getElementById('loadingSpinner').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingSpinner').style.display = 'none';
}

function showError(message) {
    const toast = document.getElementById('toastNotification');
    const toastMsg = document.getElementById('toastMessage');
    if (toast && toastMsg) {
        toastMsg.textContent = message;
        toast.style.display = 'flex';
        // Auto-hide after 8 seconds
        clearTimeout(window._toastTimeout);
        window._toastTimeout = setTimeout(hideToast, 8000);
    } else {
        // Fallback if toast element not found
        console.error('Error:', message);
    }
}

function hideToast() {
    const toast = document.getElementById('toastNotification');
    if (toast) {
        toast.style.display = 'none';
    }
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
    // Close mobile menu if open
    closeMobileMenu();

    // Show dashboard
    document.getElementById('dashboardSection').style.display = 'block';

    // Hide other sections
    hideQueryBuilder();
    document.getElementById('resultsSection').style.display = 'none';

    // Update nav
    updateActiveNav(0);
}

function showResultsSection() {
    // Close mobile menu if open
    closeMobileMenu();

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
                'Content-Type': 'application/json',
                'X-CSRF-Token': window.CSRF_TOKEN || ''
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
        console.log('Loading dashboard...');
        const data = await fetchAPI('/api/policies');
        console.log('Dashboard data loaded:', data);
        allPoliciesData = data;

        // Update stats
        if (data.counts) {
            document.getElementById('compliancePolicyCount').textContent = data.counts.compliance_policies || 0;
            document.getElementById('configPolicyCount').textContent = data.counts.configuration_policies || 0;
            document.getElementById('securityPolicyCount').textContent = data.counts.endpoint_security_intents || 0;
        } else {
            console.error('No counts data in response');
        }

        // Load device count
        loadDeviceCount();

        // Create dashboard charts
        if (data.data) {
            createDashboardCharts(data.data);
        } else {
            console.error('No policy data in response');
        }

    } catch (error) {
        console.error('Failed to load dashboard:', error);
        // Show error to user
        showError('Failed to load dashboard: ' + error.message);
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

// Store chart instances globally for cleanup
let dashboardCharts = {
    category: null,
    assignment: null,
    platform: null,
    type: null
};

// Get theme-aware colors
function getChartColors() {
    const theme = document.documentElement.getAttribute('data-theme') || 'dark';
    const isLight = theme === 'light';

    return {
        green: isLight ? '#047857' : '#10b981',
        blue: isLight ? '#0369a1' : '#3b82f6',
        orange: isLight ? '#c2410c' : '#f59e0b',
        red: isLight ? '#b91c1c' : '#ef4444',
        purple: isLight ? '#7c3aed' : '#8b5cf6',
        pink: isLight ? '#be185d' : '#ec4899',
        teal: isLight ? '#0f766e' : '#14b8a6',
        amber: isLight ? '#d97706' : '#fb923c',
        gray: isLight ? '#64748b' : '#6b7280',
        gridColor: isLight ? 'rgba(226, 232, 240, 0.3)' : 'rgba(107, 114, 128, 0.1)',
        textColor: isLight ? '#475569' : '#9ca3af',
        tooltipBg: isLight ? '#ffffff' : '#111827',
        tooltipBorder: isLight ? '#e2e8f0' : '#374151',
        backgroundColor: isLight ? [
            'rgba(4, 120, 87, 0.8)',
            'rgba(3, 105, 161, 0.8)',
            'rgba(194, 65, 12, 0.8)',
            'rgba(185, 28, 28, 0.8)',
            'rgba(124, 58, 237, 0.8)',
            'rgba(190, 24, 93, 0.8)',
            'rgba(15, 118, 110, 0.8)',
            'rgba(217, 119, 6, 0.8)'
        ] : [
            'rgba(16, 185, 129, 0.8)',
            'rgba(59, 130, 246, 0.8)',
            'rgba(245, 158, 11, 0.8)',
            'rgba(239, 68, 68, 0.8)',
            'rgba(139, 92, 246, 0.8)',
            'rgba(236, 72, 153, 0.8)',
            'rgba(20, 184, 166, 0.8)',
            'rgba(251, 146, 60, 0.8)'
        ]
    };
}

function createDashboardCharts(policies) {
    // Destroy existing charts
    Object.values(dashboardCharts).forEach(chart => {
        if (chart) chart.destroy();
    });

    // Collect all policies into single array for analysis
    const allPolicies = [
        ...(policies.compliance_policies || []),
        ...(policies.configuration_policies || []),
        ...(policies.endpoint_security_intents || []),
        ...(policies.configuration_profiles || [])
    ];

    // Deduplicate by ID
    const policyMap = new Map();
    allPolicies.forEach(p => {
        if (!policyMap.has(p.id)) {
            policyMap.set(p.id, p);
        }
    });
    const uniquePolicies = Array.from(policyMap.values());

    // Create charts
    dashboardCharts.category = createCategoryChart(uniquePolicies);
    dashboardCharts.assignment = createAssignmentChart(uniquePolicies);
    dashboardCharts.platform = createPlatformChart(uniquePolicies);
    dashboardCharts.type = createTypeChart(policies);
}

function createCategoryChart(policies) {
    const categoryCounts = {};
    const colors = getChartColors();

    policies.forEach(policy => {
        const category = categorizePolicyType(policy);
        categoryCounts[category] = (categoryCounts[category] || 0) + 1;
    });

    const ctx = document.getElementById('categoryChart');
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(categoryCounts),
            datasets: [{
                data: Object.values(categoryCounts),
                backgroundColor: colors.backgroundColor,
                borderColor: colors.tooltipBorder,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: colors.textColor,
                        font: {
                            family: 'JetBrains Mono',
                            size: 11
                        },
                        padding: 12
                    }
                },
                tooltip: {
                    backgroundColor: colors.tooltipBg,
                    titleColor: colors.green,
                    bodyColor: colors.textColor,
                    borderColor: colors.tooltipBorder,
                    borderWidth: 1,
                    titleFont: {
                        family: 'JetBrains Mono'
                    },
                    bodyFont: {
                        family: 'JetBrains Mono'
                    }
                }
            }
        }
    });
}

function createAssignmentChart(policies) {
    const colors = getChartColors();
    let assigned = 0;
    let unassigned = 0;

    policies.forEach(policy => {
        const assignmentCount = policy.assignmentCount || 0;
        if (assignmentCount > 0) {
            assigned++;
        } else {
            unassigned++;
        }
    });

    const ctx = document.getElementById('assignmentChart');
    if (!ctx) return null;

    const theme = document.documentElement.getAttribute('data-theme') || 'dark';
    const grayColor = theme === 'light' ? 'rgba(100, 116, 139, 0.5)' : 'rgba(107, 114, 128, 0.5)';

    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Assigned', 'Unassigned'],
            datasets: [{
                data: [assigned, unassigned],
                backgroundColor: [colors.backgroundColor[0], grayColor],
                borderColor: colors.tooltipBorder,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: colors.textColor,
                        font: {
                            family: 'JetBrains Mono',
                            size: 11
                        },
                        padding: 12
                    }
                },
                tooltip: {
                    backgroundColor: colors.tooltipBg,
                    titleColor: colors.green,
                    bodyColor: colors.textColor,
                    borderColor: colors.tooltipBorder,
                    borderWidth: 1,
                    titleFont: {
                        family: 'JetBrains Mono'
                    },
                    bodyFont: {
                        family: 'JetBrains Mono'
                    }
                }
            }
        }
    });
}

function createPlatformChart(policies) {
    const colors = getChartColors();
    const platformCounts = {};

    policies.forEach(policy => {
        const platform = getPolicyPlatform(policy);
        platformCounts[platform] = (platformCounts[platform] || 0) + 1;
    });

    const ctx = document.getElementById('platformChart');
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(platformCounts),
            datasets: [{
                label: 'Policies',
                data: Object.values(platformCounts),
                backgroundColor: colors.backgroundColor[0],
                borderColor: colors.green,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: colors.textColor,
                        font: {
                            family: 'JetBrains Mono'
                        },
                        stepSize: 1
                    },
                    grid: {
                        color: colors.gridColor
                    }
                },
                x: {
                    ticks: {
                        color: colors.textColor,
                        font: {
                            family: 'JetBrains Mono',
                            size: 10
                        }
                    },
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: colors.tooltipBg,
                    titleColor: colors.green,
                    bodyColor: colors.textColor,
                    borderColor: colors.tooltipBorder,
                    borderWidth: 1,
                    titleFont: {
                        family: 'JetBrains Mono'
                    },
                    bodyFont: {
                        family: 'JetBrains Mono'
                    }
                }
            }
        }
    });
}

function createTypeChart(policies) {
    const colors = getChartColors();
    const typeCounts = {
        'Compliance': policies.compliance_policies?.length || 0,
        'Configuration': policies.configuration_policies?.length || 0,
        'Endpoint Security': policies.endpoint_security_intents?.length || 0,
        'Settings Catalog': policies.configuration_profiles?.length || 0
    };

    const ctx = document.getElementById('typeChart');
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(typeCounts),
            datasets: [{
                label: 'Policies',
                data: Object.values(typeCounts),
                backgroundColor: [
                    colors.blue,
                    colors.green,
                    colors.red,
                    colors.orange
                ],
                borderColor: [
                    colors.blue,
                    colors.green,
                    colors.red,
                    colors.orange
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: colors.textColor,
                        font: {
                            family: 'JetBrains Mono'
                        },
                        stepSize: 1
                    },
                    grid: {
                        color: colors.gridColor
                    }
                },
                x: {
                    ticks: {
                        color: colors.textColor,
                        font: {
                            family: 'JetBrains Mono',
                            size: 10
                        }
                    },
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: colors.tooltipBg,
                    titleColor: colors.green,
                    bodyColor: colors.textColor,
                    borderColor: colors.tooltipBorder,
                    borderWidth: 1,
                    titleFont: {
                        family: 'JetBrains Mono'
                    },
                    bodyFont: {
                        family: 'JetBrains Mono'
                    }
                }
            }
        }
    });
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

    resultsTitle.textContent = 'all_endpoint_policies';
    updateActiveNav(1);

    console.log('Policies data:', policies);

    // Use a Map to deduplicate policies by ID
    const policyMap = new Map();

    // Collect all policies, deduplicating by ID (keep first occurrence)
    if (policies.compliance_policies) {
        console.log('Compliance policies:', policies.compliance_policies.length);
        policies.compliance_policies.forEach(p => {
            if (!policyMap.has(p.id)) {
                policyMap.set(p.id, {...p, sourceType: 'Compliance Policy'});
            }
        });
    }

    if (policies.configuration_policies) {
        console.log('Configuration policies:', policies.configuration_policies.length);
        policies.configuration_policies.forEach(p => {
            if (!policyMap.has(p.id)) {
                policyMap.set(p.id, {...p, sourceType: 'Configuration Policy'});
            }
        });
    }

    if (policies.endpoint_security_intents) {
        console.log('Endpoint security intents:', policies.endpoint_security_intents.length);
        policies.endpoint_security_intents.forEach(p => {
            if (!policyMap.has(p.id)) {
                policyMap.set(p.id, {...p, sourceType: 'Endpoint Security'});
            }
        });
    }

    if (policies.configuration_profiles) {
        console.log('Configuration profiles:', policies.configuration_profiles.length);
        policies.configuration_profiles.forEach(p => {
            if (!policyMap.has(p.id)) {
                policyMap.set(p.id, {...p, sourceType: 'Settings Catalog'});
            }
        });
    }

    // Convert map to array for display
    const allPolicies = Array.from(policyMap.values());
    const totalCount = allPolicies.length;

    console.log('Total unique policies:', totalCount);
    console.log('All policies array:', allPolicies);

    if (totalCount === 0) {
        resultsContent.innerHTML = '<p class="text-muted">No policies found</p>';
        return;
    }

    // Store policies globally for filtering and sorting
    window.allPoliciesData = allPolicies;
    window.currentSortColumn = null;
    window.currentSortDirection = 'asc';

    // Extract unique values for filters
    const categories = [...new Set(allPolicies.map(p => categorizePolicyType(p)))].sort();
    const types = [...new Set(allPolicies.map(p => p.sourceType))].sort();
    const platforms = [...new Set(allPolicies.map(p => getPolicyPlatform(p)))].sort();

    // Create filters and table
    let html = `
        <div style="margin-bottom: 24px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <p><strong>Total Policies: <span id="filteredCount">${totalCount}</span> / ${totalCount}</strong></p>
                <button class="btn-secondary" onclick="clearAllFilters()" style="padding: 6px 12px; font-size: 12px;">
                    <i class="fas fa-times"></i> clear_filters()
                </button>
            </div>

            <div class="filter-grid">
                <div class="filter-group">
                    <label class="filter-label">Category</label>
                    <select id="filterCategory" multiple class="filter-select" onchange="applyFilters()">
                        ${categories.map(cat => `<option value="${cat}">${cat}</option>`).join('')}
                    </select>
                </div>

                <div class="filter-group">
                    <label class="filter-label">Type</label>
                    <select id="filterType" multiple class="filter-select" onchange="applyFilters()">
                        ${types.map(type => `<option value="${type}">${type}</option>`).join('')}
                    </select>
                </div>

                <div class="filter-group">
                    <label class="filter-label">Platform</label>
                    <select id="filterPlatform" multiple class="filter-select" onchange="applyFilters()">
                        ${platforms.map(plat => `<option value="${plat}">${plat}</option>`).join('')}
                    </select>
                </div>

                <div class="filter-group">
                    <label class="filter-label">Assignments</label>
                    <select id="filterAssignments" class="filter-select" onchange="applyFilters()">
                        <option value="">All</option>
                        <option value="assigned">Assigned (> 0)</option>
                        <option value="unassigned">Unassigned (0)</option>
                    </select>
                </div>

                <div class="filter-group">
                    <label class="filter-label">Group Name</label>
                    <input type="text" id="filterGroupName" class="filter-select" placeholder="Enter group name..." oninput="applyFilters()" style="padding: 8px;">
                </div>
            </div>
        </div>

        <table class="data-table">
            <thead>
                <tr>
                    <th onclick="sortTable('name')" style="cursor: pointer;">
                        Policy Name <span id="sort-name" class="sort-indicator"></span>
                    </th>
                    <th onclick="sortTable('category')" style="cursor: pointer;">
                        Category <span id="sort-category" class="sort-indicator"></span>
                    </th>
                    <th onclick="sortTable('type')" style="cursor: pointer;">
                        Type <span id="sort-type" class="sort-indicator"></span>
                    </th>
                    <th onclick="sortTable('platform')" style="cursor: pointer;">
                        Platform <span id="sort-platform" class="sort-indicator"></span>
                    </th>
                    <th onclick="sortTable('assignments')" style="cursor: pointer;">
                        Assignments <span id="sort-assignments" class="sort-indicator"></span>
                    </th>
                    <th onclick="sortTable('created')" style="cursor: pointer;">
                        Created <span id="sort-created" class="sort-indicator"></span>
                    </th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="policyTableBody">
    `;

    try {
        allPolicies.forEach((policy, index) => {
            const displayName = getPolicyDisplayName(policy);
            const category = categorizePolicyType(policy);
            const policyType = getPolicyType(policy);
            const sourceType = policy.sourceType || 'Unknown';
            const platform = getPolicyPlatform(policy);
            const assignmentCount = policy.assignmentCount !== undefined ? policy.assignmentCount : 0;
            const assignmentText = assignmentCount + ' group(s)';
            const assignmentGroups = policy.assignmentGroups || [];
            const groupNamesStr = assignmentGroups.join('|').toLowerCase();

            // Format created date
            const createdDate = policy.createdDateTime || policy.creationDate;
            const createdText = createdDate ? new Date(createdDate).toLocaleDateString() : 'N/A';
            const createdSort = createdDate ? new Date(createdDate).getTime() : 0;

            html += `
                <tr data-index="${index}"
                    data-category="${escapeHtml(category)}"
                    data-type="${escapeHtml(sourceType)}"
                    data-platform="${escapeHtml(platform)}"
                    data-assignments="${assignmentCount}"
                    data-name="${escapeHtml(displayName.toLowerCase())}"
                    data-created="${createdSort}"
                    data-groups="${escapeHtml(groupNamesStr)}"
                    onclick="viewPolicyDetails('${escapeHtml(policyType)}', '${escapeHtml(policy.id)}')" style="cursor: pointer;">
                    <td><strong>${escapeHtml(displayName)}</strong></td>
                    <td><span class="policy-badge badge-security" style="font-size: 12px;">${escapeHtml(category)}</span></td>
                    <td>${escapeHtml(sourceType)}</td>
                    <td>${escapeHtml(platform)}</td>
                    <td>${escapeHtml(assignmentText)}</td>
                    <td style="font-size: 12px; color: var(--text-secondary);">${escapeHtml(createdText)}</td>
                    <td>
                        <button class="btn btn-secondary" style="padding: 4px 12px; font-size: 12px;"
                                onclick="event.stopPropagation(); viewPolicyDetails('${escapeHtml(policyType)}', '${escapeHtml(policy.id)}')">
                            View
                        </button>
                    </td>
                </tr>
            `;
        });
    } catch (error) {
        console.error('Error building table:', error);
        resultsContent.innerHTML = `<p class="text-muted">Error displaying policies: ${escapeHtml(error.message)}</p>`;
        return;
    }

    html += `
            </tbody>
        </table>
    `;

    resultsContent.innerHTML = html;
    console.log('Table rendered successfully');
}

function getPolicyPlatform(policy) {
    const name = getPolicyDisplayName(policy).toLowerCase();
    const odataType = policy['@odata.type'] || '';

    // Check policy name for platform indicators
    if (name.includes('macos') || name.includes('mac os')) {
        return 'macOS';
    } else if (name.includes('ios')) {
        return 'iOS';
    } else if (name.includes('android')) {
        return 'Android';
    } else if (name.includes('windows') || name.includes('win -') || name.includes('win-')) {
        return 'Windows';
    }

    // Check @odata.type for platform
    if (odataType.includes('windows')) {
        return 'Windows';
    } else if (odataType.includes('macOS') || odataType.includes('mac')) {
        return 'macOS';
    } else if (odataType.includes('ios')) {
        return 'iOS';
    } else if (odataType.includes('android')) {
        return 'Android';
    }

    // Check policy platforms array if available
    if (policy.platforms && Array.isArray(policy.platforms) && policy.platforms.length > 0) {
        return policy.platforms.join(', ');
    }

    return 'Multi-platform';
}

function getPolicyDisplayName(policy) {
    return policy.displayName || policy.name || 'Unnamed Policy';
}

function getPolicyType(policy) {
    const name = getPolicyDisplayName(policy).toLowerCase();

    // Check policySource first (set by backend - most accurate)
    if (policy.policySource) {
        if (policy.policySource === 'intents') return 'intent';
        if (policy.policySource === 'configurationPolicies') return 'configuration_profile';
        if (policy.policySource === 'windows10EndpointProtectionConfiguration') return 'configuration';
        if (policy.policySource === 'deviceConfigurations') return 'configuration';
    }

    // Check sourceType (set when displaying in table)
    if (policy.sourceType) {
        if (policy.sourceType === 'Compliance Policy') return 'compliance';
        if (policy.sourceType === 'Configuration Policy') return 'configuration';
        if (policy.sourceType === 'Endpoint Security') return 'intent';
        if (policy.sourceType === 'Settings Catalog') return 'configuration_profile';
    }

    // Fallback to checking @odata.type
    const odataType = policy['@odata.type'] || '';
    if (odataType.includes('deviceCompliancePolicy')) return 'compliance';
    if (odataType.includes('windows10EndpointProtectionConfiguration')) return 'configuration';

    return 'configuration_profile';
}

function categorizePolicyType(policy) {
    // First check templateFamily for accurate categorization
    if (policy.templateReference && policy.templateReference.templateFamily) {
        const family = policy.templateReference.templateFamily.toLowerCase();
        if (family.includes('antivirus') || family.includes('defender')) return 'Antivirus';
        if (family.includes('firewall')) return 'Firewall';
        if (family.includes('attacksurfacereduction') || family.includes('asr')) return 'Attack Surface Reduction';
        if (family.includes('devicecontrol')) return 'Device Control';
        if (family.includes('accountprotection')) return 'Account Protection';
        if (family.includes('applicationcontrol')) return 'App Control';
        if (family.includes('bitlocker') || family.includes('encryption')) return 'Encryption';
        if (family.includes('edr') || family.includes('onboarding')) return 'EDR';
    }

    // Check templateDisplayName
    if (policy.templateReference && policy.templateReference.templateDisplayName) {
        const displayName = policy.templateReference.templateDisplayName.toLowerCase();
        if (displayName.includes('antivirus')) return 'Antivirus';
        if (displayName.includes('firewall')) return 'Firewall';
        if (displayName.includes('attack surface')) return 'Attack Surface Reduction';
        if (displayName.includes('device control')) return 'Device Control';
        if (displayName.includes('account protection')) return 'Account Protection';
        if (displayName.includes('application control') || displayName.includes('app control')) return 'App Control';
        if (displayName.includes('bitlocker') || displayName.includes('encryption')) return 'Encryption';
        if (displayName.includes('edr') || displayName.includes('onboard')) return 'EDR';
    }

    // Fall back to policy name
    const name = getPolicyDisplayName(policy).toLowerCase();
    if (name.includes('antivirus') || name.includes('defender') || name.includes('av -')) {
        return 'Antivirus';
    } else if (name.includes('firewall') || name.includes('mdfw')) {
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
        <div class="policy-item" onclick="viewPolicyDetails('${escapeHtml(policyType)}', '${escapeHtml(policy.id)}')">
            <div class="policy-header">
                <div class="policy-name">${escapeHtml(displayName)}</div>
                <div style="display: flex; gap: 8px;">
                    <span class="policy-badge ${badgeClass}">${escapeHtml(category)}</span>
                </div>
            </div>
            <div class="policy-description">${escapeHtml(description)}</div>
        </div>
    `;
}

async function viewPolicyDetails(policyType, policyId) {
    try {
        const data = await fetchAPI(`/api/policies/${policyType}/${policyId}`);
        const policy = data.data;

        const displayName = policy.displayName || policy.name || 'Policy Details';

        let html = `
            <h2>${escapeHtml(displayName)}</h2>
            <div style="margin-top: 20px;">
                <h3>Information</h3>
                <table class="data-table">
                    <tr>
                        <th>Property</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>ID</td>
                        <td>${escapeHtml(policy.id)}</td>
                    </tr>
                    <tr>
                        <td>Display Name</td>
                        <td>${escapeHtml(displayName)}</td>
                    </tr>
                    <tr>
                        <td>Description</td>
                        <td>${escapeHtml(policy.description || 'N/A')}</td>
                    </tr>
                    <tr>
                        <td>Created</td>
                        <td>${escapeHtml(policy.createdDateTime || 'N/A')}</td>
                    </tr>
                    <tr>
                        <td>Modified</td>
                        <td>${escapeHtml(policy.lastModifiedDateTime || 'N/A')}</td>
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
                html += `<tr><td>${escapeHtml(groupName)}</td><td>${escapeHtml(targetType)}</td></tr>`;
            });
            html += '</table>';
        }

        // Settings (simplified JSON view)
        html += '<h3 style="margin-top: 24px;">Settings</h3>';
        html += '<pre style="background: var(--darker-bg); padding: 16px; border-radius: 8px; overflow-x: auto; max-height: 300px;">';
        html += escapeHtml(JSON.stringify(policy, null, 2));
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

    let html = '<table class="data-table"><tr><th>Device Name</th><th>OS</th><th>Compliance</th><th>Last Sync</th><th>Actions</th></tr>';

    devices.forEach(device => {
        const lastSync = device.lastSyncDateTime ? new Date(device.lastSyncDateTime).toLocaleString() : 'N/A';
        html += `
            <tr onclick="viewDeviceDetails('${escapeHtml(device.id)}')" style="cursor: pointer;">
                <td><strong>${escapeHtml(device.deviceName || 'Unknown')}</strong></td>
                <td>${escapeHtml(device.operatingSystem || 'N/A')}</td>
                <td><span class="policy-badge" style="font-size: 12px;">${escapeHtml(device.complianceState || 'Unknown')}</span></td>
                <td style="font-size: 12px;">${escapeHtml(lastSync)}</td>
                <td>
                    <button class="btn btn-secondary" style="padding: 4px 12px; font-size: 12px;"
                            onclick="event.stopPropagation(); viewDeviceDetails('${escapeHtml(device.id)}')">
                        View Details
                    </button>
                </td>
            </tr>
        `;
    });

    html += '</table>';
    resultsContent.innerHTML = html;
}

async function viewDeviceDetails(deviceId) {
    try {
        const data = await fetchAPI(`/api/devices/${deviceId}`);
        const device = data.data;

        const deviceName = device.deviceName || 'Unknown Device';
        const assignedPolicies = device.assignedPolicies || [];
        const groupMemberships = device.groupMemberships || [];

        let html = `
            <h2>${escapeHtml(deviceName)}</h2>
            <div style="margin-top: 20px;">
                <h3>Device Information</h3>
                <table class="data-table">
                    <tr><th>Property</th><th>Value</th></tr>
                    <tr><td>Device Name</td><td>${escapeHtml(device.deviceName || 'N/A')}</td></tr>
                    <tr><td>Operating System</td><td>${escapeHtml(device.operatingSystem || 'N/A')} ${escapeHtml(device.osVersion || '')}</td></tr>
                    <tr><td>Compliance State</td><td>${escapeHtml(device.complianceState || 'Unknown')}</td></tr>
                    <tr><td>Enrollment Date</td><td>${escapeHtml(device.enrolledDateTime ? new Date(device.enrolledDateTime).toLocaleString() : 'N/A')}</td></tr>
                    <tr><td>Last Sync</td><td>${escapeHtml(device.lastSyncDateTime ? new Date(device.lastSyncDateTime).toLocaleString() : 'N/A')}</td></tr>
                    <tr><td>Serial Number</td><td>${escapeHtml(device.serialNumber || 'N/A')}</td></tr>
                    <tr><td>Model</td><td>${escapeHtml(device.model || 'N/A')}</td></tr>
                    <tr><td>Manufacturer</td><td>${escapeHtml(device.manufacturer || 'N/A')}</td></tr>
                </table>

                <h3 style="margin-top: 24px;">Group Memberships (${groupMemberships.length})</h3>
        `;

        if (groupMemberships.length > 0) {
            html += '<table class="data-table"><tr><th>Group Name</th></tr>';
            groupMemberships.forEach(group => {
                html += `<tr><td>${escapeHtml(group.displayName)}</td></tr>`;
            });
            html += '</table>';
        } else {
            html += '<p class="text-muted">No group memberships found</p>';
        }

        html += `
                <h3 style="margin-top: 24px;">Assigned Policies (${assignedPolicies.length})</h3>
        `;

        if (assignedPolicies.length > 0) {
            html += '<table class="data-table"><tr><th>Policy Name</th><th>Type</th><th>Assigned Via</th></tr>';
            assignedPolicies.forEach(policy => {
                const assignedGroups = policy.assignedGroups.join(', ') || 'Direct Assignment';
                html += `
                    <tr>
                        <td><strong>${escapeHtml(policy.name)}</strong></td>
                        <td><span class="policy-badge" style="font-size: 12px;">${escapeHtml(policy.type)}</span></td>
                        <td style="font-size: 12px;">${escapeHtml(assignedGroups)}</td>
                    </tr>
                `;
            });
            html += '</table>';
        } else {
            html += '<p class="text-muted">No policies assigned to this device</p>';
        }

        html += '</div>';

        showModal(html);
    } catch (error) {
        console.error('Failed to load device details:', error);
    }
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

    let html = '<table class="data-table"><tr><th>Computer Name</th><th>OS Platform</th><th>Onboarded Status</th><th>Health Status</th><th>Risk Score</th><th>Actions</th></tr>';

    machines.forEach(machine => {
        const onboardingStatus = machine.onboardingStatus || 'Unknown';
        const healthStatus = machine.healthStatus || 'Unknown';
        const riskScore = machine.riskScore || 'N/A';
        const lastSeen = machine.lastSeen ? new Date(machine.lastSeen).toLocaleString() : 'N/A';

        html += `
            <tr onclick="viewMachineDetails('${escapeHtml(machine.id)}')" style="cursor: pointer;">
                <td><strong>${escapeHtml(machine.computerDnsName || 'Unknown')}</strong></td>
                <td>${escapeHtml(machine.osPlatform || 'N/A')}</td>
                <td><span class="policy-badge" style="font-size: 12px;">${escapeHtml(onboardingStatus)}</span></td>
                <td><span class="policy-badge" style="font-size: 12px;">${escapeHtml(healthStatus)}</span></td>
                <td>${escapeHtml(riskScore)}</td>
                <td>
                    <button class="btn btn-secondary" style="padding: 4px 12px; font-size: 12px;"
                            onclick="event.stopPropagation(); viewMachineDetails('${escapeHtml(machine.id)}')">
                        View Details
                    </button>
                </td>
            </tr>
        `;
    });

    html += '</table>';
    resultsContent.innerHTML = html;
}

async function viewMachineDetails(machineId) {
    try {
        const data = await fetchAPI(`/api/defender/machines/${machineId}`);
        const machine = data.data;

        const machineName = machine.computerDnsName || 'Unknown Machine';
        const assignedPolicies = machine.assignedPolicies || [];
        const groupMemberships = machine.groupMemberships || [];
        const intuneDeviceFound = machine.intuneDeviceFound || false;

        let html = `
            <h2>${escapeHtml(machineName)}</h2>
            <div style="margin-top: 20px;">
                <h3>Machine Information</h3>
                <table class="data-table">
                    <tr><th>Property</th><th>Value</th></tr>
                    <tr><td>Computer Name</td><td>${escapeHtml(machine.computerDnsName || 'N/A')}</td></tr>
                    <tr><td>OS Platform</td><td>${escapeHtml(machine.osPlatform || 'N/A')}</td></tr>
                    <tr><td>OS Version</td><td>${escapeHtml(machine.osVersion || 'N/A')}</td></tr>
                    <tr><td>Onboarding Status</td><td><span class="policy-badge" style="font-size: 12px;">${escapeHtml(machine.onboardingStatus || 'Unknown')}</span></td></tr>
                    <tr><td>Health Status</td><td><span class="policy-badge" style="font-size: 12px;">${escapeHtml(machine.healthStatus || 'Unknown')}</span></td></tr>
                    <tr><td>Risk Score</td><td>${escapeHtml(machine.riskScore || 'N/A')}</td></tr>
                    <tr><td>Exposure Level</td><td>${escapeHtml(machine.exposureLevel || 'N/A')}</td></tr>
                    <tr><td>Last Seen</td><td>${escapeHtml(machine.lastSeen ? new Date(machine.lastSeen).toLocaleString() : 'N/A')}</td></tr>
                    <tr><td>First Seen</td><td>${escapeHtml(machine.firstSeen ? new Date(machine.firstSeen).toLocaleString() : 'N/A')}</td></tr>
                    <tr><td>IP Addresses</td><td>${escapeHtml(machine.ipAddresses ? machine.ipAddresses.join(', ') : 'N/A')}</td></tr>
                    <tr><td>Machine Tags</td><td>${escapeHtml(machine.machineTags ? machine.machineTags.join(', ') : 'None')}</td></tr>
                </table>
        `;

        if (!intuneDeviceFound) {
            html += '<p style="margin-top: 16px; padding: 12px; background: rgba(239, 68, 68, 0.1); border-radius: 8px; color: var(--danger);"><strong>Note:</strong> No matching Intune device found. Policy information may not be available.</p>';
        }

        html += `
                <h3 style="margin-top: 24px;">Group Memberships (${groupMemberships.length})</h3>
        `;

        if (groupMemberships.length > 0) {
            html += '<table class="data-table"><tr><th>Group Name</th></tr>';
            groupMemberships.forEach(group => {
                html += `<tr><td>${escapeHtml(group.displayName)}</td></tr>`;
            });
            html += '</table>';
        } else {
            html += '<p class="text-muted">No group memberships found</p>';
        }

        html += `
                <h3 style="margin-top: 24px;">Assigned Policies (${assignedPolicies.length})</h3>
        `;

        if (assignedPolicies.length > 0) {
            html += '<table class="data-table"><tr><th>Policy Name</th><th>Type</th><th>Assigned Via</th></tr>';
            assignedPolicies.forEach(policy => {
                const assignedGroups = policy.assignedGroups.join(', ') || 'Direct Assignment';
                html += `
                    <tr>
                        <td><strong>${escapeHtml(policy.name)}</strong></td>
                        <td><span class="policy-badge" style="font-size: 12px;">${escapeHtml(policy.type)}</span></td>
                        <td style="font-size: 12px;">${escapeHtml(assignedGroups)}</td>
                    </tr>
                `;
            });
            html += '</table>';
        } else {
            html += '<p class="text-muted">No policies assigned to this machine</p>';
        }

        html += '</div>';

        showModal(html);
    } catch (error) {
        console.error('Failed to load machine details:', error);
    }
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
                <td>${escapeHtml(alert.title || 'Unknown')}</td>
                <td>${escapeHtml(alert.severity || 'N/A')}</td>
                <td>${escapeHtml(alert.status || 'Unknown')}</td>
                <td>${escapeHtml(alert.createdDateTime || 'N/A')}</td>
            </tr>
        `;
    });

    html += '</table>';
    resultsContent.innerHTML = html;
}

// Query Functions
function showQueryBuilder() {
    // Close mobile menu if open
    closeMobileMenu();

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
        html += `<th>${escapeHtml(col)}</th>`;
    });
    html += '</tr>';

    data.data.forEach(row => {
        html += '<tr>';
        columns.forEach(col => {
            html += `<td>${escapeHtml(row[col] !== null && row[col] !== undefined ? row[col] : 'N/A')}</td>`;
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

// Filter functions
function applyFilters() {
    const categoryFilter = document.getElementById('filterCategory');
    const typeFilter = document.getElementById('filterType');
    const platformFilter = document.getElementById('filterPlatform');
    const assignmentsFilter = document.getElementById('filterAssignments');
    const groupNameFilter = document.getElementById('filterGroupName');

    if (!categoryFilter || !typeFilter || !platformFilter || !assignmentsFilter) {
        return;
    }

    // Get selected values
    const selectedCategories = Array.from(categoryFilter.selectedOptions).map(opt => opt.value);
    const selectedTypes = Array.from(typeFilter.selectedOptions).map(opt => opt.value);
    const selectedPlatforms = Array.from(platformFilter.selectedOptions).map(opt => opt.value);
    const assignmentValue = assignmentsFilter.value;
    const groupNameValue = groupNameFilter ? groupNameFilter.value.toLowerCase().trim() : '';

    // Get all table rows
    const tbody = document.getElementById('policyTableBody');
    if (!tbody) return;

    const rows = tbody.querySelectorAll('tr');
    let visibleCount = 0;

    rows.forEach(row => {
        const category = row.getAttribute('data-category');
        const type = row.getAttribute('data-type');
        const platform = row.getAttribute('data-platform');
        const assignments = parseInt(row.getAttribute('data-assignments'));
        const groups = row.getAttribute('data-groups') || '';

        let showRow = true;

        // Apply category filter
        if (selectedCategories.length > 0 && !selectedCategories.includes(category)) {
            showRow = false;
        }

        // Apply type filter
        if (selectedTypes.length > 0 && !selectedTypes.includes(type)) {
            showRow = false;
        }

        // Apply platform filter
        if (selectedPlatforms.length > 0 && !selectedPlatforms.includes(platform)) {
            showRow = false;
        }

        // Apply assignments filter
        if (assignmentValue === 'assigned' && assignments === 0) {
            showRow = false;
        } else if (assignmentValue === 'unassigned' && assignments > 0) {
            showRow = false;
        }

        // Apply group name filter (case-insensitive partial match)
        if (groupNameValue && !groups.includes(groupNameValue)) {
            showRow = false;
        }

        // Show/hide row
        row.style.display = showRow ? '' : 'none';
        if (showRow) visibleCount++;
    });

    // Update count
    const filteredCountEl = document.getElementById('filteredCount');
    if (filteredCountEl) {
        filteredCountEl.textContent = visibleCount;
    }
}

function clearAllFilters() {
    const categoryFilter = document.getElementById('filterCategory');
    const typeFilter = document.getElementById('filterType');
    const platformFilter = document.getElementById('filterPlatform');
    const assignmentsFilter = document.getElementById('filterAssignments');
    const groupNameFilter = document.getElementById('filterGroupName');

    // Clear all selections
    if (categoryFilter) {
        Array.from(categoryFilter.options).forEach(opt => opt.selected = false);
    }
    if (typeFilter) {
        Array.from(typeFilter.options).forEach(opt => opt.selected = false);
    }
    if (platformFilter) {
        Array.from(platformFilter.options).forEach(opt => opt.selected = false);
    }
    if (assignmentsFilter) {
        assignmentsFilter.value = '';
    }
    if (groupNameFilter) {
        groupNameFilter.value = '';
    }

    // Reapply filters (which will show all)
    applyFilters();
}

// Table Sorting Function
function sortTable(column) {
    const tbody = document.getElementById('policyTableBody');
    if (!tbody) return;

    const rows = Array.from(tbody.querySelectorAll('tr'));

    // Determine sort direction
    if (window.currentSortColumn === column) {
        // Toggle direction if clicking same column
        window.currentSortDirection = window.currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        // New column, default to ascending
        window.currentSortColumn = column;
        window.currentSortDirection = 'asc';
    }

    // Sort rows
    rows.sort((a, b) => {
        let aVal, bVal;

        switch(column) {
            case 'name':
                aVal = a.dataset.name || '';
                bVal = b.dataset.name || '';
                break;
            case 'category':
                aVal = a.dataset.category || '';
                bVal = b.dataset.category || '';
                break;
            case 'type':
                aVal = a.dataset.type || '';
                bVal = b.dataset.type || '';
                break;
            case 'platform':
                aVal = a.dataset.platform || '';
                bVal = b.dataset.platform || '';
                break;
            case 'assignments':
                aVal = parseInt(a.dataset.assignments) || 0;
                bVal = parseInt(b.dataset.assignments) || 0;
                break;
            case 'created':
                aVal = parseInt(a.dataset.created) || 0;
                bVal = parseInt(b.dataset.created) || 0;
                break;
            default:
                return 0;
        }

        // Compare values
        if (column === 'assignments' || column === 'created') {
            // Numeric comparison
            return window.currentSortDirection === 'asc' ? aVal - bVal : bVal - aVal;
        } else {
            // String comparison
            if (aVal < bVal) return window.currentSortDirection === 'asc' ? -1 : 1;
            if (aVal > bVal) return window.currentSortDirection === 'asc' ? 1 : -1;
            return 0;
        }
    });

    // Clear and re-append sorted rows
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));

    // Update sort indicators
    updateSortIndicators(column, window.currentSortDirection);
}

function updateSortIndicators(column, direction) {
    // Clear all indicators
    ['name', 'category', 'type', 'platform', 'assignments', 'created'].forEach(col => {
        const indicator = document.getElementById(`sort-${col}`);
        if (indicator) {
            indicator.textContent = '';
            indicator.style.color = '';
        }
    });

    // Set active indicator
    const activeIndicator = document.getElementById(`sort-${column}`);
    if (activeIndicator) {
        activeIndicator.textContent = direction === 'asc' ? ' ▲' : ' ▼';
        activeIndicator.style.color = 'var(--accent-color)';
    }
}
