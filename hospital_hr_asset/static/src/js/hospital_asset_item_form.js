/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";

export class AssetItemFormController extends FormController {
    setup() {
        super.setup();
        this.actionService = useService("action");
        window._hospitalAssetItemController = this;

        onMounted(() => {
            setTimeout(() => {
                const closeBtn = document.querySelector('.btn-custom-close');
                if (closeBtn) {
                    closeBtn.addEventListener('click', async (ev) => {
                        ev.preventDefault();
                        ev.stopPropagation();
                        await this.model.root.discard();
                        // Go back to the list view
                        this.actionService.doAction("hospital_hr_asset.action_asset_item", { clearBreadcrumbs: true });
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
                            name: 'Items',
                            res_model: 'hospital.asset.item',
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

export const assetItemFormView = {
    ...formView,
    Controller: AssetItemFormController,
};

registry.category("views").add("hospital_asset_item_form_view", assetItemFormView);
