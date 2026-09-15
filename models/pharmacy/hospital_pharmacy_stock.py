from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HospitalPharmacyStock(models.Model):
    _name = 'hospital.pharmacy.stock'
    _description = 'Hospital Pharmacy Stock'
    _rec_name = 'medicine_name'
    _order = 'medicine_name asc'



    _medicine_code_uniq = models.Constraint(
        'UNIQUE(medicine_code)',
        'This Item Code already exists! Please use a unique Item Code.'
    )

    @api.constrains('batch_number')
    def _check_unique_batch_number(self):
        for record in self:
            if record.batch_number:
                domain = [('batch_number', '=', record.batch_number), ('id', '!=', record.id)]
                if self.env['hospital.pharmacy.stock'].search(domain, limit=1):
                    raise ValidationError("This Batch Number already exists! Please use a unique Batch Number.")



    # BASIC MEDICINE INFORMATION

    medicine_name = fields.Char(
        string='Medicine Name',
        required=True,
    )

    medicine_code = fields.Char(
        string='Medicine Code',
        required=True,
        copy=False,
    )

    category = fields.Selection([
        ('Tablet', 'Tablets'),
        ('Syrup', 'Syrup'),
        ('Capsule', 'Capsules'),
        ('Injection', 'Injections'),
        ('Ointment', 'Ointments'),
        ('Drops', 'Drops'),
        ('Gel', 'Gel'),
        ('Cream', 'Cream'),
        ('Lotion', 'Lotion'),
        ('Other', 'Other')
    ], string='Category', default='Tablet')

    # BATCH INFORMATION

    batch_number = fields.Char(
        string='Batch Number',
    )

    expiry_date = fields.Char(
        string='Expiry Date',
    )

    hsn_code = fields.Char(
        string='HSN Code',
    )

    # PRICING

    purchase_price = fields.Float(
        string='Purchase Price',
    )
    
    mrp = fields.Float(
        string='MRP',
    )
    
    item_category = fields.Selection([
        ('strip', 'Strips'),
        ('pack', 'Packs'),
        ('box', 'Boxes'),
        ('bottle', 'Bottles'),
        ('vial', 'Vials'),
        ('ampoule', 'Ampoules'),
        ('tube', 'Tubes'),
        ('piece', 'Pieces'),
    ], string='Item Category', default='strip')
    
    qty_in_category = fields.Integer(
        string='Qty in Category',
        default=1,
    )
    
    amount_per_item = fields.Float(
        string='Amount/Item',
        compute='_compute_pricing',
        store=True,
    )

    selling_price_percent = fields.Float(
        string='Selling Price (%)',
        default=0.0,
    )

    selling_price = fields.Float(
        string='Selling Price Amount',
        compute='_compute_pricing',
        store=True,
    )
    
    cgst = fields.Float(
        string='CGST (%)',
        default=0.0,
    )

    cgst_amount = fields.Float(
        string='CGST (INR)',
        compute='_compute_pricing',
        store=True,
    )

    sgst = fields.Float(
        string='SGST (%)',
        default=0.0,
    )

    sgst_amount = fields.Float(
        string='SGST (INR)',
        compute='_compute_pricing',
        store=True,
    )

    igst = fields.Float(
        string='IGST (%)',
        default=0.0,
    )

    igst_amount = fields.Float(
        string='IGST (INR)',
        compute='_compute_pricing',
        store=True,
    )

    discount_percent = fields.Float(
        string='Discount (%)',
        default=0.0,
    )
    
    discount_amount = fields.Float(
        string='Discount Amount',
        compute='_compute_pricing',
        store=True,
    )
    
    taxable_amount = fields.Float(
        string='Taxable Amount',
        compute='_compute_pricing',
        store=True,
    )

    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_pricing',
        store=True,
    )

    @api.depends('purchase_price', 'qty_in_category', 'discount_percent', 'selling_price_percent', 'cgst', 'sgst', 'igst')
    def _compute_pricing(self):
        for record in self:
            qty = record.qty_in_category if record.qty_in_category > 0 else 1
            amt_per_item = record.purchase_price / qty
            disc_amt = amt_per_item * (record.discount_percent / 100.0)
            taxable = amt_per_item - disc_amt
            
            record.amount_per_item = amt_per_item
            record.discount_amount = disc_amt
            record.taxable_amount = taxable
            
            record.cgst_amount = taxable * (record.cgst / 100.0)
            record.sgst_amount = taxable * (record.sgst / 100.0)
            record.igst_amount = taxable * (record.igst / 100.0)
            
            tot_amt = taxable + record.cgst_amount + record.sgst_amount + record.igst_amount
            record.total_amount = tot_amt
            
            record.selling_price = tot_amt + (tot_amt * (record.selling_price_percent / 100.0))

    # STOCK

    total_stock = fields.Float(
        string='Total Stock',
        default=0.0,
    )

    reorder_level = fields.Float(
        string='Reorder Level',
        default=30.0,
    )

    emergency_stock = fields.Float(
        string='Emergency Stock',
        default=0.0,
    )

    quantity = fields.Float(
        string='Stock in Hand',
        compute='_compute_stock_in_hand',
        search='_search_quantity',
    )

    @api.depends("total_stock", "emergency_stock")
    def _compute_stock_in_hand(self):
        for record in self:
            # Calculate reserved stock from active draft/held bills
            lines = self.env['hospital.pharmacy.bill.line'].search([
                ('stock_id', '=', record.id),
                ('bill_id.state', 'in', ['draft', 'held'])
            ])
            reserved = sum(lines.mapped('qty'))
            record.quantity = record.total_stock - record.emergency_stock - reserved

    def _search_quantity(self, operator, value):
        # Fetch all records, evaluate in python
        # This is a small dataset, so it's acceptable.
        self.env.cr.execute("SELECT id FROM hospital_pharmacy_stock")
        ids = [r[0] for r in self.env.cr.fetchall()]
        records = self.browse(ids)
        
        matching_ids = []
        for rec in records:
            if operator == '<':
                if rec.quantity < value: matching_ids.append(rec.id)
            elif operator == '<=':
                if rec.quantity <= value: matching_ids.append(rec.id)
            elif operator == '=':
                if rec.quantity == value: matching_ids.append(rec.id)
            elif operator == '>':
                if rec.quantity > value: matching_ids.append(rec.id)
            elif operator == '>=':
                if rec.quantity >= value: matching_ids.append(rec.id)
                
        return [('id', 'in', matching_ids)]

    is_reorder_needed = fields.Boolean(
        string='Needs Reorder',
        compute='_compute_reorder_needed',
        search='_search_reorder_needed',
    )

    @api.depends('total_stock', 'emergency_stock', 'reorder_level')
    def _compute_reorder_needed(self):
        for rec in self:
            rec.is_reorder_needed = rec.quantity < rec.reorder_level

    def _search_reorder_needed(self, operator, value):
        self.env.cr.execute("SELECT id FROM hospital_pharmacy_stock")
        ids = [r[0] for r in self.env.cr.fetchall()]
        records = self.browse(ids)
        
        matching_ids = []
        # Normalise operator and value
        check_true = False
        if operator == '=' and value is True: check_true = True
        if operator == 'in' and True in value: check_true = True
        
        check_false = False
        if operator == '=' and value is False: check_false = True
        if operator == 'in' and False in value: check_false = True
        
        for rec in records:
            if check_true and rec.quantity < rec.reorder_level:
                matching_ids.append(rec.id)
            elif check_false and rec.quantity >= rec.reorder_level:
                matching_ids.append(rec.id)
                
        # Must return a valid domain, if no ids, return an impossible condition
        if not matching_ids:
            return [('id', '=', -1)]
        return [('id', 'in', matching_ids)]

    # SUPPLIER & REORDERING



    supplier = fields.Char(
        string='Legacy Supplier (Text)',
    )
    
    vendor_ids = fields.Many2many(
        'res.partner',
        string='Connected Vendors',
    )
    
    default_order_qty = fields.Float(
        string='Default Order Quantity',
        default=200.0,
    )




    @api.model_create_multi
    def create(self, vals_list):
        records = super(HospitalPharmacyStock, self).create(vals_list)
        records.env['hospital.pharmacy.stock']._cron_auto_reorder()
        return records

    def write(self, vals):
        res = super(HospitalPharmacyStock, self).write(vals)
        if 'total_stock' in vals or 'emergency_stock' in vals or 'reorder_level' in vals:
            self.env['hospital.pharmacy.stock']._cron_auto_reorder()
        return res


    def action_clear_form(self):
        pass

    def action_close_form(self):
        pass

    def action_save(self):
        # Trigger the automated reorder engine immediately so user doesn't have to wait for cron
        self._cron_auto_reorder()
        
        # Load the fully-formed action from the database so Odoo's frontend doesn't crash missing the 'views' mapping
        # We use sudo() here because regular users don't have direct read access to 'ir.actions.act_window' records
        action = self.env.ref('hospital_management.action_hospital_pharmacy_stock_records').sudo().read()[0]
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Saved successfully',
                'type': 'success',
                'sticky': False,
                'next': action,
            }
        }
    # STATUS

    stock_status = fields.Selection(
        [
            ('available', 'Available'),
            ('low', 'Low Stock'),
            ('critical', 'Critical'),
            ('out', 'Out of Stock'),
            ('expired', 'Expired'),
        ],
        string='Stock Status',
        compute='_compute_stock_status',
        store=True,
    )

    active = fields.Boolean(
        string='Active',
        default=True,
    )

    # COMPUTE STOCK STATUS

    @api.depends('total_stock', 'emergency_stock', 'expiry_date')
    def _compute_stock_status(self):

        for record in self:

            if record.quantity <= 0:
                record.stock_status = 'out'

            elif record.quantity < 20:
                record.stock_status = 'critical'

            elif record.quantity <= 50:
                record.stock_status = 'low'

            else:
                record.stock_status = 'available'
            
    def name_get(self):
        result = []
        for rec in self:
            name = rec.medicine_name
            if rec.batch_number:
                name = f"{name} [{rec.batch_number}]"
            result.append((rec.id, name))
        return result

    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=10, order=None):
        domain = domain or []
        if name:
            domain = [
                '|',
                ('medicine_name', operator, name),
                ('medicine_code', operator, name),
            ] + domain
        return self._search(domain, limit=limit, order=order)


    # AUTOMATED ACTIONS
    
    @api.model
    def _cron_auto_reorder(self):
        # Find all medicines where stock is below reorder level
        low_stock_medicines = self.search([('is_reorder_needed', '=', True)])
        
        for med in low_stock_medicines:
            # Check if an Intent or Draft Order already exists for this medicine
            existing_order = self.env['hospital.pharmacy.purchase.line'].search([
                ('medicine_id', '=', med.id),
                ('purchase_id.state', 'in', ['intent', 'draft'])
            ], limit=1)
            
            if not existing_order:
                # Automatically create an Intent in 'intent' state
                vendor = med.vendor_ids[0] if med.vendor_ids else None
                intent_vals = {
                    'state': 'intent',
                    'supplier_id': vendor.id if vendor else False,
                    'purchase_type': 'stock',
                    'line_ids': [(0, 0, {
                        'medicine_id': med.id,
                        'batch_no': med.batch_number,
                        'qty': 200.0,
                        'purchase_price': med.purchase_price,
                    })]
                }
                
                if vendor:
                    intent_vals['mobile_number'] = vendor.phone if hasattr(vendor, 'phone') else ""
                    parts = []
                    if hasattr(vendor, 'street') and vendor.street: parts.append(vendor.street)
                    if hasattr(vendor, 'street2') and vendor.street2: parts.append(vendor.street2)
                    if hasattr(vendor, 'city') and vendor.city: parts.append(vendor.city)
                    if hasattr(vendor, 'state_id') and vendor.state_id: parts.append(vendor.state_id.name)
                    intent_vals['address'] = ", ".join(parts) if parts else ""
                    
                self.env['hospital.pharmacy.purchase'].create(intent_vals)


