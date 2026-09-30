/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { registry } from "@web/core/registry";
import { onPatched, onMounted, useEffect, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class LabFormController extends FormController {
    setup() {
        super.setup();
        this.actionService = useService("action");
        
        const updateSaveButton = () => {
            try {
                // In Odoo, buttons use name="..." in DOM or are identifiable by classes.
                const btns = document.querySelectorAll('button[name="action_tech_save_lab_appointment"], button[name="action_save_lab_appointment"], .hospital-save-btn');
                if (!btns.length) return;
                const isDirty = this.model.root.isDirty || this.model.root.isNew;
                btns.forEach(btn => {
                    if (isDirty) {
                        btn.style.setProperty('display', 'inline-block', 'important');
                        btn.classList.remove('d-none');
                    } else {
                        btn.style.setProperty('display', 'none', 'important');
                        btn.classList.add('d-none');
                    }
                });
            } catch (e) {}
        };

        useEffect(() => {
            updateSaveButton();
        });
        
        const intervalId = setInterval(updateSaveButton, 200);
        
        onWillUnmount(() => {
            clearInterval(intervalId);
        });
    }

    displayName() {
        return "LAB TEST";
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

export class LabTechFormController extends LabFormController {
    displayName() {
        return "LAB REPORT";
    }

    async beforeExecuteActionButton(clickParams) {
        if (clickParams.name === 'action_tech_save_lab_appointment') {
            // Hide instantly on click
            if (clickParams.event && clickParams.event.target) {
                const btn = clickParams.event.target.closest('button');
                if (btn) {
                    btn.style.setProperty('display', 'none', 'important');
                    btn.classList.add('d-none');
                }
            }
        }
        if (clickParams.name === 'action_close_to_appointments') {
            await this.model.root.discard();
            this.actionService.doAction('hospital_management.action_hospital_lab_technician_appointments', {
                clearBreadcrumbs: true,
            });
            return false;
        }
        return super.beforeExecuteActionButton(clickParams);
    }
}

export const labTechFormView = {
    ...formView,
    Controller: LabTechFormController,
};

registry.category("views").add("lab_tech_form_view", labTechFormView);
