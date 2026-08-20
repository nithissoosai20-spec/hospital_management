from odoo import models, fields, api
from datetime import datetime


class HospitalAppointment(models.Model):
    _name = 'hospital.appointment'
    _description = 'Hospital Appointment'
    _order = 'appointment_date desc, id desc'

    name = fields.Char(
        string='Appointment Reference',
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

        # ---------------------------------------------------------
    # PATIENT PREVIEW
    # ---------------------------------------------------------

    patient_code = fields.Char(
        string='Patient ID',
        related='patient_id.patient_id',
        readonly=True
    )

    patient_name = fields.Char(
        string='Patient Name',
        related='patient_id.name',
        readonly=True
    )

    patient_age = fields.Integer(
        string='Age',
        related='patient_id.age',
        readonly=True
    )

    patient_date_of_birth = fields.Date(
        string='Date of Birth',
        related='patient_id.date_of_birth',
        readonly=True
    )

    patient_gender = fields.Selection(
        string='Gender',
        related='patient_id.gender',
        readonly=True
    )

    patient_phone = fields.Char(
        string='Mobile Number',
        related='patient_id.phone',
        readonly=True
    )

    doctor_id = fields.Many2one(
    'hospital.user',
    string='Doctor',
    domain=[('role_id.name', '=', 'Doctor')]
    )

    department_id = fields.Many2one(
        'hospital.department',
        string='Department',
        related='doctor_id.department_id',
        store=True,
        readonly=True
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

    visit_type = fields.Selection(
        [
            ('new', 'New Visit'),
            ('followup', 'Follow-up'),
        ],
        string='Visit Type',
        required=True,
        default='new'
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

    appointment_mode = fields.Selection(
        [
            ('walkin', 'Walk-in'),
            ('phone', 'Phone'),
            ('online', 'Online'),
        ],
        string='Appointment Mode',
        required=True,
        default='walkin'
    )

    token_number = fields.Char(
        string='Token Number',
        copy=False,
        readonly=True
    )

    reason = fields.Text(
        string='Reason / Symptoms'
    )

    consultation_fee = fields.Float(
        string='Consultation Fee',
        default=0.0
    )

    discount = fields.Float(
        string='Discount',
        default=0.0
    )

    net_amount = fields.Float(
        string='Net Amount',
        compute='_compute_net_amount',
        store=True
    )

    payment_mode = fields.Selection(
        [
            ('cash', 'Cash'),
            ('card', 'Card'),
            ('upi', 'UPI'),
            ('online', 'Online'),
        ],
        string='Payment Mode'
    )

    payment_status = fields.Selection(
        [
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('partial', 'Partially Paid'),
        ],
        string='Payment Status',
        default='pending'
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('booked', 'Booked'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True
    )

    # ---------------------------------------------------------
    # COMPUTE
    # ---------------------------------------------------------

    @api.depends('consultation_fee', 'discount')
    def _compute_net_amount(self):
        for record in self:
            record.net_amount = max(
                record.consultation_fee - record.discount,
                0.0
            )

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env[
                    'ir.sequence'
                ].next_by_code(
                    'hospital.appointment'
                ) or 'New'

            if not vals.get('token_number'):
                vals['token_number'] = self.env[
                    'ir.sequence'
                ].next_by_code(
                    'hospital.appointment.token'
                ) or 'TOKEN'

        return super().create(vals_list)

    # ---------------------------------------------------------
    # WORKFLOW
    # ---------------------------------------------------------

    def action_book(self):
        for record in self:
            if record.state == 'draft':
                record.state = 'booked'

        return True

    def action_complete(self):
        for record in self:
            if record.state == 'booked':
                record.state = 'completed'

        return True

    def action_cancel(self):
        for record in self:
            if record.state in ('draft', 'booked'):
                record.state = 'cancelled'

        return True

    def action_reset_to_draft(self):
        for record in self:
            if record.state == 'cancelled':
                record.state = 'draft'

        return True
    