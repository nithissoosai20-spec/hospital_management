from odoo import api, fields, models
from odoo.exceptions import UserError


class HospitalPharmacyBill(models.Model):
    _name = 'hospital.pharmacy.bill'
    _description = 'Pharmacy Bill'
    _order = 'id desc'

    name = fields.Char(
        string='Bill Number',
        required=True,
        ondelete='cascade',
        readonly=True,
        copy=False,
        default='New',
    )

    patient_id = fields.Many2one(
        'hospital.patient',
        string='Patient',
        ondelete='restrict',
    )

    appointment_id = fields.Many2one(
        'hospital.appointment',
        string='Appointment',
        ondelete='set null',
    )

    doctor_id = fields.Many2one(
        'hospital.user',
        string='Doctor',
        domain="[('role_id.name', 'ilike', 'doctor')]",
        ondelete='set null',
    )

    doctor_department_id = fields.Many2one(
        'hospital.department',
        string='Department',
        readonly=True,
    )

    bill_date = fields.Datetime(
        string='Bill Date',
        default=fields.Datetime.now,
        required=True,
        ondelete='cascade',
    )

    walkin_name = fields.Char(string='Walk-in Name')
    walkin_phone = fields.Char(string='Walk-in Phone')
    walkin_address = fields.Char(string='Walk-in Address')

    customer_name = fields.Char(
        string='Patient',
        compute='_compute_customer_name',
        store=True
    )

    @api.depends('customer_type', 'patient_id.name', 'walkin_name')
    def _compute_customer_name(self):
        for rec in self:
            if rec.customer_type == 'walkin':
                rec.customer_name = rec.walkin_name or ''
            else:
                rec.customer_name = rec.patient_id.name if rec.patient_id else ''

    customer_type = fields.Selection(
        [
            ('patient', 'Patient'),
            ('walkin', 'Walk-in'),
        ],
        string='Mode',
        default='patient',
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('held', 'Hold'),
            ('paid', 'Paid'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        ondelete='cascade',
        copy=False,
    )

    payment_mode = fields.Selection(
        [
            ('cash', 'Cash'),
            ('card', 'Card'),
            ('upi', 'UPI'),
            ('wallet', 'Wallet'),
            ('insurance', 'Insurance'),
            ('others', 'Others'),
        ],
        string='Payment Mode',
        default='cash',
    )

    paid_amount = fields.Float(
        string='Paid Amount',
        default=0.0,
    )

    bill_discount = fields.Float(
        string='Discount',
        default=0.0,
    )

    notes = fields.Text(
        string='Notes',
    )

    line_ids = fields.One2many(
        'hospital.pharmacy.bill.line',
        'bill_id',
        string='Medicine Items',
        copy=True,
    )

    subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_amounts',
        store=True,
    )

    discount_amount = fields.Float(
        string='Discount Amount',
        compute='_compute_amounts',
        store=True,
    )

    taxable_amount = fields.Float(
        string='Taxable Amount',
        compute='_compute_amounts',
        store=True,
    )

    gst_amount = fields.Float(
        string='GST',
        compute='_compute_amounts',
        store=True,
    )

    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_amounts',
        store=True,
    )

    @api.onchange('doctor_id')
    def _onchange_doctor_id(self):
        if self.doctor_id and self.doctor_id.department_id:
            self.doctor_department_id = self.doctor_id.department_id
        else:
            self.doctor_department_id = False

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env['ir.sequence']

        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = sequence.next_by_code(
                    'hospital.pharmacy.bill'
                ) or 'PH-BILL-000001'

        records = super().create(vals_list)
        for record in records:
            if record.state == 'paid':
                record._reduce_stock()
        return records

    def write(self, vals):
        # Check if transitioning to paid
        res = super().write(vals)
        if vals.get('state') == 'paid':
            for record in self:
                record._reduce_stock()
        return res

    def _reduce_stock(self):
        for line in self.line_ids:
            if line.stock_id:
                line.stock_id.total_stock -= line.qty
            else:
                # Try to find stock by name or code if stock_id isn't explicitly linked
                stock = self.env['hospital.pharmacy.stock'].search([
                    '|', 
                    ('medicine_name', '=', line.medicine_name),
                    ('medicine_code', '=', line.medicine_name)
                ], limit=1)
                if stock:
                    stock.total_stock -= line.qty


    @api.depends(
        'line_ids.amount',
        'line_ids.discount_amount',
        'line_ids.gst_amount',
        'bill_discount',
    )
    def _compute_amounts(self):
        for bill in self:
            subtotal = sum(
                bill.line_ids.mapped('amount')
            )

            line_discount = sum(
                bill.line_ids.mapped('discount_amount')
            )

            line_gst = 0.0

            taxable = subtotal - bill.bill_discount

            if taxable < 0:
                taxable = 0.0

            bill.subtotal = subtotal
            bill.total_amount = taxable

    def action_save_draft(self):
        for bill in self:
            if bill.state not in ('draft', 'held'):
                continue

            bill.state = 'draft'

        return True

    def action_hold(self):
        for bill in self:
            if bill.state != 'paid':
                bill.state = 'held'

        return True

    def action_cancel(self):
        for bill in self:
            if bill.state != 'paid':
                bill.state = 'cancelled'

        return True

    def action_collect_payment(self):
        for bill in self:
            if bill.state == 'paid':
                continue

            if bill.total_amount <= 0:
                raise UserError('Cannot collect payment for an empty bill.')

            if bill.paid_amount == 0.0:
                bill.paid_amount = bill.total_amount
            elif bill.paid_amount < bill.total_amount:
                raise UserError('Please enter a Paid Amount equal to or greater than the Total Amount.')

            bill.state = 'paid'

        return True


class HospitalPharmacyBillLine(models.Model):
    _name = 'hospital.pharmacy.bill.line'
    _description = 'Pharmacy Bill Line'
    _order = 'id'

    bill_id = fields.Many2one(
        'hospital.pharmacy.bill',
        string='Bill',
        required=True,
        ondelete='cascade',
    )

    stock_id = fields.Many2one(
        'hospital.pharmacy.stock',
        string='Medicine',
        ondelete='set null',
    )

    medicine_name = fields.Char(
        string='Medicine Name',
        required=True,
        ondelete='cascade',
    )

    composition = fields.Char(
        string='Composition',
    )

    batch = fields.Char(
        string='Batch No.',
    )

    expiry = fields.Char(
        string='Expiry Date',
    )

    available_stock = fields.Float(
        string='Stock',
        readonly=True,
        default=0.0,
    )

    qty = fields.Float(
        string='Quantity',
        default=1.0,
    )

    unit = fields.Char(
        string='Unit',
        default='Tab',
    )

    mrp = fields.Float(
        string='MRP',
        default=0.0,
    )

    discount = fields.Float(
        string='Discount %',
        default=0.0,
    )

    gst = fields.Float(
        string='GST %',
        default=12.0,
    )

    amount = fields.Float(
        string='Amount',
        compute='_compute_amounts',
        store=True,
    )

    discount_amount = fields.Float(
        string='Discount Amount',
        compute='_compute_amounts',
        store=True,
    )

    taxable_amount = fields.Float(
        string='Taxable Amount',
        compute='_compute_amounts',
        store=True,
    )

    gst_amount = fields.Float(
        string='GST Amount',
        compute='_compute_amounts',
        store=True,
    )

    @api.onchange('stock_id')
    def _onchange_stock_id(self):
        if self.stock_id:
            s = self.stock_id
            self.medicine_name = s.medicine_name
            self.batch = s.batch_number or ''
            self.expiry = str(s.expiry_date) if s.expiry_date else ''
            self.available_stock = s.quantity
            self.mrp = s.selling_price
        else:
            self.batch = ''
            self.expiry = ''
            self.available_stock = 0.0

    @api.depends(
        'qty',
        'mrp',
        'discount',
        'gst',
    )
    def _compute_amounts(self):
        for line in self:
            gross = line.qty * line.mrp

            discount_amount = (
                gross * line.discount / 100.0
            )

            taxable = gross - discount_amount

            gst_amount = 0.0

            line.amount = taxable
            line.discount_amount = discount_amount
            line.taxable_amount = taxable
            line.gst_amount = gst_amount
            