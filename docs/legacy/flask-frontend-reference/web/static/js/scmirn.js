let map;
let markers = [];
let userMarker;
let streetLayer;
let satelliteLayer;
let chatWindow = document.getElementById('chatWindow');
let documentModalInstance = null;
let mapSearchMarker = null;

// Initialize Map
function initMap() {
    const mapElement = document.getElementById('civicMap');
    if (!mapElement || typeof L === 'undefined') {
        return;
    }

    map = L.map('civicMap', {
        zoomControl: false,
        attributionControl: false
    }).setView([28.6139, 77.2090], 15);

    streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 22,
        attribution: '© OpenStreetMap contributors',
        subdomains: 'abc'
    }).addTo(map);

    satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19,
        attribution: '© Esri'
    });

    const baseMaps = {
        "Detailed Streets": streetLayer,
        "Satellite View": satelliteLayer
    };
    L.control.layers(baseMaps).addTo(map);

    L.control.zoom({ position: 'bottomright' }).addTo(map);
    L.control.scale({ imperial: false, metric: true, position: 'bottomleft' }).addTo(map);

    // Load issues from embedded JSON
    let issues = [];
    const dataEl = document.getElementById('scmirn-issues-data');
    if (dataEl && dataEl.textContent) {
        try {
            issues = JSON.parse(dataEl.textContent);
        } catch (err) {
            issues = [];
        }
    }

    const icons = {
        critical: L.divIcon({
            className: 'custom-marker',
            html: '<div style="background:#ef4444;width:30px;height:30px;border-radius:50%;border:3px solid white;box-shadow:0 4px 12px rgba(239,68,68,0.5);display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;font-size:14px;">!</div>',
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        }),
        high: L.divIcon({
            className: 'custom-marker',
            html: '<div style="background:#f59e0b;width:24px;height:24px;border-radius:50%;border:3px solid white;box-shadow:0 4px 12px rgba(245,158,11,0.5);"></div>',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        }),
        medium: L.divIcon({
            className: 'custom-marker',
            html: '<div style="background:#06b6d4;width:20px;height:20px;border-radius:50%;border:3px solid white;box-shadow:0 4px 12px rgba(6,182,212,0.5);"></div>',
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        })
    };

    issues.forEach((issue) => {
        const marker = L.marker([issue.lat, issue.lng], {
            icon: icons[issue.tier] || icons.medium,
            title: issue.title
        }).addTo(map);

        const description = issue.description || '';
        const shortDesc = description.length > 120 ? `${description.slice(0, 120)}...` : description;
        const fund = Number(issue.fund || 0);
        const target = Number(issue.target || 0);
        const progress = target > 0 ? Math.min((fund / target) * 100, 100) : 0;

        const popup = `
            <div style="min-width: 280px; max-width: 320px;">
                <img src="${issue.photo}" style="width: 100%; height: 140px; object-fit: cover; border-radius: 8px; margin-bottom: 12px;">
                <div style="font-weight: 700; font-size: 15px; margin-bottom: 8px; line-height: 1.3;">${issue.title}</div>
                <div style="font-size: 13px; color: #64748b; margin-bottom: 8px; line-height: 1.4;">${shortDesc}</div>
                <div style="display: flex; gap: 8px; margin-bottom: 12px;">
                    <span class="badge bg-${issue.tier === 'critical' ? 'danger' : issue.tier === 'high' ? 'warning' : 'info'}">${issue.tier.toUpperCase()}</span>
                    <span class="badge bg-light text-dark border">${issue.category}</span>
                </div>
                <div style="background: #f0fdf4; padding: 10px; border-radius: 6px; margin-bottom: 12px;">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 13px; color: #166534;">Raised: <strong>₹${fund.toLocaleString()}</strong></span>
                        <span style="font-size: 12px; color: #64748b; margin-left: auto;">of ₹${target.toLocaleString()}</span>
                    </div>
                    <div class="progress" style="height: 6px; margin-top: 6px;">
                        <div class="progress-bar bg-success" style="width: ${progress.toFixed(0)}%"></div>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                    <button onclick="donate(${issue.id || 0})" class="btn btn-sm btn-dark w-100">
                        <i class="fas fa-donate me-1"></i> Fund
                    </button>
                    <button onclick="getDirections(${issue.lat}, ${issue.lng})" class="btn btn-sm btn-outline-secondary w-100">
                        <i class="fas fa-directions me-1"></i> Directions
                    </button>
                </div>
            </div>
        `;

        marker.bindPopup(popup, {
            maxWidth: 350,
            className: 'custom-popup'
        });

        marker.on('mouseover', function() {
            this.openPopup();
        });

        markers.push({ marker, tier: issue.tier, data: issue });
    });

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                const accuracy = position.coords.accuracy;

                const latInput = document.getElementById('latInput');
                const lonInput = document.getElementById('lonInput');
                if (latInput) latInput.value = lat;
                if (lonInput) lonInput.value = lng;

                userMarker = L.marker([lat, lng], {
                    icon: L.divIcon({
                        className: 'user-location',
                        html: '<div style="background:#06b6d4;width:16px;height:16px;border-radius:50%;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.3);animation:pulse 2s infinite;"></div>',
                        iconSize: [16, 16]
                    })
                }).addTo(map).bindPopup(`<b>You are here</b><br>Accuracy: ${Math.round(accuracy)} meters`).openPopup();

                L.circle([lat, lng], {
                    radius: accuracy,
                    color: '#06b6d4',
                    fillColor: '#06b6d4',
                    fillOpacity: 0.1,
                    weight: 1
                }).addTo(map);

                map.setView([lat, lng], 17);
            },
            (error) => {
                console.log('Geolocation error:', error);
                map.setView([28.6139, 77.2090], 15);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    }
}

function getDirections(lat, lng) {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&travelmode=driving`;
    window.open(url, '_blank');
}

function filterMap(tier) {
    markers.forEach(m => {
        if (tier === 'all') {
            m.marker.addTo(map);
        } else if (m.tier === tier) {
            m.marker.addTo(map);
            m.marker.setZIndexOffset(1000);
        } else {
            map.removeLayer(m.marker);
        }
    });

    document.querySelectorAll('.btn-group .btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.toLowerCase().includes(tier) || (tier === 'all' && btn.textContent.includes('All'))) {
            btn.classList.add('active');
        }
    });
}

function handleMapSearchKey(e) {
    if (e.key === 'Enter') {
        searchMapLocation();
    }
}

function setMapSearchStatus(message, isError = false) {
    const statusEl = document.getElementById('mapSearchStatus');
    if (!statusEl) return;
    statusEl.textContent = message || '';
    statusEl.className = `${isError ? 'text-danger' : 'text-muted'} d-block mt-2`;
}

function findLocalMapMatches(query) {
    const q = query.toLowerCase();
    return markers.filter(item => {
        const title = (item.data?.title || '').toLowerCase();
        const category = (item.data?.category || '').toLowerCase();
        const description = (item.data?.description || '').toLowerCase();
        return title.includes(q) || category.includes(q) || description.includes(q);
    });
}

async function searchMapLocation() {
    const input = document.getElementById('mapSearchInput');
    if (!input || !map) return;

    const query = input.value.trim();
    if (!query) {
        setMapSearchStatus('Enter a search query.');
        return;
    }

    setMapSearchStatus('Searching...');

    const localMatches = findLocalMapMatches(query);
    if (localMatches.length > 0) {
        const bounds = L.latLngBounds(localMatches.map(m => m.marker.getLatLng()));
        map.fitBounds(bounds.pad(0.25));
        localMatches[0].marker.openPopup();
        setMapSearchStatus(`Found ${localMatches.length} local result(s).`);
        return;
    }

    try {
        const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(query)}`;
        const res = await fetch(url, {
            headers: { 'Accept': 'application/json' }
        });
        const results = await res.json();

        if (!Array.isArray(results) || results.length === 0) {
            setMapSearchStatus('No result found for this query.', true);
            return;
        }

        const first = results[0];
        const lat = parseFloat(first.lat);
        const lon = parseFloat(first.lon);
        if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
            setMapSearchStatus('Invalid location result.', true);
            return;
        }

        map.setView([lat, lon], 16);

        if (mapSearchMarker) {
            map.removeLayer(mapSearchMarker);
        }
        mapSearchMarker = L.marker([lat, lon]).addTo(map);
        mapSearchMarker.bindPopup(`<strong>${first.display_name || query}</strong>`).openPopup();

        setMapSearchStatus('External location found.');
    } catch (err) {
        setMapSearchStatus('Search service unavailable. Please try again.', true);
    }
}

// Chatbot Functions
function toggleChat() {
    const display = chatWindow.style.display;
    chatWindow.style.display = display === 'flex' ? 'none' : 'flex';
    if (chatWindow.style.display === 'flex') {
        document.getElementById('chatInput').focus();
    }
}

function handleChatKey(e) {
    if (e.key === 'Enter') sendChatMessage();
}

function sendQuick(text) {
    document.getElementById('chatInput').value = text;
    sendChatMessage();
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text) return;
    
    addMessage(text, 'user');
    input.value = '';
    
    // Show typing indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message-ai';
    loadingDiv.innerHTML = '<i class="fas fa-circle-notch fa-spin text-primary"></i> Analyzing legal framework & government data...';
    loadingDiv.id = 'loadingMsg';
    document.getElementById('chatBody').appendChild(loadingDiv);
    document.getElementById('chatBody').scrollTop = document.getElementById('chatBody').scrollHeight;
    
    try {
        const res = await fetch('/api/ai-assistant', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: text})
        });
        const data = await res.json();
        
        document.getElementById('loadingMsg').remove();
        
        // Format response with rich text
        let formatted = data.response
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>')
            .replace(/•/g, '&bull;');
        
        addMessage(formatted, 'ai');
        
        if (data.action === 'show_document_generator') {
            const suggestedType = data.document_type || 'rti';
            addMessage(`<div class="suggestion-chip" onclick="openDocumentModal('${suggestedType}')">Open Document Generator</div>`, 'ai');
        }
    } catch (err) {
        document.getElementById('loadingMsg').remove();
        addMessage('Sorry, experiencing high traffic. Please try again.', 'ai');
    }
}

function addMessage(html, sender) {
    const div = document.createElement('div');
    div.className = sender === 'ai' ? 'message-ai' : 'message-user';
    div.innerHTML = html;
    document.getElementById('chatBody').appendChild(div);
    document.getElementById('chatBody').scrollTop = document.getElementById('chatBody').scrollHeight;
}

// Report Functions
function openReportModal() {
    new bootstrap.Modal(document.getElementById('reportModal')).show();
}

function openDocumentModal(docType = 'rti') {
    const modalEl = document.getElementById('documentModal');
    if (!modalEl) return;

    const select = document.getElementById('docTypeSelect');
    if (select) {
        select.value = docType;
        if (!select.value) {
            select.value = 'rti';
        }
    }

    if (!documentModalInstance) {
        documentModalInstance = new bootstrap.Modal(modalEl);
    }
    documentModalInstance.show();
}

function previewPhotos(input) {
    const preview = document.getElementById('photoPreview');
    preview.innerHTML = '';
    Array.from(input.files).forEach(file => {
        const reader = new FileReader();
        reader.onload = e => {
            preview.innerHTML += `<img src="${e.target.result}" class="rounded" style="width: 80px; height: 60px; object-fit: cover;">`;
        };
        reader.readAsDataURL(file);
    });
}

async function submitReport(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const btn = e.target.querySelector('button[type="submit"]');
    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin me-2"></i>AI Analyzing Priority...';
    btn.disabled = true;
    
    try {
        const res = await fetch('/api/report-issue', {method: 'POST', body: formData});
        const data = await res.json();
        
        if (data.success) {
            alert(`✅ ${data.message}\n\nAI classified this as ${data.priority} priority based on safety analysis.`);
            location.reload();
        }
    } catch (err) {
        alert('Error submitting report');
    } finally {
        btn.innerHTML = '<i class="fas fa-paper-plane me-2"></i>Submit Report & AI Analysis';
        btn.disabled = false;
    }
}

async function donate(issueId) {
    const amount = prompt('Enter donation amount (₹):', '1000');
    if (!amount) return;
    
    try {
        const res = await fetch('/api/donate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({issue_id: issueId, amount: parseFloat(amount)})
        });
        const data = await res.json();
        if (data.success) {
            alert(`✅ Thank you! ₹${amount} donated successfully.`);
            location.reload();
        }
    } catch (err) {
        alert('Donation failed');
    }
}

function buildTemplateData(formValues) {
    const today = new Date().toISOString().slice(0, 10);
    const fullName = formValues.name;

    const base = {
        date: today,
        name: fullName,
        applicant_name: fullName,
        applicant_address: formValues.address,
        address: formValues.address,
        phone: formValues.phone,
        email: 'citizen@example.com',
        issue_details: formValues.issue,
        issue_summary: formValues.issue,
        office_address: formValues.address,
        department: formValues.department || 'Concerned Department',
        district: 'District Office',
        utility_name: formValues.department || 'Electricity Department'
    };

    const byType = {
        rti: {
            department: formValues.department || 'Public Information Officer',
            address: formValues.address,
            query_details: formValues.issue,
            specific_question_1: 'Provide complete file noting related to this matter.',
            specific_question_2: 'Provide current status with expected completion date.',
            specific_question_3: 'Provide names/designations of responsible officials.',
            payment_mode: 'Postal Order',
            applicant_name: fullName,
            applicant_address: formValues.address,
            place: 'India'
        },
        fir: {
            district: 'District Police Office',
            offense_nature: 'cognizable offense',
            incident_date: today,
            police_station: formValues.department || 'Local Police Station',
            incident_description: formValues.issue,
            ipc_sections: 'relevant IPC sections',
            officer_name: 'Duty Officer',
            reason_given: 'no valid reason',
            address: formValues.address
        },
        consumer: {
            year: new Date().getFullYear(),
            complainant_name: fullName,
            company_name: formValues.department || 'Service Provider',
            defect_description: formValues.issue,
            refund_or_replacement: 'Refund/replacement and corrective service',
            amount: '50000',
            purchase_date: today,
            product: 'Product/Service',
            price: '0',
            defect_date: today,
            defect_details: formValues.issue,
            complaint_date: today,
            value: '0',
            signature: fullName
        },
        electricity: {
            utility_name: formValues.department || 'Electricity Department',
            consumer_number: 'NA',
            issue_summary: formValues.issue,
            issue_details: formValues.issue,
            name: fullName
        },
        rent: {
            landlord_name: 'Landlord Name',
            landlord_address: formValues.address,
            tenant_name: fullName,
            property_address: formValues.address,
            facts: formValues.issue
        },
        scholarship: {
            department: formValues.department || 'Scholarship Department',
            academic_year: String(new Date().getFullYear()),
            student_name: fullName,
            institution: 'Institute Name',
            application_id: 'NA',
            issue_details: formValues.issue
        },
        pension: {
            department: formValues.department || 'Pension Department',
            ppo_number: 'NA',
            applicant_name: fullName,
            account_last4: '0000',
            issue_details: formValues.issue
        },
        cybercrime: {
            district: 'Cyber Crime Cell',
            incident_type: 'online fraud',
            name: fullName,
            phone: formValues.phone,
            email: 'citizen@example.com',
            incident_details: formValues.issue
        }
    };

    return {
        ...base,
        ...(byType[formValues.docType] || {})
    };
}

async function submitDocument(e) {
    e.preventDefault();

    const submitBtn = document.getElementById('documentSubmitBtn');
    const output = document.getElementById('documentOutput');
    const docType = (document.getElementById('docTypeSelect') || {}).value || 'rti';

    const formValues = {
        docType,
        department: (document.getElementById('docDepartment') || {}).value || '',
        name: (document.getElementById('docName') || {}).value || '',
        phone: (document.getElementById('docPhone') || {}).value || '',
        address: (document.getElementById('docAddress') || {}).value || '',
        issue: (document.getElementById('docIssue') || {}).value || ''
    };

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin me-2"></i>Generating...';
    }

    try {
        const payload = {
            doc_type: docType,
            template_data: buildTemplateData(formValues)
        };

        const res = await fetch('/api/documents/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (!res.ok || !data.success) {
            const details = (data && data.error) ? data.error : 'Failed to generate draft';
            throw new Error(details);
        }

        if (output) {
            output.value = data.content || 'No content returned';
        }
    } catch (err) {
        if (output) {
            output.value = `Generation error: ${err.message}`;
        }
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-file-signature me-2"></i>Generate Draft';
        }
    }
}

function formatRightsSection(title, items) {
    if (!items || !items.length) return '';
    const rows = items.map(i => `<li>${i}</li>`).join('');
    return `<div class="mb-2"><div class="fw-semibold">${title}</div><ul class="mb-0">${rows}</ul></div>`;
}

async function analyzeRights() {
    const queryEl = document.getElementById('rightsQuery');
    const resultEl = document.getElementById('rightsResult');
    if (!queryEl || !resultEl) return;

    const query = queryEl.value.trim();
    if (!query) {
        resultEl.innerHTML = '<span class="text-danger">Enter a query to analyze rights.</span>';
        return;
    }

    resultEl.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Analyzing...';
    try {
        const res = await fetch('/api/rights/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query})
        });
        const data = await res.json();
        if (!res.ok || !data.success) {
            throw new Error((data && data.error) || 'Rights analysis failed');
        }

        const analysis = data.analysis || {};
        const html = `
            <div class="fw-bold mb-2">${analysis.title || 'Rights Analysis'}</div>
            ${formatRightsSection('Rights', analysis.rights || [])}
            ${formatRightsSection('Timelines', analysis.timelines || [])}
            ${formatRightsSection('Next Steps', analysis.next_steps || [])}
        `;
        resultEl.innerHTML = html;
    } catch (err) {
        resultEl.innerHTML = `<span class="text-danger">Error: ${err.message}</span>`;
    }
}

function launchPillar(pillar) {
    if (pillar === 'problem_solver') {
        toggleChat();
        const input = document.getElementById('chatInput');
        if (input) {
            input.value = 'Help me solve my civic issue step by step';
            input.focus();
        }
        return;
    }
    if (pillar === 'office_locator') {
        window.location.href = '/offices';
        return;
    }
    if (pillar === 'rights_engine') {
        const section = document.getElementById('rights');
        if (section) {
            section.scrollIntoView({ behavior: 'smooth' });
        }
        const input = document.getElementById('rightsQuery');
        if (input) {
            setTimeout(() => input.focus(), 350);
        }
        return;
    }
    if (pillar === 'document_gen') {
        openDocumentModal('rti');
        return;
    }
    if (pillar === 'heatmap') {
        window.location.href = '/heatmap';
        return;
    }
    if (pillar === 'tracker') {
        window.location.href = '/tracker';
        return;
    }
    if (pillar === 'predictive') {
        window.location.href = '/analytics';
    }
}

function statusClass(status) {
    if (status === 'resolved') return 'status-pill status-pill-resolved';
    if (status === 'in_progress' || status === 'funded') return 'status-pill status-pill-progress';
    return 'status-pill status-pill-open';
}

async function loadTrackerDashboard() {
    const tableBody = document.getElementById('trackerTableBody');
    if (!tableBody) return;

    tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">Loading tracker data...</td></tr>';

    try {
        const res = await fetch('/api/tracker/summary?limit=30');
        const data = await res.json();
        if (!res.ok || !data.success) {
            throw new Error((data && data.error) || 'Unable to load tracker');
        }

        const kpi = data.kpis || {};
        const items = data.items || [];

        const openEl = document.getElementById('trackerOpen');
        const escalationEl = document.getElementById('trackerEscalations');
        const etaEl = document.getElementById('trackerEta');
        const fundedEl = document.getElementById('trackerFunded');
        if (openEl) openEl.textContent = String(kpi.open_cases || 0);
        if (escalationEl) escalationEl.textContent = String(kpi.due_escalations || 0);
        if (etaEl) etaEl.textContent = String(kpi.avg_eta_days || 0);
        if (fundedEl) fundedEl.textContent = `${kpi.avg_funded_progress || 0}%`;

        if (!items.length) {
            tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No cases found.</td></tr>';
            return;
        }

        tableBody.innerHTML = items.map(item => `
            <tr>
                <td>
                    <div class="fw-semibold">${item.title}</div>
                    <small class="text-muted">${item.public_id || 'N/A'}</small>
                </td>
                <td><span class="${statusClass(item.status)}">${item.status}</span></td>
                <td><span class="badge bg-${item.priority_tier === 'critical' ? 'danger' : item.priority_tier === 'high' ? 'warning' : 'info'}">${item.priority_tier}</span></td>
                <td class="text-capitalize">${item.category}</td>
                <td>${item.eta_days}d</td>
                <td>${item.escalation_ready ? '<span class="text-danger fw-semibold">Due</span>' : '<span class="text-success">On Track</span>'}</td>
            </tr>
        `).join('');
    } catch (err) {
        tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger py-4">${err.message}</td></tr>`;
    }
}

let categoryChartRef = null;
let statusChartRef = null;

function buildBarChart(canvasId, labels, values, color) {
    if (typeof Chart === 'undefined') return null;
    const el = document.getElementById(canvasId);
    if (!el) return null;
    return new Chart(el, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Count',
                data: values,
                borderRadius: 8,
                backgroundColor: color
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
        }
    });
}

async function loadAnalyticsDashboard() {
    const totalEl = document.getElementById('analyticsTotal');
    if (!totalEl) return;

    try {
        const res = await fetch('/api/analytics/summary');
        const data = await res.json();
        if (!res.ok || !data.success) {
            throw new Error((data && data.error) || 'Unable to load analytics');
        }

        const summary = data.summary || {};
        const categories = data.category_distribution || {};
        const statuses = data.status_distribution || {};

        document.getElementById('analyticsTotal').textContent = String(summary.total_reports || 0);
        document.getElementById('analyticsCritical').textContent = `${summary.critical_share || 0}%`;
        document.getElementById('analyticsSla').textContent = summary.predicted_sla || '-';
        document.getElementById('analyticsBottleneck').textContent = summary.top_bottleneck || '-';

        if (categoryChartRef) categoryChartRef.destroy();
        if (statusChartRef) statusChartRef.destroy();

        categoryChartRef = buildBarChart(
            'analyticsCategoryChart',
            Object.keys(categories),
            Object.values(categories),
            'rgba(6, 182, 212, 0.75)'
        );
        statusChartRef = buildBarChart(
            'analyticsStatusChart',
            Object.keys(statuses),
            Object.values(statuses),
            'rgba(15, 23, 42, 0.75)'
        );
    } catch (err) {
        document.getElementById('analyticsBottleneck').textContent = 'Error';
    }
}

function bootScmirn() {
    initMap();
    loadTrackerDashboard();
    loadAnalyticsDashboard();
}

window.addEventListener('DOMContentLoaded', bootScmirn);

