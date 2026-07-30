/**
 * Capitec Daily Reconciliation System - Web Dashboard
 * Production-grade JavaScript - Final Production Refinement
 */

let currentPage = 'dashboard';
let trendChart = null, errorTrendChart = null, errorDistributionChart = null, validationTrendChart = null;
let refreshInterval = 15000, autoRefreshTimer = null, headerUpdateTimer = null, progressPollTimer = null, refreshController = null;
const animationStore = {};
let validationWorkspaceInitialized = false;
let lastDashboardData = null;
let lastRefreshTime = 0;
const MIN_REFRESH_INTERVAL = 5000; // Minimum 5 seconds between dashboard refreshes

document.addEventListener('DOMContentLoaded', function() {
    console.log('CDRS Dashboard - Initializing');
    const path = window.location.pathname.replace('/', '');
    const pageMap = { '': 'dashboard', '/': 'dashboard', 'validation': 'validation', 'analytics': 'analytics', 'audit': 'audit', 'settings': 'settings', 'about': 'about' };
    showPage(pageMap[path] || 'dashboard');
    window.addEventListener('popstate', e => { const p = window.location.pathname.replace('/', ''); showPage(pageMap[p] || 'dashboard'); });
    refreshDashboard();
    setupAutoRefresh();
    setupNavigation();
    setupCardSelection();
    loadSettings();
    initValidationWorkspace();
    updateHeaderDateTime();
    headerUpdateTimer = setInterval(updateHeaderDateTime, 1000);
    window.addEventListener('beforeunload', () => { clearInterval(headerUpdateTimer); clearInterval(autoRefreshTimer); clearInterval(progressPollTimer); if (refreshController) refreshController.abort(); });
});

function updateHeaderDateTime() {
    const now = new Date();
    const d = String(now.getDate()).padStart(2,'0'), m = String(now.getMonth()+1).padStart(2,'0'), y = now.getFullYear();
    const h = String(now.getHours()).padStart(2,'0'), min = String(now.getMinutes()).padStart(2,'0');
    const de = document.getElementById('headerDate'), te = document.getElementById('headerTime');
    if (de) de.textContent = d + '/' + m + '/' + y;
    if (te) te.textContent = h + ':' + min;
}

function setupNavigation() {
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.dataset.page;
            showPage(page);
            history.pushState({page}, '', page === 'dashboard' ? '/' : '/' + page);
        });
    });
}

function showPage(pageName) {
    currentPage = pageName;
    document.querySelectorAll('.page-content').forEach(el => { el.classList.remove('active'); el.style.display = 'none'; });
    document.querySelectorAll('.navbar-nav .nav-link').forEach(l => l.classList.remove('active'));
    const pe = document.getElementById(pageName + '-page');
    if (pe) { pe.classList.add('active'); pe.style.display = ''; }
    const nl = document.querySelector(`.navbar-nav .nav-link[data-page="${pageName}"]`);
    if (nl) nl.classList.add('active');
    switch(pageName) {
        case 'dashboard': refreshDashboard(); break;
        case 'validation': 
            console.log('Switching to validation page...');
            if (!validationWorkspaceInitialized) {
                console.log('First time validation page visit, initializing...');
                setTimeout(initValidationWorkspace, 100);
                validationWorkspaceInitialized = true;
            } else {
                console.log('Validation workspace already initialized');
            }
            loadRecentValidationsForValidation(); 
            break;
        case 'analytics': loadAnalyticsCharts(); break;
        case 'audit': loadAuditHistory(); break;
        case 'settings': loadSettings(); break;
        case 'about': loadAboutPage(); break;
    }
}

function setupAutoRefresh() {
    autoRefreshTimer = setInterval(() => {
        if (currentPage === 'dashboard') refreshDashboard();
        else if (currentPage === 'validation') loadRecentValidationsForValidation();
        else if (currentPage === 'analytics') loadAnalyticsCharts();
        else if (currentPage === 'audit') loadAuditHistory();
    }, refreshInterval);
}

// ================================================================
// CARD SELECTION
// ================================================================
function setupCardSelection() {
    const cards = document.querySelectorAll('.kpi-card.professional');
    cards.forEach(card => {
        card.addEventListener('click', function(e) {
            if (e.target.closest('button') || e.target.closest('a') || e.target.closest('input')) return;
            const isSelected = this.classList.contains('selected');
            document.querySelectorAll('.kpi-card.professional.selected').forEach(c => { c.classList.remove('selected'); });
            if (!isSelected) this.classList.add('selected');
        });
    });
    const container = document.querySelector('.kpi-vertical-container');
    if (container) {
        const observer = new MutationObserver(() => {
            document.querySelectorAll('.kpi-card.professional:not([data-card-listener])').forEach(card => {
                card.setAttribute('data-card-listener', 'true');
                card.addEventListener('click', function(e) {
                    if (e.target.closest('button') || e.target.closest('a') || e.target.closest('input')) return;
                    const isSelected = this.classList.contains('selected');
                    document.querySelectorAll('.kpi-card.professional.selected').forEach(c => { c.classList.remove('selected'); });
                    if (!isSelected) this.classList.add('selected');
                });
            });
        });
        observer.observe(container, { childList: true, subtree: true });
    }
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.kpi-card.professional')) {
            document.querySelectorAll('.kpi-card.professional.selected').forEach(c => { c.classList.remove('selected'); });
        }
    });
}

// ================================================================
// PROGRESS POLLING
// ================================================================
function startProgressPolling() {
    if (progressPollTimer) { clearInterval(progressPollTimer); progressPollTimer = null; }
    console.log('Starting progress polling...');
    progressPollTimer = setInterval(() => {
        fetch('/api/dashboard/validation-progress').then(r => r.json()).then(data => {
            console.log('Progress update received:', data);
            updateLiveProgress(data);
            if (data.status === 'completed' || data.status === 'failed' || data.status === 'error') {
                console.log('Validation finished, stopping poll');
                if (progressPollTimer) { clearInterval(progressPollTimer); progressPollTimer = null; }
                if (data.status === 'error') {
                    showToast(data.error || 'Validation failed', 'error');
                    stopValidationProgress(false);
                }
                setTimeout(refreshDashboard, 1000);
            }
        }).catch(err => {
            console.error('Progress poll error:', err);
            if (progressPollTimer) { clearInterval(progressPollTimer); progressPollTimer = null; }
        });
    }, 500);
}

function updateLiveProgress(data) {
    console.log('updateLiveProgress called with:', data);
    const ps = document.getElementById('progressSection');
    const vp = document.getElementById('validation-page');
    if (!ps && !vp) {
        console.warn('No progress container found');
        return;
    }
    if (data.status === 'running') {
        if (ps) { ps.style.display = ''; }
        const bar = ps ? document.getElementById('liveProgressBar') : null;
        const stage = ps ? document.getElementById('liveProgressStage') : null;
        const pct = ps ? document.getElementById('liveProgressPercent') : null;
        const spinner = ps ? document.getElementById('progressSpinner') : null;
        const title = ps ? document.getElementById('progressTitle') : null;
        if (bar) bar.style.width = data.percent + '%';
        if (pct) pct.textContent = data.percent + '%';
        if (spinner) spinner.style.display = 'inline-block';
        if (title) title.textContent = 'Validation Running';
        if (stage) {
            const icon = data.percent < 50 ? 'fa-hourglass-start' : data.percent < 90 ? 'fa-hourglass-half' : 'fa-hourglass-end';
            stage.innerHTML = '<i class="fas ' + icon + '"></i> ' + data.stage;
        }
        // Update validation page progress bar if present
        if (vp) {
            const vpBar = vp.querySelector('#validationProgressBar');
            const vpPct = vp.querySelector('#progressPercentage');
            const vpStep = vp.querySelector('#validationStepText');
            if (vpBar) vpBar.style.width = data.percent + '%';
            if (vpPct) vpPct.textContent = data.percent + '%';
            if (vpStep) vpStep.innerHTML = '<i class="fas fa-hourglass-half"></i> ' + data.stage;
        }
    } else if (data.status === 'completed') {
        if (ps) { ps.style.display = ''; }
        const bar = ps ? document.getElementById('liveProgressBar') : null;
        const stage = ps ? document.getElementById('liveProgressStage') : null;
        const pct = ps ? document.getElementById('liveProgressPercent') : null;
        const spinner = ps ? document.getElementById('progressSpinner') : null;
        const title = ps ? document.getElementById('progressTitle') : null;
        if (bar) { bar.style.width = '100%'; bar.style.background = 'linear-gradient(90deg, #28a745, #34ce57)'; }
        if (pct) pct.textContent = '100%';
        if (spinner) spinner.style.display = 'none';
        if (title) title.textContent = '✅ Validation Completed';
        if (stage) stage.innerHTML = '<i class="fas fa-check-circle text-success"></i> Validation Completed Successfully <span class="check-dashboard-msg"><i class="fas fa-chart-bar"></i> Please check results via Dashboard</span>';
        const vcs = document.getElementById('validationCompletionSmiley');
        if (vcs) vcs.style.display = 'block';
        const vcf = document.getElementById('validationFailureSmiley');
        if (vcf) vcf.style.display = 'none';
        // Update validation page progress bar to 100%
        if (vp) {
            const vpBar = vp.querySelector('#validationProgressBar');
            const vpPct = vp.querySelector('#progressPercentage');
            const vpStep = vp.querySelector('#validationStepText');
            if (vpBar) { vpBar.style.width = '100%'; vpBar.style.background = 'linear-gradient(90deg, #28a745, #34ce57)'; }
            if (vpPct) vpPct.textContent = '100%';
            if (vpStep) vpStep.innerHTML = '<i class="fas fa-check-circle text-success"></i> Validation Completed';
        }
        setTimeout(() => { if (ps) { ps.style.display = 'none'; if (bar) { bar.style.width = '0%'; bar.style.background = ''; } } }, 8000);
    } else if (data.status === 'failed') {
        if (ps) ps.style.display = '';
        const bar = ps ? document.getElementById('liveProgressBar') : null;
        const stage = ps ? document.getElementById('liveProgressStage') : null;
        const pct = ps ? document.getElementById('liveProgressPercent') : null;
        const spinner = ps ? document.getElementById('progressSpinner') : null;
        const title = ps ? document.getElementById('progressTitle') : null;
        if (bar) { bar.style.width = '100%'; bar.style.background = 'linear-gradient(90deg, #dc3545, #ff6b7a)'; }
        if (pct) pct.textContent = 'Failed';
        if (spinner) spinner.style.display = 'none';
        if (title) title.textContent = '❌ Validation Failed';
        if (stage) stage.innerHTML = '<i class="fas fa-times-circle text-danger"></i> Validation Failed <span class="failure-smiley-inline" style="filter: none; font-size: 1.3rem;">😞</span> <span class="check-dashboard-msg" style="color:#dc3545;font-weight:600;"><i class="fas fa-exclamation-triangle"></i> Please fix errors and try again</span>';
        const vfs = document.getElementById('validationFailureSmiley');
        if (vfs) vfs.style.display = 'block';
        const vcs = document.getElementById('validationCompletionSmiley');
        if (vcs) vcs.style.display = 'none';
        setTimeout(() => { if (ps) { ps.style.display = 'none'; if (bar) { bar.style.width = '0%'; bar.style.background = ''; } } }, 8000);
    } else {
        if (ps) ps.style.display = 'none';
    }
}

// ================================================================
// DASHBOARD RESET
// ================================================================
function resetDashboardDisplay() {
    ['kpiRowsProcessed','kpiSimOrders','kpiSimCards','kpiBankOrders','kpiBankCards','kpiTotalOrders','kpiTotalCards','kpiValidationErrors'].forEach(id => {
        const el = document.getElementById(id); if (el) el.textContent = '0';
    });
    const sb = document.getElementById('dashboardStatusBadge');
    if (sb) { sb.className = 'badge bg-secondary'; sb.innerHTML = '<i class="fas fa-clock"></i> Waiting for Validation'; }
    const wc = document.getElementById('currentWorkbookContainer'), dc = document.getElementById('validationDateContainer');
    if (wc) wc.style.display = 'none'; if (dc) dc.style.display = 'none';
    const cc = document.getElementById('checklistContainer');
    if (cc) cc.innerHTML = '<div class="text-center text-muted py-3"><i class="fas fa-inbox fa-2x mb-2"></i><p>Waiting for validation...</p></div>';
    const rs = document.getElementById('releaseStatusBadge');
    if (rs) { rs.className = 'badge bg-secondary'; rs.innerHTML = '<i class="fas fa-clock"></i> Waiting'; }
    const rr = document.getElementById('releaseReasons'); if (rr) rr.style.display = 'none';
    const ps = document.getElementById('progressSection');
    if (ps) {
        ps.style.display = '';
        const bar = document.getElementById('liveProgressBar'), stage = document.getElementById('liveProgressStage');
        const pct = document.getElementById('liveProgressPercent'), spinner = document.getElementById('progressSpinner');
        const title = document.getElementById('progressTitle');
        if (bar) { bar.style.width = '0%'; bar.style.background = ''; }
        if (pct) pct.textContent = '0%'; if (spinner) spinner.style.display = 'inline-block';
        if (title) title.textContent = 'Validation Running';
        if (stage) stage.innerHTML = '<i class="fas fa-hourglass-start"></i> Preparing validation...';
    }
}

// ================================================================
// DASHBOARD REFRESH
// ================================================================
function shouldRefreshDashboard() {
    const now = Date.now();
    if (now - lastRefreshTime < MIN_REFRESH_INTERVAL) {
        return false;
    }
    lastRefreshTime = now;
    return true;
}

function refreshDashboard() {
    // Throttle dashboard refreshes to prevent excessive API calls
    if (!shouldRefreshDashboard()) {
        return;
    }
    
    if (refreshController) { refreshController.abort(); refreshController = null; }
    refreshController = new AbortController();
    const signal = refreshController.signal;
    
    // Use single combined API call when possible
    Promise.all([
        fetch('/api/dashboard/latest', {signal}).then(r=>r.json()),
        fetch('/api/dashboard/business-kpi', {signal}).then(r=>r.json()),
        fetch('/api/dashboard/checklist', {signal}).then(r=>r.json()),
        fetch('/api/dashboard/release-status', {signal}).then(r=>r.json()),
        fetch('/api/dashboard/failure-details', {signal}).then(r=>r.json()),
        fetch('/api/dashboard/recent', {signal}).then(r=>r.json()),
        fetch('/api/dashboard/trend', {signal}).then(r=>r.json()),
        fetch('/api/dashboard/error-trend', {signal}).then(r=>r.json()),
        fetch('/api/user/avatar', {signal}).then(r=>r.json())
    ]).then(([latest, kpi, checklist, release, failure, recent, trend, errorTrend, avatar]) => {
        // Cache data to avoid unnecessary DOM updates
        lastDashboardData = { latest, kpi, checklist, release, failure, recent, trend, errorTrend };
        
        updateDashboardStatus(latest);
        updateBusinessKPI(kpi);
        updateValidationChecklist(checklist);
        updateReleaseStatus(release);
        updateValidationStatusCard(latest, failure, checklist);
        updateRecentValidations(recent);
        updateCharts(trend, errorTrend);
        updateLastUpdatedTime();
        updateProfilePicture(avatar);
    }).catch(error => { 
        if (error.name === 'AbortError') return; 
        console.error('Dashboard refresh error:', error); 
        // Retry after a longer delay on error
        setTimeout(() => {
            if (currentPage === 'dashboard') {
                lastRefreshTime = 0; // Reset throttle on error
            }
        }, 5000);
    });
}

// ================================================================
// ABOUT PAGE
// ================================================================
function loadAboutPage() {
    fetch('/api/dashboard/engine-info').then(r => r.json()).then(data => {
        if (!data) return;
        const v = document.getElementById('aboutEngineVersion');
        const r = document.getElementById('aboutEngineRules');
        const e = document.getElementById('aboutEngineLastExecuted');
        if (v) v.textContent = data.version || '—';
        if (r) r.textContent = data.rules_loaded || '—';
        if (e) e.textContent = data.last_executed ? formatDate(data.last_executed) : '—';
    }).catch(() => {});
}

// ================================================================
// DASHBOARD STATUS
// ================================================================
function updateDashboardStatus(data) {
    const sb = document.getElementById('dashboardStatusBadge'), wc = document.getElementById('currentWorkbookContainer');
    const wn = document.getElementById('currentWorkbookName'), dc = document.getElementById('validationDateContainer');
    const de = document.getElementById('currentValidationDate');
    
    // Workbook Information Panel elements
    const wsName = document.getElementById('worksheetName');
    const valId = document.getElementById('validationId');
    const operator = document.getElementById('operatorName');
    const infoPanel = document.getElementById('dashboardWorkbookInfoPanel');
    
    if (!data || !data.workbook) {
        if (sb) { sb.className = 'badge bg-secondary'; sb.innerHTML = '<i class="fas fa-clock"></i> Waiting for Validation'; }
        if (wc) wc.style.display = 'none'; if (dc) dc.style.display = 'none';
        if (infoPanel) infoPanel.style.display = 'none';
        const eds = document.getElementById('errorDetailsSection');
        if (eds) eds.style.display = 'none';
        return;
    }
    const passed = data.status === 'PASS';
    if (sb) {
        sb.className = 'badge ' + (passed ? 'bg-success' : 'bg-danger');
        sb.innerHTML = '<i class="fas ' + (passed ? 'fa-check-circle' : 'fa-times-circle') + '"></i> ' + (passed ? 'Validation Completed' : 'Validation Failed');
        sb.style.fontSize = '1rem'; sb.style.padding = '0.5rem 1.5rem';
    }
    if (wc) wc.style.display = ''; if (wn) wn.textContent = data.workbook;
    if (dc) dc.style.display = ''; 
    if (de) {
        // Use formatted date if available, otherwise fallback to formatDate
        de.textContent = data.validation_date_formatted || formatDate(data.validation_date);
    }
    
    // Update workbook information grid
    if (infoPanel) {
        infoPanel.style.display = 'block';
        if (wsName) {
            // Use daily_output_file if available, otherwise worksheet_name, otherwise static default
            wsName.textContent = data.daily_output_file || data.worksheet_name || 'N/A';
        }
        if (valId) valId.textContent = data.validation_id || 'N/A';
        if (operator) {
            // Use the real logged-in username from the API response
            operator.textContent = data.operator || 'Unknown';
        }
    }
    
    // Show error section if validation failed
    const hasErrors = data.status === 'FAIL' || (data.error_count !== undefined && data.error_count > 0);
    const eds = document.getElementById('errorDetailsSection');
    if (eds) {
        if (hasErrors) {
            eds.style.display = 'block';
            // Populate error table if we have error data
            if (data.validation_errors && data.validation_errors.length > 0) {
                populateErrorTable({validation_errors: data.validation_errors, errors: data.errors || []});
            }
        } else {
            eds.style.display = 'none';
        }
    }
}

// ================================================================
// BUSINESS KPI CARDS
// ================================================================
function updateBusinessKPI(data) {
    if (!data) return;
    animateValue('kpiRowsProcessed', data.rows_processed||0);
    animateValue('kpiSimOrders', data.sim_orders||0);
    animateValue('kpiSimCards', data.sim_cards||0);
    animateValue('kpiBankOrders', data.bank_orders||0);
    animateValue('kpiBankCards', data.bank_cards||0);
    animateValue('kpiTotalOrders', data.total_orders||0);
    animateValue('kpiTotalCards', data.total_cards||0);
    animateValue('kpiValidationErrors', data.validation_errors||0);
}

// ================================================================
// RELEASE STATUS
// ================================================================
function updateReleaseStatus(data) {
    const badge = document.getElementById('releaseStatusBadge');
    const reasons = document.getElementById('releaseReasons');
    if (!badge) return;
    if (!data || data.status === 'WAITING') {
        badge.className = 'badge bg-secondary'; badge.innerHTML = '<i class="fas fa-clock"></i> Waiting';
        if (reasons) reasons.style.display = 'none'; return;
    }
    const ready = data.ready;
    badge.className = 'badge ' + (ready ? 'bg-success' : 'bg-danger');
    badge.innerHTML = '<i class="fas ' + (ready ? 'fa-check-circle' : 'fa-times-circle') + '"></i> ' + data.status;
    if (reasons && data.reasons && data.reasons.length > 0) {
        reasons.style.display = ''; reasons.innerHTML = data.reasons.map(r => '<div class="small text-danger">• ' + r + '</div>').join('');
    } else if (reasons) { reasons.style.display = 'none'; }
}

// ================================================================
// VALIDATION CHECKLIST - Updates BOTH dashboard and validation pages
// ================================================================
function updateValidationChecklist(data) {
    const containers = [];
    const c1 = document.getElementById('checklistContainer');
    const c2 = document.getElementById('validationPageChecklistContainer');
    if (c1) containers.push(c1);
    if (c2) containers.push(c2);
    if (containers.length === 0) return;
    
    const emptyHtml = '<div class="text-center text-muted py-3"><i class="fas fa-inbox fa-2x mb-2"></i><p>Waiting for validation...</p></div>';
    if (!data || data.length === 0) {
        containers.forEach(c => c.innerHTML = emptyHtml);
        return;
    }
    const html = data.map((item, idx) => {
        let icon, colorClass;
        if (item.status === 'PASS') { icon = '<i class="fas fa-check-circle text-success"></i>'; colorClass = 'checklist-pass'; }
        else if (item.status === 'FAIL') { icon = '<i class="fas fa-times-circle text-danger"></i>'; colorClass = 'checklist-fail'; }
        else { icon = '<i class="fas fa-minus-circle text-secondary"></i>'; colorClass = 'checklist-not-run'; }
        
        let detailsHtml = '';
        if (item.details && item.details.length > 0) {
            detailsHtml = '<div class="checklist-details">';
            item.details.forEach(d => {
                if (d.BatchNumber) detailsHtml += '<div class="checklist-detail-row"><span class="checklist-detail-label">Batch</span><span class="checklist-detail-value">' + escapeHtml(d.BatchNumber) + '</span></div>';
                if (d.RowNumber) detailsHtml += '<div class="checklist-detail-row"><span class="checklist-detail-label">Row</span><span class="checklist-detail-value">' + d.RowNumber + '</span></div>';
                if (d.message) detailsHtml += '<div class="checklist-detail-row"><span class="checklist-detail-label">Error</span><span class="checklist-detail-value">' + escapeHtml(d.message) + '</span></div>';
            });
            detailsHtml += '</div>';
        } else if (item.rows_checked > 0 || item.error_count > 0) {
            detailsHtml = '<div class="checklist-details"><div class="checklist-detail-row"><span class="checklist-detail-label">Rows Checked</span><span class="checklist-detail-value">' + item.rows_checked + '</span></div><div class="checklist-detail-row"><span class="checklist-detail-label">Errors</span><span class="checklist-detail-value">' + item.error_count + '</span></div></div>';
        }
        
        return '<div class="checklist-item ' + colorClass + '" onclick="toggleChecklistItem(this)"><span class="checklist-icon">' + icon + '</span><span class="checklist-label">' + escapeHtml(item.label) + '</span><span class="checklist-status ms-auto badge ' + (item.status === 'PASS' ? 'bg-success' : item.status === 'FAIL' ? 'bg-danger' : 'bg-secondary') + '">' + item.status + '</span>' + detailsHtml + '</div>';
    }).join('');
    containers.forEach(c => c.innerHTML = html);
}

function toggleChecklistItem(el) {
    el.classList.toggle('expanded');
}

// ================================================================
// VALIDATION STATUS CARD
// ================================================================
function generateFailureGuidance(failure) {
    if (!failure || !failure.has_failure) return '';
    const stage = (failure.failed_stage || '').toLowerCase();
    const reason = (failure.reason || '').toLowerCase();
    
    if (stage.includes('daily output') || reason.includes('worksheet') || reason.includes('workbook')) {
        return 'Ensure the workbook contains a valid "Daily Output File" worksheet with the correct structure. Check that the sheet name matches the expected format.';
    }
    if (reason.includes('header') || reason.includes('missing required headers')) {
        return 'Open the worksheet and verify that all required column headers are present and spelled correctly. Required headers may include Batch_No, Bag_No, Card_Type, No_of_Batches, etc.';
    }
    if (stage.includes('duplicate') || reason.includes('duplicate batch')) {
        return 'Review the listed batch numbers in the source file for duplicate entries. Each batch number should appear only once across all rows. Remove or correct duplicate rows.';
    }
    if (reason.includes('no_of_batches') || reason.includes('batch mismatch')) {
        return 'The number of batches declared does not match the actual batch count in the data. Verify the No_of_Batches value and ensure it reflects the true number of unique batch numbers.';
    }
    if (reason.includes('bag') || reason.includes('invalid bag')) {
        return 'Check the Bag_No format. Bag numbers must follow the correct format (e.g., alphanumeric with expected length). Correct any malformed bag number entries.';
    }
    if (reason.includes('blank')) {
        return 'Search for empty cells in the flagged rows and columns. All required fields must have values — blank cells will cause validation failure. Fill in missing data.';
    }
    if (reason.includes('card type') || reason.includes('card_type')) {
        return 'Verify that all Card_Type values are either "SIM" or "DMCCLS" (Capitec Bank). Any other values will be rejected. Correct invalid card type entries.';
    }
    if (reason.includes('cross') || reason.includes('cross-workbook')) {
        return 'The same batch number was found in a previously processed workbook. This indicates a duplicate submission. Verify whether this batch was already processed.';
    }
    return 'Review the error details in the Validation page for specific rows and values that need correction. Address each error listed and re-run validation.';
}

function updateValidationStatusCard(data, failure, checklist) {
    const card = document.getElementById('validationStatusCard');
    if (!card) return;
    
    card.style.display = '';
    
    const passContent = document.getElementById('statusPassContent');
    const failContent = document.getElementById('statusFailContent');
    const waitingContent = document.getElementById('statusWaitingContent');
    const titleEl = document.getElementById('validationStatusCardTitle');
    
    if (passContent) passContent.style.display = 'none';
    if (failContent) failContent.style.display = 'none';
    if (waitingContent) waitingContent.style.display = 'none';
    
    const noValidation = !data || !data.workbook;
    const hasFailed = failure && failure.has_failure;
    const hasPassed = data && data.workbook && data.status === 'PASS';
    
    if (noValidation) {
        if (waitingContent) waitingContent.style.display = '';
        if (titleEl) titleEl.innerHTML = '<i class="fas fa-clock text-secondary"></i> Validation Status';
    } else if (hasFailed) {
        if (failContent) failContent.style.display = '';
        if (titleEl) titleEl.innerHTML = '<i class="fas fa-exclamation-triangle text-danger"></i> Validation Failed — Investigation Required';
        
        const stage = document.getElementById('failureStage');
        const reason = document.getElementById('failureReason');
        const rows = document.getElementById('failureRows');
        const batches = document.getElementById('failureBatchNumbers');
        const totalErrors = document.getElementById('failureTotalErrors');
        const guidance = document.getElementById('failureGuidance');
        const checklistSummary = document.getElementById('failureChecklistSummary');
        const errorSummary = document.getElementById('failureErrorSummary');
        
        if (stage) {
            const firstFailedStage = failure.failed_stages && failure.failed_stages.length > 0 ? failure.failed_stages[0] : (failure.failed_stage || 'Unknown');
            stage.textContent = firstFailedStage;
        }
        if (reason) reason.textContent = failure.reason || 'Validation failed';
        if (guidance) guidance.textContent = generateFailureGuidance(failure);
        if (totalErrors) totalErrors.textContent = failure.total_errors || 0;
        
        if (rows) {
            if (failure.affected_rows && failure.affected_rows.length > 0) {
                rows.innerHTML = failure.affected_rows.map(r => '<span class="failure-row-badge">Row ' + r + '</span>').join('');
            } else { rows.textContent = '—'; }
        }
        if (batches) {
            if (failure.batch_numbers && failure.batch_numbers.length > 0) {
                batches.innerHTML = failure.batch_numbers.map(b => '<span class="failure-batch-badge">' + escapeHtml(b) + '</span>').join('');
            } else { batches.textContent = '—'; }
        }
        
        // Display failed stages without duplicating root cause
        const failedStagesContainer = document.getElementById('failedStagesContainer');
        const failedStagesList = document.getElementById('failedStagesList');
        if (failedStagesContainer && failedStagesList && failure.failed_stages && failure.failed_stages.length > 0) {
            failedStagesList.innerHTML = failure.failed_stages.map(s => '<li><i class="fas fa-times-circle text-danger"></i> ' + escapeHtml(s) + '</li>').join('');
            failedStagesContainer.style.display = '';
        } else {
            if (failedStagesContainer) failedStagesContainer.style.display = 'none';
        }
        
        if (checklist && checklist.length > 0) {
            const passed = checklist.filter(i => i.status === 'PASS').length;
            const failed = checklist.filter(i => i.status === 'FAIL').length;
            if (checklistSummary) checklistSummary.textContent = passed + ' checks passed';
            if (errorSummary) errorSummary.textContent = failed + ' checks failed';
        } else {
            if (checklistSummary) checklistSummary.textContent = '—';
            if (errorSummary) errorSummary.textContent = '—';
        }
    } else if (hasPassed) {
        if (passContent) passContent.style.display = '';
        if (titleEl) titleEl.innerHTML = '<i class="fas fa-check-circle text-success"></i> Validation Passed — Ready for Release';
        
        const workbookEl = document.getElementById('statusPassWorkbook');
        const dateEl = document.getElementById('statusPassDate');
        const passCheckSummary = document.getElementById('passChecklistSummary');
        
        if (workbookEl) workbookEl.textContent = data.workbook || '—';
        if (dateEl) dateEl.textContent = formatDate(data.validation_date) || '—';
        
        if (checklist && checklist.length > 0) {
            const passed = checklist.filter(i => i.status === 'PASS').length;
            if (passCheckSummary) passCheckSummary.textContent = passed + ' checks passed';
        } else {
            if (passCheckSummary) passCheckSummary.textContent = 'All checks passed';
        }
    } else {
        if (waitingContent) waitingContent.style.display = '';
        if (titleEl) titleEl.innerHTML = '<i class="fas fa-clock text-secondary"></i> Validation Status';
    }
}

// ================================================================
// RECENT VALIDATIONS - Updates BOTH dashboard and validation pages
// ================================================================
function updateRecentValidations(data) {
    const containers = [];
    const t1 = document.getElementById('recentValidationsTable');
    const t2 = document.getElementById('validationPageRecentValidationsTable');
    if (t1) containers.push(t1);
    if (t2) containers.push(t2);
    if (containers.length === 0) return;
    
    const emptyHtml = '<tr><td colspan="9" class="text-center text-muted">No validations yet</td></tr>';
    if (!data || data.length === 0) {
        containers.forEach(t => t.innerHTML = emptyHtml);
        const ce = document.getElementById('validationCount');
        if (ce) ce.textContent = '0 runs';
        return;
    }
    
    const rowHtml = data.map(run => '<tr class="history-row" onclick="loadHistoricalRun(' + run.RunID + ')" title="Click to view this validation run\'s data"><td>' + formatDate(run.date) + '</td><td>' + (run.workbook || 'Unknown') + '</td><td><span class="badge ' + (run.status === 'PASS' ? 'bg-success' : 'bg-danger') + '">' + run.status + '</span></td><td>' + (run.sim_orders || 0) + '</td><td>' + (run.bank_orders || 0) + '</td><td>' + (run.total_cards || 0) + '</td><td><span class="badge bg-warning">' + (run.errors || 0) + '</span></td><td>' + (run.duration || 0) + 's</td><td><button class="btn btn-sm btn-outline-danger delete-run-btn" onclick="event.stopPropagation(); deleteValidationRun(' + run.RunID + ', \'' + escapeHtml(run.workbook || '') + '\')" title="Delete this validation run"><i class="fas fa-trash-alt"></i></button></td></tr>').join('');
    
    containers.forEach(t => t.innerHTML = rowHtml);
    const ce = document.getElementById('validationCount');
    if (ce) { const c = data.length; ce.textContent = c + ' ' + (c === 1 ? 'run' : 'runs'); }
}

function loadHistoricalRun(runId) {
    showToast('Loading historical validation data...', 'info', 2000);
    fetch('/api/dashboard/run-data/' + runId).then(r => r.json()).then(data => {
        if (data.error) { showToast('Error: ' + data.error, 'error'); return; }
        updateDashboardStatus(data.latest);
        updateBusinessKPI(data.kpi);
        updateValidationChecklist(data.checklist);
        updateReleaseStatus(data.release);
        updateValidationStatusCard(data.latest, data.failure, data.checklist);
        showToast('Viewing validation run #' + runId + ' — ' + data.latest.workbook, 'success', 3000);
    }).catch(err => {
        showToast('Failed to load historical validation data', 'error');
        console.error('Historical load error:', err);
    });
}

function deleteValidationRun(runId, workbookName) {
    if (!confirm('Are you sure you want to delete the validation run for "' + workbookName + '"?\n\nThis will permanently remove all associated data including errors, duplicates, and statistics.')) {
        return;
    }
    fetch('/api/dashboard/delete-run', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({run_id: runId})
    }).then(r => r.json()).then(data => {
        if (data.status === 'ok') {
            showToast('Validation run "' + workbookName + '" deleted successfully', 'success');
            refreshDashboard();
        } else {
            showToast('Delete failed: ' + (data.error || 'Unknown error'), 'error');
        }
    }).catch(err => {
        showToast('Failed to delete validation run', 'error');
        console.error('Delete error:', err);
    });
}

// ================================================================
// CHARTS
// ================================================================
function updateCharts(trend, errorTrend) { updateTrendChart(trend); updateErrorTrendChart(errorTrend); }

function updateTrendChart(trend) {
    const ctx = document.getElementById('trendChart'); if (!ctx) return;
    if (trendChart) { trendChart.data.labels = trend.dates||[]; trendChart.data.datasets[0].data = trend.counts||[]; trendChart.update(); }
    else {
        trendChart = new Chart(ctx, { type: 'line', data: { labels: trend.dates||[], datasets: [{ label: 'Daily Validations', data: trend.counts||[], borderColor: '#00A651', backgroundColor: 'rgba(0,166,81,0.1)', tension: 0.4, fill: true }] }, options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { display: true } }, scales: { y: { beginAtZero: true } } } });
    }
}

function updateErrorTrendChart(data) {
    const ctx = document.getElementById('errorTrendChart'); if (!ctx) return;
    if (errorTrendChart) { errorTrendChart.data.labels = data.dates||[]; errorTrendChart.data.datasets[0].data = data.counts||[]; errorTrendChart.update(); }
    else {
        errorTrendChart = new Chart(ctx, { type: 'line', data: { labels: data.dates||[], datasets: [{ label: 'Errors', data: data.counts||[], borderColor: '#dc3545', backgroundColor: 'rgba(220,53,69,0.1)', tension: 0.4, fill: true }] }, options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { display: true } }, scales: { y: { beginAtZero: true } } } });
    }
}

function loadAnalyticsCharts() { fetch('/api/analytics/charts').then(r=>r.json()).then(d=>{ updateErrorDistributionChart(d.errors); updateValidationTrendChart(d.trend); }); }

function updateErrorDistributionChart(errors) {
    const ctx = document.getElementById('errorDistributionChart'); if (!ctx) return;
    const cd = [errors.duplicates||0, errors.batch_errors||0, errors.bag_errors||0, errors.blank_errors||0, errors.card_type_errors||0, errors.cross_workbook_errors||0];
    if (errorDistributionChart) { errorDistributionChart.data.datasets[0].data = cd; errorDistributionChart.update(); }
    else { errorDistributionChart = new Chart(ctx, { type: 'bar', data: { labels: ['Duplicates','Batch','Bag','Blank','Card Type','Cross WB'], datasets: [{ label: 'Error Count', data: cd, backgroundColor: '#00A651' }] }, options: { responsive: true, maintainAspectRatio: true, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true } } } }); }
}

function updateValidationTrendChart(trend) {
    const ctx = document.getElementById('validationTrendChart'); if (!ctx) return;
    if (validationTrendChart) { validationTrendChart.data.labels = trend.dates||[]; validationTrendChart.data.datasets[0].data = trend.counts||[]; validationTrendChart.update(); }
    else { validationTrendChart = new Chart(ctx, { type: 'line', data: { labels: trend.dates||[], datasets: [{ label: 'Validations', data: trend.counts||[], borderColor: '#00A651', backgroundColor: 'rgba(0,166,81,0.1)', tension: 0.4, fill: true }] }, options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { display: true } } } }); }
}

function loadAuditHistory() {
    fetch('/api/audit/history').then(r=>r.json()).then(data => {
        const table = document.getElementById('auditTable'); if (!table) return;
        if (!data||data.length===0) { table.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No audit records</td></tr>'; return; }
        table.innerHTML = data.map(r => '<tr><td>' + formatDate(r.date) + '</td><td>' + r.action + '</td><td>' + (r.user||'-') + '</td><td><span class="badge bg-info">' + r.result + '</span></td><td>' + (r.description||'-') + '</td></tr>').join('');
    });
}

function exportAuditCSV() { window.location.href = '/api/audit/export'; }

// ================================================================
// SETTINGS
// ================================================================
function applyTheme(theme) { if (theme === 'Dark') document.body.classList.add('dark-mode'); else document.body.classList.remove('dark-mode'); }

function loadSettings() {
    fetch('/api/settings/get').then(r=>r.json()).then(data => {
        const theme = data.THEME || 'Light';
        document.getElementById('themeSetting').value = theme;
        document.getElementById('autoHighlight').checked = data.AUTO_HIGHLIGHT === 'TRUE';
        document.getElementById('autoBackup').checked = data.AUTO_BACKUP === 'TRUE';
        applyTheme(theme);
    });
}

function saveSettings() {
    const theme = document.getElementById('themeSetting').value;
    const settings = { 'THEME': theme, 'AUTO_HIGHLIGHT': document.getElementById('autoHighlight').checked ? 'TRUE' : 'FALSE', 'AUTO_BACKUP': document.getElementById('autoBackup').checked ? 'TRUE' : 'FALSE' };
    fetch('/api/settings/save', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(settings) }).then(r=>r.json()).then(() => { applyTheme(theme); alert('Settings saved successfully'); });
}

// ================================================================
// ANIMATION & UTILITY
// ================================================================
function animateValue(elementId, endValue, suffix = '') {
    const element = document.getElementById(elementId); if (!element) return;
    const target = Number(endValue) || 0;
    const currentDisplay = element.textContent.replace(suffix, '').trim();
    const displayedValue = parseInt(currentDisplay) || 0;
    if (displayedValue === target) return;
    if (animationStore[elementId]) { clearInterval(animationStore[elementId]); animationStore[elementId] = null; }
    const startValue = displayedValue, duration = 300, steps = 30, increment = (target - startValue) / steps;
    let current = startValue, step = 0;
    const timer = setInterval(() => { step++; current += increment; if (step >= steps) { current = target; clearInterval(timer); animationStore[elementId] = null; } element.textContent = Math.floor(current) + suffix; }, duration / steps);
    animationStore[elementId] = timer;
}

function updateLastUpdatedTime() { const el = document.getElementById('lastUpdated'); if (el) el.textContent = new Date().toLocaleTimeString(); }

function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer'); if (!container) return;
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div'); toast.id = toastId; toast.className = 'toast ' + type;
    const icons = { 'success': 'fa-check-circle', 'error': 'fa-exclamation-circle', 'warning': 'fa-exclamation-triangle', 'info': 'fa-info-circle' };
    toast.innerHTML = '<div style="padding:1rem;display:flex;align-items:center;gap:1rem;"><i class="fas ' + (icons[type]||icons.info) + '"></i><span>' + message + '</span><button type="button" onclick="document.getElementById(\'' + toastId + '\').remove()" style="background:none;border:none;cursor:pointer;font-size:1.2rem;opacity:0.7;margin-left:auto;">&times;</button></div>';
    container.appendChild(toast);
    if (duration > 0) { setTimeout(() => { const el = document.getElementById(toastId); if (el) { el.style.animation = 'slideOut 0.3s ease-out'; setTimeout(() => el.remove(), 300); } }, duration); }
}

function formatDate(dateString) {
    if (!dateString) return '—';
    const date = new Date(dateString);
    return String(date.getDate()).padStart(2,'0') + '/' + String(date.getMonth()+1).padStart(2,'0') + '/' + date.getFullYear() + ' ' + String(date.getHours()).padStart(2,'0') + ':' + String(date.getMinutes()).padStart(2,'0');
}

function escapeHtml(text) { const div = document.createElement('div'); div.textContent = text; return div.innerHTML; }

function updateProfilePicture(avatar) {
    if (!avatar || !avatar.avatar_url) return;
    const container = document.querySelector('.col-lg-4 .dashboard-card .card-body');
    if (!container) return;
    
    const existingImg = container.querySelector('.profile-avatar-img');
    if (existingImg) {
        existingImg.src = avatar.avatar_url;
    } else {
        container.innerHTML = '';
        const wrapper = document.createElement('div');
        wrapper.className = 'profile-card';
        wrapper.style.cssText = 'display:flex;justify-content:center;align-items:center;padding:16px 0;';
        
        const img = document.createElement('img');
        img.src = avatar.avatar_url;
        img.alt = 'Profile Picture';
        img.className = 'profile-avatar-img';
        img.style.cssText = 'width:220px;height:220px;border-radius:50%;object-fit:cover;border:4px solid #198754;box-shadow:0 4px 12px rgba(0,0,0,0.2);';
        
        wrapper.appendChild(img);
        container.appendChild(wrapper);
    }
}

// ================================================================
// VALIDATION WORKSPACE
// ================================================================
let currentValidation = { file: null, fileName: '', fileSize: 0, startTime: null, elapsed: 0, results: null, errors: [] };
let validationElapsedTimer = null, validationProgressTimer = null;
let currentJobId = null;

function initValidationWorkspace() {
    console.log('Initializing validation workspace...');
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    
    if (!uploadZone || !fileInput) {
        console.warn('Validation workspace elements not found:', { uploadZone: !!uploadZone, fileInput: !!fileInput });
        return;
    }
    
    // Add event listeners directly without cloning
    uploadZone.addEventListener('dragover', function(e) { 
        e.preventDefault(); 
        this.classList.add('drag-over'); 
    });
    uploadZone.addEventListener('dragleave', function() { 
        this.classList.remove('drag-over'); 
    });
    uploadZone.addEventListener('drop', function(e) { 
        e.preventDefault(); 
        this.classList.remove('drag-over'); 
        if (e.dataTransfer.files.length > 0) { 
            fileInput.files = e.dataTransfer.files; 
            handleFileSelected(e.dataTransfer.files[0]); 
        } 
    });
    
    fileInput.addEventListener('change', function(e) { 
        if (e.target.files.length > 0) { 
            console.log('File selected via input:', e.target.files[0].name);
            handleFileSelected(e.target.files[0]); 
        } 
    });
    
    const es = document.getElementById('errorSearch'), ef = document.getElementById('errorTypeFilter');
    if (es && !es.dataset.listenerAdded) {
        es.addEventListener('keyup', filterErrorTable);
        es.dataset.listenerAdded = 'true';
    }
    if (ef && !ef.dataset.listenerAdded) {
        ef.addEventListener('change', filterErrorTable);
        ef.dataset.listenerAdded = 'true';
    }
    
    console.log('Validation workspace initialized successfully');
}

function resetValidationUI() {
    const vp = document.getElementById('validation-page');
    if (!vp) { console.error('Validation page container not found'); return; }
    const infoPanel = vp.querySelector('[data-role="workbook-info"]');
    const noFile = vp.querySelector('#validationNoFileSelected');
    const validateBtn = vp.querySelector('[data-role="validate-btn"]');
    if (infoPanel) { infoPanel.style.display = 'none'; }
    if (noFile) { noFile.style.display = ''; }
    if (validateBtn) { validateBtn.style.display = 'none'; }
}

function handleFileSelected(file) {
    console.log('File selected:', file.name, 'Size:', file.size);
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['xlsx','xlsm','xls'].includes(ext)) { 
        showToast('Invalid file format. Please upload .xlsx, .xlsm, or .xls files.', 'error'); 
        console.error('Invalid file extension:', ext);
        return; 
    }
    if (file.size > 500*1024*1024) { 
        showToast('File too large. Maximum size is 500 MB.', 'error'); 
        console.error('File too large:', file.size);
        return; 
    }
    currentValidation.file = file; 
    currentValidation.fileName = file.name; 
    currentValidation.fileSize = file.size;
    console.log('Displaying workbook info for:', file.name);
    resetValidationUI();
    displayWorkbookInfo(file);
}

function displayWorkbookInfo(file) {
    const vp = document.getElementById('validation-page');
    if (!vp) { console.error('Validation page container not found'); return; }
    const nf = vp.querySelector('#validationNoFileSelected');
    const ip = vp.querySelector('[data-role="workbook-info"]');
    const vb = vp.querySelector('[data-role="validate-btn"]');
    if (nf) nf.style.display = 'none'; if (ip) ip.style.display = 'block'; if (vb) vb.style.display = 'block';
    const fs = (file.size / (1024*1024)).toFixed(2), lm = new Date(file.lastModified);
    const ne = document.getElementById('workbookFileName'), se = document.getElementById('workbookFileSize'), me = document.getElementById('workbookModifiedDate'), she = document.getElementById('workbookSheetCount');
    if (ne) ne.textContent = file.name; if (se) se.textContent = fs + ' MB';
    if (me) me.textContent = lm.toLocaleDateString() + ' ' + lm.toLocaleTimeString(); if (she) she.textContent = 'Auto-detected';
    // Set dynamic daily output file name and operator
    const dailyOutputEl = vp.querySelector('[data-role="daily-output-file"]');
    if (dailyOutputEl) {
        const now = new Date();
        const d = String(now.getDate()).padStart(2,'0');
        const m = String(now.getMonth()+1).padStart(2,'0');
        const y = now.getFullYear();
        dailyOutputEl.textContent = 'DAILY OUTPUT FILE ' + d + '-' + m + '-' + y;
    }
    const operatorEl = vp.querySelector('[data-role="operator"]');
    if (operatorEl) {
        const navUser = document.getElementById('navUsername');
        operatorEl.textContent = navUser ? navUser.textContent : 'Unknown';
    }
    // Reset previous validation results UI
    const summarySection = document.getElementById('validationSummarySection');
    const errorSection = document.getElementById('errorDetailsSection');
    const completionSection = document.getElementById('validationCompletionSection');
    if (summarySection) summarySection.style.display = 'none';
    if (errorSection) errorSection.style.display = 'none';
    if (completionSection) completionSection.style.display = 'none';
    const successSmiley = document.getElementById('validationCompletionSmiley');
    const failureSmiley = document.getElementById('validationFailureSmiley');
    if (successSmiley) successSmiley.style.display = 'none';
    if (failureSmiley) failureSmiley.style.display = 'none';
}

function startValidation() {
    if (!currentValidation.file) { showToast('Please select a file first.', 'error'); return; }
    resetDashboardDisplay();
    resetValidationUI();
    startProgressPolling();
    const vp = document.getElementById('validation-page');
    const progressRow = vp ? vp.querySelector('#validationProgressRow') : document.getElementById('validationProgressRow');
    const summarySection = vp ? vp.querySelector('#validationSummarySection') : document.getElementById('validationSummarySection');
    const errorSection = vp ? vp.querySelector('#errorDetailsSection') : document.getElementById('errorDetailsSection');
    const completionSection = vp ? vp.querySelector('#validationCompletionSection') : document.getElementById('validationCompletionSection');
    if (progressRow) progressRow.style.display = 'block';
    if (summarySection) summarySection.style.display = 'none';
    if (errorSection) errorSection.style.display = 'none';
    if (completionSection) completionSection.style.display = 'none';
    const validationBtn = vp ? vp.querySelector('[data-role="validate-btn"]') : document.querySelector('[data-role="validate-btn"]');
    if (validationBtn) validationBtn.style.display = 'none';
    const se = document.getElementById('validationStatus'); if (se) se.style.display = 'block';
    currentValidation.startTime = Date.now(); currentValidation.elapsed = 0;
    startValidationProgress(); startElapsedTimer();
    uploadFileForValidation(currentValidation.file);
}

function uploadFileForValidation(file) {
    const formData = new FormData(); formData.append('file', file);
    fetch('/api/validate/upload', { method: 'POST', body: formData })
    .then(r => r.json()).then(data => {
        console.log('Upload response received:', data);
        stopElapsedTimer();
        if (data.error) { 
            showToast('Validation error: ' + data.error, 'error'); 
            data.error_count = 1; data.warning_count = 0; data.duplicates_found = 0; data.duration_seconds = 0; data.errors = [data.error]; data.validation_errors = []; data.passed = false;
        }
        stopValidationProgress(data.passed);
        currentValidation.results = data;
        displayValidationResults(data);
        loadValidationSummary();
        setTimeout(() => { refreshDashboard(); showToast('Dashboard updated', 'info'); }, 2000);
    }).catch(error => { 
        console.error('Upload error:', error); 
        stopElapsedTimer(); 
        stopValidationProgress(false); 
        showToast('Upload failed: ' + error.message, 'error'); 
        const vps = document.getElementById('validationProgressSection'); 
        const uz = document.getElementById('uploadZone'); 
        if (vps) vps.style.display = 'none'; 
        if (uz) uz.style.display = 'block'; 
    });
}

function loadValidationSummary() {
    fetch('/api/dashboard/validation-results').then(r => r.json()).then(data => {
        if (data && Object.keys(data).length > 0) {
            console.log('Validation summary loaded:', data);
        }
    }).catch(err => console.error('Failed to load validation summary:', err));
}

function updateProgress(percent, stepText) {
    const bar = document.getElementById('validationProgressBar'), pct = document.getElementById('progressPercentage'), step = document.getElementById('validationStepText');
    if (bar) bar.style.width = percent + '%'; if (pct) pct.textContent = percent + '%'; if (step) step.innerHTML = '<i class="fas fa-hourglass-half"></i> ' + stepText;
}

const VALIDATION_PROGRESS_STAGES = [
    {pct:4,text:'Initializing validation engine...'},{pct:9,text:'Opening workbook...'},{pct:14,text:'Detecting Daily Output worksheet...'},
    {pct:20,text:'Validating worksheet structure...'},{pct:28,text:'Checking duplicate batch numbers...'},{pct:36,text:'Validating No_of_Batches...'},
    {pct:44,text:'Validating Bag_No format...'},{pct:52,text:'Checking blank fields...'},{pct:60,text:'Validating Card Types...'},
    {pct:68,text:'Calculating SIM and Bank Orders...'},{pct:76,text:'Calculating SIM and Bank Cards...'},{pct:82,text:'Updating Capitec Summary Report...'},
    {pct:88,text:'Creating backup...'},{pct:93,text:'Generating audit log...'},{pct:97,text:'Producing validation report...'}
];
const PROGRESS_MAX_AUTO = 97;

function startValidationProgress() {
    if (validationProgressTimer) { clearInterval(validationProgressTimer); validationProgressTimer = null; }
    let csi = 0, cp = 0, sp = 0, es = 0; const EASING_STEPS = 12;
    const is = VALIDATION_PROGRESS_STAGES[0]; updateProgress(is.pct, is.text); cp = is.pct;
    validationProgressTimer = setInterval(() => {
        const ts = VALIDATION_PROGRESS_STAGES[csi], tp = ts.pct, tt = ts.text;
        if (es < EASING_STEPS) { es++; const p = es/EASING_STEPS, e = 1-Math.pow(1-p,3); cp = sp+(tp-sp)*e; if (cp < PROGRESS_MAX_AUTO) updateProgress(Math.round(cp), tt); }
        else if (csi < VALIDATION_PROGRESS_STAGES.length-1) { csi++; sp = tp; es = 0; updateProgress(tp, tt); }
        else { updateProgress(PROGRESS_MAX_AUTO, 'Producing validation report...'); clearInterval(validationProgressTimer); validationProgressTimer = null; }
    }, 110);
}

function stopValidationProgress(success) {
    if (validationProgressTimer) { clearInterval(validationProgressTimer); validationProgressTimer = null; }
    const vp = document.getElementById('validation-page');
    if (!vp) { console.error('Validation page container not found'); return; }
    if (success) {
        updateProgress(100, 'Validation Complete');
        const vs = vp.querySelector('#validationStatus');
        if (vs) vs.style.display = 'none';
        const vcs = vp.querySelector('#validationCompletionSmiley');
        if (vcs) vcs.style.display = 'block';
        const vfs = vp.querySelector('#validationFailureSmiley');
        if (vfs) vfs.style.display = 'none';
    }
    else {
        const vpRow = vp.querySelector('#validationProgressRow');
        if (vpRow) vpRow.style.display = 'none';
        const vs = vp.querySelector('#validationStatus');
        if (vs) vs.style.display = 'none';
        const vb = vp.querySelector('[data-role="validate-btn"]');
        if (vb) vb.style.display = 'block';
        const vcs = vp.querySelector('#validationCompletionSmiley');
        if (vcs) vcs.style.display = 'none';
        const vfs = vp.querySelector('#validationFailureSmiley');
        if (vfs) vfs.style.display = 'block';
    }
}

function startElapsedTimer() {
    if (validationElapsedTimer) clearInterval(validationElapsedTimer);
    validationElapsedTimer = setInterval(() => { currentValidation.elapsed = Math.floor((Date.now()-currentValidation.startTime)/1000); const el = document.getElementById('validationElapsedTime'); if (el) el.textContent = currentValidation.elapsed + 's'; }, 100);
}

function stopElapsedTimer() { if (validationElapsedTimer) { clearInterval(validationElapsedTimer); validationElapsedTimer = null; } }

function displayValidationResults(data) {
    console.log('Displaying validation results:', data);
    const vp = document.getElementById('validation-page');
    if (!vp) { console.error('Validation page container not found'); return; }
    
    // Find all elements using scoped selectors
    const progressRow = vp.querySelector('#validationProgressRow');
    const statusEl = vp.querySelector('#validationStatus');
    const summarySection = vp.querySelector('#validationSummarySection');
    const errorSection = vp.querySelector('#errorDetailsSection');
    const completionSection = vp.querySelector('#validationCompletionSection');
    
    // Hide progress, show results
    if (progressRow) progressRow.style.display = 'none';
    if (statusEl) statusEl.style.display = 'none';
    if (summarySection) summarySection.style.display = 'flex';
    if (errorSection) errorSection.style.display = data.error_count > 0 ? 'block' : 'none';
    if (completionSection) completionSection.style.display = 'block';
    
    // Update summary cards with null-safe access
    const ec = data.error_count||0, wc = data.warning_count||0, dc = data.duplicates_found||0;
    const summaryPassed = vp.querySelector('#summaryPassed');
    const summaryFailed = vp.querySelector('#summaryFailed');
    const summaryWarnings = vp.querySelector('#summaryWarnings');
    const summaryDuplicates = vp.querySelector('#summaryDuplicates');
    const summaryProcessingTime = vp.querySelector('#summaryProcessingTime');
    const summaryCardsProcessed = vp.querySelector('#summaryCardsProcessed');
    const errorCount = vp.querySelector('#errorCount');
    
    if (summaryPassed) summaryPassed.textContent = Math.max(0, 100-ec);
    if (summaryFailed) summaryFailed.textContent = ec;
    if (summaryWarnings) summaryWarnings.textContent = wc;
    if (summaryDuplicates) summaryDuplicates.textContent = dc;
    if (summaryProcessingTime) summaryProcessingTime.textContent = (data.duration_seconds||0).toFixed(1)+'s';
    if (summaryCardsProcessed) summaryCardsProcessed.textContent = Math.max(0, 100-ec)+ec;
    if (errorCount) errorCount.textContent = ec;
    
    // Show validate button again so user can run another validation
    const vb = vp.querySelector('[data-role="validate-btn"]');
    if (vb) vb.style.display = 'block';
    
    // Ensure file info panel remains visible after validation
    const ip = vp.querySelector('[data-role="workbook-info"]');
    const nf = vp.querySelector('#validationNoFileSelected');
    if (ip) ip.style.display = 'block';
    if (nf) nf.style.display = 'none';
    
    // Populate error table
    populateErrorTable(data);
    
    console.log('Validation results displayed successfully');
}

function parseError(errorMessage) {
    const parsed = { row: '-', cell: '-', errorType: 'Unknown', invalidValue: '-', reason: errorMessage };
    // Match format: "Row X, cell Y: ..." or "Row X: ..."
    const rm = errorMessage.match(/^Row\s+(\d+)(?:,\s*cell\s+([^:]+))?\s*:\s*(.+)/i);
    if (rm) {
        parsed.row = rm[1];
        parsed.cell = rm[2] || '-';
        const rest = rm[3].trim();
        const im = rest.match(/^Invalid\s+(.+?)\s+'(.+?)'[\.:]?\s*(.*)/i);
        if (im) { parsed.errorType = 'INVALID_'+im[1].toUpperCase().replace(/\s+/g,'_').replace(/INVALID_NO_OF_BATCHES/,'BATCH_MISMATCH'); parsed.invalidValue = im[2]; parsed.reason = im[3]||'Invalid value'; return parsed; }
        const bm = rest.match(/^Blank\s+(.+?)\s+'(.+?)'/i);
        if (bm) { parsed.errorType = 'BLANK_FIELD'; parsed.invalidValue = bm[2]; parsed.reason = bm[0]; return parsed; }
        const bfm = rest.match(/^Blank\s+field\s+'(.+?)'/i);
        if (bfm) { parsed.errorType = 'BLANK_FIELD'; parsed.invalidValue = '(empty)'; parsed.reason = 'Blank field: ' + bfm[1]; return parsed; }
        if (rest.match(/No_of_Batches mismatch/i)) { parsed.errorType = 'BATCH_MISMATCH'; parsed.reason = rest; return parsed; }
        const bfm2 = rest.match(/^Invalid\s+Bag_No\s+format\s+'(.+?)'[\.:]?\s*(.*)/i);
        if (bfm2) { parsed.errorType = 'INVALID_BAG'; parsed.invalidValue = bfm2[1]; parsed.reason = bfm2[2]||'Invalid format'; return parsed; }
        const ctm = rest.match(/^Invalid\s+Card_Type\s+'(.+?)'[\.:]?\s*(.*)/i);
        if (ctm) { parsed.errorType = 'INVALID_CARD_TYPE'; parsed.invalidValue = ctm[1]; parsed.reason = ctm[2]||'Must be SIM or DMCCLS'; return parsed; }
        const ibm = rest.match(/^Invalid\s+No_of_Batches\s+value:\s*(.+)/i);
        if (ibm) { parsed.errorType = 'INVALID_BATCH_COUNT'; parsed.invalidValue = ibm[1]; parsed.reason = 'Invalid number of batches'; return parsed; }
        parsed.errorType = 'VALIDATION_ERROR'; parsed.reason = rest; return parsed;
    }
    const dbm = errorMessage.match(/^Duplicate\s+batch\s+'(.+?)'.*/i);
    if (dbm) { parsed.errorType = 'DUPLICATE'; parsed.invalidValue = dbm[1]; parsed.reason = errorMessage; return parsed; }
    const dbnm = errorMessage.match(/^Duplicate\s+batch\s+number\s+'(.+?)'.*/i);
    if (dbnm) { parsed.errorType = 'DUPLICATE'; parsed.invalidValue = dbnm[1]; parsed.reason = errorMessage; return parsed; }
    const cwm = errorMessage.match(/^Cross-workbook\s+duplicate\s+'(.+?)'.*/i);
    if (cwm) { parsed.errorType = 'CROSS_WORKBOOK'; parsed.invalidValue = cwm[1]; parsed.reason = errorMessage; return parsed; }
    if (errorMessage.match(/^Missing\s+required\s+headers/i)) { parsed.errorType = 'HEADER_ERROR'; parsed.reason = errorMessage; return parsed; }
    if (errorMessage.match(/^(Failed to load|Daily Output File|Error validating|Validation engine error)/i)) { parsed.errorType = 'SYSTEM_ERROR'; parsed.reason = errorMessage; return parsed; }
    return parsed;
}

function renderErrorSummary(parsedErrors) {
    const container = document.getElementById('errorSummaryContainer'); if (!container) return;
    const tc = {}; parsedErrors.forEach(e => { const l = e.errorType.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase()); if (!tc[l]) tc[l]=0; tc[l]++; });
    container.style.display = 'block'; container.innerHTML = '<div class="error-summary-title"><i class="fas fa-list"></i> Error Summary</div>';
    const bc = document.createElement('div'); bc.className = 'error-summary-badges';
    Object.entries(tc).forEach(([t,c]) => { const b = document.createElement('span'); b.className = 'badge error-summary-badge'; b.innerHTML = escapeHtml(t) + ' <strong>' + c + '</strong>'; bc.appendChild(b); });
    container.appendChild(bc);
}

function populateErrorTable(data) {
    const tb = document.getElementById('errorTableBody'); if (!tb) return; tb.innerHTML = '';
    if ((!data.errors || data.errors.length === 0) && (!data.validation_errors || data.validation_errors.length === 0)) {
        tb.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No errors found</td></tr>'; return;
    }
    // Prefer structured validation_errors if available; fall back to parsing legacy error strings
    let pe = [];
    if (data.validation_errors && data.validation_errors.length > 0) {
        pe = data.validation_errors.map(ve => ({
            row: ve.row_number || '-',
            cell: ve.cell_reference || '-',
            errorType: ve.error_type || 'UNKNOWN',
            invalidValue: ve.invalid_value || '-',
            reason: ve.error_message || ve.error_message || ''
        }));
    } else {
        pe = data.errors.map(msg => parseError(msg));
    }
    const eg = {}; pe.forEach(e => { if (!eg[e.errorType]) eg[e.errorType] = {type:e.errorType,messages:[],count:0}; eg[e.errorType].messages.push(e.reason); eg[e.errorType].count++; });
    currentValidation.errors = eg; currentValidation.parsedErrors = pe;
    renderErrorSummary(pe);
    pe.forEach(e => { const row = document.createElement('tr'); row.dataset.type = e.errorType; row.innerHTML = '<td><span class="error-row-badge">' + escapeHtml(e.row) + '</span></td><td><span class="badge error-type-badge" data-type="' + escapeHtml(e.errorType) + '">' + escapeHtml(e.errorType.replace(/_/g,' ')) + '</span></td><td><code class="error-value">' + escapeHtml(e.invalidValue) + '</code></td><td><small class="error-reason">' + escapeHtml(e.reason) + (e.cell && e.cell !== '-' ? ' <strong class="text-warning">[' + escapeHtml(e.cell) + ']</strong>' : '') + '</small></td>'; tb.appendChild(row); });
}

function filterErrorTable() {
    const filter = document.getElementById('errorTypeFilter').value.toUpperCase();
    const search = document.getElementById('errorSearch').value.toLowerCase();
    const rows = document.querySelectorAll('#errorTableBody tr'); let vc = 0;
    rows.forEach(row => {
        if (row.textContent.includes('No errors')) return;
        const rt = row.dataset.type||'', cells = row.querySelectorAll('td'), ct = Array.from(cells).map(c=>c.textContent||'').join(' ');
        const tm = !filter||rt.toUpperCase().includes(filter), sm = !search||ct.toLowerCase().includes(search);
        row.style.display = (tm&&sm) ? '' : 'none'; if (tm&&sm) vc++;
    });
    if (vc===0 && document.getElementById('errorTableBody')) document.getElementById('errorTableBody').innerHTML = '<tr><td colspan="4" class="text-center text-muted">No matching errors</td></tr>';
}

function toggleErrorTable() { const w = document.getElementById('errorTableWrapper'), c = document.getElementById('errorChevron'); if (w) w.classList.toggle('show'); if (c) c.classList.toggle('rotated'); }

function downloadValidationReport() {
    if (!currentValidation.results) { showToast('No validation results to download', 'error'); return; }
    let csv = 'CAPITEC DAILY RECONCILIATION SYSTEM - VALIDATION REPORT\nGenerated: '+new Date().toLocaleString()+'\n\nVALIDATION SUMMARY\nFile Name,'+currentValidation.fileName+'\nStatus,'+(currentValidation.results.passed?'PASSED':'FAILED')+'\nProcessing Time,'+currentValidation.results.duration_seconds+'s\nTotal Errors,'+currentValidation.results.error_count+'\nTotal Warnings,'+currentValidation.results.warning_count+'\nDuplicates Found,'+currentValidation.results.duplicates_found+'\n\nERROR DETAILS\nError Type,Description\n';
    (currentValidation.results.errors||[]).forEach(error => { csv += '"'+error.split(':')[0]+'","'+error.replace(/"/g,'""')+'"\n'; });
    const blob = new Blob([csv],{type:'text/csv'}), url = window.URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'validation-report-'+new Date().getTime()+'.csv'; a.click(); window.URL.revokeObjectURL(url);
    showToast('Report downloaded successfully', 'success', 2000);
}

function downloadErrorCSV() {
    if (!currentValidation.errors||Object.keys(currentValidation.errors).length===0) { showToast('No errors to download', 'error'); return; }
    let csv = 'Error Type,Count,First Message\n';
    Object.values(currentValidation.errors).forEach(g => { csv += '"'+g.type+'",'+g.count+',"'+ (g.messages[0]||'').replace(/"/g,'""')+'"\n'; });
    const blob = new Blob([csv],{type:'text/csv'}), url = window.URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'errors-'+new Date().getTime()+'.csv'; a.click(); window.URL.revokeObjectURL(url);
    showToast('Error report downloaded', 'success', 2000);
}

function downloadHighlightedWorkbook() { showToast('Highlighted workbook feature coming soon', 'info', 3000); }

function downloadAuditLog() {
    fetch('/api/audit/export').then(r=>r.blob()).then(blob => {
        const url = window.URL.createObjectURL(blob); const a = document.createElement('a');
        a.href = url; a.download = 'audit-log-'+new Date().getTime()+'.csv'; a.click(); window.URL.revokeObjectURL(url);
        showToast('Audit log downloaded', 'success', 2000);
    }).catch(error => { showToast('Failed to download audit log', 'error'); console.error('Error:', error); });
}