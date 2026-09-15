from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

class HospitalPharmacyPurchase(models.Model):
    _name = 'hospital.pharmacy.purchase'
    _description = 'Pharmacy Purchase'
    _order = 'id desc'

    name = fields.Char(string='Purchase No.', required=True, copy=False, readonly=True, default='New Purchase Order')
    
    medicine_names = fields.Char(string='Product Name', compute='_compute_medicine_names')

    @api.depends('line_ids.medicine_id')
    def _compute_medicine_names(self):
        for rec in self:
            names = [line.medicine_id.medicine_name for line in rec.line_ids if line.medicine_id]
            rec.medicine_names = ', '.join(names) if names else ''

    
    # 1. Supplier & Invoice Details
    supplier_id = fields.Many2one('res.partner', string='Supplier Name')
    supplier_name = fields.Char(string='Supplier') # Fallback if not using res.partner
    invoice_no = fields.Char(string='Invoice No.')
    invoice_date = fields.Date(string='Invoice Date', default=fields.Date.context_today, required=True)
    
    @api.onchange('line_ids')
    def _onchange_line_ids_supplier(self):
        if not self.supplier_id:
            for line in self.line_ids:
                if line.medicine_id and line.medicine_id.vendor_ids:
                    self.supplier_id = line.medicine_id.vendor_ids[0].id
                    break

    @api.onchange('supplier_id')
    def _onchange_supplier_id(self):
        if self.supplier_id:
            # Auto-fetch mobile number
            if not self.mobile_number:
                self.mobile_number = self.supplier_id.phone
                
            # Auto-fetch address
            if not self.address:
                parts = []
                if hasattr(self.supplier_id, 'street') and self.supplier_id.street: parts.append(self.supplier_id.street)
                if hasattr(self.supplier_id, 'street2') and self.supplier_id.street2: parts.append(self.supplier_id.street2)
                if hasattr(self.supplier_id, 'city') and self.supplier_id.city: parts.append(self.supplier_id.city)
                if hasattr(self.supplier_id, 'state_id') and self.supplier_id.state_id: parts.append(self.supplier_id.state_id.name)
                self.address = ", ".join(parts) if parts else ""

    purchase_type = fields.Selection([
        ('stock', 'Stock Purchase'),
        ('return', 'Return Purchase')
    ], string='Purchase Type', default='stock', required=True)
    
    gst_no = fields.Char(string='GST No.')
    mobile_number = fields.Char(string='Mobile Number')
    payment_terms = fields.Selection([
        ('immediate', 'Immediate'),
        ('15_days', '15 Days'),
        ('30_days', '30 Days'),
        ('45_days', '45 Days')
    ], string='Payment Terms')
    due_date = fields.Date(string='Due Date')
    address = fields.Text(string='Address')

    # 2. Item Details
    line_ids = fields.One2many('hospital.pharmacy.purchase.line', 'purchase_id', string='Items')
    total_items = fields.Integer(string='Total Items', compute='_compute_totals', store=True)

    state = fields.Selection([
        ('intent', 'Intent'),
        ('draft', 'Draft Order'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='State', default='intent')



    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New Purchase Order') == 'New Purchase Order':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.pharmacy.purchase') or 'PUR-New'
        return super().create(vals_list)

    invoice_ids = fields.One2many('hospital.pharmacy.purchase.invoice', 'purchase_id', string='Invoices')
    invoice_status = fields.Selection([
        ('pending', 'Pending'),
        ('successful', 'Successful')
    ], string="Status", compute="_compute_invoice_status", store=True)

    @api.depends('invoice_ids.state')
    def _compute_invoice_status(self):
        for rec in self:
            if any(inv.state == 'successful' for inv in rec.invoice_ids):
                rec.invoice_status = 'successful'
            else:
                rec.invoice_status = 'pending'

    invoice_count = fields.Integer(compute='_compute_invoice_count')

    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = self.env['hospital.pharmacy.purchase.invoice'].search_count([('purchase_id', '=', rec.id)])

    @api.depends('line_ids.qty')
    def _compute_totals(self):
        for rec in self:
            rec.total_items = sum(rec.line_ids.mapped('qty'))

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'name': 'Purchase Invoices',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.pharmacy.purchase.invoice',
            'view_mode': 'list,form',
            'domain': [('purchase_id', '=', self.id)],
            'context': {'default_purchase_id': self.id},
        }


    def action_print_order(self):
        return self.env.ref('hospital_management.action_report_pharmacy_purchase_order').report_action(self)

    def action_print_invoice(self):
        return self.env.ref('hospital_management.action_report_pharmacy_purchase_invoice').report_action(self)

    
    def action_delete(self):
        for rec in self:
            rec.unlink()
        return {'type': 'ir.actions.client', 'tag': 'reload'}
        
    def action_create_order(self):
        for rec in self:
            if rec.state == 'intent':
                rec.state = 'draft'
        
        # In Odoo, returning a window action from a form button can cause blank SPA routing issues.
        # It is standard to just reload the current form so the user sees the state change immediately.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_confirm(self):
        for rec in self:
            if rec.state == 'draft':
                if not rec.supplier_id:
                    raise ValidationError("Please select a Supplier Name before confirming and generating the invoice.")
                    
                # Increase Stock
                invoice_lines = []
                for line in rec.line_ids:
                    if line.medicine_id:
                        # Removed instant stock update.
                        # Stock is now updated from the Invoice via 'Update Stock' button.
                        
                        invoice_lines.append((0, 0, {
                            'medicine_id': line.medicine_id.id,
                            'batch_no': line.batch_no,
                            'qty': line.qty,
                            
                            'unit': line.unit,
                            'purchase_price': line.medicine_id.purchase_price,
                        }))

                # Generate Invoice
                if invoice_lines:
                    self.env['hospital.pharmacy.purchase.invoice'].with_context(default_state='pending').create({
                        'purchase_id': rec.id,
                        'supplier_id': rec.supplier_id.id,
                        'line_ids': invoice_lines,
                    })

                rec.state = 'done'

class HospitalPharmacyPurchaseLine(models.Model):
    _name = 'hospital.pharmacy.purchase.line'
    _description = 'Purchase Line'

    purchase_id = fields.Many2one('hospital.pharmacy.purchase', string='Purchase', ondelete='cascade')
    medicine_id = fields.Many2one('hospital.pharmacy.stock', string='Item Name', required=True)
    batch_no = fields.Char(string='Batch No.')
    unit = fields.Selection([('tab', 'Tab'), ('btl', 'Bottle'), ('tube', 'Tube'), ('inj', 'Inj')], string='Unit', default='tab')
    qty = fields.Float(string='Order Quantity', default=200.0)
    medicine_code = fields.Char(related='medicine_id.medicine_code', string='Item Code')
    purchase_price = fields.Float(string='Price')
    discount_percent = fields.Float(string='Disc(%)')
    cgst_percent = fields.Float(string='CGST(%)')
    sgst_percent = fields.Float(string='SGST(%)')
    igst_percent = fields.Float(string='IGST(%)')
    amount = fields.Float(string='Amount', compute='_compute_amounts', store=True)
    
    @api.depends('qty', 'purchase_price', 'discount_percent', 'cgst_percent', 'sgst_percent', 'igst_percent')
    def _compute_amounts(self):
        for line in self:
            base = line.qty * line.purchase_price
            disc = base * (line.discount_percent / 100.0)
            taxable = base - disc
            cgst = taxable * (line.cgst_percent / 100.0)
            sgst = taxable * (line.sgst_percent / 100.0)
            igst = taxable * (line.igst_percent / 100.0)
            line.amount = taxable + cgst + sgst + igst


    @api.onchange('medicine_id')
    def _onchange_medicine(self):
        if self.medicine_id:
            self.batch_no = self.medicine_id.batch_number
            self.qty = 200.0

