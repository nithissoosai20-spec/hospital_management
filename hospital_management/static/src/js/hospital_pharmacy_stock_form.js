/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { Many2ManyTagsField } from "@web/views/fields/many2many_tags/many2many_tags_field";
import { onMounted } from "@odoo/owl";

export class PharmacyStockFormController extends FormController {
    setup() {
        super.setup();
        this.actionService = useService("action");
        window._hospitalPharmacyStockController = this;

        onMounted(() => {
            setTimeout(() => {
                const closeBtn = document.querySelector('.btn-custom-close');
                if (closeBtn) {
                    closeBtn.addEventListener('click', async (ev) => {
                        ev.preventDefault();
                        ev.stopPropagation();
                        await this.model.root.discard();
                        // Go back to the stock list view
                        this.actionService.doAction("hospital_management.action_hospital_pharmacy_stock_records", { clearBreadcrumbs: true });
                    });
                }
                
                const clearBtn = document.querySelector('.btn-custom-clear');
                if (clearBtn) {
                    clearBtn.addEventListener('click', async (ev) => {
                        ev.preventDefault();
                        ev.stopPropagation();
                        await this.model.root.discard();
                        // Reload a fresh form view
                        this.actionService.doAction({
                            type: 'ir.actions.act_window',
                            name: 'Pharmacy Stock',
                            res_model: 'hospital.pharmacy.stock',
                            view_mode: 'form',
                            views: [[false, 'form']],
                            target: 'current',
                        }, { clearBreadcrumbs: true });
                    });
                }
            }, 200);
        });
    }

    displayName() {
        return "ITEM DETAILS";
    }

    async beforeLeave(options = {}) {
        if (this.model.root.dirty && !options.forceLeave) {
            await this.model.root.discard();
        }
        return super.beforeLeave(options);
    }

}

export const pharmacyStockFormView = {
    ...formView,
    Controller: PharmacyStockFormController,
};

registry.category("views").add("hospital_pharmacy_stock_form_view", pharmacyStockFormView);

// Patch Many2ManyTagsField to allow vendor creation in the pharmacy stock form
patch(Many2ManyTagsField.prototype, {
    get canCreate() {
        // Force creation enabled for vendor_ids on pharmacy stock model
        if (
            this.props.name === "vendor_ids" &&
            this.env.model?.config?.resModel === "hospital.pharmacy.stock"
        ) {
            return true;
        }
        return super.canCreate;
    },
});
