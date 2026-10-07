from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HospitalAssetSpecification(models.Model):
    _name = 'hospital.asset.specification'
    _description = 'Asset Specification'
    _rec_name = 'name'

    name = fields.Char(string='Specification Name', required=True)
    description = fields.Text(string='Description')
    manufacturer = fields.Char(string='Manufacturer')
    model_number = fields.Char(string='Model Number')
    warranty_period = fields.Integer(string='Warranty Period (Months)')
    active = fields.Boolean(string='Active', default=True)


class HospitalAssetItem(models.Model):
    _name = 'hospital.asset.item'
    _description = 'Asset Item'
    _rec_name = 'item_name'

    _sql_constraints = [
        ('item_code_uniq', 'UNIQUE(item_code)', 'This Item Code already exists! Please use a unique Item Code.')
    ]

    @api.constrains('batch_number')
    def _check_unique_batch_number(self):
        for record in self:
            if record.batch_number:
                domain = [('batch_number', '=', record.batch_number), ('id', '!=', record.id)]
                if self.env['hospital.asset.item'].search(domain, limit=1):
                    raise ValidationError("This Batch Number already exists! Please use a unique Batch Number.")

    item_name = fields.Char(string='Item Name', required=True)
    item_code = fields.Char(string='Item Code', required=True, copy=False)
    
    asset_category_id = fields.Many2one(
        'hospital.category.master', 
        string='Category', 
        domain="[('category_type', '=', 'asset_category')]"
    )
    specification_id = fields.Many2one(
        'hospital.asset.specification',
        string='Specification'
    )

    batch_number = fields.Char(string='Batch Number')
    expiry_date = fields.Char(string='Expiry Date')
    hsn_code = fields.Char(string='HSN Code')

    purchase_price = fields.Float(string='Purchase Price')
    mrp = fields.Float(string='MRP')
    
    uom = fields.Selection([
        ('unit', 'Units'),
        ('box', 'Boxes'),
        ('pack', 'Packs'),
        ('piece', 'Pieces'),
    ], string='Unit of Measure', default='unit')

    total_stock = fields.Float(string='Total Stock', default=0.0)
    emergency_stock = fields.Float(string='Emergency Stock', default=0.0)
    reorder_level = fields.Float(string='Reorder Level', default=0.0)
    
    quantity = fields.Float(string='Available Quantity', compute='_compute_quantity', store=True)
    
    supplier = fields.Char(string='Legacy Supplier (Text)')
    vendor_ids = fields.Many2many('res.partner', string='Connected Vendors', domain="[('supplier_rank', '>', 0)]")

    is_reorder_needed = fields.Boolean(
        string='Needs Reorder',
        compute='_compute_reorder_needed',
        store=True
    )
    
    active = fields.Boolean(string='Active', default=True)
    
    stock_status = fields.Selection([
        ('available', 'Available'),
        ('low', 'Low Stock'),
        ('critical', 'Critical'),
        ('out', 'Out of Stock')
    ], string='Stock Status', compute='_compute_stock_status', store=True)

    @api.depends('total_stock', 'emergency_stock')
    def _compute_quantity(self):
        for rec in self:
            rec.quantity = rec.total_stock - rec.emergency_stock

    @api.depends('total_stock', 'emergency_stock', 'reorder_level')
    def _compute_reorder_needed(self):
        for rec in self:
            rec.is_reorder_needed = rec.quantity < rec.reorder_level

    @api.depends('quantity')
    def _compute_stock_status(self):
        for rec in self:
            if rec.quantity <= 0:
                rec.stock_status = 'out'
            elif rec.quantity < 5:
                rec.stock_status = 'critical'
            elif rec.quantity <= 10:
                rec.stock_status = 'low'
            else:
                rec.stock_status = 'available'




    def action_save(self):
        return True


class HospitalAssetPurchaseRequest(models.Model):
    _name = 'hospital.asset.purchase.request'
    _description = 'Asset Request'

    name = fields.Char(string='Request Reference', required=True, copy=False, readonly=True, default='New')
    requested_by_id = fields.Many2one('res.users', string='Requested By', default=lambda self: self.env.user, readonly=True)
    request_date = fields.Date(string='Request Date', default=fields.Date.context_today, readonly=True)
    
    item_id = fields.Many2one('hospital.asset.item', string='Requested Item', required=True)
    quantity = fields.Integer(string='Quantity Needed', default=1, required=True)
    reason = fields.Text(string='Reason for Request', required=True)
    po_id = fields.Many2one('hospital.asset.po', string='Purchase Order', readonly=True)

    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Waiting Approval'),
        ('ready', 'Ready for Pickup'),
        ('ordered', 'Approved for Ordering'),
        ('received', 'Received'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if isinstance(vals, dict) and vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.asset.request.seq') or 'New'
        return super(HospitalAssetPurchaseRequest, self).create(vals_list)

    def action_submit(self):
        for rec in self:
            rec.state = 'submitted'

    def action_accept_ready(self):
        for rec in self:
            rec.state = 'ready'

    def action_approve_order(self):
        for rec in self:
            # Check if there is a vendor connected to this item
            vendor_id = False
            if rec.item_id.vendor_ids:
                vendor_id = rec.item_id.vendor_ids[0].id
            
            if not vendor_id:
                raise ValidationError("Please assign at least one connected vendor to the item before ordering.")

            # Create PO
            po_vals = {
                'vendor_id': vendor_id,
                'line_ids': [(0, 0, {
                    'item_id': rec.item_id.id,
                    'quantity': rec.quantity,
                    'price_unit': rec.item_id.purchase_price or 0.0,
                    'request_id': rec.id
                })]
            }
            po = self.env['hospital.asset.po'].create(po_vals)
            rec.po_id = po.id
            rec.state = 'ordered'
            
            return {
                'name': 'Asset PO',
                'type': 'ir.actions.act_window',
                'res_model': 'hospital.asset.po',
                'view_mode': 'form',
                'views': [(self.env.ref('hospital_hr_asset.view_asset_po_form').id, 'form')],
                'res_id': po.id,
                'target': 'current',
            }

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'

class HospitalAssetPo(models.Model):
    _name = 'hospital.asset.po'
    _description = 'Asset PO'

    name = fields.Char(string='PO Reference', required=True, copy=False, readonly=True, default='New')
    vendor_id = fields.Many2one('res.partner', string='Vendor', required=True, domain="[('supplier_rank', '>', 0)]")
    order_date = fields.Date(string='Order Date', default=fields.Date.context_today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed (Sent to Vendor)'),
        ('received', 'Received (Inward)'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft')
    
    line_ids = fields.One2many('hospital.asset.po.line', 'po_id', string='Order Lines')
    
    total_amount = fields.Float(string='Total Amount', compute='_compute_total', store=True)

    @api.depends('line_ids.subtotal')
    def _compute_total(self):
        for rec in self:
            rec.total_amount = sum(line.subtotal for line in rec.line_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if isinstance(vals, dict) and vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.asset.po.seq') or 'New'
        return super(HospitalAssetPo, self).create(vals_list)

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'

    def action_receive(self):
        for rec in self:
            rec.state = 'received'
            inward = self.env['hospital.asset.inward'].create({
                'po_id': rec.id,
                'line_ids': [(0, 0, {
                    'item_id': line.item_id.id,
                    'po_line_id': line.id,
                    'received_qty': line.quantity,
                }) for line in rec.line_ids]
            })
            return {
                'name': 'Asset Inward',
                'type': 'ir.actions.act_window',
                'res_model': 'hospital.asset.inward',
                'view_mode': 'form',
                'views': [(self.env.ref('hospital_hr_asset.view_asset_inward_form').id, 'form')],
                'res_id': inward.id,
                'target': 'current',
            }

class HospitalAssetPoLine(models.Model):
    _name = 'hospital.asset.po.line'
    _description = 'Asset PO Line'

    po_id = fields.Many2one('hospital.asset.po', string='Purchase Order', required=True, ondelete='cascade')
    item_id = fields.Many2one('hospital.asset.item', string='Item', required=True)
    request_id = fields.Many2one('hospital.asset.purchase.request', string='Source Request')
    quantity = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Float(string='Unit Price')
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.quantity * rec.price_unit

    @api.onchange('item_id')
    def _onchange_item_id(self):
        if self.item_id:
            self.price_unit = self.item_id.purchase_price

class HospitalAssetInward(models.Model):
    _name = 'hospital.asset.inward'
    _description = 'Asset Inward'

    name = fields.Char(string='Name', required=True, readonly=True, default='New')
    po_id = fields.Many2one('hospital.asset.po', string='Purchase Order', readonly=True)
    vendor_id = fields.Many2one('res.partner', string='Vendor', related='po_id.vendor_id')
    date_received = fields.Date(string='Date Received', default=fields.Date.context_today)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='Status', default='draft')
    line_ids = fields.One2many('hospital.asset.inward.line', 'inward_id', string='Lines')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if isinstance(vals, dict) and vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.asset.inward.seq') or 'New'
        return super(HospitalAssetInward, self).create(vals_list)

    def action_validate(self):
        for rec in self:
            for line in rec.line_ids:
                good_qty = line.received_qty - line.damaged_qty
                line.item_id.total_stock += good_qty
                if line.damaged_qty > 0:
                    self.env['hospital.asset.damage'].create({
                        'item_id': line.item_id.id,
                        'quantity': line.damaged_qty,
                        'reason': 'Damaged upon receiving',
                        'source_document': rec.name,
                        'po_id': rec.po_id.id,
                        'state': 'done'
                    })
                
                if good_qty > 0:
                    pending_requests = self.env['hospital.asset.purchase.request'].search([
                        ('item_id', '=', line.item_id.id),
                        ('state', 'in', ['submitted', 'ordered'])
                    ], order='request_date asc, id asc')
                    
                    available = good_qty
                    for req in pending_requests:
                        if available >= req.quantity:
                            self.env['hospital.asset.outward'].create({
                                'assigned_to': req.requested_by_id.id,
                                'line_ids': [(0, 0, {
                                    'item_id': req.item_id.id,
                                    'quantity': req.quantity
                                })]
                            })
                            req.state = 'ready'
                            available -= req.quantity
                        if available <= 0:
                            break

            rec.state = 'done'
            if rec.po_id:
                total_invoice_amount = 0
                damaged_notes = []
                for line in rec.line_ids:
                    good_qty = line.received_qty - line.damaged_qty
                    price = line.po_line_id.price_unit if line.po_line_id else 0
                    total_invoice_amount += good_qty * price
                    if line.damaged_qty > 0:
                        damaged_notes.append(f"Reduced by {line.damaged_qty} for damaged {line.item_id.item_name}.")
                
                notes_text = "Generated from Inward Receipt.\n" + "\n".join(damaged_notes)
                
                existing_invoice = self.env['hospital.asset.invoice'].search([('purchase_id', '=', rec.po_id.id)], limit=1)
                if not existing_invoice:
                    self.env['hospital.asset.invoice'].create({
                        'purchase_id': rec.po_id.id,
                        'amount': total_invoice_amount,
                        'notes': notes_text,
                        'state': 'draft'
                    })

    def action_view_invoice(self):
        self.ensure_one()
        if self.po_id:
            invoice = self.env['hospital.asset.invoice'].search([('purchase_id', '=', self.po_id.id)], limit=1)
            if invoice:
                return {
                    'name': 'Asset Invoice',
                    'type': 'ir.actions.act_window',
                    'res_model': 'hospital.asset.invoice',
                    'view_mode': 'form',
                    'res_id': invoice.id,
                    'target': 'current',
                }

class HospitalAssetInwardLine(models.Model):
    _name = 'hospital.asset.inward.line'
    _description = 'Asset Inward Line'

    inward_id = fields.Many2one('hospital.asset.inward', string='Inward Reference')
    po_line_id = fields.Many2one('hospital.asset.po.line', string='PO Line')
    item_id = fields.Many2one('hospital.asset.item', string='Item')
    
    requested_qty = fields.Float(string='Requested Qty', compute='_compute_qtys', store=True)
    approved_qty = fields.Float(string='Approved Qty', compute='_compute_qtys', store=True)
    
    received_qty = fields.Float(string='Received Qty', default=1.0)
    damaged_qty = fields.Float(string='Damaged Qty', default=0.0)

    @api.depends('po_line_id')
    def _compute_qtys(self):
        for rec in self:
            if rec.po_line_id:
                rec.approved_qty = rec.po_line_id.quantity
                if rec.po_line_id.request_id:
                    rec.requested_qty = rec.po_line_id.request_id.quantity
                else:
                    rec.requested_qty = 0.0
            else:
                rec.approved_qty = 0.0
                rec.requested_qty = 0.0

    @api.constrains('received_qty', 'damaged_qty')
    def _check_quantities(self):
        for rec in self:
            if rec.damaged_qty > rec.received_qty:
                raise ValidationError("Damaged Quantity cannot be greater than Received Quantity.")
            if rec.received_qty < 0 or rec.damaged_qty < 0:
                raise ValidationError("Quantities cannot be negative.")

class HospitalAssetOutward(models.Model):
    _name = 'hospital.asset.outward'
    _description = 'Asset Outward'

    name = fields.Char(string='Name', required=True, readonly=True, default='New')
    assigned_to = fields.Many2one('res.users', string='Assigned To', required=True)
    date_outward = fields.Date(string='Date Outward', default=fields.Date.context_today)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='Status', default='draft')
    line_ids = fields.One2many('hospital.asset.outward.line', 'outward_id', string='Lines')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if isinstance(vals, dict) and vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.asset.outward.seq') or 'New'
        return super(HospitalAssetOutward, self).create(vals_list)

    def action_validate(self):
        for rec in self:
            for line in rec.line_ids:
                if line.item_id.quantity < line.quantity:
                    raise ValidationError(f"Not enough stock for item {line.item_id.item_name}")
                line.item_id.total_stock -= line.quantity
            rec.state = 'done'
            if rec.name == 'New':
                rec.name = self.env['ir.sequence'].next_by_code('hospital.asset.outward.seq') or 'New'

class HospitalAssetOutwardLine(models.Model):
    _name = 'hospital.asset.outward.line'
    _description = 'Asset Outward Line'

    outward_id = fields.Many2one('hospital.asset.outward', string='Outward Reference')
    item_id = fields.Many2one('hospital.asset.item', string='Item')
    quantity = fields.Float(string='Quantity')

class HospitalAssetDamage(models.Model):
    _name = 'hospital.asset.damage'
    _description = 'Damaged & Expiry'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    item_id = fields.Many2one('hospital.asset.item', string='Item', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    reason = fields.Text(string='Reason')
    source_document = fields.Char(string='Source Document (Inward)')
    po_id = fields.Many2one('hospital.asset.po', string='Purchase Order')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='Status', default='draft')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if isinstance(vals, dict) and vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.asset.damage.seq') or 'New'
        return super(HospitalAssetDamage, self).create(vals_list)

