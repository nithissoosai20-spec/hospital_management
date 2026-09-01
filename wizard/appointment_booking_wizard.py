from odoo import models, fields


class HospitalAppointmentBookingWizard(models.TransientModel):
    _name = 'hospital.appointment.booking.wizard'
    _description = 'Appointment Booking Confirmation'

    appointment_id = fields.Many2one(
        'hospital.appointment',
        string='Appointment',
        required=True,
        readonly=True,
    )

    patient_id_display = fields.Char(
        related='appointment_id.patient_id.patient_id',
        string='Patient ID',
        readonly=True,
    )

    patient_name = fields.Char(
        related='appointment_id.patient_name',
        string='Patient',
        readonly=True,
    )

    token_number = fields.Char(
        related='appointment_id.token_number',
        string='Token Number',
        readonly=True,
    )

    def action_print_now(self):
        """Print receipt immediately."""
        self.ensure_one()

        appointment = self.appointment_id

        appointment.write({
            'print_preference': 'now',
        })

        return appointment.action_print_receipt()

    def action_print_later(self):
        """Close the popup and mark receipt for later printing."""
        self.ensure_one()

        appointment = self.appointment_id

        appointment.write({
            'print_preference': 'later',
        })

        return {
            'type': 'ir.actions.act_window_close',
        }
