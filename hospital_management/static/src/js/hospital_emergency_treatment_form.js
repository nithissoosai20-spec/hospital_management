/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";

export class EmergencyTreatmentFormController extends FormController {
    setup() {
        super.setup();
        this.actionService = useService("action");

        onMounted(() => {
            setTimeout(() => {
                const closeBtn = document.querySelector('.btn-custom-close');
                if (closeBtn) {
                    closeBtn.addEventListener('click', async (ev) => {
                        ev.preventDefault();
                        ev.stopPropagation();
                        await this.model.root.discard();
                        this.actionService.doAction("hospital_management.action_hospital_emergency_treatment", { clearBreadcrumbs: true });
                    });
                }

                const clearBtn = document.querySelector('.btn-custom-clear');
                if (clearBtn) {
                    clearBtn.addEventListener('click', async (ev) => {
                        ev.preventDefault();
                        ev.stopPropagation();
                        await this.model.root.discard();
                        this.actionService.doAction({
                            type: 'ir.actions.act_window',
                            name: 'Emergency Treatment',
                            res_model: 'hospital.emergency.treatment',
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
        return "EMERGENCY TREATMENT";
    }

    async beforeLeave(options = {}) {
        if (this.model.root.dirty && !options.forceLeave) {
            await this.model.root.discard();
        }
        return super.beforeLeave(options);
    }
}

export const emergencyTreatmentFormView = {
    ...formView,
    Controller: EmergencyTreatmentFormController,
};

registry.category("views").add("hospital_emergency_treatment_form_view", emergencyTreatmentFormView);
