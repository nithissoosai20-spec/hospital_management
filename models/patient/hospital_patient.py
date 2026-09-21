from odoo import models, fields, api


class HospitalPatient(models.Model):
    _name = 'hospital.patient'
    _description = 'Hospital Patient'
    _order = 'id desc'

    name = fields.Char(
        string='Full Name',
        required=True
    )

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

    def action_view_appointments(self):
        self.ensure_one()
        return {
            'name': 'Appointments',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.appointment',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id}
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
        # Find active appointments for this patient and this doctor
        appointments = self.env['hospital.appointment'].search([
            ('patient_id', '=', self.id),
            ('doctor_id.odoo_user_id', '=', self.env.uid),
            ('state', 'in', ['draft', 'booked'])
        ])
        if appointments:
            appointments.write({'state': 'completed'})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': 'Appointment marked as completed.',
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'}
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Info',
                    'message': 'No pending appointments found for you and this patient.',
                    'type': 'warning',
                    'sticky': False,
                }
            }
