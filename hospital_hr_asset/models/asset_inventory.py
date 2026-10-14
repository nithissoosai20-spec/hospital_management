from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HospitalAssetSpecification(models.Model):
    _name = 'hospital.asset.specification'
    _description = 'Asset Specification'
    _rec_name = 'name'

    name = fields.Char(string='Specification Name', compute='_compute_name', store=True, readonly=False, default='Specification')
    item_id = fields.Many2one('hospital.pharmacy.stock', string='Item')
    
    # Hardware
    processor = fields.Char(string='Processor (CPU)')
    ram = fields.Char(string='RAM / Memory')
    storage = fields.Char(string='Storage (HDD/SSD)')
    display_size = fields.Char(string='Display / Screen Size')
    
    # Network & Software
    operating_system = fields.Char(string='Operating System')
    mac_address = fields.Char(string='MAC Address')
    ip_address = fields.Char(string='Default IP Address')
    
    # Device Details
    serial_number = fields.Char(string='Serial Number / Service Tag')
    color = fields.Char(string='Color / Form Factor')
    
    # Warranty & Support
    description = fields.Text(string='Additional Notes')
    manufacturer = fields.Char(string='Manufacturer')
    model_number = fields.Char(string='Model Number')
    warranty_period = fields.Integer(string='Warranty Period (Months)')
    warranty_expiry_date = fields.Date(string='Warranty Expiry Date')
    support_contact = fields.Char(string='Support Contact / Phone')
    
    active = fields.Boolean(string='Active', default=True)

    @api.depends('item_id', 'item_id.medicine_name')
    def _compute_name(self):
        for rec in self:
            if rec.item_id and rec.item_id.medicine_name:
                rec.name = f"{rec.item_id.medicine_name} Specification"
            elif not rec.name or rec.name == 'New':
                rec.name = "Specification"


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
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Saved successfully!',
                'type': 'rainbow_man',
            },
            'type': 'ir.actions.act_window',
            'name': 'Items',
            'res_model': 'hospital.asset.item',
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'target': 'current'
        }


class HospitalAssetPurchaseRequest(models.Model):
    _name = 'hospital.asset.purchase.request'
    _description = 'Item Request'
    _order = 'id desc'

    name = fields.Char(string='Request Reference', required=True, copy=False, readonly=True, default='New')

    @api.model
    def _get_user_department(self, user=None):
        if not user:
            user = self.env.user
        h_user = self.env['hospital.user'].sudo().search([('odoo_user_id', '=', user.id)], limit=1)
        if h_user:
            if h_user.role_id and h_user.role_id.name:
                return h_user.role_id.name
            if h_user.department_id and h_user.department_id.name:
                return h_user.department_id.name
        # Fallbacks based on user groups
        if user.has_group('hospital_management.group_hospital_super_admin'):
            return 'Super Admin'
        if user.has_group('hospital_management.group_hospital_admin'):
            return 'Admin'
        if user.has_group('hospital_management.group_hospital_hr'):
            return 'HR Manager'
        if user.has_group('hospital_management.group_hospital_pharmacist'):
            return 'Pharmacist'
        if user.has_group('hospital_hr_asset.group_hospital_asset_manager'):
            return 'Asset Manager'
        if user.has_group('hospital_management.group_hospital_doctor'):
            return 'Doctor'
        if user.has_group('hospital_management.group_hospital_receptionist'):
            return 'Receptionist'
        if user.has_group('hospital_management.group_hospital_lab_technician') or user.has_group('hospital_management.group_hospital_lab_manager'):
            return 'Lab Manager'
        if user.has_group('hospital_management.group_hospital_nurse'):
            return 'Nurse'
        if user.has_group('hospital_management.group_hospital_billing'):
            return 'Billing'
        return 'General'

    def _default_department(self):
        return self._get_user_department(self.env.user)

    requested_by_id = fields.Many2one('res.users', string='Requested By', default=lambda self: self.env.user, readonly=True)
    request_date = fields.Datetime(string='Request Date & Time', default=fields.Datetime.now, readonly=True)
    department = fields.Char(string='Department', default=_default_department, readonly=True, index=True)

    item_id = fields.Many2one('hospital.pharmacy.stock', string='Requested Item', required=True)
    available_stock = fields.Float(related='item_id.total_stock', string='Current In-Stock', readonly=True)
    quantity = fields.Integer(string='Quantity Needed', default=1, required=True)
    reason = fields.Text(string='Reason for Request', required=True)
    po_id = fields.Many2one('hospital.asset.po', string='Legacy Purchase Order', readonly=True)
    purchase_id = fields.Many2one('hospital.pharmacy.purchase', string='Purchase Order', readonly=True)
    outward_id = fields.Many2one('hospital.asset.outward', string='Outward Delivery', readonly=True)
    delivered_qty = fields.Integer(string='Delivered Quantity', default=0, readonly=True)
    ordered_qty = fields.Integer(string='Ordered Quantity', default=0, readonly=True)
    remaining_qty = fields.Integer(string='Remaining Quantity', compute='_compute_remaining_qty', store=True)

    @api.depends('quantity', 'delivered_qty')
    def _compute_remaining_qty(self):
        for rec in self:
            rec.remaining_qty = max(0, rec.quantity - rec.delivered_qty)

    @api.onchange('requested_by_id')
    def _onchange_requested_by_id(self):
        if self.requested_by_id:
            self.department = self._get_user_department(self.requested_by_id)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Waiting Approval'),
        ('partial', 'Partially Fulfilled & Ordered'),
        ('ready', 'Ready for Pickup'),
        ('ordered', 'Approved for Ordering'),
        ('received', 'Received'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if isinstance(vals, dict):
                if vals.get('name', 'New') == 'New':
                    vals['name'] = self.env['ir.sequence'].next_by_code('hospital.asset.request.seq') or 'New'
                if not vals.get('department'):
                    user = self.env['res.users'].browse(vals['requested_by_id']) if vals.get('requested_by_id') else self.env.user
                    vals['department'] = self._get_user_department(user)
        return super(HospitalAssetPurchaseRequest, self).create(vals_list)

    def action_submit(self):
        for rec in self:
            rec.state = 'submitted'
        if self.env.user.has_group('hospital_management.group_hospital_pharmacist') and not self.env.user.has_group('hospital_hr_asset.group_hospital_asset_manager'):
            action = self.env.ref('hospital_hr_asset.action_pharmacy_item_request').sudo().read()[0]
        else:
            action = self.env.ref('hospital_hr_asset.action_asset_purchase_request').sudo().read()[0]
        action['effect'] = {
            'fadeout': 'slow',
            'message': 'Request submitted successfully!',
            'type': 'rainbow_man',
        }
        return action

    def action_close(self):
        if self.env.user.has_group('hospital_management.group_hospital_pharmacist') and not self.env.user.has_group('hospital_hr_asset.group_hospital_asset_manager'):
            return self.env.ref('hospital_hr_asset.action_pharmacy_item_request').sudo().read()[0]
        elif self.env.user.has_group('hospital_hr_asset.group_hospital_asset_manager'):
            return self.env.ref('hospital_hr_asset.action_asset_purchase_request_manager').sudo().read()[0]
        return self.env.ref('hospital_hr_asset.action_asset_purchase_request').sudo().read()[0]

    def action_accept_ready(self):
        outward = False
        for rec in self:
            rec.state = 'ready'
            rec.delivered_qty = rec.quantity
            # Auto-create draft outward record
            outward = self.env['hospital.asset.outward'].create({
                'assigned_to': rec.requested_by_id.id,
                'request_id': rec.id,
                'line_ids': [(0, 0, {
                    'item_id': rec.item_id.id,
                    'quantity': rec.quantity
                })]
            })
            rec.outward_id = outward.id
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Request Accepted!',
                'message': f'Outward Delivery {outward.name if outward else ""} created for all items.',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'}
            }
        }

    def action_approve_order(self):
        purchase = False
        for rec in self:
            # Check if there is a vendor connected to this item
            vendor_id = False
            mobile_number = False
            address = False
            if rec.item_id.vendor_ids:
                vendor = rec.item_id.vendor_ids[0]
                vendor_id = vendor.id
                mobile_number = vendor.phone or ''
                parts = []
                if hasattr(vendor, 'street') and vendor.street: parts.append(vendor.street)
                if hasattr(vendor, 'street2') and vendor.street2: parts.append(vendor.street2)
                if hasattr(vendor, 'city') and vendor.city: parts.append(vendor.city)
                if hasattr(vendor, 'state_id') and vendor.state_id: parts.append(vendor.state_id.name)
                address = ", ".join(parts) if parts else ""

            order_type = 'pharmacy' if rec.department and 'pharmac' in rec.department.lower() else 'asset'

            # Create Pharmacy Purchase with corresponding order_type
            po_vals = {
                'order_type': order_type,
                'state': 'draft',
                'supplier_id': vendor_id,
                'mobile_number': mobile_number or '',
                'address': address or '',
                'request_id': rec.id,
                'line_ids': [(0, 0, {
                    'medicine_id': rec.item_id.id,
                    'qty': float(rec.quantity),
                    'purchase_price': rec.item_id.purchase_price or 0.0,
                })]
            }
            purchase = self.env['hospital.pharmacy.purchase'].create(po_vals)
            rec.purchase_id = purchase.id
            rec.ordered_qty = rec.quantity
            rec.state = 'ordered'
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Purchase Order Created!',
                'message': f'Draft Purchase Order {purchase.name if purchase else ""} created for {self.quantity} units.',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'}
            }
        }

    def action_open_split_wizard(self):
        self.ensure_one()
        return {
            'name': 'Partial Delivery & Purchase Allocation',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.asset.request.split.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_request_id': self.id,
            }
        }

    def action_deliver_remaining(self):
        for rec in self:
            needed = rec.remaining_qty
            if needed <= 0:
                raise ValidationError("All requested items have already been delivered.")
            if rec.item_id.total_stock < needed:
                raise ValidationError(f"Insufficient stock to deliver remaining {needed} units. Current stock is {int(rec.item_id.total_stock)}. Please inward items from the Purchase Order first.")
            
            outward = self.env['hospital.asset.outward'].create({
                'assigned_to': rec.requested_by_id.id,
                'request_id': rec.id,
                'line_ids': [(0, 0, {
                    'item_id': rec.item_id.id,
                    'quantity': needed
                })]
            })
            rec.delivered_qty += needed
            rec.state = 'received'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Remaining Items Dispatched!',
                    'message': f'Outward Delivery {outward.name} created for remaining {needed} units. Request is now fully fulfilled!',
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.client', 'tag': 'reload'}
                }
            }

    def action_view_purchase_order(self):
        self.ensure_one()
        if self.purchase_id:
            return {
                'name': 'Purchase Order',
                'type': 'ir.actions.act_window',
                'res_model': 'hospital.pharmacy.purchase',
                'view_mode': 'form',
                'res_id': self.purchase_id.id,
                'target': 'current',
            }

    def action_view_outward(self):
        self.ensure_one()
        if self.outward_id:
            return {
                'name': 'Outward Delivery',
                'type': 'ir.actions.act_window',
                'res_model': 'hospital.asset.outward',
                'view_mode': 'form',
                'res_id': self.outward_id.id,
                'target': 'current',
            }

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'

class HospitalAssetRequestSplitWizard(models.TransientModel):
    _name = 'hospital.asset.request.split.wizard'
    _description = 'Partial Delivery & Purchase Allocation Wizard'

    request_id = fields.Many2one('hospital.asset.purchase.request', string='Request', required=True)
    item_id = fields.Many2one('hospital.pharmacy.stock', related='request_id.item_id', string='Requested Item', readonly=True)
    total_requested = fields.Integer(related='request_id.quantity', string='Total Requested', readonly=True)
    available_stock = fields.Float(related='request_id.available_stock', string='Current In-Stock', readonly=True)
    
    deliver_qty = fields.Integer(string='Deliver Now (From In-Stock)', required=True)
    order_qty = fields.Integer(string='Order from Vendor (Purchase Order)', required=True)
    
    supplier_id = fields.Many2one('res.partner', string='Supplier / Vendor', domain="['|', ('is_pharmacy_vendor', '=', True), ('supplier_rank', '>', 0)]")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        req_id = res.get('request_id') or self.env.context.get('default_request_id')
        if req_id:
            req = self.env['hospital.asset.purchase.request'].browse(req_id)
            res['request_id'] = req.id
            avail = int(req.available_stock) if req.available_stock > 0 else 0
            needed = req.quantity
            deliver = min(avail, needed)
            res['deliver_qty'] = deliver
            res['order_qty'] = max(0, needed - deliver)
            if req.item_id.vendor_ids:
                res['supplier_id'] = req.item_id.vendor_ids[0].id
        return res

    @api.onchange('deliver_qty')
    def _onchange_deliver_qty(self):
        if self.request_id and self.deliver_qty is not None:
            if self.deliver_qty > self.available_stock:
                self.deliver_qty = int(self.available_stock)
            if self.deliver_qty < 0:
                self.deliver_qty = 0
            self.order_qty = max(0, self.request_id.quantity - self.deliver_qty)

    def action_confirm(self):
        self.ensure_one()
        req = self.request_id
        
        if self.deliver_qty < 0 or self.order_qty < 0:
            raise ValidationError("Quantities cannot be negative.")
        if self.deliver_qty > req.available_stock:
            raise ValidationError(f"Cannot deliver {self.deliver_qty} units. Only {int(req.available_stock)} units are currently in stock.")
        if self.deliver_qty == 0 and self.order_qty == 0:
            raise ValidationError("Please specify a quantity to deliver or order.")

        created_msgs = []
        
        # 1. Handle Deliver Now -> Outward
        if self.deliver_qty > 0:
            outward = self.env['hospital.asset.outward'].create({
                'assigned_to': req.requested_by_id.id,
                'request_id': req.id,
                'line_ids': [(0, 0, {
                    'item_id': req.item_id.id,
                    'quantity': self.deliver_qty
                })]
            })
            req.outward_id = outward.id
            req.delivered_qty = self.deliver_qty
            created_msgs.append(f"Outward Delivery ({self.deliver_qty} units)")

        # 2. Handle Order from Vendor -> Purchase Order
        if self.order_qty > 0:
            vendor = self.supplier_id or (req.item_id.vendor_ids and req.item_id.vendor_ids[0]) or False
            vendor_id = vendor.id if vendor else False
            mobile = vendor.phone if vendor else ''
            address = ""
            if vendor:
                parts = []
                if vendor.street: parts.append(vendor.street)
                if vendor.street2: parts.append(vendor.street2)
                if vendor.city: parts.append(vendor.city)
                if vendor.state_id: parts.append(vendor.state_id.name)
                address = ", ".join(parts)

            order_type = 'pharmacy' if req.department and 'pharmac' in req.department.lower() else 'asset'
            po_vals = {
                'order_type': order_type,
                'state': 'draft',
                'supplier_id': vendor_id,
                'mobile_number': mobile or '',
                'address': address or '',
                'request_id': req.id,
                'line_ids': [(0, 0, {
                    'medicine_id': req.item_id.id,
                    'qty': float(self.order_qty),
                    'purchase_price': req.item_id.purchase_price or 0.0,
                })]
            }
            purchase = self.env['hospital.pharmacy.purchase'].create(po_vals)
            req.purchase_id = purchase.id
            req.ordered_qty = self.order_qty
            created_msgs.append(f"Purchase Order {purchase.name} ({self.order_qty} units)")

        # 3. Update Request State
        if self.deliver_qty > 0 and self.order_qty > 0:
            req.state = 'partial'
        elif self.deliver_qty > 0 and self.order_qty == 0:
            req.state = 'ready'
        else:
            req.state = 'ordered'

        msg = " and ".join(created_msgs) + " created successfully!"
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Allocation Confirmed!',
                'message': msg,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'}
            }
        }

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
    item_id = fields.Many2one('hospital.pharmacy.stock', string='Item', required=True)
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
                    available = line.item_id.total_stock - line.item_id.emergency_stock
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
                        damaged_notes.append(f"Reduced by {line.damaged_qty} for damaged {line.item_id.medicine_name}.")
                
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

    def action_close(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Inward',
            'res_model': 'hospital.asset.inward',
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'target': 'current'
        }

class HospitalAssetInwardLine(models.Model):
    _name = 'hospital.asset.inward.line'
    _description = 'Asset Inward Line'

    inward_id = fields.Many2one('hospital.asset.inward', string='Inward Reference')
    po_line_id = fields.Many2one('hospital.asset.po.line', string='PO Line')
    item_id = fields.Many2one('hospital.pharmacy.stock', string='Item')
    
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
    department = fields.Char(string='Department', compute='_compute_department', store=True, readonly=True, index=True)
    request_id = fields.Many2one('hospital.asset.purchase.request', string='Origin Request', readonly=True)
    date_outward = fields.Date(string='Date Outward', default=fields.Date.context_today)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='Status', default='draft')
    line_ids = fields.One2many('hospital.asset.outward.line', 'outward_id', string='Lines')

    @api.depends('assigned_to', 'request_id', 'request_id.department')
    def _compute_department(self):
        for rec in self:
            if rec.request_id and rec.request_id.department:
                rec.department = rec.request_id.department
            elif rec.assigned_to:
                rec.department = self.env['hospital.asset.purchase.request']._get_user_department(rec.assigned_to)
            else:
                rec.department = 'General'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if isinstance(vals, dict) and vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.asset.outward.seq') or 'New'
        return super(HospitalAssetOutward, self).create(vals_list)

    def action_validate(self):
        for rec in self:
            for line in rec.line_ids:
                if line.item_id.total_stock < line.quantity:
                    raise ValidationError(f"Not enough stock for item {line.item_id.medicine_name}")
                line.item_id.total_stock -= line.quantity
                
            if rec.request_id:
                if rec.request_id.delivered_qty >= rec.request_id.quantity:
                    rec.request_id.state = 'received'
                elif rec.request_id.delivered_qty > 0:
                    rec.request_id.state = 'partial'
            else:
                for line in rec.line_ids:
                    matching_requests = self.env['hospital.asset.purchase.request'].search([
                        ('item_id', '=', line.item_id.id),
                        ('requested_by_id', '=', rec.assigned_to.id),
                        ('state', 'in', ['submitted', 'ready'])
                    ], limit=1)
                    for req in matching_requests:
                        if req.delivered_qty >= req.quantity:
                            req.state = 'received'
                    
            rec.state = 'done'
            if rec.name == 'New':
                rec.name = self.env['ir.sequence'].next_by_code('hospital.asset.outward.seq') or 'New'

    def action_close(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Outward',
            'res_model': 'hospital.asset.outward',
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'target': 'current'
        }

class HospitalAssetOutwardLine(models.Model):
    _name = 'hospital.asset.outward.line'
    _description = 'Asset Outward Line'

    outward_id = fields.Many2one('hospital.asset.outward', string='Outward Reference')
    item_id = fields.Many2one('hospital.pharmacy.stock', string='Item')
    quantity = fields.Float(string='Quantity')

class HospitalAssetDamage(models.Model):
    _name = 'hospital.asset.damage'
    _description = 'Damaged & Expiry'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    item_id = fields.Many2one('hospital.pharmacy.stock', string='Item', required=True)
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

    def action_close(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Damaged & Expiry',
            'res_model': 'hospital.asset.damage',
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'target': 'current'
        }


class HospitalPharmacyPurchaseAssetExt(models.Model):
    _inherit = 'hospital.pharmacy.purchase'

    request_id = fields.Many2one('hospital.asset.purchase.request', string='Item Request', readonly=True)


class HospitalPharmacyPurchaseInvoiceAssetExt(models.Model):
    _inherit = 'hospital.pharmacy.purchase.invoice'

    def action_update_stock(self):
        res = super().action_update_stock()
        for rec in self:
            if rec.order_type == 'asset':
                if rec.purchase_id and hasattr(rec.purchase_id, 'request_id') and rec.purchase_id.request_id:
                    if rec.purchase_id.request_id.state in ('submitted', 'ordered'):
                        rec.purchase_id.request_id.state = 'ready'
                for pline in rec.line_ids:
                    if pline.medicine_id:
                        preqs = self.env['hospital.asset.purchase.request'].sudo().search([
                            ('item_id', '=', pline.medicine_id.id),
                            ('state', 'in', ['submitted', 'ordered'])
                        ], order='request_date asc, id asc')
                        avail = pline.medicine_id.total_stock - pline.medicine_id.emergency_stock
                        for pr in preqs:
                            if avail >= pr.quantity:
                                pr.state = 'ready'
                                avail -= pr.quantity
        return res


