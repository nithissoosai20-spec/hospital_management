/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";

function makePurchaseListController(newActionXmlid, existingActionXmlid) {
    class PurchaseListController extends ListController {
        setup() {
            super.setup();
            this.actionService = useService("action");
            onMounted(() => this._injectTabs());
        }

        _injectTabs() {
            const checkAndInject = () => {
                // Find the right side of the control panel (where search bar is)
                const searchArea = document.querySelector(".o_control_panel .o_cp_bottom_right, .o_control_panel_actions, .o_cp_searchview");
                if (!searchArea) {
                    setTimeout(checkAndInject, 50);
                    return;
                }
                if (document.querySelector(".ph_purchase_tabs")) return;

                const isExisting = existingActionXmlid.includes("existing") &&
                    (window.location.href.includes("action-200") || window.location.href.includes("action-204"));

                const wrapper = document.createElement("div");
                wrapper.className = "ph_purchase_tabs";
                // Place to the left of the pager
                wrapper.style.cssText = "position:absolute; right:180px; display:flex; gap:8px; align-items:center; z-index:10;";
                wrapper.innerHTML = `
                    <button class="btn btn-sm ${isExisting ? 'btn-outline-secondary' : 'btn-primary'} ph_tab_new">New</button>
                    <button class="btn btn-sm ${isExisting ? 'btn-primary' : 'btn-outline-secondary'} ph_tab_existing">Existing</button>
                `;

                const controlPanel = document.querySelector(".o_control_panel");

                if (controlPanel) {
                    // Ensure the control panel can hold absolute elements safely
                    if (getComputedStyle(controlPanel).position === 'static') {
                        controlPanel.style.position = 'relative';
                    }
                    // Append directly to control panel so it anchors to the full width
                    controlPanel.appendChild(wrapper);
                    // Align it vertically with the bottom row
                    wrapper.style.bottom = "12px";
                } else if (searchArea) {
                    searchArea.appendChild(wrapper);
                }

                wrapper.querySelector(".ph_tab_new").addEventListener("click", () => {
                    this._navigate(newActionXmlid);
                });
                wrapper.querySelector(".ph_tab_existing").addEventListener("click", () => {
                    this._navigate(existingActionXmlid);
                });
            };
            checkAndInject();
        }

        async _navigate(xmlId) {
            try {
                const res = await fetch('/web/action/load', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'same-origin',
                    body: JSON.stringify({ jsonrpc: '2.0', method: 'call', id: Date.now(), params: { action_id: xmlId } })
                });
                const data = await res.json();
                const actionId = data?.result?.id;
                if (actionId) window.location.href = `/odoo/action-${actionId}`;
            } catch(e) {
                console.error('Navigation failed:', e);
            }
        }
    }
    return PurchaseListController;
}

registry.category("views").add("purchase_order_list", {
    ...listView,
    Controller: makePurchaseListController(
        "hospital_management.action_hospital_pharmacy_purchase_list_new",
        "hospital_management.action_hospital_pharmacy_purchase_list_existing"
    ),
});

registry.category("views").add("purchase_intent_list", {
    ...listView,
    Controller: makePurchaseListController(
        "hospital_management.action_hospital_purchase_intent_new",
        "hospital_management.action_hospital_purchase_intent_existing"
    ),
});
