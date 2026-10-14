from odoo import api, fields, models, _
from datetime import datetime

class HospitalPharmacyPayment(models.Model):
    _name = 'hospital.pharmacy.payment'
    _description = 'Pharmacy Vendor Payment'
    _order = 'date desc, id desc'

    name = fields.Char(string='Payment Reference', required=True, copy=False, readonly=True, default='New Payment')
    order_type = fields.Selection([
        ('pharmacy', 'Pharmacy'),
        ('asset', 'Asset'),
    ], string='Order Type', default='pharmacy', required=True, index=True)
    vendor_id = fields.Many2one('res.partner', string='Vendor', domain="['|', ('is_pharmacy_vendor', '=', True), ('supplier_rank', '>', 0)]", required=True)
    invoice_id = fields.Many2one('hospital.pharmacy.purchase.invoice', string='Purchase Invoice', domain="[('supplier_id', '=', vendor_id)]")
    
    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        if self.invoice_id and self.invoice_id.order_type:
            self.order_type = self.invoice_id.order_type
    
    invoice_total = fields.Float(string='Invoice Total', related='invoice_id.total_amount', store=True)
    invoice_balance = fields.Float(string='Pending Balance', related='invoice_id.balance_amount', store=True)
    invoice_status = fields.Selection(string='Invoice Status', related='invoice_id.status', store=True)
    invoice_paid_amount = fields.Float(string='Already Paid', related='invoice_id.paid_amount', store=True)

    
    date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True)
    amount = fields.Float(string='Payment Amount', required=True)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('cheque', 'Cheque')
    ], string='Payment Method', default='cash', required=True)
    
    reference = fields.Char(string='Transaction Reference')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], string='Status', default='draft', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New Payment') == 'New Payment':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.pharmacy.payment') or 'New'
        return super().create(vals_list)

    def action_confirm(self):
        for rec in self:
            rec.state = 'done'
        return {'type': 'ir.actions.client', 'tag': 'reload'}
            
    def action_draft(self):
        for rec in self:
            rec.state = 'draft'
