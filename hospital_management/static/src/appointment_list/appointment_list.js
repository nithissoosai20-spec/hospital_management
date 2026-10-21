/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { RelationalModel } from "@web/model/relational_model/relational_model";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";
import { useState } from "@odoo/owl";


// CUSTOM MODEL — injects today's domain on first load

function _todayStr() {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
}

export class HospitalAppointmentModel extends RelationalModel {
    async load(params = {}) {
        // Only inject on the very first load (no domain override yet)
        if (!params.domain || params.domain.length === 0) {
            const today = _todayStr();
            params = {
                ...params,
                domain: [
                    ["appointment_date", ">=", today],
                    ["appointment_date", "<=", today],
                ],
            };
        }
        return super.load(params);
    }
}

export class HospitalAppointmentListController extends ListController {

    static template = "hospital_management.HospitalAppointmentListView";

    setup() {
        super.setup();

        const today = this._today();

        this.filterState = useState({
            fromDate: today,
            toDate: today,
            search: "",
        });
    }

    // HELPERS

    _today() {
        const d = new Date();
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, "0");
        const day = String(d.getDate()).padStart(2, "0");
        return `${y}-${m}-${day}`;
    }

    _buildDomain() {
        const domain = [];
        const q = this.filterState.search.trim();

        if (q) {
            // SEARCH MODE: Search all history, ignore dates
            domain.push(
                "|", "|",
                ["patient_name", "ilike", q],
                ["patient_code", "ilike", q],
                ["patient_phone", "ilike", q]
            );
        } else {
            // LIST MODE: Only use date filters when not searching
            if (this.filterState.fromDate) {
                domain.push(["appointment_date", ">=", this.filterState.fromDate]);
            }
            if (this.filterState.toDate) {
                domain.push(["appointment_date", "<=", this.filterState.toDate]);
            }
        }

        return domain;
    }

    async _applyFilters() {
        await this.model.root.load({ domain: this._buildDomain(), offset: 0 });
        this.render(true);
    }

    // NEW APPOINTMENT

    onNewAppointment() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "New Appointment",
            res_model: "hospital.appointment",
            views: [[false, "form"]],
            target: "current",
            context: {
                is_new_booking: true,
            },
        });
    }

    // FILTER BUTTON — only fires when user clicks Filter

    async onFilterClick() {
        await this._applyFilters();
    }

    // DATE CHANGE — just update state, do NOT auto-load

    onFromDateChange(ev) {
        this.filterState.fromDate = ev.target.value;
        if (
            this.filterState.fromDate &&
            this.filterState.toDate &&
            this.filterState.fromDate > this.filterState.toDate
        ) {
            this.filterState.toDate = this.filterState.fromDate;
        }
    }

    onToDateChange(ev) {
        this.filterState.toDate = ev.target.value;
        if (
            this.filterState.fromDate &&
            this.filterState.toDate &&
            this.filterState.toDate < this.filterState.fromDate
        ) {
            this.filterState.fromDate = this.filterState.toDate;
        }
    }

    // SEARCH — fires on Enter key only

    async onSearchKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.filterState.search = ev.target.value;
            await this._applyFilters();
        }
    }

    onSearchInput(ev) {
        this.filterState.search = ev.target.value;
    }
}


// REGISTER

export const hospitalAppointmentListView = {
    ...listView,
    Controller: HospitalAppointmentListController,
    Model: HospitalAppointmentModel,
};

registry.category("views").add(
    "hospital_appointment_list",
    hospitalAppointmentListView
);
