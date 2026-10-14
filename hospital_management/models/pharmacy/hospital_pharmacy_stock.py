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



    # IMAGES & SPECS
    image_1920 = fields.Image("Image", max_width=1920, max_height=1920)
    specification_line_ids = fields.One2many(
        'hospital.item.specification.line',
        'stock_id',
        string='Specifications'
    )

    # BASIC MEDICINE INFORMATION
    
    item_type = fields.Selection([
        ('consumable', 'Consumable'),
        ('non_consumable', 'Non-Consumable')
    ], string='Item Type', default='consumable', required=True)
    
    primary_category_id = fields.Many2one(
        'hospital.category.master',
        string='Primary Category',
        domain="[('parent_id', '=', False), ('category_type', 'not in', ['lab_category', 'pharmacy_item_category'])]"
    )

    medicine_name = fields.Char(
        string='Item Name',
        required=True,
    )

    medicine_code = fields.Char(
        string='Item Code',
        required=True,
        copy=False,
    )

    pharmacy_category_id = fields.Many2one(
        'hospital.category.master', 
        string='Secondary Category', 
        domain="[('parent_id', '=', primary_category_id), ('parent_id', '!=', False)]"
    )
    
    additional_category_id = fields.Many2one(
        'hospital.category.master',
        string='Item Category',
        domain="[('parent_id', '=', pharmacy_category_id), ('parent_id', '!=', False)]"
    )

    @api.onchange('primary_category_id')
    def _onchange_primary_category_id(self):
        if self.pharmacy_category_id and self.pharmacy_category_id.parent_id != self.primary_category_id:
            self.pharmacy_category_id = False
            self.additional_category_id = False

    @api.onchange('pharmacy_category_id')
    def _onchange_pharmacy_category_id(self):
        if self.additional_category_id and self.additional_category_id.parent_id != self.pharmacy_category_id:
            self.additional_category_id = False

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
        ('ampoule', 'Ampoules'),
        ('tube', 'Tubes'),
        ('piece', 'Pieces'),
    ], string='Old Item Category', default='strip')
    
    pharmacy_item_category_id = fields.Many2one(
        'hospital.category.master', 
        string='Category', 
        domain="[('category_type', '=', 'pharmacy_item_category')]",
        compute='_compute_pharmacy_item_category_id',
        store=True,
        readonly=False
    )
    
    @api.depends('item_category')
    def _compute_pharmacy_item_category_id(self):
        for rec in self:
            if rec.item_category and not rec.pharmacy_item_category_id:
                name_map = {
                    'strip': 'Strips', 'pack': 'Packs', 'box': 'Boxes',
                    'ampoule': 'Ampoules', 'tube': 'Tubes', 'piece': 'Pieces'
                }
                search_name = name_map.get(rec.item_category, rec.item_category)
                master = self.env['hospital.category.master'].search([
                    ('name', 'ilike', search_name), 
                    ('category_type', '=', 'pharmacy_item_category')
                ], limit=1)
                rec.pharmacy_item_category_id = master.id
    
    qty_in_category = fields.Integer(
        string='Qty in Category',
        default=1,
    )
    
    amount_per_item = fields.Float(
        string='Amount/Item',
        compute='_compute_pricing',
        store=True,
    )

    selling_price = fields.Float(
        string='Selling Amount',
        compute='_compute_pricing',
        store=True,
    )
    
    @api.onchange('item_type')
    def _onchange_item_type(self):
        if self.item_type == 'non_consumable':
            self.discount_percent = 0.0
    
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
    
    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_pricing',
        store=True,
    )

    @api.depends('purchase_price', 'mrp', 'qty_in_category', 'discount_percent', 'cgst', 'sgst', 'igst', 'item_type')
    def _compute_pricing(self):
        for record in self:
            qty = record.qty_in_category if record.qty_in_category > 0 else 1
            amt_per_item = record.purchase_price / qty
            
            if record.item_type == 'non_consumable':
                sell_amt = 0.0
                disc_amt = 0.0
            else:
                sell_amt = record.mrp / qty
                disc_amt = sell_amt * (record.discount_percent / 100.0)
            
            record.amount_per_item = amt_per_item
            record.discount_amount = disc_amt
            
            discounted_sell_amt = sell_amt - disc_amt
            
            # Taxes calculate on top of the discounted Selling Amount for consumables. 
            # For non-consumables, if selling amount is 0, these will be 0 as well. 
            # If they want tax on purchase price for non-consumables, we can calculate it against amt_per_item.
            # But normally tax here is Sales Tax. We will calculate it against discounted_sell_amt.
            if record.item_type == 'non_consumable':
                record.cgst_amount = amt_per_item * (record.cgst / 100.0)
                record.sgst_amount = amt_per_item * (record.sgst / 100.0)
                record.igst_amount = amt_per_item * (record.igst / 100.0)
                record.selling_price = 0.0
                record.total_amount = amt_per_item + record.cgst_amount + record.sgst_amount + record.igst_amount
            else:
                record.cgst_amount = discounted_sell_amt * (record.cgst / 100.0)
                record.sgst_amount = discounted_sell_amt * (record.sgst / 100.0)
                record.igst_amount = discounted_sell_amt * (record.igst / 100.0)
                record.selling_price = sell_amt
                record.total_amount = discounted_sell_amt + record.cgst_amount + record.sgst_amount + record.igst_amount

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
            lines = self.env['hospital.pharmacy.bill.line'].sudo().search([
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
        
        specs_empty = not any([
            self.spec_material, self.spec_colour, self.spec_length, self.spec_width,
            self.spec_weight, self.spec_height, self.spec_shape, self.spec_measurement_range,
            self.spec_accuracy, self.spec_display_type, self.spec_power_source,
            self.spec_battery_type, self.spec_calibration_required, self.spec_calibration_frequency,
            self.spec_sterilization_compatible, self.spec_operating_voltage, self.spec_power_consumption,
            self.spec_response_time, self.spec_memory_function, self.spec_water_resistance,
            self.spec_compatibility, self.spec_country_of_origin, self.spec_certification
        ])

        if specs_empty and not self.env.context.get('ignore_empty_specs'):
            return {
                'name': 'Missing Specifications Warning',
                'type': 'ir.actions.act_window',
                'res_model': 'hospital.empty.specs.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_stock_id': self.id}
            }
        
        return self._action_save_proceed()

    def _action_save_proceed(self):
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
            if 'hospital.asset.purchase.request' in self.env:
                existing_req = self.env['hospital.asset.purchase.request'].sudo().search([
                    ('item_id', '=', med.id),
                    ('state', 'in', ['draft', 'submitted', 'ordered'])
                ], limit=1)
                
                if not existing_req:
                    deficit = (med.reorder_level - med.quantity) if med.reorder_level > med.quantity else 100.0
                    order_qty = max(int(deficit), 10)
                    self.env['hospital.asset.purchase.request'].sudo().create({
                        'item_id': med.id,
                        'quantity': order_qty,
                        'department': 'pharmacy',
                        'reason': 'Auto-generated: Low Stock Warning (Available: %s, Reorder Level: %s)' % (int(med.quantity), int(med.reorder_level)),
                        'state': 'submitted',
                    })
                continue

            # Check if an Intent or Draft Order already exists for this medicine
            existing_order = self.env['hospital.pharmacy.purchase.line'].sudo().search([
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
                    
                self.env['hospital.pharmacy.purchase'].sudo().create(intent_vals)

    # GENERAL SPECIFICATIONS
    spec_material = fields.Char(string='Material / Composition')
    spec_colour = fields.Char(string='Colour / Finish')
    spec_length = fields.Float(string='Length')
    spec_width = fields.Float(string='Width')
    spec_weight = fields.Float(string='Weight')
    spec_height = fields.Float(string='Height')
    spec_shape = fields.Char(string='Shape')
    spec_measurement_range = fields.Char(string='Measurement Range')
    spec_accuracy = fields.Char(string='Accuracy')
    spec_display_type = fields.Char(string='Display Type')
    spec_power_source = fields.Char(string='Power Source')
    spec_battery_type = fields.Char(string='Battery Type')
    spec_calibration_required = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Calibration Required')
    spec_calibration_frequency = fields.Integer(string='Calibration Frequency (Months)')
    spec_sterilization_compatible = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Sterilization Compatible')

    # TECHNICAL SPECIFICATIONS
    spec_operating_voltage = fields.Char(string='Operating Voltage')
    spec_power_consumption = fields.Char(string='Power Consumption')
    spec_response_time = fields.Char(string='Response Time')
    spec_memory_function = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Memory Function')
    spec_water_resistance = fields.Char(string='Water Resistance')
    spec_compatibility = fields.Char(string='Compatibility')
    spec_country_of_origin = fields.Char(string='Country of Origin')
    spec_certification = fields.Char(string='Certification / Standard')

class HospitalItemSpecificationLine(models.Model):
    _name = 'hospital.item.specification.line'
    _description = 'Item Specification Line'

    stock_id = fields.Many2one('hospital.pharmacy.stock', string='Item', ondelete='cascade', required=True)
    name = fields.Char(string='Specification Name', required=True)
    data_type = fields.Selection([
        ('text', 'Text'),
        ('number', 'Number'),
        ('boolean', 'Boolean')
    ], string='Data Type', default='text', required=True)
    
    value = fields.Char(string='Value')
    
    unit = fields.Char(string='Unit', help='e.g., cm, kg, Yes/No')
    is_required = fields.Boolean(string='Required', default=False)

class HospitalEmptySpecsWizard(models.TransientModel):
    _name = 'hospital.empty.specs.wizard'
    _description = 'Empty Specs Warning Wizard'
    
    stock_id = fields.Many2one('hospital.pharmacy.stock', required=True)
    
    def action_proceed(self):
        return self.stock_id.with_context(ignore_empty_specs=True)._action_save_proceed()
