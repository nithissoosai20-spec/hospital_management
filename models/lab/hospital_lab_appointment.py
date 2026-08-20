from odoo import models, fields, api
from datetime import datetime


class HospitalLabAppointment(models.Model):
    _name = 'hospital.lab.appointment'
    _description = 'Hospital Lab Appointment'
    _order = 'appointment_date desc, id desc'

    name = fields.Char(
        string='Lab Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )

    patient_id = fields.Many2one(
        'hospital.patient',
        string='Patient',
        required=True,
        ondelete='restrict'
    )

    lab_test_id = fields.Many2one(
        'hospital.lab.test',
        string='Lab Test',
        required=True,
        ondelete='restrict'
    )

    appointment_date = fields.Date(
        string='Appointment Date',
        required=True,
        default=fields.Date.today
    )

    appointment_time = fields.Float(
        string='Appointment Time',
        required=True,
        default=lambda self: (
            datetime.now().hour
            + datetime.now().minute / 60.0
        )
    )

    doctor_id = fields.Many2one(
        'hospital.user',
        string='Referring Doctor',
        domain="[('role_id.name', '=', 'Doctor')]",
        ondelete='restrict'
    )

    priority = fields.Selection(
        [
            ('normal', 'Normal'),
            ('urgent', 'Urgent'),
            ('emergency', 'Emergency'),
        ],
        string='Priority',
        required=True,
        default='normal'
    )

    sample_type = fields.Selection(
        [
            ('blood', 'Blood'),
            ('urine', 'Urine'),
            ('stool', 'Stool'),
            ('swab', 'Swab'),
            ('serum', 'Serum'),
            ('other', 'Other'),
        ],
        string='Sample Type',
        required=True,
        default='blood'
    )

    amount = fields.Float(
        string='Amount',
        related='lab_test_id.price',
        store=True,
        readonly=True
    )

    payment_status = fields.Selection(
        [
            ('pending', 'Pending'),
            ('partial', 'Partially Paid'),
            ('paid', 'Paid'),
        ],
        string='Payment Status',
        default='pending'
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('scheduled', 'Scheduled'),
            ('sample_collected', 'Sample Collected'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True
    )

    result = fields.Text(
        string='Result'
    )

    remarks = fields.Text(
        string='Remarks'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env[
                    'ir.sequence'
                ].next_by_code(
                    'hospital.lab.appointment'
                ) or 'New'

        return super().create(vals_list)

    def action_schedule(self):
        for record in self:
            if record.state == 'draft':
                record.state = 'scheduled'
        return True

    def action_collect_sample(self):
        for record in self:
            if record.state == 'scheduled':
                record.state = 'sample_collected'
        return True

    def action_start_processing(self):
        for record in self:
            if record.state == 'sample_collected':
                record.state = 'processing'
        return True

    def action_complete(self):
        for record in self:
            if record.state == 'processing':
                record.state = 'completed'
        return True

    def action_cancel(self):
        for record in self:
            if record.state != 'completed':
                record.state = 'cancelled'
        return True