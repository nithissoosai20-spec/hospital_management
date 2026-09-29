from odoo import models, fields

class HospitalLabSubtest(models.Model):
    _name = 'hospital.lab.subtest'
    _description = 'Lab Sub-Test'

    name = fields.Char(string='Sub-Test Name', required=True)
    lab_test_id = fields.Many2one('hospital.lab.test', string='Main Test', required=True)
    category_id = fields.Many2one('hospital.category.master', related='lab_test_id.lab_category_id', string='Category', store=True)
    unit = fields.Char(string='Units')
    normal_range_display = fields.Char(string='Normal Range')
    package_id = fields.Many2one('hospital.lab.test', string='Package', domain="[('lab_category_id.name', '=', 'PACKAGES')]")
    normal_range_min = fields.Float(string='Min Range')
    normal_range_max = fields.Float(string='Max Range')

    def action_save_close(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lab Sub-Tests',
            'res_model': 'hospital.lab.subtest',
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_cancel(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lab Sub-Tests',
            'res_model': 'hospital.lab.subtest',
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_close(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lab Sub-Tests',
            'res_model': 'hospital.lab.subtest',
            'view_mode': 'list,form',
            'target': 'current',
        }
