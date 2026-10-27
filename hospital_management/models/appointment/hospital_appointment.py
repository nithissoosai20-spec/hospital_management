from datetime import datetime
import pytz
from odoo import models, fields, api
from odoo.exceptions import UserError, AccessError


class HospitalAppointment(models.Model):
    _name = 'hospital.appointment'
    _description = 'Hospital Appointment'
    _order = 'appointment_date desc, id desc'

    # APPOINTMENT REFERENCE

    name = fields.Char(
        string='Appointment Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New Appointment'
    )

    # PATIENT

    patient_id = fields.Many2one(
        'hospital.patient',
        string='Patient',
        ondelete='restrict'
    )

    search_patient = fields.Char(
        string='Search Patient',
        help='Search using Patient ID or Mobile Number.'
    )

    patient_found = fields.Boolean(
        string='Patient Found',
        default=False
    )

    # New patient details

    new_patient_name = fields.Char(
        string='New Patient Name'
    )

    new_patient_phone = fields.Char(
        string='New Patient Mobile'
    )

    new_patient_age = fields.Integer(string='New Patient Age')

    new_patient_gender = fields.Selection(
        [
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        string='New Patient Gender'
    )

    new_patient_blood_group = fields.Char(
        string='New Patient Blood Group'
    )

    new_patient_email = fields.Char(
        string='Email'
    )

    new_patient_address = fields.Text(
        string='Address'
    )



    # EXISTING PATIENT PREVIEW

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

    patient_blood_group = fields.Selection(
        string='Blood Group',
        related='patient_id.blood_group',
        readonly=True
    )

    patient_active = fields.Boolean(
        string='Active',
        related='patient_id.active',
        readonly=True
    )

    # DOCTOR / APPOINTMENT

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


    def _default_appointment_time(self):
        user_tz = self.env.user.tz or 'Asia/Kolkata'
        try:
            user_pytz = pytz.timezone(user_tz)
        except Exception:
            user_pytz = pytz.timezone('Asia/Kolkata')
        return datetime.now(user_pytz).strftime('%H:%M')

    def get_patient_title_name(self):
        self.ensure_one()
        name = (self.patient_name or '').strip()
        if not name:
            return ''
        lower_name = name.lower()
        if lower_name.startswith(('mr.', 'mr ', 'mrs.', 'mrs ', 'ms.', 'ms ', 'dr.', 'dr ')):
            return name
        gender = (self.patient_gender or self.new_patient_gender or (self.patient_id.gender if self.patient_id else False) or '').lower()
        if gender == 'male':
            return f"Mr. {name}"
        elif gender == 'female':
            return f"Mrs. {name}"
        return name

    def get_doctor_title_name(self):
        self.ensure_one()
        name = (self.doctor_id.name or '').strip()
        if not name:
            return ''
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
        return datetime.now(user_pytz).strftime('%I:%M %p')

    appointment_time = fields.Char(
        string='Appointment Time',
        default=_default_appointment_time
    )

    appointment_time_am_pm = fields.Char(
        string='Time AM/PM',
        compute='_compute_time_am_pm'
    )

    @api.depends('appointment_time')
    def _compute_time_am_pm(self):
        for rec in self:
            if rec.appointment_time:
                try:
                    parts = rec.appointment_time.split(':')
                    h = int(parts[0])
                    m = int(parts[1])
                    ampm = 'AM' if h < 12 else 'PM'
                    h12 = h % 12
                    if h12 == 0: h12 = 12
                    rec.appointment_time_am_pm = f'{h12:02d}:{m:02d} {ampm}'
                except:
                    rec.appointment_time_am_pm = rec.appointment_time
            else:
                rec.appointment_time_am_pm = ''




    visit_type = fields.Selection(
        [
            ('new', 'New Visit'),
            ('followup', 'Follow-up'),
        ],
        string='Visit Type',
        required=True,
        default='new'
    )

    consultation_type_id = fields.Many2one(
        'hospital.consultation.type',
        string='Consultation Type',
    )

    available_consultation_type_ids = fields.Many2many(
        'hospital.consultation.type',
        compute='_compute_available_consultation_types',
        string='Available Consultation Types',
    )

    @api.depends('doctor_id', 'doctor_id.consultation_line_ids.consultation_type_id')
    def _compute_available_consultation_types(self):
        for record in self:
            if record.doctor_id and record.doctor_id.consultation_line_ids:
                record.available_consultation_type_ids = record.doctor_id.consultation_line_ids.mapped('consultation_type_id')
            else:
                record.available_consultation_type_ids = self.env['hospital.consultation.type']

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

    token_generated = fields.Boolean(
        string='Token Generated',
        default=False,
        copy=False
    )

    reason = fields.Text(
        string='Reason / Symptoms'
    )

    # FEES / PAYMENT

    fees_type = fields.Selection(
        [
            ('consultation', 'Consultation Fees'),
            ('lab', 'Lab Fees'),
        ],
        string='Fees Type',
        default='consultation'
    )

    has_lab_test = fields.Boolean(compute='_compute_has_lab_test', store=False)

    pharmacy_bill_ids = fields.One2many(
        'hospital.pharmacy.bill',
        'appointment_id',
        string='Pharmacy Prescriptions'
    )
    pharmacy_bill_count = fields.Integer(
        string='Pharmacy Bills',
        compute='_compute_pharmacy_bill_count'
    )
    lab_appointment_ids = fields.One2many(
        'hospital.lab.appointment',
        'hospital_appointment_id',
        string='Lab Tests'
    )
    lab_appointment_count = fields.Integer(
        string='Lab Tests Count',
        compute='_compute_lab_appointment_count'
    )

    def _compute_pharmacy_bill_count(self):
        for rec in self:
            rec.pharmacy_bill_count = len(rec.pharmacy_bill_ids)
            
    def _compute_lab_appointment_count(self):
        for rec in self:
            rec.lab_appointment_count = len(rec.lab_appointment_ids)

    def action_open_pharmacy_prescriptions(self):
        self.ensure_one()
        return {
            'name': 'Prescribe Medicines',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.pharmacy.bill',
            'view_mode': 'list,form',
            'domain': [('appointment_id', '=', self.id)],
            'context': {
                'default_appointment_id': self.id,
                'default_patient_id': self.patient_id.id if self.patient_id else False,
                'default_doctor_id': self.doctor_id.id if self.doctor_id else False,
            }
        }
        
    def action_open_lab_prescriptions(self):
        self.ensure_one()
        return {
            'name': 'Prescribe Lab Tests',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.lab.appointment',
            'view_mode': 'list,form',
            'domain': [('hospital_appointment_id', '=', self.id)],
            'context': {
                'default_hospital_appointment_id': self.id,
                'default_patient_id': self.patient_id.id if self.patient_id else False,
                'default_doctor_id': self.doctor_id.id if self.doctor_id else False,
                'default_appointment_date': self.appointment_date,
            }
        }


    def _compute_has_lab_test(self):
        for rec in self:
            lab_count = self.env['hospital.lab.appointment'].search_count([('hospital_appointment_id', '=', rec.id)])
            rec.has_lab_test = bool(lab_count > 0)

    consultation_fee = fields.Float(
        string='Consultation Fee',
        compute='_compute_consultation_fee',
        store=True,
        readonly=True
    )

    discount = fields.Float(
        string='Discount',
        default=0.0
    )

    
    round_off = fields.Float(
        string='Round Off',
        compute='_compute_net_amount',
        store=True
    )

    net_amount = fields.Float(
        string='Net Amount',
        compute='_compute_net_amount',
        store=True
    )

    payment_mode = fields.Selection(
        [
            ('none', 'None'),
            ('card', 'Card'),
            ('upi', 'UPI'),
            ('online', 'Online'),
        ],
        string='Type of Digital Payment Mode', default='none'
    )

    payment_status = fields.Selection(
        [
            ('pending', 'Pending'),
            ('paid', 'Paid'),
        ],
        string='Payment Status',
        default='pending'
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
        'net_amount', 'online_paid_amount'
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
            record.amount_to_collect = record.net_amount - record.online_paid_amount
            
            # Balance Amount = Due by patient
            record.balance_amount = record.amount_to_collect - total_recv + total_ret

    def action_open_cash_wizard(self):
        self.ensure_one()
        
        # Find the form view for the cash wizard
        view_id = self.env.ref('hospital_management.view_hospital_appointment_cash_wizard_form').id
        return {
            'name': 'Cash Payment',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.appointment',
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
            
        if self.online_paid_amount <= 0:
            self.payment_mode = 'none'
            
        if not self.patient_id and self.new_patient_name:
            self._create_patient_from_appointment()
            
        self.payment_status = 'paid'
        # Book the appointment and mark as paid
        self.write({
            'state': 'booked',
            'payment_status': 'paid',
        })
        
        return {'type': 'ir.actions.act_window_close'}
        # Open the booking success wizard
        wizard = self.env['hospital.appointment.booking.wizard'].create({
            'appointment_id': self.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appointment Booked',
            'res_model': 'hospital.appointment.booking.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }

    def action_hold_cash(self):
        """Close the wizard and save the state (Hold)."""
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}

    # PRINTING

    print_preference = fields.Selection(
        [
            ('now', 'Print Now'),
            ('later', 'Print Later'),
        ],
        string='Print Preference',
        default='now',
        required=True
    )

    receipt_printed = fields.Boolean(
        string='Receipt Printed',
        default=False,
        copy=False
    )

    token_printed = fields.Boolean(
        string='Token Printed',
        default=False,
        copy=False
    )

    # WORKFLOW

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

    # AUTOMATIC CONSULTATION FEE

    @api.depends(
        'doctor_id',
        'doctor_id.department_id',
        'doctor_id.designation_id',
        'doctor_id.consultation_line_ids',
        'doctor_id.consultation_line_ids.fee',
        'doctor_id.consultation_line_ids.consultation_type_id',
        'consultation_type_id',
    )
    def _compute_consultation_fee(self):
        Fee = self.env['hospital.consultation.fee']

        for record in self:
            record.consultation_fee = 0.0

            # Mandatory rule: If doctor or consultation type is not selected, fee must be 0.0
            if not record.doctor_id or not record.consultation_type_id:
                continue

            department = record.doctor_id.department_id
            designation = record.doctor_id.designation_id
            consultation_type = record.consultation_type_id

            # 1. Primary: Doctor-specific Consultation Type Line
            doctor_line = record.doctor_id.consultation_line_ids.filtered(
                lambda l: l.consultation_type_id.id == consultation_type.id
            )
            if doctor_line:
                record.consultation_fee = doctor_line[0].fee
                continue

            # 2. Secondary: Consultation fee master rule for Doctor + Consultation Type
            fee = Fee.search([
                ('doctor_id', '=', record.doctor_id.id),
                ('consultation_type_id', '=', consultation_type.id),
                ('active', '=', True),
            ], limit=1)

            # 3. Department standard fee for this Consultation Type
            if not fee and department and designation:
                fee = Fee.search([
                    ('department_id', '=', department.id),
                    ('designation_id', '=', designation.id),
                    ('consultation_type_id', '=', consultation_type.id),
                    ('doctor_id', '=', False),
                    ('active', '=', True),
                ], limit=1)

            if fee:
                record.consultation_fee = fee.amount
            else:
                record.consultation_fee = 0.0

    @api.onchange('doctor_id')
    def _onchange_doctor_id(self):
        self.consultation_type_id = False
        self.consultation_fee = 0.0
        self._compute_net_amount()
        if self.doctor_id and self.doctor_id.consultation_line_ids:
            return {
                'domain': {
                    'consultation_type_id': [('id', 'in', self.doctor_id.consultation_line_ids.mapped('consultation_type_id.id'))]
                }
            }
        return {
            'domain': {
                'consultation_type_id': [('id', 'in', [])]
            }
        }

    @api.onchange('consultation_type_id')
    def _onchange_consultation_type_id(self):
        self._compute_consultation_fee()
        self._compute_net_amount()

    @api.onchange('search_patient')
    def _onchange_search_patient(self):
        if self.search_patient:
            self._do_search_patient()
        elif not self.patient_found:
            self.visit_type = 'new'

    @api.onchange('new_patient_phone')
    def _onchange_new_patient_phone(self):
        if self.new_patient_phone and not self.patient_found:
            phone = self.new_patient_phone.strip()
            existing_patient = self.env['hospital.patient'].search([('phone', '=', phone)], limit=1)
            if existing_patient:
                self.patient_id = existing_patient.id
                self.patient_found = True
                self.visit_type = 'followup'
                self.new_patient_name = existing_patient.name
                self.new_patient_age = existing_patient.age
                self.new_patient_gender = existing_patient.gender
                self.new_patient_blood_group = existing_patient.blood_group
                self.new_patient_email = existing_patient.email
                self.new_patient_address = existing_patient.address
                last_appointment = self.env['hospital.appointment'].search(
                    [('patient_id', '=', existing_patient.id), ('state', '!=', 'draft'), ('id', '!=', self.id)],
                    order='appointment_date desc, id desc',
                    limit=1
                )
                if last_appointment:
                    if last_appointment.doctor_id:
                        self.doctor_id = last_appointment.doctor_id.id
                    if last_appointment.department_id:
                        self.department_id = last_appointment.department_id.id
            else:
                self.visit_type = 'new'

    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        if self.patient_id:
            self.visit_type = 'followup'
        else:
            self.visit_type = 'new'




    # COMPUTE

    @api.depends('consultation_fee', 'discount')
    def _compute_net_amount(self):
        for record in self:
            record.net_amount = max(
                record.consultation_fee - record.discount,
                0.0
            )



    # DEFAULT / CREATE

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'visit_type' in fields_list and not res.get('visit_type'):
            res['visit_type'] = 'new'
        return res

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            if vals.get('name', 'New Appointment') == 'New Appointment':

                vals['name'] = self.env[
                    'ir.sequence'
                ].next_by_code(
                    'hospital.appointment'
                ) or 'New'

        return super().create(vals_list)


    # CLEAR APPOINTMENT FORM

    def action_clear_form(self):

        self.ensure_one()

        self.write({

            # -------------------------------------------------
            # PATIENT SEARCH
            # -------------------------------------------------

            'search_patient': False,
            'patient_id': False,
            'patient_found': False,
            'visit_type': 'new',

            # -------------------------------------------------
            # NEW PATIENT DETAILS
            # -------------------------------------------------

            'new_patient_name': False,
            'new_patient_phone': False,
            'new_patient_age': False,
            'new_patient_gender': False,
            'new_patient_blood_group': False,
            'new_patient_email': False,
            'new_patient_address': False,

            # -------------------------------------------------
            # APPOINTMENT INPUT
            # -------------------------------------------------

            'doctor_id': False,
            'department_id': False,
            'consultation_type_id': False,

            # -------------------------------------------------
            # TOKEN
            # -------------------------------------------------

            'token_number': False,
            'token_generated': False,

            # -------------------------------------------------
            # PAYMENT
            # -------------------------------------------------

            'consultation_fee': 0.0,
            'discount': 0.0,
            'payment_mode': False,
            'payment_status': 'pending',
            'transaction_id': False,
        })

        return True


    def _do_search_patient(self):
        """Core search logic reused by both button and action."""
        value = (self.search_patient or '').strip()
        if not value:
            self.patient_id = False
            self.patient_found = False
            self.visit_type = 'new'
            return None

        Patient = self.env['hospital.patient']

        # SEARCH BY PATIENT ID

        patient = Patient.search(
            [('patient_id', '=ilike', value)],
            limit=1
        )

        # SEARCH BY MOBILE NUMBER

        if not patient:
            patient = Patient.search(
                [('phone', '=', value)],
                limit=1
            )

        # EXISTING PATIENT FOUND

        if patient:

            self.patient_id = patient.id
            self.patient_found = True

            # Existing patient = Follow-up
            self.visit_type = 'followup'

            # Fetch last appointment for this patient
            last_appointment = self.env['hospital.appointment'].search(
                [('patient_id', '=', patient.id), ('state', '!=', 'draft'), ('id', '!=', self.id)],
                order='appointment_date desc, id desc',
                limit=1
            )
            if last_appointment:
                if last_appointment.doctor_id:
                    self.doctor_id = last_appointment.doctor_id.id
                if last_appointment.department_id:
                    self.department_id = last_appointment.department_id.id

            self.new_patient_name = patient.name
            self.new_patient_phone = patient.phone
            self.new_patient_age = patient.age
            self.new_patient_gender = patient.gender
            self.new_patient_blood_group = patient.blood_group
            self.new_patient_email = patient.email
            self.new_patient_address = patient.address

            return None

        # PATIENT NOT FOUND
        self.patient_id = False
        self.patient_found = False
        self.visit_type = 'new'
        self.new_patient_name = False

        if value.isdigit():
            self.new_patient_phone = value
        else:
            self.new_patient_phone = False

        self.new_patient_age = False
        self.new_patient_gender = False
        self.new_patient_blood_group = False
        self.new_patient_email = False
        self.new_patient_address = False

        return None
    # CREATE PATIENT FROM APPOINTMENT

    def _create_patient_from_appointment(self):

        self.ensure_one()

        if not self.new_patient_name:

            raise UserError(
                'Please enter the patient name.'
            )

        if not self.new_patient_phone:

            raise UserError(
                'Please enter the patient mobile number.'
            )

        existing = self.env['hospital.patient'].search(
            [
                (
                    'phone',
                    '=',
                    self.new_patient_phone.strip()
                )
            ],
            limit=1
        )

        if existing:

            self.patient_id = existing.id
            self.patient_found = True
            if not self.visit_type:
                self.visit_type = 'followup'

            return existing

        patient = self.env['hospital.patient'].create({

            'name': self.new_patient_name.strip(),

            'phone': self.new_patient_phone.strip(),

            'age':
                self.new_patient_age,

            'gender':
                self.new_patient_gender,

            'blood_group':
                self.new_patient_blood_group,

            'email':
                self.new_patient_email,

            'address':
                self.new_patient_address,
        })

        self.patient_id = patient.id
        self.patient_found = True

        return patient

    # NEW APPOINTMENT

    def action_new_appointment(self):
        self.ensure_one()

        context = {
            'default_appointment_date': fields.Date.today(),
            'default_visit_type': 'new',
        }

        # If opened from an existing appointment,
        # create the new appointment for the same patient.
        if self.patient_id:
            context.update({
                'default_patient_id': self.patient_id.id,
                'default_visit_type': 'followup',
                'default_patient_found': True,
            })

        return {
            'type': 'ir.actions.act_window',
            'name': 'New Appointment',
            'res_model': 'hospital.appointment',
            'view_mode': 'form',
            'views': [
                (
                    self.env.ref(
                        'hospital_management.view_hospital_appointment_form'
                    ).id,
                    'form'
                )
            ],
            'target': 'current',
            'context': context,
        }


    # LAB APPOINTMENT

    def action_lab_appointment(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'Lab Appointment',
            'res_model': 'hospital.lab.appointment',
            'view_mode': 'form',
            'target': 'current',
        }

    # GENERATE TOKEN

    def action_generate_token(self):

        for record in self:

            # PATIENT VALIDATION

            # Existing patient
            if record.patient_id:
                pass

            # New patient
            else:

                # Patient Name
                if not record.new_patient_name or not record.new_patient_name.strip():
                    raise UserError(
                        'Please enter Patient Name.'
                    )

                # Mobile
                if not record.new_patient_phone or not record.new_patient_phone.strip():
                    raise UserError(
                        'Please enter Mobile Number.'
                    )

                # Date of Birth
                if record.new_patient_age <= 0:
                    raise UserError(
                        'Patient Age must be greater than zero!'
                    )

                # Gender
                if not record.new_patient_gender:
                    raise UserError(
                        'Please select Gender.'
                    )

                # Address
                if not record.new_patient_address or not record.new_patient_address.strip():
                    raise UserError(
                        'Please enter Address.'
                    )

                # Email is intentionally OPTIONAL
                # No validation required for new_patient_email.

                # Create patient
                record._create_patient_from_appointment()

            # APPOINTMENT VALIDATION

            # Doctor
            if not record.doctor_id:
                raise UserError(
                    'Please select a Doctor.'
                )

            # Department
            if not record.department_id:
                raise UserError(
                    'Doctor does not have a Department assigned.'
                )

            # Consultation Type
            if not record.consultation_type_id:
                raise UserError(
                    'Please select a Consultation Type.'
                )

            # Appointment Date
            if not record.appointment_date:
                raise UserError(
                    'Please select Appointment Date.'
                )

            # Appointment Time
            if record.appointment_time is False or record.appointment_time is None:
                raise UserError(
                    'Please enter Appointment Time.'
                )

            # Visit Type
            if not record.visit_type:
                raise UserError(
                    'Please select Visit Type.'
                )

            # Priority
            if not record.priority:
                raise UserError(
                    'Please select Priority.'
                )

            # Appointment Mode
            if not record.appointment_mode:
                raise UserError(
                    'Please select Appointment Mode.'
                )

            # PREVENT DUPLICATE TOKEN

            if record.token_number:
                raise UserError(
                    'Token has already been generated.'
                )

            # GENERATE TOKEN

            token = self.env[
                'ir.sequence'
            ].next_by_code(
                'hospital.appointment.token'
            )

            if not token:
                raise UserError(
                    'Appointment token sequence is not configured.'
                )

            record.write({
                'token_number': token,
                'token_generated': True,
            })

        return True
    # PATIENT HISTORY

    def action_view_patient_history(self):

        self.ensure_one()

        if not self.patient_id:

            raise UserError(
                'Please select a patient first.'
            )

        return {

            'type': 'ir.actions.act_window',

            'name': 'Patient History',

            'res_model': 'hospital.appointment',

            'view_mode': 'list,form',

            'domain': [
                (
                    'patient_id',
                    '=',
                    self.patient_id.id
                )
            ],

            'context': {
                'default_patient_id':
                    self.patient_id.id,
            },
        }

    # BOOK APPOINTMENT

    def action_book(self):
        self.ensure_one()

        # ---------------------------------------------------------
        # PATIENT REQUIRED
        # ---------------------------------------------------------
        if not self.patient_id:

            if self.new_patient_name:
                self._create_patient_from_appointment()
            else:
                raise UserError(
                    'Please search for a patient or enter '
                    'new patient details.'
                )

        # ---------------------------------------------------------
        # DOCTOR REQUIRED
        # ---------------------------------------------------------
        if not self.doctor_id:
            raise UserError(
                'Please select a doctor before booking '
                'the appointment.'
            )

        # ---------------------------------------------------------
        # CONSULTATION TYPE REQUIRED
        # ---------------------------------------------------------
        if not self.consultation_type_id:
            raise UserError(
                'Please select a Consultation Type before booking '
                'the appointment.'
            )

        # ---------------------------------------------------------
        # TOKEN REQUIRED
        # ---------------------------------------------------------
        if not self.token_generated or not self.token_number:
            raise UserError(
                'Please generate the token before '
                'booking the appointment.'
            )

        # ---------------------------------------------------------
        # ONLY DRAFT CAN BE BOOKED
        # ---------------------------------------------------------
        if self.state != 'draft':
            raise UserError(
                'This appointment has already been booked.'
            )

        # ---------------------------------------------------------
        # PAYMENT MODE REQUIRED
        # ---------------------------------------------------------
        if not self.payment_mode or (self.payment_mode == 'none' and self.total_cash_received <= 0):
            raise UserError(
                'Please select a Digital Payment Mode or click Cash to enter a cash payment before booking.'
            )

        # ---------------------------------------------------------
        # TRANSACTION ID REQUIRED FOR DIGITAL PAYMENTS
        # ---------------------------------------------------------
        if self.payment_mode not in (False, 'none') and not (self.transaction_id or '').strip():
            raise UserError(
                'Please enter the Transaction ID for %s payment.' % self.payment_mode.upper()
            )

        # ---------------------------------------------------------
        # BOOK APPOINTMENT
        # ---------------------------------------------------------
        self.write({
            'state': 'booked',
            'payment_status': 'paid',
        })

        # ---------------------------------------------------------
        # OPEN SUCCESS / PRINT DIALOG
        # ---------------------------------------------------------
        wizard = self.env[
            'hospital.appointment.booking.wizard'
        ].create({
            'appointment_id': self.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Appointment Booked',
            'res_model': 'hospital.appointment.booking.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
            'views': [
                (
                    self.env.ref(
                        'hospital_management.'
                        'view_hospital_appointment_booking_wizard'
                    ).id,
                    'form',
                )
            ],
        }

    # LAB FEES

    def action_set_lab_fees(self):

        self.ensure_one()

        # -----------------------------------------------------
        # ONLY AFTER BOOKING
        # -----------------------------------------------------

        if self.state not in ('booked', 'completed'):
            raise UserError(
                'Lab Fees can be selected only after '
                'booking the appointment.'
            )

        # -----------------------------------------------------
        # PATIENT REQUIRED
        # -----------------------------------------------------

        if not self.patient_id:
            raise UserError(
                'Please select a patient before creating '
                'a Lab Appointment.'
            )

        # -----------------------------------------------------
        # FIND EXISTING LAB APPOINTMENT
        # -----------------------------------------------------

        lab_appointment = self.env[
            'hospital.lab.appointment'
        ].search(
            [
                (
                    'hospital_appointment_id',
                    '=',
                    self.id
                )
            ],
            limit=1
        )

        # -----------------------------------------------------
        # CREATE ONLY IF IT DOES NOT EXIST
        # -----------------------------------------------------

        if not lab_appointment:

            lab_appointment = self.env[
                'hospital.lab.appointment'
            ].create(
                {
                    'patient_id': self.patient_id.id,

                    'hospital_appointment_id':
                        self.id,

                    'doctor_id':
                        self.doctor_id.id
                        if self.doctor_id
                        else False,

                    'appointment_date':
                        self.appointment_date,

                    'appointment_time':
                        self.appointment_time,

                    'priority':
                        self.priority,

                    'state':
                        'draft',

                    'payment_mode':
                        'none',

                    'payment_status':
                        'pending',
                }
            )

        # -----------------------------------------------------
        # OPEN EXISTING / NEWLY CREATED LAB APPOINTMENT
        # -----------------------------------------------------

        return {
            'type': 'ir.actions.act_window',

            'name': 'Lab Appointment',

            'res_model': 'hospital.lab.appointment',

            'res_id': lab_appointment.id,

            'view_mode': 'form',

            'views': [
                (
                    self.env.ref(
                        'hospital_management.'
                        'view_hospital_lab_appointment_form'
                    ).id,
                    'form',
                ),
            ],

            'target': 'current',


            'context': {

                # -------------------------------------------------
                # PATIENT
                # -------------------------------------------------

                'default_patient_id':
                    self.patient_id.id,

                # -------------------------------------------------
                # ORIGINAL HOSPITAL APPOINTMENT
                # -------------------------------------------------

                'default_hospital_appointment_id':
                    self.id,

                # -------------------------------------------------
                # DOCTOR
                # -------------------------------------------------

                'default_doctor_id':
                    self.doctor_id.id
                    if self.doctor_id
                    else False,

                # -------------------------------------------------
                # DATE
                # -------------------------------------------------

                'default_appointment_date':
                    self.appointment_date,

                # -------------------------------------------------
                # TIME
                # -------------------------------------------------

                'default_appointment_time':
                    self.appointment_time,

                # -------------------------------------------------
                # PRIORITY
                # -------------------------------------------------

                'default_priority':
                    self.priority,
            },
        }

    # VIEW APPOINTMENT

    def action_view_appointment(self):

        self.ensure_one()

        return {

            'type': 'ir.actions.act_window',

            'name': 'Appointment',

            'res_model': 'hospital.appointment',

            'view_mode': 'form',

            'views': [
                (
                    self.env.ref(
                        'hospital_management.'
                        'view_hospital_appointment_form'
                    ).id,
                    'form'
                )
            ],

            'res_id': self.id,

            'target': 'current',

            'context': {
                'view_only': True,
            },
        }

    # EDIT APPOINTMENT

    def action_edit_appointment(self):

        self.ensure_one()

        if self.state not in (
            'draft',
            'booked'
        ):

            raise UserError(
                'Only Draft and Booked appointments '
                'can be edited.'
            )

        return {

            'type': 'ir.actions.act_window',

            'name': 'Appointment',

            'res_model': 'hospital.appointment',

            'view_mode': 'form',

            'views': [
                (
                    self.env.ref(
                        'hospital_management.'
                        'view_hospital_appointment_form'
                    ).id,
                    'form'
                )
            ],

            'res_id': self.id,

            'target': 'current',

            'context': {
                'view_only': False,
                'is_new_booking': False,
                'is_editing': True,
            },
        }

    # PRINT RECEIPT

    def action_dummy(self):
        pass

    def action_print_receipt(self):

        self.ensure_one()

        if self.state not in ['booked', 'completed']:
            return

        self.receipt_printed = True

        return self.env.ref(
            'hospital_management.action_report_hospital_appointment_token'
        ).report_action(self)

    def action_save_appointment(self):
        """Save the appointment and keep the user on the current form without redirecting."""
        self.ensure_one()
        if not self.patient_id and self.new_patient_name and self.new_patient_phone:
            self._create_patient_from_appointment()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Saved',
                'message': 'Appointment saved successfully!',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_close_form(self):
        """Navigate back to the appointment list view."""
        return self.env['ir.actions.act_window']._for_xml_id('hospital_management.action_hospital_appointment')

    # OPEN LAB TESTS

    def action_open_lab_test(self):
        self.ensure_one()
        lab_appointment = self.env['hospital.lab.appointment'].search(
            [('hospital_appointment_id', '=', self.id)],
            limit=1
        )

        if not lab_appointment:
            if not self.patient_id:
                raise UserError('Please select a patient before opening Lab Tests.')

            # Check if doctor already created a draft lab appointment without an appointment ID
            lab_appointment = self.env['hospital.lab.appointment'].search([
                ('patient_id', '=', self.patient_id.id),
                ('state', '=', 'draft'),
                ('hospital_appointment_id', '=', False)
            ], limit=1)
            
            if lab_appointment:
                lab_appointment.write({
                    'hospital_appointment_id': self.id,
                    'doctor_id': self.doctor_id.id if self.doctor_id else lab_appointment.doctor_id.id,
                })
            else:
                lab_appointment = self.env['hospital.lab.appointment'].create({
                    'patient_id': self.patient_id.id,
                    'hospital_appointment_id': self.id,
                    'doctor_id': self.doctor_id.id if self.doctor_id else False,
                    'appointment_date': self.appointment_date,
                    'appointment_time': self.appointment_time,
                    'priority': self.priority,
                    'state': 'draft',
                    'payment_mode': 'none',
                    'payment_status': 'pending',
                })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Lab Tests',
            'res_model': 'hospital.lab.appointment',
            'res_id': lab_appointment.id,
            'view_mode': 'form',
            'views': [(
                self.env.ref(
                    'hospital_management.view_hospital_lab_appointment_form'
                ).id,
                'form',
            )],
            'target': 'current',
            'context': {
                'default_hospital_appointment_id': self.id,
                'default_patient_id': self.patient_id.id if self.patient_id else False,
                'default_doctor_id': self.doctor_id.id if self.doctor_id else False,
                'default_appointment_date': self.appointment_date,
                'default_appointment_time': self.appointment_time,
                'default_priority': self.priority,
            },
        }

    # PRINT TOKEN

    def action_print_token(self):

        self.ensure_one()

        if not self.token_number:

            raise UserError(
                'Please generate the token first.'
            )

        self.token_printed = True

        return self.env.ref(
            'hospital_management.action_report_hospital_appointment_receipt'
        ).report_action(self)

    # COMPLETE APPOINTMENT
    # PHARMACIST ONLY

    def action_complete(self):

        # Server-side security check.
        #
        # This is intentionally NOT exposed as a button
        # on the Appointment form.
        #
        # Pharmacy can call this action from the pharmacy
        # workflow.

        if not self.env.user.has_group(
            'hospital_management.group_hospital_pharmacist'
        ):

            raise AccessError(
                'Only Pharmacy users can complete '
                'a booked appointment.'
            )

        for record in self:

            if record.state != 'booked':
                continue

            record.state = 'completed'

        return True

    # CANCEL

    def action_cancel(self):

        for record in self:

            if record.state in (
                'draft',
                'booked'
            ):

                record.state = 'cancelled'

        return True

    # RESET TO DRAFT

    def action_reset_to_draft(self):

        for record in self:

            if record.state == 'cancelled':

                record.state = 'draft'

                record.token_number = False

                record.token_generated = False

        return True

    # PRINT LATER

    def action_print_later(self):

        self.ensure_one()

        if self.state != 'booked':

            raise UserError(
                'Please book the appointment before '
                'selecting Print Later.'
            )

        self.print_preference = 'later'

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    def action_search_patient(self):
        self.ensure_one()
        self._do_search_patient()
        return True


