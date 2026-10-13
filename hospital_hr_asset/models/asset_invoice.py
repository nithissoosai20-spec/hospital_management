from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HospitalAssetInvoice(models.Model):
    _name = 'hospital.asset.invoice'
    _description = 'Asset Invoice'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    purchase_id = fields.Many2one('hospital.asset.po', string='Purchase Order', required=True)
    vendor_id = fields.Many2one('res.partner', related='purchase_id.vendor_id', string='Vendor', store=True)
    
    amount = fields.Float(string='Total Amount', default=0.0)
    paid_amount = fields.Float(string='Amount Paid', default=0.0)
    current_payment_amount = fields.Float(string='Current Payment', default=0.0)
    balance_amount = fields.Float(string='Balance Due', compute='_compute_balance', store=True)
    notes = fields.Text(string='Adjustment Notes')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid')
    ], string='Status', default='draft')
    payment_date = fields.Date(string='Last Payment Date')
    payment_ids = fields.One2many('hospital.asset.invoice.payment', 'invoice_id', string='Payment History')

    @api.depends('amount', 'paid_amount')
    def _compute_balance(self):
        for rec in self:
            rec.balance_amount = rec.amount - rec.paid_amount

    def action_pay(self):
        for rec in self:
            if rec.name == 'New':
                rec.name = self.env['ir.sequence'].next_by_code('hospital.asset.invoice.seq') or 'New'
            
            if rec.current_payment_amount > 0:
                if rec.current_payment_amount > rec.balance_amount:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Overpayment Error',
                            'message': f'You cannot pay more than the pending balance of {rec.balance_amount}',
                            'type': 'danger',
                            'sticky': False,
                        }
                    }
                    
                new_balance = rec.amount - (rec.paid_amount + rec.current_payment_amount)
                # Create history record
                self.env['hospital.asset.invoice.payment'].create({
                    'invoice_id': rec.id,
                    'amount': rec.current_payment_amount,
                    'date': fields.Datetime.now(),
                    'remaining_balance': new_balance if new_balance > 0 else 0.0
                })
                
                rec.paid_amount += rec.current_payment_amount
                rec.current_payment_amount = 0.0
                rec.payment_date = fields.Date.today()

            if rec.paid_amount >= rec.amount:
                rec.state = 'paid'
            elif rec.paid_amount > 0:
                rec.state = 'partial'
            else:
                rec.state = 'draft'
                
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Payment processed successfully!',
                'type': 'rainbow_man',
            },
            'type': 'ir.actions.act_window',
            'name': 'Vendor Bills',
            'res_model': 'hospital.asset.invoice',
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'target': 'current'
        }

    def action_close(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Bills',
            'res_model': 'hospital.asset.invoice',
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'target': 'current'
        }

class HospitalAssetInvoicePayment(models.Model):
    _name = 'hospital.asset.invoice.payment'
    _description = 'Asset Invoice Payment History'
    _order = 'date desc'

    invoice_id = fields.Many2one('hospital.asset.invoice', string='Invoice', ondelete='cascade')
    amount = fields.Float(string='Paid Amount', required=True)
    date = fields.Datetime(string='Date & Time', required=True, default=fields.Datetime.now)
    remaining_balance = fields.Float(string='Remaining Balance')

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
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Payment registered successfully!',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

    def action_clear(self):
        self.amount_to_pay = 0.0
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.asset.payment.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new'
        }

