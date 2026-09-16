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

    is_profile = fields.Boolean(
        string='Is a Profile/Package',
        default=False
    )

    parameter_ids = fields.Many2many(
        'hospital.lab.test',
        'hospital_lab_test_parameter_rel',
        'profile_id',
        'parameter_id',
        string='Test Parameters',
        domain="[('is_profile', '=', False)]"
    )

    normal_range_min = fields.Float(
        string='Min Value',
        default=0.0
    )

    normal_range_max = fields.Float(
        string='Max Value',
        default=0.0
    )

    unit = fields.Char(
        string='Unit'
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

    def action_save(self):
        # Implicitly saves in Odoo.
        pass

    def action_clear(self):
        for rec in self:
            rec.name = False
            rec.code = False
            rec.category = False
            rec.sample_type = False
            rec.price = 0.0
            rec.turnaround_time = False
            rec.notes = False
            rec.active = True

    def action_close(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lab Fees',
            'res_model': 'hospital.lab.test',
            'view_mode': 'list,form',
            'target': 'current',
        }