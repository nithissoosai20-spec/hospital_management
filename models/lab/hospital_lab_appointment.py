import base64
from pathlib import Path

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime


class HospitalLabAppointment(models.Model):
    _name = 'hospital.lab.appointment'
    _description = 'Hospital Lab Appointment'
    _order = 'appointment_date desc, id desc'


    def _get_bill_background(self):
        self.ensure_one()

        image_path = (
            Path(__file__).resolve().parents[2]
            / 'static'
            / 'src'
            / 'img'
            / 'bill.png'
        )

        if not image_path.exists():
            return ''

        with image_path.open('rb') as image_file:
            return base64.b64encode(
                image_file.read()
            ).decode('utf-8')

        
    name = fields.Char(
        string='Lab Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )

    hospital_appointment_id = fields.Many2one(
        'hospital.appointment',
        string='Hospital Appointment',
        readonly=True,
        ondelete='set null',
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
        required=False,
        ondelete='restrict'
    )

    # MULTIPLE LAB TESTS

    line_ids = fields.One2many(
        'hospital.lab.appointment.line',
        'lab_appointment_id',
        string='Lab Tests',
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
        string='Total Amount',
        compute='_compute_amount',
        store=True,
        readonly=True,
    )

    @api.depends(
        'line_ids',
        'line_ids.price',
    )
    def _compute_amount(self):

        for record in self:

            record.amount = sum(
                record.line_ids.mapped('price')
            )
    payment_status = fields.Selection(
        [
            ('pending', 'Pending'),
            ('paid', 'Paid'),
        ],
        string='Payment Status',
        default='pending'
    )

    receipt_ready = fields.Boolean(
        string='Receipt Ready',
        default=False,
        copy=False,
    )

    payment_mode = fields.Selection(
        [
            ('cash', 'Cash'),
            ('card', 'Card'),
            ('upi', 'UPI'),
            ('bank', 'Bank Transfer'),
        ],
        string='Payment Mode',
        default='cash',
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

            # Receipt becomes available only when
            # the record is actually created as Paid.
            vals['receipt_ready'] = (
                vals.get('payment_status') == 'paid'
            )

        return super().create(vals_list)


    def write(self, vals):

        if 'payment_status' in vals:

            vals['receipt_ready'] = (
                vals['payment_status'] == 'paid'
            )

        return super().write(vals)


    def action_save_lab_appointment(self):
        self.ensure_one()

        # Make sure the current form values are saved first.
        self.write({
            'payment_status': self.payment_status,
            'payment_mode': self.payment_mode,
        })

        # Only show the print question when the saved
        # payment status is Paid.
        if self.payment_status == 'paid':

            return {
                'type': 'ir.actions.act_window',
                'name': 'Lab Appointment Saved',
                'res_model': 'hospital.lab.receipt.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_lab_appointment_id': self.id,
                },
            }

        # Pending payment: just save and stay on the record.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    
    def action_schedule(self):

        for record in self:

            if record.state != 'draft':
                continue

            # -------------------------------------------------
            # LAB TEST REQUIRED
            # -------------------------------------------------

            if not record.line_ids:
                raise UserError(
                    'Please select at least one Lab Test '
                    'before scheduling the appointment.'
                )

            # -------------------------------------------------
            # SCHEDULE
            # -------------------------------------------------

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

    _sql_constraints = [
        (
            'unique_lab_test_per_appointment',
            'unique(lab_appointment_id, lab_test_id)',
            'This Lab Test has already been selected.'
        ),
    ]

# LAB APPOINTMENT LINE

class HospitalLabAppointmentLine(models.Model):

    _name = 'hospital.lab.appointment.line'
    _description = 'Hospital Lab Appointment Line'

    # APPOINTMENT

    lab_appointment_id = fields.Many2one(
        'hospital.lab.appointment',
        string='Lab Appointment',
        required=True,
        ondelete='cascade',
    )

    # LAB TEST

    lab_test_id = fields.Many2one(
        'hospital.lab.test',
        string='Lab Test',
        required=True,
        ondelete='restrict',
    )

    # TEST DETAILS

    test_code = fields.Char(
        related='lab_test_id.code',
        string='Code',
        readonly=True,
    )

    category = fields.Selection(
        related='lab_test_id.category',
        string='Category',
        readonly=True,
    )

    sample_type = fields.Selection(
        related='lab_test_id.sample_type',
        string='Sample Type',
        readonly=True,
    )

    price = fields.Float(
        related='lab_test_id.price',
        string='Price',
        readonly=True,
    )


    