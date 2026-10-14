/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class AppointmentFormController extends FormController {
    setup() {
        super.setup();
        this.notification = useService("notification");
        this.actionService = useService("action");
    }

    displayName() {
        return "Appointment Booking";
    }

    async beforeExecuteActionButton(clickParams) {
        if (clickParams.name === 'action_close_form') {
            await this.model.root.discard();
            this.actionService.doAction('hospital_management.action_hospital_appointment', {
                clearBreadcrumbs: true,
            });
            return false;
        }
        
        if (clickParams.name === 'action_generate_token') {
            const record = this.model.root;
            if (!record.data.patient_found) {
                const missing = [];
                if (!record.data.new_patient_name) missing.push("Patient Name");
                if (!record.data.new_patient_phone) missing.push("Mobile");
                if (!record.data.new_patient_age || record.data.new_patient_age <= 0) missing.push("Age");
                if (!record.data.new_patient_gender) missing.push("Gender");
                if (!record.data.new_patient_address) missing.push("Address");

                if (missing.length > 0) {
                    this.notification.add(
                        "Missing required fields:\n" + missing.join(", "),
                        { type: "danger" }
                    );
                    
                    const formEl = document.querySelector('.hospital_appointment_form');
                    if (formEl) {
                        const checkAndHighlight = (fieldName) => {
                            // Find any element with the field name (could be div, input, etc.)
                            const fieldEls = formEl.querySelectorAll('[name="' + fieldName + '"]');
                            fieldEls.forEach(el => {
                                // Apply the invalid class to the widget wrapper
                                const widgetEl = el.closest('.o_field_widget') || el;
                                
                                if (fieldName === 'new_patient_age') {
                                    if (!record.data[fieldName] || record.data[fieldName] <= 0) {
                                        widgetEl.classList.add('o_field_invalid');
                                    } else {
                                        widgetEl.classList.remove('o_field_invalid');
                                    }
                                } else {
                                    if (!record.data[fieldName]) {
                                        widgetEl.classList.add('o_field_invalid');
                                    } else {
                                        widgetEl.classList.remove('o_field_invalid');
                                    }
                                }

                            });
                        };
                        checkAndHighlight('new_patient_name');
                        checkAndHighlight('new_patient_phone');
                        checkAndHighlight('new_patient_age');
                        checkAndHighlight('new_patient_gender');
                        checkAndHighlight('new_patient_address');
                    }
                    
                    return false;
                }
            }

            if (!record.data.doctor_id) {
                this.notification.add("Please select a Doctor.", { type: "danger" });
                const formEl = document.querySelector('.hospital_appointment_form');
                if (formEl) {
                    const el = formEl.querySelector('[name="doctor_id"]');
                    if (el) (el.closest('.o_field_widget') || el).classList.add('o_field_invalid');
                }
                return false;
            }

            if (!record.data.consultation_type_id) {
                this.notification.add("Please select a Consultation Type.", { type: "danger" });
                const formEl = document.querySelector('.hospital_appointment_form');
                if (formEl) {
                    const el = formEl.querySelector('[name="consultation_type_id"]');
                    if (el) (el.closest('.o_field_widget') || el).classList.add('o_field_invalid');
                }
                return false;
            }
        }
        return super.beforeExecuteActionButton(clickParams);
    }
}

export const appointmentFormView = {
    ...formView,
    Controller: AppointmentFormController,
};

registry.category("views").add("hospital_appointment_form_view", appointmentFormView);
