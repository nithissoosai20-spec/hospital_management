/** @odoo-module **/

import { SwitchCompanyMenu } from "@web/webclient/switch_company_menu/switch_company_menu";
import { UserMenu } from "@web/webclient/user_menu/user_menu";
import { session } from "@web/session";
import { user } from "@web/core/user";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

let userDesignationCache = session.hospital_user_designation || session.user_designation || "";

async function loadDesignation(orm, comp) {
    if (userDesignationCache) {
        return userDesignationCache;
    }
    try {
        if (user.isAdmin || user.userId === 2 || user.login === "admin") {
            userDesignationCache = "Administrator";
            if (comp && comp.render) {
                comp.render();
            }
            return userDesignationCache;
        }
        const records = await orm.call(
            "hospital.user",
            "search_read",
            [[["odoo_user_id", "=", user.userId]]],
            { fields: ["role_id", "designation_id", "name"], limit: 1 }
        );
        if (records && records.length > 0) {
            const r = records[0];
            if (r.role_id && r.role_id[1]) {
                userDesignationCache = r.role_id[1];
            } else if (r.designation_id && r.designation_id[1]) {
                userDesignationCache = r.designation_id[1];
            }
        }
        if (!userDesignationCache) {
            userDesignationCache = "Staff";
        }
        if (comp && comp.render) {
            comp.render();
        }
    } catch (e) {
        console.warn("Failed to load user designation:", e);
    }
    return userDesignationCache;
}

patch(SwitchCompanyMenu.prototype, {
    setup() {
        super.setup(...arguments);
        try {
            this.orm = useService("orm");
            if (!userDesignationCache && this.orm) {
                loadDesignation(this.orm, this);
            }
        } catch (e) {
            // Service not available
        }
    },
    get userDesignation() {
        return userDesignationCache || "";
    },
});

patch(UserMenu.prototype, {
    setup() {
        super.setup(...arguments);
        try {
            this.orm = useService("orm");
            if (!userDesignationCache && this.orm) {
                loadDesignation(this.orm, this);
            }
        } catch (e) {
            // Service not available
        }
    },
    get userDesignation() {
        return userDesignationCache || "";
    },
});
