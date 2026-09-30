from odoo import models, fields, api


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
            ('cardiology', 'Cardiology'),
            ('other', 'Other Testing'),
        ],
        string='Old Category',
        default='other'
    )

    sample_type = fields.Selection(
        [
            ('blood', 'Blood Testing'),
            ('urine', 'Urine Testing'),
            ('serum', 'Serum Testing'),
            ('other', 'Other Testing'),
        ],
        string='Old Sub Category',
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

    lab_category_id = fields.Many2one(
        'hospital.category.master',
        string='Category',
        domain="[('category_type', '=', 'lab_category')]",
        compute='_compute_lab_category_id',
        store=True,
        readonly=False
    )
    
    @api.depends('category')
    def _compute_lab_category_id(self):
        for rec in self:
            if rec.category and not rec.lab_category_id:
                master = self.env['hospital.category.master'].search([
                    ('name', 'ilike', rec.category), 
                    ('category_type', '=', 'lab_category')
                ], limit=1)
                rec.lab_category_id = master.id

    lab_sub_category_id = fields.Many2one(
        'hospital.category.master',
        string='Sub Category',
        domain="[('category_type', '=', 'lab_sub_category')]",
        compute='_compute_lab_sub_category_id',
        store=True,
        readonly=False
    )
    
    @api.depends('sample_type')
    def _compute_lab_sub_category_id(self):
        for rec in self:
            if rec.sample_type and not rec.lab_sub_category_id:
                name_map = {'blood': 'Blood', 'urine': 'Urine', 'serum': 'Serum', 'other': 'Other'}
                search_name = name_map.get(rec.sample_type, rec.sample_type)
                master = self.env['hospital.category.master'].search([
                    ('name', 'ilike', search_name), 
                    ('category_type', '=', 'lab_sub_category')
                ], limit=1)
                rec.lab_sub_category_id = master.id
                

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