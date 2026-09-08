from odoo import models, fields, api


class HospitalPharmacyStock(models.Model):
    _name = 'hospital.pharmacy.stock'
    _description = 'Hospital Pharmacy Stock'
    _rec_name = 'medicine_name'
    _order = 'medicine_name asc'

    

    _medicine_code_uniq = models.Constraint(
        'UNIQUE(medicine_code)',
        'This Item Code already exists! Please use a unique Item Code.'
    )

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
        ('Other', 'Other')
    ], string='Category', default='Tablet')

    # BATCH INFORMATION

    batch_number = fields.Char(
        string='Batch Number',
    )

    expiry_date = fields.Date(
        string='Expiry Date',
    )

    # PRICING

    purchase_price = fields.Float(
        string='Purchase Price',
    )

    selling_price = fields.Float(
        string='Selling Price',
    )

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
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Saved & Procurement Checked',
                'message': 'Record saved! Automated procurement engine checked for low stock.',
                'type': 'success',
                'sticky': False,
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

        today = fields.Date.today()

        for record in self:

            if (
                record.expiry_date
                and record.expiry_date < today
            ):
                record.stock_status = 'expired'

            elif record.quantity <= 0:
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
                self.env['hospital.pharmacy.purchase'].create({
                    'state': 'intent',
                    'supplier_id': med.vendor_ids[0].id if med.vendor_ids else False,
                    'purchase_type': 'stock',
                    'line_ids': [(0, 0, {
                        'medicine_id': med.id,
                        'batch_no': med.batch_number,
                        'qty': 200.0,
                        'purchase_price': med.purchase_price,
                    })]
                })


