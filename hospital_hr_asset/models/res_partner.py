from odoo import api, models
from odoo.fields import Domain


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, order=None):
        if self.env.context.get('res_partner_search_mode') == 'supplier':
            domain = Domain(domain or []) & Domain([('supplier_rank', '>', 0)])
        return super()._name_search(name, domain=domain, operator=operator, limit=limit, order=order)
