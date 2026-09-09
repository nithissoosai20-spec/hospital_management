/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { Many2ManyTagsField } from "@web/views/fields/many2many_tags/many2many_tags_field";

export class PharmacyStockFormController extends FormController {
    setup() {
        super.setup();
        this.actionService = useService("action");
        window._hospitalPharmacyStockController = this;
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
