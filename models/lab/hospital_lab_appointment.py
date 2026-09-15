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
        default='New Lab Test'
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

    appointment_time = fields.Char(
        string='Appointment Time',
        required=True,
        default='10:30'
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
            ('none', 'None'),
            ('card', 'Card'),
            ('upi', 'UPI'),
            ('bank', 'Bank Transfer'),
            ('online', 'Online'),
        ],
        string='Payment Mode',
        default='none',
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

    transaction_id = fields.Char(
        string='Transaction ID',
        copy=False
    )

    online_paid_amount = fields.Float(
        string='Online Paid Amount'
    )

    # CASH DENOMINATIONS - RECEIVED
    notes_500 = fields.Integer(string='₹500 Received')
    notes_200 = fields.Integer(string='₹200 Received')
    notes_100 = fields.Integer(string='₹100 Received')
    notes_50 = fields.Integer(string='₹50 Received')
    notes_20 = fields.Integer(string='₹20 Received')
    notes_10 = fields.Integer(string='₹10 Received')
    coins_received = fields.Float(string='Coins Received')

    amt_500_recv = fields.Float(compute='_compute_cash_totals')
    amt_200_recv = fields.Float(compute='_compute_cash_totals')
    amt_100_recv = fields.Float(compute='_compute_cash_totals')
    amt_50_recv = fields.Float(compute='_compute_cash_totals')
    amt_20_recv = fields.Float(compute='_compute_cash_totals')
    amt_10_recv = fields.Float(compute='_compute_cash_totals')

    # CASH DENOMINATIONS - RETURNED
    return_500 = fields.Integer(string='₹500 Returned')
    return_200 = fields.Integer(string='₹200 Returned')
    return_100 = fields.Integer(string='₹100 Returned')
    return_50 = fields.Integer(string='₹50 Returned')
    return_20 = fields.Integer(string='₹20 Returned')
    return_10 = fields.Integer(string='₹10 Returned')
    coins_return = fields.Float(string='Coins Returned')

    amt_500_ret = fields.Float(compute='_compute_cash_totals')
    amt_200_ret = fields.Float(compute='_compute_cash_totals')
    amt_100_ret = fields.Float(compute='_compute_cash_totals')
    amt_50_ret = fields.Float(compute='_compute_cash_totals')
    amt_20_ret = fields.Float(compute='_compute_cash_totals')
    amt_10_ret = fields.Float(compute='_compute_cash_totals')

    total_cash_received = fields.Float(
        string='Total Received Payment',
        compute='_compute_cash_totals'
    )
    total_cash_returned = fields.Float(
        string='Total Returned Payment',
        compute='_compute_cash_totals'
    )
    balance_amount = fields.Float(
        string='Balance Amount',
        compute='_compute_cash_totals'
    )
    amount_to_collect = fields.Float(
        string='Remaining Amount',
        compute='_compute_cash_totals'
    )

    @api.depends(
        'notes_500', 'notes_200', 'notes_100', 'notes_50', 'notes_20', 'notes_10', 'coins_received',
        'return_500', 'return_200', 'return_100', 'return_50', 'return_20', 'return_10', 'coins_return',
        'amount', 'online_paid_amount'
    )
    def _compute_cash_totals(self):
        for record in self:
            record.amt_500_recv = record.notes_500 * 500
            record.amt_200_recv = record.notes_200 * 200
            record.amt_100_recv = record.notes_100 * 100
            record.amt_50_recv = record.notes_50 * 50
            record.amt_20_recv = record.notes_20 * 20
            record.amt_10_recv = record.notes_10 * 10

            record.amt_500_ret = record.return_500 * 500
            record.amt_200_ret = record.return_200 * 200
            record.amt_100_ret = record.return_100 * 100
            record.amt_50_ret = record.return_50 * 50
            record.amt_20_ret = record.return_20 * 20
            record.amt_10_ret = record.return_10 * 10

            total_recv = record.amt_500_recv + record.amt_200_recv + record.amt_100_recv + \
                         record.amt_50_recv + record.amt_20_recv + record.amt_10_recv + record.coins_received
            
            total_ret = record.amt_500_ret + record.amt_200_ret + record.amt_100_ret + \
                        record.amt_50_ret + record.amt_20_ret + record.amt_10_ret + record.coins_return

            record.total_cash_received = total_recv
            record.total_cash_returned = total_ret
            
            # The fixed amount they need to pay via cash
            record.amount_to_collect = record.amount - record.online_paid_amount
            
            # Balance Amount = Due by patient
            record.balance_amount = record.amount_to_collect - total_recv + total_ret

    def action_open_cash_wizard(self):
        self.ensure_one()
        
        # Odoo's frontend treats 0.00 as a valid number, so it bypasses the frontend 'required' check.
        # We manually catch 0.00 and spawn the native red toast notification to mimic frontend validation.


        # Find the form view for the cash wizard
        view_id = self.env.ref('hospital_management.view_hospital_lab_cash_wizard_form').id
        return {
            'name': 'Cash Payment',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.lab.appointment',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
        }

    def action_confirm_cash(self):
        self.ensure_one()
        if self.balance_amount > 0:
            raise UserError('Insufficient Payment! Please collect the full amount.')
        if self.balance_amount < 0:
            raise UserError('Unbalanced Payment! Please log the exact return denominations so the balance is 0.')
        
        if self.payment_mode and self.payment_mode != 'none' and self.online_paid_amount <= 0:
            raise UserError('Online Paid Amount must be greater than 0.00 for digital payments.')
        
        # If they paid entirely by cash (online paid amount is 0), default to 'none' mode.
        if self.online_paid_amount <= 0:
            self.payment_mode = 'none'

        self.write({
            'payment_status': 'paid',
            'receipt_ready': True,
        })

        # Return the receipt wizard after confirming payment
        return {
            'type': 'ir.actions.act_window',
            'name': 'Print Lab Receipt',
            'res_model': 'hospital.lab.receipt.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lab_appointment_id': self.id,
            },
        }

    def action_hold_cash(self):
        """Close the wizard and save the state (Hold)."""
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'New Lab Test':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.lab.appointment') or 'New'
        return super().create(vals_list)


    def write(self, vals):

        if 'payment_status' in vals:

            vals['receipt_ready'] = (
                vals['payment_status'] == 'paid'
            )

        return super().write(vals)


    def action_save_lab_appointment(self):
        self.ensure_one()

        if not self.line_ids:
            from odoo.exceptions import UserError
            raise UserError('Please add at least one test before saving.')

        # Open the cash wizard directly!
        return self.action_open_cash_wizard()


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

    def action_close_to_appointments(self):
        """Navigate back to the main patient appointments list."""
        return self.env['ir.actions.act_window']._for_xml_id('hospital_management.action_hospital_appointment')


    _sql_constraints = [
        ('unique_lab_appointment_test', 'UNIQUE(lab_appointment_id, lab_test_id)',
         'This Lab Test has already been selected.'),
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




