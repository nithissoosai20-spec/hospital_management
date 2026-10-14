/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";

// ── Cache action XML IDs → database action IDs ──────────────────────────────
const _cache = {};
async function resolveActionId(xmlId) {
    if (_cache[xmlId]) return _cache[xmlId];
    try {
        const res = await fetch('/web/action/load', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ jsonrpc: '2.0', method: 'call', id: Date.now(), params: { action_id: xmlId } })
        });
        const data = await res.json();
        const id = data?.result?.id;
        if (id) _cache[xmlId] = id;
        return id || null;
    } catch(e) { return null; }
}

// Pre-warm cache when this module loads (runs once)
[
    'hospital_management.action_hospital_purchase_intent_new',
    'hospital_management.action_hospital_purchase_intent_existing',
    'hospital_management.action_hospital_pharmacy_purchase_list_new',
    'hospital_management.action_hospital_pharmacy_purchase_list_existing',
    'hospital_management.action_hospital_pharmacy_purchase_invoice_new',
    'hospital_management.action_hospital_pharmacy_purchase_invoice_existing',
].forEach(resolveActionId);

// ── Factory ──────────────────────────────────────────────────────────────────
function makePurchaseListController(newActionXmlid, existingActionXmlid, hideNewButton, showNewOrderBtn) {
    class PurchaseListController extends ListController {
        setup() {
            super.setup();
            this.actionService = useService("action");
            onMounted(() => this._injectTabs());
        }

        async _injectTabs() {
            // Determine active tab by comparing current URL to existing action's database ID
            const existingId = await resolveActionId(existingActionXmlid);
            const isExistingTab = existingId
                ? window.location.href.includes(`action-${existingId}`)
                : false;

            const doInject = () => {
                const controlPanel = document.querySelector(".o_control_panel");
                if (!controlPanel) { setTimeout(doInject, 50); return; }
                if (document.querySelector(".ph_purchase_tabs")) return;

                // Build underline-style tabs
                const tabs = document.createElement("div");
                tabs.className = "ph_purchase_tabs";
                tabs.style.cssText = "display:inline-flex; align-items:flex-end; gap:0;";

                const newStyle = `
                    background:none; border:none;
                    border-bottom: 3px solid ${!isExistingTab ? '#2563eb' : 'transparent'};
                    cursor:pointer; font-size:13px; font-weight:700;
                    letter-spacing:1px; text-transform:uppercase;
                    padding:4px 18px 6px 18px;
                    color:${!isExistingTab ? '#2563eb' : '#9ca3af'};
                `;
                const existingStyle = `
                    background:none; border:none;
                    border-bottom: 3px solid ${isExistingTab ? '#2563eb' : 'transparent'};
                    cursor:pointer; font-size:13px; font-weight:700;
                    letter-spacing:1px; text-transform:uppercase;
                    padding:4px 18px 6px 18px;
                    color:${isExistingTab ? '#2563eb' : '#9ca3af'};
                `;

                tabs.innerHTML = `
                    <button class="ph_tab_new" style="${newStyle}">NEW</button>
                    <button class="ph_tab_existing" style="${existingStyle}">EXISTING</button>
                `;

                // Find left-side area and prepend tabs
                const leftArea = controlPanel.querySelector(
                    ".o_control_panel_breadcrumbs_actions, .o_list_buttons, .o_control_panel_breadcrumbs"
                );
                if (leftArea) {
                    // Remove native "New" button from DOM
                    controlPanel.querySelectorAll(
                        ".o_form_button_create, .o_list_button_add, button[data-hotkey='c']"
                    ).forEach(btn => btn.remove());
                    leftArea.prepend(tabs);
                } else {
                    if (getComputedStyle(controlPanel).position === "static") {
                        controlPanel.style.position = "relative";
                    }
                    tabs.style.position = "absolute";
                    tabs.style.left = "12px";
                    tabs.style.bottom = "10px";
                    tabs.style.zIndex = "10";
                    controlPanel.appendChild(tabs);
                }

                // Orders page: add "New Order" button on the right
                if (showNewOrderBtn && !document.querySelector(".ph_new_order_btn")) {
                    if (getComputedStyle(controlPanel).position === "static") {
                        controlPanel.style.position = "relative";
                    }
                    const btn = document.createElement("button");
                    btn.className = "ph_new_order_btn btn btn-primary";
                    btn.textContent = "New Order";
                    btn.style.cssText = "position:absolute; right:180px; bottom:8px; z-index:10;";
                    btn.addEventListener("click", () => this._newRecord(newActionXmlid));
                    controlPanel.appendChild(btn);
                }

                // Wire tab clicks
                tabs.querySelector(".ph_tab_new").addEventListener("click", () => this._go(newActionXmlid));
                tabs.querySelector(".ph_tab_existing").addEventListener("click", () => this._go(existingActionXmlid));
            };

            doInject();
        }

        async _newRecord(xmlId) {
            const id = await resolveActionId(xmlId);
            if (id) window.location.href = `/odoo/action-${id}/new`;
        }

        async _go(xmlId) {
            const id = await resolveActionId(xmlId);
            if (id) window.location.href = `/odoo/action-${id}`;
        }
    }
    return PurchaseListController;
}

// Purchase Orders — tabs LEFT, "New Order" btn RIGHT
registry.category("views").add("purchase_order_list", {
    ...listView,
    Controller: makePurchaseListController(
        "hospital_management.action_hospital_pharmacy_purchase_list_new",
        "hospital_management.action_hospital_pharmacy_purchase_list_existing",
        true,
        true
    ),
});

// Purchase Intent — tabs LEFT, no New button
registry.category("views").add("purchase_intent_list", {
    ...listView,
    Controller: makePurchaseListController(
        "hospital_management.action_hospital_purchase_intent_new",
        "hospital_management.action_hospital_purchase_intent_existing",
        true,
        false
    ),
});

// Purchase Invoices — tabs LEFT, no New button
registry.category("views").add("purchase_invoice_list", {
    ...listView,
    Controller: makePurchaseListController(
        "hospital_management.action_hospital_pharmacy_purchase_invoice_new",
        "hospital_management.action_hospital_pharmacy_purchase_invoice_existing",
        true,
        false
    ),
});
