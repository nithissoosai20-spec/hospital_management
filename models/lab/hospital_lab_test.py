from odoo import models, fields


class HospitalLabTest(models.Model):
    _name = 'hospital.lab.test'
    _description = 'Hospital Lab Test Master'
    _order = 'name'

    name = fields.Char(
        string='Test Name',
        required=True
    )

    code = fields.Char(
        string='Test Code',
        required=True
    )

    category = fields.Selection(
        [
            ('hematology', 'Hematology'),
            ('biochemistry', 'Biochemistry'),
            ('microbiology', 'Microbiology'),
            ('pathology', 'Pathology'),
            ('radiology', 'Radiology'),
            ('cardiology', 'Cardiology'),
            ('other', 'Other'),
        ],
        string='Category',
        required=True,
        default='other'
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

    price = fields.Float(
        string='Price',
        required=True,
        default=0.0
    )

    turnaround_time = fields.Char(
        string='Turnaround Time'
    )

    active = fields.Boolean(
        string='Active',
        default=True
    )

    notes = fields.Text(
        string='Notes'
    )