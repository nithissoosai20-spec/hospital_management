from odoo import models, fields


class HospitalLabReceiptWizard(models.TransientModel):
    _name = 'hospital.lab.receipt.wizard'
    _description = 'Lab Receipt Confirmation'

    lab_appointment_id = fields.Many2one(
        'hospital.lab.appointment',
        string='Lab Appointment',
        required=True,
        readonly=True,
    )

    def action_print_now(self):
        self.ensure_one()

        action = self.env.ref(
            'hospital_management.action_report_hospital_lab_receipt'
        ).report_action(
            self.lab_appointment_id
        )
        action['close_on_report_download'] = True
        return action

    def action_print_later(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window_close',
        }
class HospitalLabResultWizard(models.TransientModel):
    _name = 'hospital.lab.result.wizard'
    _description = 'Lab Result Confirmation'

    lab_appointment_id = fields.Many2one(
        'hospital.lab.appointment',
        string='Lab Appointment',
        required=True,
        readonly=True,
    )

    def action_print_now(self):
        self.ensure_one()
        action = self.env.ref(
            'hospital_management.action_report_hospital_lab_result'
        ).report_action(
            self.lab_appointment_id
        )
        action['close_on_report_download'] = True
        return action

    def action_print_later(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}
