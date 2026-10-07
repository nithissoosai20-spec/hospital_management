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
        ('asset_category', 'Item Category'),
        
    ], string='Module / Type', required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_type_uniq', 'unique (name, category_type)', 'The category name must be unique per type!')
    ]

    pharmacy_category_type = fields.Selection([
        ('pharmacy_category', 'Pharmacy Category'),
        ('pharmacy_item_category', 'Pharmacy Item Category')
    ], string='Module / Type', compute='_compute_pharmacy_type', inverse='_inverse_pharmacy_type')

    @api.depends('category_type')
    def _compute_pharmacy_type(self):
        for rec in self:
            if rec.category_type in ['pharmacy_category', 'pharmacy_item_category']:
                rec.pharmacy_category_type = rec.category_type
            else:
                rec.pharmacy_category_type = False

    def _inverse_pharmacy_type(self):
        for rec in self:
            if rec.pharmacy_category_type:
                rec.category_type = rec.pharmacy_category_type

    def action_save_and_close(self):
        self.ensure_one()
        if self.env.context.get('pharmacy_view'):
            action = self.env.ref('hospital_management.action_hospital_pharmacy_category').sudo().read()[0]
        else:
            action = self.env.ref('hospital_management.action_hospital_category_master').sudo().read()[0]
        action['target'] = 'main'
        return action

    def action_go_back(self):
        if self.env.context.get('pharmacy_view'):
            action = self.env.ref('hospital_management.action_hospital_pharmacy_category').sudo().read()[0]
        else:
            action = self.env.ref('hospital_management.action_hospital_category_master').sudo().read()[0]
        action['target'] = 'main'
        return action
