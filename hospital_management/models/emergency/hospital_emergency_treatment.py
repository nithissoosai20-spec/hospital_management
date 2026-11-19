from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HospitalEmergencyTreatment(models.Model):
    _name = 'hospital.emergency.treatment'
    _description = 'Emergency Treatment & Inpatient Admission'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'admission_date desc, id desc'

    name = fields.Char(
        string='Emergency Code',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        index=True
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )

    # ---------------------------------------------------------
    # PATIENT CORE DETAILS
    # ---------------------------------------------------------
    patient_id = fields.Many2one(
        'hospital.patient',
        string='Existing Patient',
        help='Optional: Link to an existing registered hospital patient'
    )
    patient_name = fields.Char(
        string='Patient Name',
        tracking=True
    )
    age = fields.Integer(
        string='Age'
    )
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Gender', default='male')

    phone = fields.Char(
        string='Phone Number',
        tracking=True
    )
    blood_group = fields.Char(
        string='Blood Group',
        tracking=True
    )

    admission_date = fields.Datetime(
        string='Emergency / Arrival Date',
        default=fields.Datetime.now,
        tracking=True
    )

    # ---------------------------------------------------------
    # ADMISSION ENTRY SOURCES (From Mentor Chart)
    # ---------------------------------------------------------
    entry_source = fields.Selection([
        ('op', 'OP (Out-Patient)'),
        ('referred_doctor', 'Referred by Doctor'),
        ('emergency', 'Emergency'),
        ('direct', 'Direct'),
        ('other_hospital', 'Other Hospital')
    ], string='Admission Entry Source', default='emergency', tracking=True)

    # Attender / Guardian Details
    attender_name = fields.Char(
        string='Attender / Guardian Name',
        tracking=True
    )
    attender_relation = fields.Selection([
        ('spouse', 'Spouse'),
        ('parent', 'Parent / Guardian'),
        ('child', 'Child / Son / Daughter'),
        ('sibling', 'Brother / Sister'),
        ('friend', 'Friend / Colleague'),
        ('ambulance_staff', 'Ambulance Staff'),
        ('other', 'Other')
    ], string='Attender Relationship', default='spouse')
    attender_phone = fields.Char(
        string='Attender Phone'
    )

    # Referral & Transfer Details
    referring_doctor = fields.Char(
        string='Referring Doctor / Clinic Name'
    )
    transferring_hospital = fields.Char(
        string='Transferring Hospital Name'
    )
    referral_notes = fields.Text(
        string='Referral / Transfer Notes'
    )

    # ---------------------------------------------------------
    # CLIENT COVERAGE & INSURANCE / MEDICLAIM
    # ---------------------------------------------------------
    coverage_type = fields.Selection([
        ('self_pay', 'Self-Pay / Cash'),
        ('mediclaim', 'Mediclaim'),
        ('private_insurance', 'Private Insurance'),
        ('state_govt', 'State Govt Insurance (CMCHIS)'),
        ('central_govt', 'Central Govt Insurance (PM-JAY / CGHS / ECHS)')
    ], string='Coverage / Payment Mode', default='self_pay', tracking=True)

    has_insurance = fields.Boolean(
        string='Has Insurance / Mediclaim',
        compute='_compute_has_insurance',
        store=True
    )
    insurance_provider = fields.Char(
        string='Insurance / TPA Provider Name'
    )
    policy_number = fields.Char(
        string='Policy / Card / Beneficiary ID'
    )
    mediclaim_number = fields.Char(
        string='Mediclaim / Pre-Auth Reference'
    )
    claim_status = fields.Selection([
        ('not_applicable', 'Not Applicable'),
        ('pending', 'Pre-Auth Pending'),
        ('approved', 'Pre-Auth Approved'),
        ('rejected', 'Claim Denied / Rejected')
    ], string='Claim Status', default='not_applicable', tracking=True)

    # ---------------------------------------------------------
    # CLINICAL TRIAGE & NOTES
    # ---------------------------------------------------------
    triage_level = fields.Selection([
        ('red', 'Priority 1 - Critical / Resuscitation'),
        ('yellow', 'Priority 2 - Emergency / Urgent'),
        ('green', 'Priority 3 - Non-Urgent / Stable')
    ], string='Triage Level', default='yellow', tracking=True)

    chief_complaint = fields.Text(
        string='Chief Complaint / Emergency Condition'
    )
    treatment_notes = fields.Text(
        string='Emergency Care & Procedures Given'
    )

    # ---------------------------------------------------------
    # WORKFLOW STATUS (From Mentor Diagram)
    # ---------------------------------------------------------
    state = fields.Selection([
        ('pre_admission', 'Pre-Admission'),
        ('observation', 'Under Observation'),
        ('admitted', 'Admitted to IP'),
        ('discharged', 'Discharged / Complete'),
        ('transferred', 'Transferred Out')
    ], string='Status', default='pre_admission', tracking=True, copy=False)

    # ---------------------------------------------------------
    # COMPUTES & ONCHANGES
    # ---------------------------------------------------------
    @api.depends('coverage_type')
    def _compute_has_insurance(self):
        for rec in self:
            rec.has_insurance = rec.coverage_type != 'self_pay'

    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        if self.patient_id:
            self.patient_name = self.patient_id.name
            self.age = self.patient_id.age
            self.gender = self.patient_id.gender or 'male'
            self.phone = self.patient_id.phone

    @api.onchange('coverage_type')
    def _onchange_coverage_type(self):
        if self.coverage_type == 'self_pay':
            self.claim_status = 'not_applicable'
        elif self.claim_status == 'not_applicable':
            self.claim_status = 'pending'

    # ---------------------------------------------------------
    # CRUD OVERRIDES
    # ---------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.emergency.treatment') or _('New')
        return super().create(vals_list)

    # ---------------------------------------------------------
    # WORKFLOW & FORM ACTIONS
    # ---------------------------------------------------------
    def action_save(self):
        self.ensure_one()
        if not self.patient_name or not self.patient_name.strip():
            raise ValidationError(_("Please enter Patient Name before saving."))
        action = self.env['ir.actions.act_window']._for_xml_id('hospital_management.action_hospital_emergency_treatment')
        action['target'] = 'main'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Saved'),
                'message': _('Emergency Treatment record %s saved successfully.') % (self.name or ''),
                'type': 'success',
                'sticky': False,
                'next': action,
            }
        }

    def action_close(self):
        for rec in self:
            if not rec.patient_name or not rec.patient_name.strip():
                rec.unlink()
        action = self.env['ir.actions.act_window']._for_xml_id('hospital_management.action_hospital_emergency_treatment')
        action['target'] = 'main'
        return action

    def action_clear(self):
        for rec in self:
            rec.patient_id = False
            rec.patient_name = False
            rec.phone = False
            rec.age = 0
            rec.gender = 'male'
            rec.blood_group = False
            rec.entry_source = 'emergency'
            rec.attender_name = False
            rec.attender_relation = 'spouse'
            rec.attender_phone = False
            rec.referring_doctor = False
            rec.transferring_hospital = False
            rec.referral_notes = False
            rec.coverage_type = 'self_pay'
            rec.insurance_provider = False
            rec.policy_number = False
            rec.mediclaim_number = False
            rec.claim_status = 'not_applicable'
            rec.triage_level = 'yellow'
            rec.chief_complaint = False
            rec.treatment_notes = False

    def action_send_to_observation(self):
        self.write({'state': 'observation'})

    def action_admit_ip(self):
        self.write({'state': 'admitted'})

    def action_discharge(self):
        self.write({'state': 'discharged'})

    def action_transfer(self):
        self.write({'state': 'transferred'})

    def action_reset_pre_admission(self):
        self.write({'state': 'pre_admission'})
