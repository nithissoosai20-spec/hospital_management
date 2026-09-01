from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_pharmacy_vendor = fields.Boolean(string="Is Pharmacy Vendor", default=False)
