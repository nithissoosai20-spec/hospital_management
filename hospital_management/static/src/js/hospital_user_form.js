/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { onMounted, onPatched } from "@odoo/owl";

export class HospitalUserFormController extends FormController {
    setup() {
        super.setup();
        this.actionService = useService("action");

        onMounted(() => {
            this.attachPasswordToggles();
        });

        onPatched(() => {
            this.attachPasswordToggles();
        });
    }

    attachPasswordToggles() {
        const formEl = document.querySelector('.hospital_user_form');
        if (!formEl) return;

        ['password', 'password_confirm'].forEach((fieldName) => {
            const fieldWidget = formEl.querySelector(`[name="${fieldName}"]`);
            if (!fieldWidget) return;

            const input = fieldWidget.querySelector('input');
            if (!input) return;

            if (fieldWidget.querySelector('.password-toggle-btn')) return;

            fieldWidget.style.position = 'relative';
            fieldWidget.style.display = 'block';
            input.style.paddingRight = '36px';

            const toggleBtn = document.createElement('span');
            toggleBtn.className = 'password-toggle-btn';
            toggleBtn.innerHTML = '<i class="fa fa-eye"></i>';
            toggleBtn.title = 'Show / Hide Password';
            toggleBtn.style.position = 'absolute';
            toggleBtn.style.right = '12px';
            toggleBtn.style.top = '50%';
            toggleBtn.style.transform = 'translateY(-50%)';
            toggleBtn.style.cursor = 'pointer';
            toggleBtn.style.color = '#64748b';
            toggleBtn.style.zIndex = '10';
            toggleBtn.style.padding = '4px';

            toggleBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const icon = toggleBtn.querySelector('i');
                if (input.type === 'password') {
                    input.type = 'text';
                    icon.classList.remove('fa-eye');
                    icon.classList.add('fa-eye-slash');
                    toggleBtn.style.color = '#2563eb';
                } else {
                    input.type = 'password';
                    icon.classList.remove('fa-eye-slash');
                    icon.classList.add('fa-eye');
                    toggleBtn.style.color = '#64748b';
                }
            });

            fieldWidget.appendChild(toggleBtn);
        });
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
