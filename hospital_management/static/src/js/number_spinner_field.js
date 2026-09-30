/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component } from "@odoo/owl";

export class NumberSpinnerField extends Component {
    static template = "hospital_management.NumberSpinnerField";
    static props = { ...standardFieldProps };

    get value() {
        return this.props.record.data[this.props.name] || 0;
    }

    onChange(ev) {
        let val = parseFloat(ev.target.value);
        if (isNaN(val)) val = 0;
        if (val < 0) val = 0;
        this.props.record.update({ [this.props.name]: val });
    }
}

registry.category("fields").add("number_spinner", {
    component: NumberSpinnerField,
});
