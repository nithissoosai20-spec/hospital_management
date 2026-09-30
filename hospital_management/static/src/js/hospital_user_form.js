/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class HospitalUserFormController extends FormController {
    setup() {
        super.setup();
        this.actionService = useService("action");
    }

    displayName() {
        const name = this.model.root.data.name;
        return (name ? name : "New") + " User Details";
    }

    async beforeExecuteActionButton(clickParams) {
        if (clickParams.name === 'action_close_user_form') {
            await this.model.root.discard();
            this.actionService.doAction('hospital_management.action_hospital_users', {
                clearBreadcrumbs: true,
            });
            return false;
        }
        return super.beforeExecuteActionButton(clickParams);
    }
}

export const hospitalUserFormView = {
    ...formView,
    Controller: HospitalUserFormController,
};

registry.category("views").add("hospital_user_form_view", hospitalUserFormView);
