from odoo import api, fields, models, _

class HospitalAssetInvoice(models.Model):
    _name = 'hospital.asset.invoice'
    _description = 'Asset Invoice'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    purchase_id = fields.Many2one('hospital.asset.purchase', string='Purchase Order', required=True)
    vendor_id = fields.Many2one('res.partner', related='purchase_id.vendor_id', string='Vendor', store=True)
    amount = fields.Float(related='purchase_id.total_amount', string='Amount', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid')
    ], string='Status', default='draft')
    payment_date = fields.Date(string='Payment Date')

    def action_pay(self):
        for rec in self:
            if rec.name == 'New':
                rec.name = self.env['ir.sequence'].next_by_code('hospital.asset.invoice.seq') or 'New'
            rec.state = 'paid'
            rec.payment_date = fields.Date.today()
