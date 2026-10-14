/** @odoo-module **/

import { App } from "@odoo/owl";

// Auto-clean stale treatment hash from URL if user had old page open
if (window.location.hash && window.location.hash.includes('treatment')) {
    window.location.hash = '';
    window.location.reload();
}

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
            const activeMenu = document.querySelector('.o_nav_entry.active, .dropdown-item.active, .o_menu_sections .active');
            if (activeMenu && activeMenu.textContent.trim().toUpperCase() !== 'ODOO') {
                return activeMenu.textContent.trim();
            }
            return 'Purchase Intent'; // fallback
        }
        if (text.toUpperCase() === 'ODOO' || text === 'Create Bill') {
            const url = window.location.href;
            if (url.includes('hospital_pharmacy_billing')) return 'Pharmacy Billing';
            if (url.includes('action-189') || url.includes('action-120')) return 'Pharmacy Billing'; // Based on screenshot URL
            
            const activeMenu = document.querySelector('.o_nav_entry.active, .dropdown-item.active, .o_menu_sections .active');
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
    if (banner && banner.dataset.pageName === pageName) {
        return;
    }
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

    if (false && pageName === 'Purchase Intent') { // tabs removed — handled by left-side buttons
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
                    ">New </a>
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
    banner.dataset.pageName = pageName;

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

async function getActionId(xmlId) {
    try {
        const res = await fetch('/web/action/load', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ jsonrpc: '2.0', method: 'call', id: Date.now(), params: { action_id: xmlId } })
        });
        const data = await res.json();
        return data?.result?.id || null;
    } catch(e) { return null; }
}

// Intercept Close buttons on forms in capture phase to prevent Odoo's form validation
window.addEventListener('click', function(e) {
    const closeBtn = e.target.closest('.btn-custom-close-request, button[name="action_close"]');
    if (closeBtn) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();

        const match = window.location.href.match(/action-(\d+)/);
        if (match) {
            window.location.href = '/odoo/action-' + match[1];
        } else {
            window.history.back();
        }
    }
}, true);

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

// ─── NEW VENDOR BUTTON INJECTION ─────────────────────────────────────────────
// Watches for the "Search: Connected Vendors" dialog and injects a "New Vendor" button
(function () {
    function injectNewVendorBtn(node) {
        // Look for modal dialogs
        const dialogs = node.querySelectorAll ? node.querySelectorAll('.modal, .o_dialog') : [];
        const targets = dialogs.length > 0 ? Array.from(dialogs) : (
            (node.classList && (node.classList.contains('modal') || node.classList.contains('o_dialog'))) ? [node] : []
        );

        targets.forEach(function(dialog) {
            const title = dialog.querySelector('.modal-title, .o_dialog_title, h4, h5, .o_dialog_header span');
            if (!title) return;
            if (!/Connected Vendors/i.test(title.textContent)) return;
            if (dialog.querySelector('.hospital-new-vendor-btn')) return;

            const footer = dialog.querySelector('.modal-footer, .o_dialog_footer, .o_btns_area, footer');
            if (!footer) return;

            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn-primary hospital-new-vendor-btn me-auto';
            btn.style.cssText = 'margin-right: auto !important; order: -1;';
            btn.textContent = 'New Vendor';

            btn.addEventListener('click', function (event) {
                event.stopPropagation();
                event.preventDefault();
                // Build a custom popup form to create a new vendor
                const existingPopup = document.getElementById('hospital-new-vendor-popup');
                if (existingPopup) existingPopup.remove();

                const popup = document.createElement('div');
                popup.id = 'hospital-new-vendor-popup';
                popup.style.cssText = [
                    'position:fixed','top:0','left:0','width:100%','height:100%',
                    'background:rgba(0,0,0,0.55)','z-index:999999',
                    'display:flex','align-items:center','justify-content:center'
                ].join(';');

                popup.innerHTML = `
                    <div style="background:#fff;border-radius:10px;width:440px;max-height:90vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,0.4);font-family:Arial,sans-serif;overflow:hidden;">
                        <div style="background:#1e3a8a;color:#fff;padding:14px 20px;display:flex;justify-content:space-between;align-items:center;">
                            <strong style="font-size:15px;">New Vendor</strong>
                            <span id="hnv-close" style="cursor:pointer;font-size:20px;line-height:1;">×</span>
                        </div>
                        <div style="padding:20px;">
                            <div style="margin-bottom:12px;">
                                <label style="display:block;font-weight:600;font-size:13px;margin-bottom:4px;color:#374151;">Vendor Name <span style="color:red;">*</span></label>
                                <input id="hnv-name" type="text" placeholder="e.g. MediCorp Supplies" style="width:100%;padding:8px 10px;border:1px solid #d1d5db;border-radius:5px;font-size:13px;box-sizing:border-box;"/>
                            </div>
                            <div style="margin-bottom:12px;">
                                <label style="display:block;font-weight:600;font-size:13px;margin-bottom:4px;color:#374151;">Phone</label>
                                <input id="hnv-phone" type="text" placeholder="e.g. 9876543210" style="width:100%;padding:8px 10px;border:1px solid #d1d5db;border-radius:5px;font-size:13px;box-sizing:border-box;"/>
                            </div>
                            <div style="margin-bottom:12px;">
                                <label style="display:block;font-weight:600;font-size:13px;margin-bottom:4px;color:#374151;">Email</label>
                                <input id="hnv-email" type="email" placeholder="e.g. vendor@example.com" style="width:100%;padding:8px 10px;border:1px solid #d1d5db;border-radius:5px;font-size:13px;box-sizing:border-box;"/>
                            </div>
                            <div style="margin-bottom:12px;">
                                <label style="display:block;font-weight:600;font-size:13px;margin-bottom:4px;color:#374151;">Address</label>
                                <input id="hnv-address" type="text" placeholder="e.g. No.5, Main Street, City" style="width:100%;padding:8px 10px;border:1px solid #d1d5db;border-radius:5px;font-size:13px;box-sizing:border-box;"/>
                            </div>
                            <div style="margin-bottom:16px;">
                                <label style="display:block;font-weight:600;font-size:13px;margin-bottom:4px;color:#374151;">GST No.</label>
                                <input id="hnv-gst" type="text" placeholder="e.g. 33ABCDE1234F1Z5" style="width:100%;padding:8px 10px;border:1px solid #d1d5db;border-radius:5px;font-size:13px;box-sizing:border-box;"/>
                            </div>
                            <div id="hnv-error" style="color:red;font-size:12px;margin-bottom:8px;display:none;"></div>
                            <div style="display:flex;gap:10px;justify-content:flex-end;">
                                <button id="hnv-cancel" type="button" style="padding:8px 18px;border:1px solid #d1d5db;border-radius:5px;background:#fff;cursor:pointer;font-size:13px;">Cancel</button>
                                <button id="hnv-save" type="button" style="padding:8px 20px;border:none;border-radius:5px;background:#1e3a8a;color:#fff;cursor:pointer;font-size:13px;font-weight:600;">Save Vendor</button>
                            </div>
                        </div>
                    </div>
                `;

                document.body.appendChild(popup);

                popup.querySelector('#hnv-close').onclick = function() { popup.remove(); };
                popup.querySelector('#hnv-cancel').onclick = function() { popup.remove(); };

                popup.querySelector('#hnv-save').onclick = async function() {
                    const name = popup.querySelector('#hnv-name').value.trim();
                    const phone = popup.querySelector('#hnv-phone').value.trim();
                    const email = popup.querySelector('#hnv-email').value.trim();
                    const address = popup.querySelector('#hnv-address').value.trim();
                    const gst = popup.querySelector('#hnv-gst').value.trim();
                    const errDiv = popup.querySelector('#hnv-error');

                    if (!name) {
                        errDiv.textContent = 'Vendor Name is required.';
                        errDiv.style.display = 'block';
                        return;
                    }
                    errDiv.style.display = 'none';

                    const saveBtn = popup.querySelector('#hnv-save');
                    saveBtn.textContent = 'Saving...';
                    saveBtn.disabled = true;

                    try {
                        const csrfToken = document.cookie.match(/csrf_token=([^;]+)/)?.[1] || '';
                        const res = await fetch('/hospital/create_vendor', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                ...(csrfToken ? { 'X-Csrf-Token': csrfToken } : {})
                            },
                            credentials: 'include',
                            body: JSON.stringify({
                                jsonrpc: '2.0', method: 'call', id: Date.now(),
                                params: {
                                    name: name,
                                    phone: phone || null,
                                    email: email || null,
                                    street: address || null,
                                    vat: gst || null,
                                }
                            })
                        });
                        const data = await res.json();
                        if (data.error) throw new Error(data.error.data?.message || 'Save failed');
                        if (data.result && !data.result.success) throw new Error(data.result.error || 'Save failed');

                        popup.remove();
                        const toast = document.createElement('div');
                        toast.textContent = `Vendor "${name}" created successfully!`;
                        toast.style.cssText = 'position:fixed;bottom:30px;right:30px;background:#16a34a;color:#fff;padding:12px 20px;border-radius:8px;z-index:999999;font-family:Arial,sans-serif;font-size:14px;box-shadow:0 4px 15px rgba(0,0,0,0.2);';
                        document.body.appendChild(toast);
                        setTimeout(() => toast.remove(), 3000);
                    } catch(e) {
                        errDiv.textContent = e.message || 'Failed to save vendor. Please try again.';
                        errDiv.style.display = 'block';
                        saveBtn.textContent = 'Save Vendor';
                        saveBtn.disabled = false;
                    }
                };
            });

            footer.insertBefore(btn, footer.firstChild);
        });
    }

    const observer = new MutationObserver(function (mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType !== 1) return;
                setTimeout(function() { injectNewVendorBtn(node); }, 80);
            });
        });
    });

    function startObserving() {
        if (document.body) {
            observer.observe(document.body, { childList: true, subtree: true });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', startObserving);
    } else {
        startObserving();
    }
})();

// ============================================================
// FORCE FULL RELOAD when clicking Purchase Intent / Purchase Orders / Purchase Invoices nav links
// This ensures the NEW tab always loads with fresh data
// ============================================================
(async function forcePurchaseNavReload() {
    const INTENT_NEW_XMLID = 'hospital_management.action_hospital_purchase_intent_new';
    const ORDERS_NEW_XMLID = 'hospital_management.action_hospital_pharmacy_purchase_list_new';
    const INVOICES_NEW_XMLID = 'hospital_management.action_hospital_pharmacy_purchase_invoice_new';

    let intentActionId = null;
    let ordersActionId = null;
    let invoicesActionId = null;

    // Pre-fetch action IDs once
    document.addEventListener('DOMContentLoaded', async () => {
        intentActionId = await getActionId(INTENT_NEW_XMLID);
        ordersActionId = await getActionId(ORDERS_NEW_XMLID);
        invoicesActionId = await getActionId(INVOICES_NEW_XMLID);
    });

    // Intercept nav menu clicks and force full page reload to the correct "new" tab action
    document.addEventListener('click', function(e) {
        const link = e.target.closest('.o_nav_entry, .o_menu_sections a');
        if (!link) return;
        const text = link.textContent.trim();

        if (text === 'Purchase Intent') {
            e.preventDefault();
            e.stopImmediatePropagation();
            if (intentActionId) {
                window.location.href = '/odoo/action-' + intentActionId;
            } else {
                getActionId(INTENT_NEW_XMLID).then(id => {
                    if (id) window.location.href = '/odoo/action-' + id;
                });
            }
        } else if (text === 'Purchase Orders') {
            e.preventDefault();
            e.stopImmediatePropagation();
            if (ordersActionId) {
                window.location.href = '/odoo/action-' + ordersActionId;
            } else {
                getActionId(ORDERS_NEW_XMLID).then(id => {
                    if (id) window.location.href = '/odoo/action-' + id;
                });
            }
        } else if (text === 'Purchase Invoices') {
            e.preventDefault();
            e.stopImmediatePropagation();
            if (invoicesActionId) {
                window.location.href = '/odoo/action-' + invoicesActionId;
            } else {
                getActionId(INVOICES_NEW_XMLID).then(id => {
                    if (id) window.location.href = '/odoo/action-' + id;
                });
            }
        }
    }, true); // true = capture phase so we intercept before Odoo's router
})();

(function() {
    document.addEventListener('DOMContentLoaded', () => {
        const observer = new MutationObserver((mutations) => {
            const breadcrumbs = document.querySelector('.o_control_panel_breadcrumbs .breadcrumb-item.active, .o_breadcrumb .active, .o_last_breadcrumb_item');
            if (breadcrumbs) {
                const title = breadcrumbs.textContent.trim().toUpperCase();
                const newBtn = document.querySelector('.o_list_button_add, .o_control_panel_main_buttons button.btn-primary');
                
                if (newBtn && newBtn.textContent.trim() === 'New') {
                    if (title === 'PURCHASE INVOICES') {
                        newBtn.textContent = 'New Purchase Invoice';
                    } else if (title === 'VENDOR PAYMENTS') {
                        newBtn.textContent = 'New Payment';
                    } else if (title === 'CONSULTATION FEES') {
                        newBtn.textContent = 'New Consultation Fees';
                    } else if (title === 'CONSULTATION TYPES') {
                        newBtn.textContent = 'New Consultation Type';
                    } else if (title === 'LAB FEES') {
                        newBtn.textContent = 'New Lab Fees';
                    } else if (title === 'USERS') {
                        newBtn.textContent = 'New User';
                    } else if (title === 'PHARMACY STOCK') {
                        newBtn.textContent = 'New Stock';
                    }
                }
            }

        });
        if (document.body) {
            observer.observe(document.body, { childList: true, subtree: true });
        }
    });
})();

// --- DYNAMIC NEW BUTTON TEXT (Hospital UI Tweak) ---
(function() {
    function updateNewButtons() {
        let modelName = '';
        const breadcrumbs = document.querySelectorAll('.o_control_panel_breadcrumbs .breadcrumb-item, .o_breadcrumb li');
        if (breadcrumbs.length > 0) {
            modelName = breadcrumbs[0].textContent.trim();
        }
        if (!modelName) {
            let fullTitle = document.title || '';
            modelName = fullTitle.split(' - ')[0].trim();
        }
        
        if (!modelName || modelName === 'Odoo') return;
        
        if (modelName.toLowerCase().includes('specification')) modelName = 'Specification';
        else if (modelName === 'Items') modelName = 'Item';
        else if (modelName.includes('Requests')) modelName = 'Asset Request';
        else if (modelName.includes('Damaged')) modelName = 'Damage Record';
        else if (modelName.endsWith('s') && modelName !== 'Asset PO') modelName = modelName.substring(0, modelName.length - 1);
        
        const listBtn = document.querySelector('.o_list_button_add');
        const formBtn = document.querySelector('.o_form_button_create');
        
        if (listBtn && listBtn.textContent.trim() === 'New') listBtn.textContent = 'New ' + modelName;
        if (formBtn && formBtn.textContent.trim() === 'New') formBtn.textContent = 'New ' + modelName;
    }

    const observer = new MutationObserver(() => { updateNewButtons(); });
    const initInterval = setInterval(() => {
        if (document.body) {
            observer.observe(document.body, { childList: true, subtree: true, characterData: true });
            clearInterval(initInterval);
        }
    }, 100);
})();

// ============================================================
// DOCTOR PROFILE: Filter out already selected Consultation Types from dropdown
// ============================================================
(function () {
    function filterDoctorConsultationDropdown(input) {
        const table = input.closest('.doctor_consultation_table');
        if (!table) return;

        // Collect all consultation types selected in other rows
        const currentTr = input.closest('tr');
        const selectedNames = new Set();

        table.querySelectorAll('tbody tr.o_data_row').forEach(tr => {
            if (tr === currentTr) return;
            const typeCell = tr.querySelector('[name="consultation_type_id"]');
            if (typeCell) {
                const text = typeCell.textContent.trim().toLowerCase();
                if (text) selectedNames.add(text);
            }
        });

        // Hide matching options in the open autocomplete menu
        const dropdown = input.closest('.o-autocomplete')?.querySelector('.o-autocomplete--dropdown-menu');
        if (dropdown) {
            dropdown.querySelectorAll('.o-autocomplete--dropdown-item').forEach(item => {
                const itemText = item.textContent.trim().toLowerCase();
                if (selectedNames.has(itemText)) {
                    item.style.display = 'none';
                }
            });
        }
    }

    document.addEventListener('focusin', function (e) {
        const input = e.target.closest('.doctor_consultation_table .o-autocomplete--input');
        if (!input) return;

        const acContainer = input.closest('.o-autocomplete');
        if (!acContainer) return;

        const observer = new MutationObserver(() => {
            filterDoctorConsultationDropdown(input);
        });

        observer.observe(acContainer, { childList: true, subtree: true });
        setTimeout(() => filterDoctorConsultationDropdown(input), 50);
        setTimeout(() => filterDoctorConsultationDropdown(input), 150);
        setTimeout(() => filterDoctorConsultationDropdown(input), 300);
    });
})();