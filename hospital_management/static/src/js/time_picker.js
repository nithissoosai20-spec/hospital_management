/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, xml } from "@odoo/owl";

export class TimePickerField extends Component {
    static template = xml`
        <t t-if="props.readonly">
            <span t-esc="formatTime(props.record.data[props.name])" />
        </t>
        <t t-else="">
            <input type="time" class="o_input" t-att-value="props.record.data[props.name]" t-on-change="onChange"/>
        </t>
    `;
    static props = {
        ...standardFieldProps,
    };
    formatTime(val) {
        if (!val) return "";
        try {
            let parts = val.split(':');
            let h = parseInt(parts[0]);
            let m = parts[1];
            let ampm = h < 12 ? 'AM' : 'PM';
            let hr12 = h % 12;
            if (hr12 === 0) hr12 = 12;
            return hr12.toString().padStart(2, '0') + ':' + m + ' ' + ampm;
        } catch(e) {
            return val;
        }
    }
    onChange(ev) {
        this.props.record.update({ [this.props.name]: ev.target.value });
    }
}

registry.category("fields").add("html_time", {
    component: TimePickerField,
    supportedTypes: ["char"],
});
