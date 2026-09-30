from odoo import models, fields, api

class HospitalPharmacyPurchaseInvoice(models.Model):
    _name = 'hospital.pharmacy.purchase.invoice'
    _description = 'Purchase Invoice'
    _order = 'id desc'

    name = fields.Char(string='Invoice No.', required=True, copy=False, readonly=True, default='New Purchase Invoice')
    purchase_id = fields.Many2one('hospital.pharmacy.purchase', string='Purchase Order', readonly=True)
    
    supplier_id = fields.Many2one('res.partner', string='Supplier Name', required=True, domain="[('is_pharmacy_vendor', '=', True)]")
    invoice_date = fields.Date(string='Invoice Date', default=fields.Date.context_today, required=True)
    
    @api.onchange('purchase_id')
    def _onchange_purchase_id(self):
        if self.purchase_id and self.purchase_id.supplier_id:
            self.supplier_id = self.purchase_id.supplier_id
    
    # Lines
    line_ids = fields.One2many('hospital.pharmacy.purchase.invoice.line', 'invoice_id', string='Items')
    total_items = fields.Integer(string='Total Items', compute='_compute_totals', store=True)

    # Payment Details
    taxable_amount = fields.Float(string='Taxable Amount', compute='_compute_totals', store=True, readonly=False)
    discount_amount = fields.Float(string='Discount Amount', default=0.0)
    gst_amount = fields.Float(string='GST Amount', compute='_compute_totals', store=True, readonly=False)
    other_charges = fields.Float(string='Other Charges')
    round_off = fields.Float(string='Round Off')
    
    total_amount = fields.Float(string='Total Amount', compute='_compute_totals', store=True, readonly=False)
    payment_ids = fields.One2many('hospital.pharmacy.payment', 'invoice_id', string='Payments')
    paid_amount = fields.Float(string='Paid Amount', compute='_compute_paid_amount', store=True)
    balance_amount = fields.Float(string='Balance Amount', compute='_compute_totals', store=True, readonly=False)
    
    reference_no = fields.Char(string='Reference No.')
    
    # Additional Info
    remarks = fields.Text(string='Remarks')
    attachment = fields.Binary(string='Attachment')
    attachment_name = fields.Char(string='Attachment Name')

    state = fields.Selection([
        ('pending', 'Pending'),
        ('successful', 'Successful')
    ], string='Status', default='pending')
    
    status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('partial', 'Partial'),
        ('paid', 'Paid')
    ], string='Payment Status', compute='_compute_status', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New Purchase Invoice') == 'New Purchase Invoice':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.pharmacy.purchase.invoice') or 'New'
        return super().create(vals_list)

    @api.depends('payment_ids.amount', 'payment_ids.state')
    def _compute_paid_amount(self):
        for rec in self:
            done_payments = rec.payment_ids.filtered(lambda p: p.state == 'done')
            rec.paid_amount = sum(done_payments.mapped('amount'))

    @api.depends('line_ids.amount', 'line_ids.qty', 'other_charges', 'round_off', 'discount_amount', 'paid_amount', 'line_ids.discount_val', 'line_ids.cgst_val', 'line_ids.sgst_val', 'line_ids.igst_val', 'line_ids.taxable_val')
    def _compute_totals(self):
        for rec in self:
            rec.total_items = sum(rec.line_ids.mapped('qty'))
            rec.taxable_amount = sum(rec.line_ids.mapped('taxable_val'))
            rec.gst_amount = sum(rec.line_ids.mapped('cgst_val')) + sum(rec.line_ids.mapped('sgst_val')) + sum(rec.line_ids.mapped('igst_val'))
            
            lines_total = sum(rec.line_ids.mapped('amount'))
            
            rec.total_amount = lines_total - rec.discount_amount + rec.other_charges + rec.round_off
            rec.balance_amount = rec.total_amount - rec.paid_amount

    @api.depends('total_amount', 'paid_amount')
    def _compute_status(self):
        for rec in self:
            if rec.paid_amount >= rec.total_amount and rec.total_amount > 0:
                rec.status = 'paid'
            elif rec.paid_amount > 0:
                rec.status = 'partial'
            else:
                rec.status = 'unpaid'

    
    def action_update_stock(self):
        for rec in self:
            if rec.state == 'pending':
                for line in rec.line_ids:
                    if line.medicine_id and line.received_qty > 0:
                        line.medicine_id.total_stock += line.received_qty
                
                # Auto-generate a draft payment for the payments menu
                self.env['hospital.pharmacy.payment'].create({
                    'vendor_id': rec.supplier_id.id,
                    'invoice_id': rec.id,
                    'amount': rec.total_amount,
                    'state': 'draft',
                    'reference': f"Payment for {rec.name}"
                })
                
                rec.state = 'successful'





class HospitalPharmacyPurchaseInvoiceLine(models.Model):
    _name = 'hospital.pharmacy.purchase.invoice.line'
    _description = 'Purchase Invoice Line'

    invoice_id = fields.Many2one('hospital.pharmacy.purchase.invoice', string='Invoice', ondelete='cascade')
    medicine_id = fields.Many2one('hospital.pharmacy.stock', string='Item', required=True)
    medicine_code = fields.Char(related='medicine_id.medicine_code', string='Item Code')
    batch_no = fields.Char(string='Batch No.')
    expiry_date = fields.Char(string='Expiry Date')
    unit = fields.Selection([('tab', 'Tab'), ('btl', 'Bottle'), ('tube', 'Tube'), ('inj', 'Inj')], string='Unit', default='tab')
    qty = fields.Float(string='Ordered Qty', default=1.0)
    received_qty = fields.Float(string='Received Qty', default=0.0)
    
    purchase_price = fields.Float(string='Purchase Price')
    discount_percent = fields.Float(string='Discount (%)')
    cgst_percent = fields.Float(string='CGST(%)')
    sgst_percent = fields.Float(string='SGST(%)')
    igst_percent = fields.Float(string='IGST(%)')
    
    taxable_val = fields.Float(compute='_compute_amounts', store=True)
    discount_val = fields.Float(compute='_compute_amounts', store=True)
    cgst_val = fields.Float(compute='_compute_amounts', store=True)
    sgst_val = fields.Float(compute='_compute_amounts', store=True)
    igst_val = fields.Float(compute='_compute_amounts', store=True)
    amount = fields.Float(string='Amount', compute='_compute_amounts', store=True)

    @api.depends('received_qty', 'purchase_price', 'discount_percent', 'cgst_percent', 'sgst_percent', 'igst_percent')
    def _compute_amounts(self):
        for line in self:
            base = line.received_qty * line.purchase_price
            disc = base * (line.discount_percent / 100.0)
            taxable = base - disc
            
            cgst = taxable * (line.cgst_percent / 100.0)
            sgst = taxable * (line.sgst_percent / 100.0)
            igst = taxable * (line.igst_percent / 100.0)
            
            line.discount_val = disc
            line.taxable_val = taxable
            line.cgst_val = cgst
            line.sgst_val = sgst
            line.igst_val = igst
            line.amount = taxable + cgst + sgst + igst

    @api.onchange('medicine_id')
    def _onchange_medicine(self):
        if self.medicine_id:
            self.purchase_price = self.medicine_id.purchase_price
            self.batch_no = self.medicine_id.batch_number
            self.expiry_date = self.medicine_id.expiry_date
