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

    date_of_birth = fields.Date(
        string='Date of Birth'
    )

    age = fields.Integer(
        string='Age',
        compute='_compute_age'
    )

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

    @api.depends('date_of_birth')
    def _compute_age(self):
        today = fields.Date.today()

        for record in self:
            if record.date_of_birth:
                birth_date = record.date_of_birth

                age = today.year - birth_date.year

                if (today.month, today.day) < (
                    birth_date.month,
                    birth_date.day
                ):
                    age -= 1

                record.age = age
            else:
                record.age = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('patient_id', 'New') == 'New':
                vals['patient_id'] = self.env['ir.sequence'].next_by_code(
                    'hospital.patient'
                ) or 'New'

        return super().create(vals_list)