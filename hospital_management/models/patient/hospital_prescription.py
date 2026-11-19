from odoo import models, fields, api

class HospitalPrescription(models.Model):
    _name = 'hospital.prescription'
    _description = 'Medicine Prescription'
    _order = 'id desc'

    name = fields.Char(
        string='Prescription ID',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )
    
    patient_id = fields.Many2one(
        'hospital.patient',
        string='Patient',
        required=True,
        ondelete='restrict'
    )
    
    doctor_id = fields.Many2one(
        'hospital.user',
        string='Prescribing Doctor',
        domain="[('role_id.name', 'ilike', 'doctor')]",
        ondelete='restrict'
    )
    
    date_prescribed = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
        required=True
    )
    
    state = fields.Selection([
        ('draft', 'Prescribed'),
        ('billed', 'Billed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    
    line_ids = fields.One2many(
        'hospital.prescription.line',
        'prescription_id',
        string='Medicines'
    )
    
    medicine_names = fields.Char(
        string='Prescribed Medicines',
        compute='_compute_medicine_names',
    )
    
    @api.depends('line_ids', 'line_ids.medicine_id')
    def _compute_medicine_names(self):
        for rec in self:
            rec.medicine_names = ', '.join([line.medicine_id.display_name for line in rec.line_ids if line.medicine_id])
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.prescription') or 'New'
        return super().create(vals_list)

class HospitalPrescriptionLine(models.Model):
    _name = 'hospital.prescription.line'
    _description = 'Prescription Line'

    prescription_id = fields.Many2one(
        'hospital.prescription',
        string='Prescription',
        ondelete='cascade',
        required=True
    )
    
    medicine_id = fields.Many2one(
        'hospital.pharmacy.stock',
        string='Medicine',
        required=True
    )

    state = fields.Selection(related='prescription_id.state', string='Status', store=False)
    date_prescribed = fields.Datetime(related='prescription_id.date_prescribed', string='Date', store=False)
    
    qty = fields.Integer(string='Total Qty', default=1)
    
    morning = fields.Boolean(string='Morning')
    afternoon = fields.Boolean(string='Afternoon')
    evening = fields.Boolean(string='Evening')
    night = fields.Boolean(string='Night')
    
    timing = fields.Selection([
        ('before', 'Before Meal'),
        ('after', 'After Meal')
    ], string='Instructions', default='after')

    dosage_display = fields.Char(string='Dosage / Timing', compute='_compute_dosage_display')

    @api.depends('morning', 'afternoon', 'evening', 'night', 'timing')
    def _compute_dosage_display(self):
        for rec in self:
            m = '1' if rec.morning else '0'
            a = '1' if rec.afternoon else '0'
            e = '1' if rec.evening else '0'
            n = '1' if rec.night else '0'
            timing_str = 'Before Meal' if rec.timing == 'before' else 'After Meal'
            rec.dosage_display = f"{m}-{a}-{e}-{n} ({timing_str})"

