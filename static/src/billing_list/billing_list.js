/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { onMounted, onPatched } from "@odoo/owl";

export class BillingListController extends ListController {
    setup() {
        super.setup();
        this.action = useService("action");
        
        const updateButtonText = () => {
            const btn = document.querySelector(".o_list_button_add");
            if (btn && btn.textContent.trim() === "New") {
                btn.textContent = "Create Bill";
            }
        };
        onMounted(updateButtonText);
        onPatched(updateButtonText);
    }

    async createRecord() {
        await this.action.doAction("hospital_management.action_hospital_pharmacy_billing");
    }

    async openRecord(record) {
        await this.action.doAction({
            type: "ir.actions.client",
            tag: "hospital_pharmacy_billing",
            context: {
                active_id: record.resId,
            }
        });
    }
}

registry.category("views").add("billing_list", {
    ...listView,
    Controller: BillingListController,
});