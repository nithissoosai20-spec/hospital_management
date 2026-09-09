from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_pharmacy_vendor = fields.Boolean(string="Is Pharmacy Vendor", default=False)

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, order=None):
        """Override so that when searching with is_pharmacy_vendor domain,
        we still show the Create option by not restricting the name search itself."""
        return super()._name_search(name=name, domain=domain, operator=operator, limit=limit, order=order)

    @api.model
    def name_create(self, name):
        """When quick-creating a vendor (typing name + pressing Enter or clicking Create),
        auto-set is_pharmacy_vendor = True so the new vendor appears in future filtered searches."""
        if self.env.context.get('default_is_pharmacy_vendor'):
            record = self.create({
                'name': name,
                'is_pharmacy_vendor': True,
                'supplier_rank': self.env.context.get('default_supplier_rank', 1),
            })
            return record.id, record.display_name
        return super().name_create(name)
