/** @odoo-module **/

import { App } from "@odoo/owl";

// ─── PRINT PREVIEW MODAL ─────────────────────────────────────────────────────
(function () {
    function showPrintPreviewModal(reportHtmlUrl, reportPdfUrl) {
        // Remove any existing modal
        const existing = document.getElementById('hospital-print-preview-overlay');
        if (existing) existing.remove();

        const overlay = document.createElement('div');
        overlay.id = 'hospital-print-preview-overlay';
        overlay.style.cssText = [
            'position:fixed', 'top:0', 'left:0', 'width:100%', 'height:100%',
            'background:rgba(0,0,0,0.75)', 'z-index:100000',
            'display:flex', 'flex-direction:column',
            'align-items:center', 'justify-content:center'
        ].join(';');

        const modal = document.createElement('div');
        modal.style.cssText = [
            'background:#fff', 'width:88%', 'height:90%',
            'border-radius:8px', 'display:flex', 'flex-direction:column',
            'overflow:hidden', 'box-shadow:0 20px 60px rgba(0,0,0,0.5)'
        ].join(';');

        const toolbar = document.createElement('div');
        toolbar.style.cssText = [
            'background:#1e3a8a', 'color:#fff', 'padding:10px 20px',
            'display:flex', 'justify-content:space-between', 'align-items:center',
            'flex-shrink:0'
        ].join(';');
        toolbar.innerHTML = `
            <span style="font-weight:700;font-size:15px;letter-spacing:1px;">📄 Print Preview</span>
            <div style="display:flex;gap:10px;">
                <button id="hpm-print" style="background:#10b981;color:#fff;border:none;padding:7px 18px;border-radius:5px;cursor:pointer;font-size:13px;font-weight:600;">🖨️ Print</button>
                <button id="hpm-pdf" style="background:#3b82f6;color:#fff;border:none;padding:7px 18px;border-radius:5px;cursor:pointer;font-size:13px;font-weight:600;">⬇️ Download PDF</button>
                <button id="hpm-close" style="background:#ef4444;color:#fff;border:none;padding:7px 18px;border-radius:5px;cursor:pointer;font-size:13px;font-weight:600;">✕ Close</button>
            </div>
        `;

        const iframe = document.createElement('iframe');
        iframe.style.cssText = 'flex:1;border:none;width:100%;background:#f3f4f6;';
        iframe.src = reportHtmlUrl;

        modal.appendChild(toolbar);
        modal.appendChild(iframe);
        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        document.getElementById('hpm-close').onclick = () => overlay.remove();
        overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };

        document.getElementById('hpm-print').onclick = () => {
            try { iframe.contentWindow.print(); }
            catch(e) { window.open(reportHtmlUrl); }
        };

        document.getElementById('hpm-pdf').onclick = () => {
            const a = document.createElement('a');
            a.href = reportPdfUrl;
            a.download = '';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        };
    }

    // Override XMLHttpRequest to intercept Odoo's report PDF calls
    // Odoo sends the report via /report/pdf endpoint - we intercept the action service
    // by hooking into the fetch API which Odoo uses for RPC calls
    const _origFetch = window.fetch;
    window.fetch = async function (...args) {
        const response = await _origFetch.apply(this, args);
        return response;
    };

    // Primary approach: intercept window.open for /report/ URLs
    const _origOpen = window.open;
    window.open = function (url, target, features) {
        if (url && typeof url === 'string' && url.includes('/report/pdf/')) {
            const htmlUrl = url.replace('/report/pdf/', '/report/html/');
            showPrintPreviewModal(htmlUrl, url);
            return null;
        }
        if (url && typeof url === 'string' && url.includes('/report/html/')) {
            showPrintPreviewModal(url, url.replace('/report/html/', '/report/pdf/'));
            return null;
        }
        return _origOpen.call(this, url, target, features);
    };

    // Secondary approach: intercept navigation to report PDF via link clicks
    document.addEventListener('click', function (e) {
        const anchor = e.target.closest('a[href]');
        if (anchor) {
            const href = anchor.getAttribute('href');
            if (href && href.includes('/report/pdf/')) {
                e.preventDefault();
                e.stopPropagation();
                const htmlUrl = href.replace('/report/pdf/', '/report/html/');
                showPrintPreviewModal(htmlUrl, href);
            }
        }
    }, true); // capture phase

})();

function getPageName() {
    let title = document.title; // e.g. "Hospital Users - Odoo"
    if (!title) return '';
    let parts = title.split('-');
    if (parts.length > 0) {
        let text = parts[0].trim();
        // Exception for appointment forms to accurately grab "Appointment Booking"
        if (text === 'New' && window.location.href.match(/\/hospital\.appointment\/(new|\d+)/)) {
            return 'Appointment Booking';
        }
        if (text === 'PINV') {
            return 'Purchase Invoices';
        }
        if (text === 'PAY') {
            return 'Payments';
        }
        if (text === 'PUR') {
            const url = window.location.href;
            if (url.includes('action-203') || url.includes('action-204')) {
                return 'Purchase Intent';
            }
            if (url.includes('action-199') || url.includes('action-200')) {
                return 'Purchase Orders';
            }
            return 'Purchase Intent'; // fallback
        }
        if (text.toUpperCase() === 'ODOO') {
            const url = window.location.href;
            if (url.includes('hospital_pharmacy_billing')) return 'Pharmacy Billing';
            if (url.includes('hospital_pharmacy_purchase')) return 'Purchase Intent';
            if (url.includes('action-189') || url.includes('action-120')) return 'Pharmacy Billing'; // Based on screenshot URL
            
            const activeMenu = document.querySelector('.o_nav_entry.active, .dropdown-item.active');
            if (activeMenu && activeMenu.textContent.trim().toUpperCase() !== 'ODOO') {
                return activeMenu.textContent.trim();
            }
            return ''; // Avoid returning "ODOO"
        }
        return text;
    }
    return '';
}

function injectPageTitle() {
    let pageName = getPageName();
    if (!pageName) return;

    let banner = document.querySelector('.hospital-page-title-banner');
    if (!banner) {
        let actionManager = document.querySelector('.o_action_manager');
        if (!actionManager) return;
        
        // Exclude the user form entirely
        if (document.querySelector('.hospital_user_form')) {
            return;
        }

        banner = document.createElement('div');
        banner.className = 'hospital-page-title-banner';
        banner.style.cssText = `
            width: 100%;
            background: white;
            border-bottom: 1px solid #dee2e6;
            padding: 10px 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            min-height: 40px;
        `;
        
        actionManager.insertBefore(banner, actionManager.firstChild);
    }

    let innerHtml = `
        <span style="
            font-size: 14px;
            font-weight: 800;
            color: #29398f;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            font-family: Arial, sans-serif;
            background: rgba(255, 255, 255, 0.85);
            padding: 3px 10px;
            border-radius: 4px;
        ">${pageName}</span>
    `;

    if (pageName === 'Purchase Intent' || pageName === 'Existing Purchase Intents' || pageName === 'Purchase Orders' || pageName === 'Existing Purchase Orders') {
        const isPO = pageName.includes('Orders');
        const isNew = pageName === 'Purchase Intent' || pageName === 'Purchase Orders';
        const titleText = isPO ? 'Purchase Orders' : 'Purchase Intent';
        const tabClass = isPO ? 'custom-po-tab' : 'custom-pi-tab';

        innerHtml = `
            <div style="
                background: white;
                padding: 8px 20px 0 20px;
                position: relative;
                z-index: 1;
                display: flex;
                flex-direction: column;
                align-items: flex-start;
                text-transform: uppercase;
                font-weight: 800;
            ">
                <span style="color: #29398f; font-size: 16px; margin-bottom: 6px;">${titleText}</span>
                <div style="display: flex; gap: 30px; font-size: 13px;">
                    <a class="${tabClass}" data-target="new" style="
                        cursor: pointer;
                        color: ${isNew ? '#29398f' : '#6c757d'};
                        border-bottom: ${isNew ? '3px solid #29398f' : '3px solid transparent'};
                        padding-bottom: 4px;
                        text-decoration: none;
                    ">New</a>
                    <a class="${tabClass}" data-target="existing" style="
                        cursor: pointer;
                        color: ${!isNew ? '#29398f' : '#6c757d'};
                        border-bottom: ${!isNew ? '3px solid #29398f' : '3px solid transparent'};
                        padding-bottom: 4px;
                        text-decoration: none;
                    ">Existing</a>
                </div>
            </div>
        `;
    }

    banner.innerHTML = innerHtml;

    // Attach direct click listeners on tab elements so OWL can't intercept
    banner.querySelectorAll('.custom-pi-tab, .custom-po-tab').forEach(tab => {
        tab.addEventListener('click', function(ev) {
            ev.preventDefault();
            ev.stopPropagation();
            const isPO = this.classList.contains('custom-po-tab');
            const tgt = this.dataset.target;
            const xmlId = isPO
                ? (tgt === 'new'
                    ? 'hospital_management.action_hospital_pharmacy_purchase_list_new'
                    : 'hospital_management.action_hospital_pharmacy_purchase_list_existing')
                : (tgt === 'new'
                    ? 'hospital_management.action_hospital_purchase_intent_new'
                    : 'hospital_management.action_hospital_purchase_intent_existing');
            doOdooAction(xmlId);
        });
    });
}

let observerTimer = null;
function startObserving() {
    const targetNode = document.body;
    const config = { childList: true, subtree: true };

    const callback = function(mutationsList, observer) {
        if (observerTimer) clearTimeout(observerTimer);
        observerTimer = setTimeout(() => {
            if (document.querySelector('.o_action_manager')) {
                injectPageTitle();
            }
        }, 50);
    };

    const observer = new MutationObserver(callback);
    observer.observe(targetNode, config);
}

if (document.readyState === 'loading') {
    window.addEventListener('DOMContentLoaded', startObserving);
} else {
    startObserving();
}

// Global tab handlers for Purchase Intent & Purchase Orders
window.addEventListener('click', async function(e) {
    if (e.target.closest('.btn-custom-close-pinv')) {
        e.preventDefault();
        const existingActionId = await getActionId('hospital_management.action_hospital_pharmacy_purchase_invoice');
        if (existingActionId) window.location.href = `/odoo/action-${existingActionId}`;
        return;
    }
    if (e.target.closest('.btn-custom-close-pay')) {
        e.preventDefault();
        const existingActionId = await getActionId('hospital_management.action_hospital_pharmacy_payment');
        if (existingActionId) window.location.href = `/odoo/action-${existingActionId}`;
        return;
    }
    if (e.target.closest('.btn-custom-clear')) {
        e.preventDefault();
        if (window._hospitalPharmacyStockController && window._hospitalPharmacyStockController.actionService) {
            await window._hospitalPharmacyStockController.model.root.discard();
            window._hospitalPharmacyStockController.actionService.doAction({
                type: 'ir.actions.act_window',
                res_model: 'hospital.pharmacy.stock',
                views: [[false, 'form']],
                target: 'current'
            }, { replaceLastAction: true });
        } else {
            window.location.reload();
        }
    }
    if (e.target.closest('.btn-custom-close')) {
        e.preventDefault();
        if (window._hospitalPharmacyStockController && window._hospitalPharmacyStockController.actionService) {
            await window._hospitalPharmacyStockController.model.root.discard();
            window._hospitalPharmacyStockController.actionService.doAction('hospital_management.action_hospital_pharmacy_stock_records', {
                clearBreadcrumbs: true,
            });
        } else {
            window.history.back();
        }
    }
    
    // Tab Navigation - Purchase Intent
    if (e.target.classList.contains('custom-pi-tab')) {
        e.preventDefault();
        const target = e.target.dataset.target;
        const xmlId = target === 'new'
            ? 'hospital_management.action_hospital_purchase_intent_new'
            : 'hospital_management.action_hospital_purchase_intent_existing';
        doOdooAction(xmlId);
    }
    // Tab Navigation - Purchase Orders
    if (e.target.classList.contains('custom-po-tab')) {
        e.preventDefault();
        const target = e.target.dataset.target;
        const xmlId = target === 'new'
            ? 'hospital_management.action_hospital_pharmacy_purchase_list_new'
            : 'hospital_management.action_hospital_pharmacy_purchase_list_existing';
        doOdooAction(xmlId);
    }
});

// Navigate using Odoo's OWL action service directly — resolves XML IDs natively
function doOdooAction(xmlId) {
    // Approach 1: app.root.component.env.services.action (OWL 2 correct path)
    try {
        for (const app of App.apps) {
            const env = app.root?.component?.env;
            if (env?.services?.action) {
                env.services.action.doAction(xmlId, { clearBreadcrumbs: true });
                return;
            }
        }
    } catch(e) { }

    // Approach 2: app.env.services.action (OWL 1 / older path)
    try {
        for (const app of App.apps) {
            if (app.env?.services?.action) {
                app.env.services.action.doAction(xmlId, { clearBreadcrumbs: true });
                return;
            }
        }
    } catch(e) { }

    console.warn("OWL action service not found, falling back to RPC for:", xmlId);
    _fetchAndNavigate(xmlId);
}

// Helper to dynamically fetch action IDs
async function _fetchAndNavigate(xmlId) {
    try {
        const [module, name] = xmlId.split('.');
        // Get CSRF token from Odoo session if available
        const csrfToken = window.odoo?.csrf_token || '';

        const res = await fetch('/web/dataset/call_kw', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(csrfToken ? { 'X-Csrf-Token': csrfToken } : {})
            },
            credentials: 'include',  // Send session cookie
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                id: 1,
                params: {
                    model: 'ir.model.data',
                    method: 'search_read',
                    args: [[['module', '=', module], ['name', '=', name]]],
                    kwargs: {
                        fields: ['res_id'],
                        limit: 1,
                        context: {}
                    }
                }
            })
        });
        const data = await res.json();
        if (data && data.result && data.result.length > 0) {
            window.location.href = `/odoo/action-${data.result[0].res_id}`;
            return;
        }
        console.warn('_fetchAndNavigate: no result for', xmlId, data);
    } catch (err) {
        console.error("Failed to fetch action ID for", xmlId, err);
    }
}
