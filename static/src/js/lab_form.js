/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { registry } from "@web/core/registry";
import { onPatched, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class LabFormController extends FormController {
    setup() {
        super.setup();
        this.actionService = useService("action");
        
        const updateSaveButton = () => {
            const btn = document.querySelector('.hospital-save-btn');
            if (btn) {
                if (this.model.root.isDirty || this.model.root.isNew) {
                    btn.style.display = '';
                } else {
                    btn.style.display = 'none';
                }
            }
        };

        onMounted(() => {
            updateSaveButton();
        });

        onPatched(() => {
            updateSaveButton();
        });

    }

    async beforeExecuteActionButton(clickParams) {
        if (clickParams.name === 'action_close_to_appointments') {
            await this.model.root.discard();
            this.actionService.doAction('hospital_management.action_hospital_appointment', {
                clearBreadcrumbs: true,
            });
            return false;
        }
        return super.beforeExecuteActionButton(clickParams);
    }
}

export const labFormView = {
    ...formView,
    Controller: LabFormController,
};

registry.category("views").add("lab_form_view", labFormView);
