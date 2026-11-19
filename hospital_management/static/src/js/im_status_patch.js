/** @odoo-module **/

import { ImStatusDropdown } from "@mail/core/common/im_status_dropdown";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(ImStatusDropdown.prototype, {
    setup() {
        super.setup();
        if (this.store && this.store.self && (!this.store.self.im_status || this.store.self.im_status === "im_partner")) {
            this.store.self.im_status = "online";
        }
        if (this.store && this.store.self_partner && (!this.store.self_partner.im_status || this.store.self_partner.im_status === "im_partner")) {
            this.store.self_partner.im_status = "online";
        }
    },

    get readableImStatus() {
        let imStatus = this.store?.self?.im_status;
        if (!imStatus || imStatus === "im_partner") {
            imStatus = "online";
            if (this.store?.self) {
                this.store.self.im_status = "online";
            }
        }
        for (const status in this.readableImStatusByCode) {
            if (imStatus.includes(status)) {
                return this.readableImStatusByCode[status];
            }
        }
        return _t("Online");
    },

    async setManualImStatus(status) {
        if (this.store?.self) {
            this.store.self.im_status = status;
        }
        if (this.store?.self_partner) {
            this.store.self_partner.im_status = status;
        }
        try {
            await super.setManualImStatus(...arguments);
        } catch (e) {
            console.warn("setManualImStatus error:", e);
        }
        if (this.store?.self) {
            this.store.self.im_status = status;
        }
        if (this.store?.self_partner) {
            this.store.self_partner.im_status = status;
        }
    },
});
