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
        default='New'
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
        string='Patient Name'
    )

    new_patient_phone = fields.Char(
        string='Mobile Number'
    )

    new_patient_date_of_birth = fields.Date(
        string='Date of Birth'
    )

    new_patient_gender = fields.Selection(
        [
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        string='Gender'
    )

    new_patient_blood_group = fields.Selection(
        [
            ('a+', 'A+'),
            ('a-', 'A-'),
            ('b+', 'B+'),
            ('b-', 'B-'),
            ('ab+', 'AB+'),
            ('ab-', 'AB-'),
            ('o+', 'O+'),
            ('o-', 'O-'),
        ],
        string='Blood Group'
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

    appointment_time = fields.Float(
        string='Appointment Time',
        required=True,
        default=lambda self: (
            fields.Datetime.now().hour
            + fields.Datetime.now().minute / 60.0
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
        ],
        string='Payment Status',
        default='pending'
    )

    transaction_id = fields.Char(
        string='Transaction ID',
        copy=False
    )

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
    )
    def _compute_consultation_fee(self):

        Fee = self.env['hospital.consultation.fee']

        for record in self:

            record.consultation_fee = 0.0

            if not record.doctor_id:
                continue

            department = record.doctor_id.department_id
            designation = record.doctor_id.designation_id

            if not department or not designation:
                continue

            fee = Fee.search(
                [
                    ('department_id', '=', department.id),
                    ('designation_id', '=', designation.id),
                    ('active', '=', True),
                ],
                limit=1,
            )

            if fee:
                record.consultation_fee = fee.amount

      
    

    # COMPUTE

    @api.depends('consultation_fee', 'discount')
    def _compute_net_amount(self):
        for record in self:
            record.net_amount = max(
                record.consultation_fee - record.discount,
                0.0
            )


    
    # CREATE

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            if vals.get('name', 'New') == 'New':

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

            # -------------------------------------------------
            # NEW PATIENT DETAILS
            # -------------------------------------------------

            'new_patient_name': False,
            'new_patient_phone': False,
            'new_patient_date_of_birth': False,
            'new_patient_gender': False,
            'new_patient_blood_group': False,
            'new_patient_email': False,
            'new_patient_address': False,

            # -------------------------------------------------
            # APPOINTMENT INPUT
            # -------------------------------------------------

            'doctor_id': False,
            'department_id': False,

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
    

    def action_search_patient(self):

        self.ensure_one()

        value = (self.search_patient or '').strip()

        if not value:
            raise UserError(
                'Please enter Patient ID or Mobile Number.'
            )

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

            # -------------------------------------------------
            # FILL VISIBLE PATIENT DETAILS
            # -------------------------------------------------

            self.new_patient_name = patient.name
            self.new_patient_phone = patient.phone
            self.new_patient_date_of_birth = patient.date_of_birth
            self.new_patient_gender = patient.gender
            self.new_patient_blood_group = patient.blood_group
            self.new_patient_email = patient.email
            self.new_patient_address = patient.address

            return True

        # PATIENT NOT FOUND

        self.patient_id = False
        self.patient_found = False

        # New patient = New Visit
        self.visit_type = 'new'

        # Clear patient entry fields
        self.new_patient_name = False
        self.new_patient_phone = False
        self.new_patient_date_of_birth = False
        self.new_patient_gender = False
        self.new_patient_blood_group = False
        self.new_patient_email = False
        self.new_patient_address = False

        return True
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
            self.visit_type = 'followup'

            return existing

        patient = self.env['hospital.patient'].create({

            'name': self.new_patient_name.strip(),

            'phone': self.new_patient_phone.strip(),

            'date_of_birth':
                self.new_patient_date_of_birth,

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
                if not record.new_patient_date_of_birth:
                    raise UserError(
                        'Please enter Date of Birth.'
                    )

                # Gender
                if not record.new_patient_gender:
                    raise UserError(
                        'Please select Gender.'
                    )

                # Blood Group
                if not record.new_patient_blood_group:
                    raise UserError(
                        'Please select Blood Group.'
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
        # BOOK APPOINTMENT
        # ---------------------------------------------------------
        self.write({
            'state': 'booked',
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

        if self.state != 'booked':
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
                        'cash',

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
            'hospital_management.action_report_hospital_appointment_receipt'
        ).report_action(self)

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

            lab_appointment = self.env['hospital.lab.appointment'].create({
                'patient_id': self.patient_id.id,
                'hospital_appointment_id': self.id,
                'doctor_id': self.doctor_id.id if self.doctor_id else False,
                'appointment_date': self.appointment_date,
                'appointment_time': self.appointment_time,
                'priority': self.priority,
                'state': 'draft',
                'payment_mode': 'cash',
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
            'hospital_management.'
            'action_report_hospital_appointment_token'
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