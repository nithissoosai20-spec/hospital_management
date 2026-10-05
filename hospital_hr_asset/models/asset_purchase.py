from odoo import api, fields, models, _

class HospitalAssetPurchase(models.Model):
    _name = 'hospital.asset.purchase'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Asset Purchase'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    state = fields.Selection([
        ('intent', 'Intent'),
        ('po', 'Purchase Order'),
        ('received', 'Received'),
        ('cancel', 'Cancelled')
    ], string='Status', default='intent', tracking=True)
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    date_order = fields.Datetime(string='Order Date', default=fields.Datetime.now)
    line_ids = fields.One2many('hospital.asset.purchase.line', 'purchase_id', string='Lines')
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)
    invoice_id = fields.Many2one('hospital.asset.invoice', string='Invoice', copy=False)

    def action_create_bill(self):
        for rec in self:
            if not rec.invoice_id:
                invoice = self.env['hospital.asset.invoice'].with_context(default_state='draft').create({
                    'purchase_id': rec.id,
                })
                rec.invoice_id = invoice.id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Bill',
            'res_model': 'hospital.asset.invoice',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


    @api.depends('line_ids.subtotal')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = sum(rec.line_ids.mapped('subtotal'))

    def action_confirm_po(self):
        for rec in self:
            if rec.name == 'New':
                rec.name = self.env['ir.sequence'].next_by_code('hospital.asset.purchase.seq') or 'New'
            rec.state = 'po'

    def action_receive(self):
        for rec in self:
            for line in rec.line_ids:
                for _ in range(line.qty):
                    self.env['maintenance.equipment'].create({
                        'name': line.name,
                        'category_id': line.category_id.id,
                    })
            rec.state = 'received'

class HospitalAssetPurchaseLine(models.Model):
    _name = 'hospital.asset.purchase.line'
    _description = 'Asset Purchase Line'

    purchase_id = fields.Many2one('hospital.asset.purchase', string='Purchase Reference', required=True, ondelete='cascade')
    category_id = fields.Many2one('maintenance.equipment.category', string='Asset Category', required=True)
    name = fields.Char(string='Description', required=True)
    qty = fields.Integer(string='Quantity', default=1, required=True)
    price_unit = fields.Float(string='Unit Price', required=True)
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)

    @api.depends('qty', 'price_unit')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.qty * rec.price_unit
