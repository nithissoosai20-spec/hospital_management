from datetime import datetime
import pytz
from odoo import api, fields, models
from odoo.exceptions import UserError


class HospitalLabBill(models.Model):
    _name = 'hospital.lab.bill'
    _description = 'Lab Bill'
    _order = 'id desc'

    name = fields.Char(
        string='Bill Number',
        required=True,
        readonly=True,
        copy=False,
        default='Create Bill',
    )

    admission_type = fields.Selection(
        [
            ('with_admission', 'With Admission'),
            ('without_admission', 'Without Admission'),
        ],
        string='Admission Type',
        default='with_admission',
        required=True,
    )

    patient_id = fields.Many2one(
        'hospital.patient',
        string='Patient',
        ondelete='restrict',
    )

    patient_id_display = fields.Char(
        string='Patient ID',
        related='patient_id.patient_id',
        readonly=True,
    )

    appointment_id = fields.Many2one(
        'hospital.appointment',
        string='Appointment',
        ondelete='set null',
    )

    lab_appointment_id = fields.Many2one(
        'hospital.lab.appointment',
        string='Lab Appointment',
        ondelete='set null',
    )

    doctor_id = fields.Many2one(
        'hospital.user',
        string='Doctor',
        domain="[('role_id.name', 'ilike', 'doctor')]",
        ondelete='set null',
    )

    doctor_department_id = fields.Many2one(
        'hospital.department',
        string='Department',
        readonly=True,
    )

    bill_date = fields.Datetime(
        string='Bill Date',
        default=fields.Datetime.now,
        required=True,
    )

    walkin_name = fields.Char(string='Walk-in Name')
    walkin_phone = fields.Char(string='Walk-in Phone')
    walkin_age = fields.Integer(string='Walk-in Age')
    walkin_gender = fields.Selection(
        [
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        string='Walk-in Gender',
        default='male'
    )
    walkin_address = fields.Char(string='Walk-in Address')

    customer_name = fields.Char(
        string='Customer Name',
        compute='_compute_customer_name',
        store=True,
    )

    @api.depends('admission_type', 'patient_id.name', 'walkin_name')
    def _compute_customer_name(self):
        for rec in self:
            if rec.admission_type == 'without_admission':
                rec.customer_name = rec.walkin_name or ''
            else:
                rec.customer_name = rec.patient_id.name if rec.patient_id else ''

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('held', 'Hold'),
            ('paid', 'Paid'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        copy=False,
    )

    payment_mode = fields.Selection(
        [
            ('cash', 'Cash'),
            ('card', 'Card'),
            ('upi', 'UPI'),
            ('credit', 'Credit'),
            ('wallet', 'Wallet'),
            ('others', 'Others'),
        ],
        string='Payment Mode',
        default='cash',
    )

    paid_amount = fields.Float(
        string='Paid Amount',
        default=0.0,
    )

    bill_discount = fields.Float(
        string='Discount',
        default=0.0,
    )

    notes = fields.Text(
        string='Notes',
    )

    line_ids = fields.One2many(
        'hospital.lab.bill.line',
        'bill_id',
        string='Lab Tests',
        copy=True,
    )

    subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_amounts',
        store=True,
    )

    discount_amount = fields.Float(
        string='Discount Amount',
        compute='_compute_amounts',
        store=True,
    )

    round_off = fields.Float(
        string='Round Off',
        compute='_compute_amounts',
        store=True,
    )

    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_amounts',
        store=True,
    )

    @api.depends('line_ids.price', 'line_ids.discount', 'bill_discount')
    def _compute_amounts(self):
        for bill in self:
            subtotal = 0.0
            line_discount = 0.0
            for line in bill.line_ids:
                line_sub = line.price
                disc = line_sub * (line.discount / 100.0) if line.discount else 0.0
                line.discount_amount = disc
                line.total_amount = line_sub - disc
                subtotal += line_sub
                line_discount += disc

            total_disc = line_discount + (bill.bill_discount or 0.0)
            raw_total = max(0.0, subtotal - total_disc)
            rounded_total = round(raw_total)

            bill.subtotal = subtotal
            bill.discount_amount = total_disc
            bill.round_off = rounded_total - raw_total
            bill.total_amount = rounded_total

    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        if self.patient_id:
            # Find active draft lab appointment for this patient
            lab_app = self.env['hospital.lab.appointment'].search([
                ('patient_id', '=', self.patient_id.id),
                ('payment_status', '=', 'pending'),
            ], order='id desc', limit=1)

            if lab_app:
                self.lab_appointment_id = lab_app.id
                if lab_app.doctor_id:
                    self.doctor_id = lab_app.doctor_id
                if lab_app.hospital_appointment_id:
                    self.appointment_id = lab_app.hospital_appointment_id

                lines = []
                for b_line in lab_app.billing_line_ids:
                    if b_line.lab_test_id:
                        lines.append((0, 0, {
                            'lab_test_id': b_line.lab_test_id.id,
                            'test_name': b_line.lab_test_id.name,
                            'test_code': b_line.lab_test_id.code or '',
                            'category_name': b_line.lab_test_id.lab_category_id.name if b_line.lab_test_id.lab_category_id else '',
                            'price': b_line.price or b_line.lab_test_id.price or 0.0,
                            'discount': 0.0,
                        }))
                self.line_ids = lines

    @api.onchange('doctor_id')
    def _onchange_doctor_id(self):
        if self.doctor_id and self.doctor_id.department_id:
            self.doctor_department_id = self.doctor_id.department_id
        else:
            self.doctor_department_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Create Bill') in ('Create Bill', '/', False):
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.lab.bill') or 'LAB-BILL-0001'
        records = super().create(vals_list)
        for rec in records:
            if rec.state == 'paid':
                rec._post_payment_process()
        return records

    def write(self, vals):
        res = super().write(vals)
        if vals.get('state') == 'paid':
            for rec in self:
                rec._post_payment_process()
        return res

    def _post_payment_process(self):
        """When lab bill is paid, update or create lab appointment with paid status."""
        self.ensure_one()
        # With Admission:
        if self.admission_type == 'with_admission' and self.patient_id:
            lab_app = self.lab_appointment_id
            if not lab_app:
                lab_app = self.env['hospital.lab.appointment'].search([
                    ('patient_id', '=', self.patient_id.id),
                    ('payment_status', '=', 'pending'),
                ], order='id desc', limit=1)

            if lab_app:
                lab_app.write({
                    'payment_status': 'paid',
                    'payment_mode': self.payment_mode or 'cash',
                    'state': 'scheduled',
                    'round_off': self.round_off,
                    'amount': self.total_amount,
                    'net_amount': self.total_amount,
                })
            else:
                # Create lab appointment
                new_app = self.env['hospital.lab.appointment'].create({
                    'patient_id': self.patient_id.id,
                    'doctor_id': self.doctor_id.id if self.doctor_id else False,
                    'hospital_appointment_id': self.appointment_id.id if self.appointment_id else False,
                    'payment_status': 'paid',
                    'payment_mode': self.payment_mode or 'cash',
                    'state': 'scheduled',
                    'appointment_date': fields.Date.today(),
                })
                for line in self.line_ids:
                    if line.lab_test_id:
                        self.env['hospital.lab.appointment.line'].create({
                            'lab_appointment_id': new_app.id,
                            'lab_test_id': line.lab_test_id.id,
                            'price': line.total_amount,
                        })
        elif self.admission_type == 'without_admission':
            # Create a patient or use/create lab appointment
            patient = self.patient_id
            if not patient and self.walkin_name:
                patient = self.env['hospital.patient'].create({
                    'name': self.walkin_name,
                    'phone': self.walkin_phone or '0000000000',
                    'gender': self.walkin_gender or 'male',
                    'age': self.walkin_age or 0,
                    'address': self.walkin_address or '',
                })
                self.patient_id = patient.id

            if patient:
                new_app = self.env['hospital.lab.appointment'].create({
                    'patient_id': patient.id,
                    'doctor_id': self.doctor_id.id if self.doctor_id else False,
                    'payment_status': 'paid',
                    'payment_mode': self.payment_mode or 'cash',
                    'state': 'scheduled',
                    'appointment_date': fields.Date.today(),
                })
                for line in self.line_ids:
                    if line.lab_test_id:
                        self.env['hospital.lab.appointment.line'].create({
                            'lab_appointment_id': new_app.id,
                            'lab_test_id': line.lab_test_id.id,
                            'price': line.total_amount,
                        })

    def action_collect_payment(self):
        self.ensure_one()
        self.state = 'paid'

    def get_patient_title_name(self):
        self.ensure_one()
        name = (self.patient_id.name if self.patient_id else self.walkin_name) or ''
        name = name.strip()
        if not name:
            return ''
        lower_name = name.lower()
        if lower_name.startswith(('mr.', 'mr ', 'mrs.', 'mrs ', 'ms.', 'ms ', 'dr.', 'dr ')):
            return name
        gender = (self.patient_id.gender if self.patient_id else self.walkin_gender) or ''
        gender = gender.lower()
        if gender == 'male':
            return f"Mr. {name}"
        elif gender == 'female':
            return f"Mrs. {name}"
        return name

    def get_doctor_title_name(self):
        self.ensure_one()
        if not self.doctor_id:
            return '--'
        name = (self.doctor_id.name or '').strip()
        if not name:
            return '--'
        lower_name = name.lower()
        if lower_name.startswith(('dr.', 'dr ')):
            return name
        return f"Dr. {name}"

    def get_exact_current_time(self):
        user_tz = self.env.user.tz or 'Asia/Kolkata'
        try:
            user_pytz = pytz.timezone(user_tz)
        except Exception:
            user_pytz = pytz.timezone('Asia/Kolkata')
        return datetime.now(user_pytz).strftime('%d/%m/%Y %I:%M %p')


class HospitalLabBillLine(models.Model):
    _name = 'hospital.lab.bill.line'
    _description = 'Lab Bill Line'

    bill_id = fields.Many2one(
        'hospital.lab.bill',
        string='Lab Bill',
        required=True,
        ondelete='cascade',
    )

    lab_test_id = fields.Many2one(
        'hospital.lab.test',
        string='Lab Test',
        required=True,
    )

    test_code = fields.Char(
        string='Test Code',
    )

    test_name = fields.Char(
        string='Test Name',
        required=True,
    )

    category_name = fields.Char(
        string='Category',
    )

    price = fields.Float(
        string='Rate (₹)',
        default=0.0,
    )

    discount = fields.Float(
        string='Discount (%)',
        default=0.0,
    )

    discount_amount = fields.Float(
        string='Discount Amount',
        default=0.0,
    )

    total_amount = fields.Float(
        string='Total Amount (₹)',
        default=0.0,
    )

    @api.onchange('lab_test_id')
    def _onchange_lab_test_id(self):
        if self.lab_test_id:
            self.test_name = self.lab_test_id.name
            self.test_code = self.lab_test_id.code or ''
            self.category_name = self.lab_test_id.lab_category_id.name if self.lab_test_id.lab_category_id else ''
            self.price = self.lab_test_id.price or 0.0
