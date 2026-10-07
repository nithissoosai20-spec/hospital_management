from odoo import api, fields, models, _

class HospitalAssetInvoice(models.Model):
    _name = 'hospital.asset.invoice'
    _description = 'Asset Invoice'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    purchase_id = fields.Many2one('hospital.asset.po', string='Purchase Order', required=True)
    vendor_id = fields.Many2one('res.partner', related='purchase_id.vendor_id', string='Vendor', store=True)
    
    amount = fields.Float(string='Total Amount', default=0.0)
    paid_amount = fields.Float(string='Amount Paid', default=0.0)
    balance_amount = fields.Float(string='Balance Due', compute='_compute_balance', store=True)
    notes = fields.Text(string='Adjustment Notes')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid')
    ], string='Status', default='draft')
    payment_date = fields.Date(string='Last Payment Date')

    @api.depends('amount', 'paid_amount')
    def _compute_balance(self):
        for rec in self:
            rec.balance_amount = rec.amount - rec.paid_amount

    def action_register_payment(self):
        self.ensure_one()
        return {
            'name': 'Register Payment',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.asset.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoice_id': self.id,
                'default_amount_to_pay': self.balance_amount
            }
        }

class HospitalAssetPaymentWizard(models.TransientModel):
    _name = 'hospital.asset.payment.wizard'
    _description = 'Asset Payment Wizard'

    invoice_id = fields.Many2one('hospital.asset.invoice', string='Invoice', required=True)
    amount_to_pay = fields.Float(string='Payment Amount', required=True)

    def action_save(self):
        self.ensure_one()
        if self.invoice_id.name == 'New':
            self.invoice_id.name = self.env['ir.sequence'].next_by_code('hospital.asset.invoice.seq') or 'New'
            
        self.invoice_id.paid_amount += self.amount_to_pay
        self.invoice_id.payment_date = fields.Date.today()
        
        if self.invoice_id.paid_amount >= self.invoice_id.amount:
            self.invoice_id.state = 'paid'
        else:
            self.invoice_id.state = 'partial'

    def action_clear(self):
        self.amount_to_pay = 0.0
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.asset.payment.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new'
        }

