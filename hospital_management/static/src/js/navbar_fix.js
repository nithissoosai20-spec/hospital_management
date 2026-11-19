/** @odoo-module **/

import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";

patch(NavBar.prototype, {
    get currentApp() {
        let app = super.currentApp;
        if (!app) {
            const apps = this.menuService.getApps();
            if (apps && apps.length > 0) {
                app = apps[0];
            }
        }
        return app;
    },
});
