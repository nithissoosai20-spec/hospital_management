/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

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
