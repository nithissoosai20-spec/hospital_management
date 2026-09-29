from odoo import models, fields, api


class HospitalPatient(models.Model):
    _name = 'hospital.patient'
    _description = 'Hospital Patient'
    _order = 'id desc'

    name = fields.Char(
        string='Full Name',
        required=True
    )


    last_appointment_time = fields.Datetime(
        string='Last Appointment Time',
        compute='_compute_last_appointment_time',
        store=True
    )

    @api.depends('appointment_ids', 'appointment_ids.create_date')
    def _compute_last_appointment_time(self):
        for rec in self:
            if rec.appointment_ids:
                # get the max create_date from appointments
                dates = rec.appointment_ids.mapped('create_date')
                dates = [d for d in dates if d]
                rec.last_appointment_time = max(dates) if dates else False
            else:
                rec.last_appointment_time = False

    patient_id = fields.Char(
        string='Patient ID',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )

    age = fields.Integer(string='Age')

    gender = fields.Selection(
        [
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        string='Gender'
    )

    phone = fields.Char(
        string='Phone'
    )

    email = fields.Char(
        string='Email'
    )

    blood_group = fields.Selection(
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

    address = fields.Text(
        string='Address'
    )

    active = fields.Boolean(
        string='Active',
        default=True
    )

    prescription_ids = fields.One2many(
        'hospital.prescription',
        'patient_id',
        string='Prescriptions'
    )
    lab_appointment_ids = fields.One2many(
        'hospital.lab.appointment',
        'patient_id',
        string='Lab Tests'
    )

    current_prescription_line_ids = fields.Many2many(
        'hospital.prescription.line',
        compute='_compute_current_prescriptions',
        string='Current Medicines'
    )

    current_lab_line_ids = fields.Many2many(
        'hospital.lab.appointment.line',
        compute='_compute_current_labs',
        string='Current Lab Tests'
    )

    @api.depends('prescription_ids', 'prescription_ids.line_ids')
    def _compute_current_prescriptions(self):
        today = fields.Date.context_today(self)
        for rec in self:
            lines = rec.prescription_ids.filtered(
                lambda p: p.date_prescribed and p.date_prescribed.date() == today
            ).mapped('line_ids')
            rec.current_prescription_line_ids = lines

    @api.depends('lab_appointment_ids', 'lab_appointment_ids.line_ids')
    def _compute_current_labs(self):
        today = fields.Date.context_today(self)
        for rec in self:
            lines = rec.lab_appointment_ids.filtered(
                lambda l: l.appointment_date == today
            ).mapped('line_ids')
            rec.current_lab_line_ids = lines.filtered(lambda l: not l.is_parameter)

    appointment_ids = fields.One2many(
        'hospital.appointment',
        'patient_id',
        string='Appointment History',
        readonly=True,
    )



    def action_prescribe_medicine(self):
        self.ensure_one()
        return {
            'name': 'Prescribe Medicines',
            'type': 'ir.actions.act_window',
            'res_model': 'patient.medicine.prescription.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_patient_id': self.id}
        }

    def action_prescribe_lab_test(self):
        self.ensure_one()
        return {
            'name': 'Select Lab Tests',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.lab.test.selector',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_patient_id': self.id}
        }

    all_prescription_line_ids = fields.Many2many(
        'hospital.prescription.line',
        compute='_compute_all_history_lines',
        string='All Medicines History'
    )

    all_lab_line_ids = fields.Many2many(
        'hospital.lab.appointment.line',
        compute='_compute_all_history_lines',
        string='All Lab Tests History'
    )

    def _compute_all_history_lines(self):
        for rec in self:
            rec.all_prescription_line_ids = rec.prescription_ids.mapped('line_ids')
            rec.all_lab_line_ids = rec.lab_appointment_ids.mapped('line_ids')

    def action_view_appointments(self):
        self.ensure_one()
        view_id = self.env.ref('hospital_management.view_hospital_patient_history_form').id
        return {
            'name': f'Clinical History - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.patient',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'context': {'create': False, 'edit': False}
        }


    suggestions_before_test = fields.Text(string='Suggestions Before Test')
    suggestions_after_test = fields.Text(string='Suggestions After Test')
    
    appointment_count = fields.Integer(string='Appointment Count', compute='_compute_appointment_count')


    def _compute_appointment_count(self):
        for rec in self:
            rec.appointment_count = len(rec.appointment_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('patient_id', 'New') == 'New':
                vals['patient_id'] = self.env['ir.sequence'].next_by_code(
                    'hospital.patient'
                ) or 'New'

        return super().create(vals_list)

    def action_complete_doctor_appointment(self):
        self.ensure_one()
        appointments = self.env['hospital.appointment'].search([
            ('patient_id', '=', self.id),
            ('doctor_id.odoo_user_id', '=', self.env.uid),
            ('state', 'in', ['draft', 'booked'])
        ])
        if appointments:
            appointments.write({'state': 'completed'})
            
        return self.action_close_patient()

    def action_close_patient(self):
        if self.env.user.has_group('hospital_management.group_hospital_doctor'):
            action = self.env['ir.actions.act_window']._for_xml_id('hospital_management.action_hospital_doctor_patients_queue')
        else:
            action = self.env['ir.actions.act_window']._for_xml_id('hospital_management.action_hospital_patient')
        action['target'] = 'main'
        return action
