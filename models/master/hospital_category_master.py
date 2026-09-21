from odoo import models, fields, api

class HospitalCategoryMaster(models.Model):
    _name = 'hospital.category.master'
    _description = 'Master Category Configuration'
    _order = 'category_type, name'

    name = fields.Char(string='Category Name', required=True)
    category_type = fields.Selection([
        ('pharmacy_category', 'Pharmacy Category'),
        ('pharmacy_item_category', 'Pharmacy Item Category'),
        ('lab_category', 'Lab Category'),
        ('lab_sub_category', 'Lab Sub Category')
    ], string='Module / Type', required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_type_uniq', 'unique (name, category_type)', 'The category name must be unique per type!')
    ]

    def action_save_and_close(self):
        self.ensure_one()
        action = self.env.ref('hospital_management.action_hospital_category_master').read()[0]
        action['target'] = 'main'
        return action

    def action_go_back(self):
        # We don't want to save if they clicked close, but object buttons save.
        # So we just return the action
        action = self.env.ref('hospital_management.action_hospital_category_master').read()[0]
        action['target'] = 'main'
        return action
