/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";

registry.category("views").add("purchase_order_list", {
    ...listView,
    Controller: ListController,
});

registry.category("views").add("purchase_intent_list", {
    ...listView,
    Controller: ListController,
});
