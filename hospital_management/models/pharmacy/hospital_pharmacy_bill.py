from datetime import datetime
import pytz
from odoo import api, fields, models
from odoo.exceptions import UserError


class HospitalPharmacyBill(models.Model):
    _name = 'hospital.pharmacy.bill'
    _description = 'Pharmacy Bill'
    _order = 'id desc'

    name = fields.Char(
        string='Bill Number',
        required=True,
        readonly=True,
        copy=False,
        default='Create Bill',
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
    )

    walkin_name = fields.Char(string='Walk-in Name')
    walkin_phone = fields.Char(string='Walk-in Phone')
    walkin_address = fields.Char(string='Walk-in Address')

    customer_name = fields.Char(
        string='Customer Name',
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

    
    round_off = fields.Float(
        string='Round Off',
        compute='_compute_amounts',
        store=True,
    )

    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_amounts',
        store=True,
    )


    prescription_ids = fields.Many2many(
        'hospital.prescription',
        string='Prescriptions'
    )

    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        if self.patient_id:
            prescriptions = self.env['hospital.prescription'].search([
                ('patient_id', '=', self.patient_id.id),
                ('state', '=', 'draft')
            ])
            if prescriptions:
                self.prescription_ids = [(6, 0, prescriptions.ids)]
                lines = []
                for p in prescriptions:
                    for p_line in p.line_ids:
                        lines.append((0, 0, {
                            'stock_id': p_line.medicine_id.id,
                            'medicine_name': p_line.medicine_id.medicine_name,
                            'qty': p_line.qty,
                            'mrp': p_line.medicine_id.total_amount,
                            'available_stock': p_line.medicine_id.quantity,
                            'batch': p_line.medicine_id.batch_number or '',
                            'expiry': p_line.medicine_id.expiry_date or '',
                            'cgst_percent': p_line.medicine_id.cgst,
                            'sgst_percent': p_line.medicine_id.sgst,
                            'igst_percent': p_line.medicine_id.igst,
                        }))
                self.line_ids = lines

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
            if vals.get('name', 'Create Bill') == 'Create Bill':
                vals['name'] = sequence.next_by_code(
                    'hospital.pharmacy.bill'
                ) or 'PH-BILL-000001'

            # Auto-link prescriptions if patient_id is provided and no prescriptions linked
            if vals.get('patient_id') and 'prescription_ids' not in vals:
                prescriptions = self.env['hospital.prescription'].search([
                    ('patient_id', '=', vals['patient_id']),
                    ('state', '=', 'draft')
                ])
                if prescriptions:
                    vals['prescription_ids'] = [(6, 0, prescriptions.ids)]

        records = super().create(vals_list)
        for record in records:
            if record.state == 'paid':
                record._reduce_stock()
                record.prescription_ids.write({'state': 'billed'})
        return records


    def write(self, vals):
        res = super().write(vals)
        if vals.get('state') == 'paid':
            for record in self:
                record._reduce_stock()
                record.prescription_ids.write({'state': 'billed'})
        return res


    def _reduce_stock(self):
        for line in self.line_ids:
            stock = line.stock_id
            if not stock and line.medicine_name:
                stock = self.env['hospital.pharmacy.stock'].search([
                    '|',
                    ('medicine_name', '=', line.medicine_name),
                    ('medicine_code', '=', line.medicine_name),
                ], limit=1)
            if stock and line.qty > 0:
                new_qty = stock.total_stock - line.qty
                stock.total_stock = max(new_qty, 0.0)


    @api.depends(
        'line_ids.amount',
        'line_ids.discount_amount',
        'line_ids.gst_amount',
        'line_ids.total_amount',
        'bill_discount',
    )
    def _compute_amounts(self):
        for bill in self:
            subtotal = sum(bill.line_ids.mapped('amount'))
            line_discount = sum(bill.line_ids.mapped('discount_amount'))
            line_gst = sum(bill.line_ids.mapped('gst_amount'))
            
            taxable = subtotal - line_discount - bill.bill_discount
            
            total_calculated = sum(bill.line_ids.mapped('total_amount')) - bill.bill_discount
            
            rounded_total = round(total_calculated)
            round_off = rounded_total - total_calculated

            bill.subtotal = subtotal
            bill.discount_amount = line_discount + bill.bill_discount
            bill.taxable_amount = taxable
            bill.gst_amount = line_gst
            bill.round_off = round_off
            bill.total_amount = rounded_total

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

            # Deduct from Total Stock
            for line in bill.bill_line_ids:
                if line.stock_id:
                    if line.stock_id.total_stock < line.qty:
                        raise UserError(f'Not enough stock for {line.stock_id.medicine_name}.')
                    line.stock_id.total_stock -= line.qty

            bill.state = 'paid'
            bill.prescription_ids.write({'state': 'billed'})
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

    free_qty = fields.Integer(
        string='Free Qty',
        default=0,
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

    cgst_percent = fields.Float(string='CGST %', default=0.0)
    sgst_percent = fields.Float(string='SGST %', default=0.0)
    igst_percent = fields.Float(string='IGST %', default=0.0)

    amount = fields.Float(
        string='Amount',
        compute='_compute_amounts',
        store=True,
    )

    cgst = fields.Float(string='CGST', compute='_compute_amounts', store=True)
    sgst = fields.Float(string='SGST', compute='_compute_amounts', store=True)
    igst = fields.Float(string='IGST', compute='_compute_amounts', store=True)

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

    
    round_off = fields.Float(
        string='Round Off',
        compute='_compute_amounts',
        store=True,
    )

    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_amounts',
        store=True,
    )

    @api.onchange('stock_id')
    def _onchange_stock_id(self):
        if self.stock_id:
            s = self.stock_id
            self.medicine_name = s.medicine_name
            self.batch = s.batch_number or ''
            self.expiry = s.expiry_date or ''
            # self.expiry = str(s.expiry_date) if s.expiry_date else ''
            self.available_stock = s.quantity
            self.mrp = s.total_amount
            self.cgst_percent = s.cgst
            self.sgst_percent = s.sgst
            self.igst_percent = s.igst
        else:
            self.batch = ''
            self.expiry = ''
            self.available_stock = 0.0

    @api.depends(
        'qty',
        'mrp',
        'discount',
        'cgst_percent',
        'sgst_percent',
        'igst_percent',
    )
    def _compute_amounts(self):
        for line in self:
            amt = line.qty * line.mrp
            disc_amt = amt * line.discount / 100.0
            taxable = amt - disc_amt

            c_amt = taxable * line.cgst_percent / 100.0
            s_amt = taxable * line.sgst_percent / 100.0
            i_amt = taxable * line.igst_percent / 100.0

            line.amount = amt
            line.discount_amount = disc_amt
            line.taxable_amount = taxable
            line.cgst = c_amt
            line.sgst = s_amt
            line.igst = i_amt
            line.gst_amount = c_amt + s_amt + i_amt
            line.total_amount = taxable + line.gst_amount

    def get_patient_title_name(self):
        self.ensure_one()
        name = (self.patient_id.name if self.patient_id else self.walkin_name) or ''
        name = name.strip()
        if not name:
            return ''
        lower_name = name.lower()
        if lower_name.startswith(('mr.', 'mr ', 'mrs.', 'mrs ', 'ms.', 'ms ', 'dr.', 'dr ')):
            return name
        gender = (self.patient_id.gender or '').lower() if self.patient_id else ''
        if gender == 'male':
            return f"Mr. {name}"
        elif gender == 'female':
            return f"Mrs. {name}"
        return name

    def get_doctor_title_name(self):
        self.ensure_one()
        name = (self.doctor_id.name or '').strip()
        if not name:
            return ''
        lower_name = name.lower()
        if lower_name.startswith(('dr.', 'dr ')):
            return name
        return f"Dr. {name}"

    def get_exact_current_time(self):
        user_tz = self.env.user.tz or 'Asia/Kolkata'
        try:
            user_pytz = pytz.timezone(user_tz)
        except Exception:
            user_pytz = pytz.timezone('Asia/Kolkata')
        return datetime.now(user_pytz).strftime('%d-%b-%Y %I:%M %p')
