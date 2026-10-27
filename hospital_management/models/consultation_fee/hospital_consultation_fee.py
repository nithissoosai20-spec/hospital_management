from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HospitalConsultationFee(models.Model):
    _name = 'hospital.consultation.fee'
    _description = 'Hospital Consultation Fee'
    _order = 'department_id, designation_id'

    def init(self):
        super().init()
        self.env.cr.execute("""
            ALTER TABLE hospital_consultation_fee 
            DROP CONSTRAINT IF EXISTS hospital_consultation_fee_unique_department_id_designation_id;
            ALTER TABLE hospital_consultation_fee 
            DROP CONSTRAINT IF EXISTS hospital_consultation_fee_department_id_designation_id_uniq;
        """)

    def _compute_display_name(self):
        for rec in self:
            parts = []
            if rec.department_id:
                parts.append(rec.department_id.name)
            if rec.designation_id:
                parts.append(rec.designation_id.name)
            if rec.consultation_type_id:
                parts.append(rec.consultation_type_id.name)
            if rec.doctor_id:
                parts.append(f"Dr. {rec.doctor_id.name}")
            rec.display_name = " - ".join(parts) if parts else "Consultation Fee"

    _check_amount_positive = models.Constraint(
        'CHECK(amount >= 0)',
        'Consultation Fee cannot be negative.',
    )

    department_id = fields.Many2one(
        'hospital.department',
        string='Department',
        required=True,
        ondelete='cascade',
    )

    designation_id = fields.Many2one(
        'hospital.designation',
        string='Designation',
        required=True,
        ondelete='cascade',
        domain="[('department_id', '=', department_id)]",
    )

    consultation_type_id = fields.Many2one(
        'hospital.consultation.type',
        string='Consultation Type',
    )

    doctor_id = fields.Many2one(
        'hospital.user',
        string='Doctor',
        domain="[('role_id.name', '=', 'Doctor'), ('department_id', '=', department_id)]",
        help="Optional: Set a specific fee for this doctor. Leave blank for standard department fee."
    )

    amount = fields.Float(
        string='Consultation Fee',
        required=True,
        default=0.0,
    )

    active = fields.Boolean(
        string='Active',
        default=True,
    )

    def action_save(self):
        action = self.env.ref('hospital_management.action_hospital_consultation_fees').sudo().read()[0]
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

    def action_clear(self):
        for rec in self:
            rec.department_id = False
            rec.designation_id = False
            rec.consultation_type_id = False
            rec.doctor_id = False
            rec.amount = 0.0
            rec.active = True

    def action_close(self):
        return self.env.ref('hospital_management.action_hospital_consultation_fees').sudo().read()[0]

    @api.onchange('department_id')
    def _onchange_department_id(self):
        self.designation_id = False
        self.doctor_id = False

    @api.onchange('doctor_id')
    def _onchange_doctor_id(self):
        if self.doctor_id:
            if self.doctor_id.department_id:
                self.department_id = self.doctor_id.department_id
            if self.doctor_id.designation_id:
                self.designation_id = self.doctor_id.designation_id

    @api.constrains('department_id', 'designation_id')
    def _check_designation_department(self):
        for record in self:
            if (
                record.department_id
                and record.designation_id
                and record.designation_id.department_id != record.department_id
            ):
                raise ValidationError(
                    'The selected Designation does not belong to the selected Department.'
                )

    @api.constrains('department_id', 'designation_id', 'consultation_type_id', 'doctor_id')
    def _check_unique_consultation_fee(self):
        for record in self:
            if not record.active:
                continue
            domain = [
                ('id', '!=', record.id),
                ('active', '=', True),
                ('department_id', '=', record.department_id.id),
                ('designation_id', '=', record.designation_id.id),
                ('consultation_type_id', '=', record.consultation_type_id.id if record.consultation_type_id else False),
                ('doctor_id', '=', record.doctor_id.id if record.doctor_id else False),
            ]
            if self.search_count(domain) > 0:
                doc_str = f" for Doctor '{record.doctor_id.name}'" if record.doctor_id else ""
                type_str = f" and Consultation Type '{record.consultation_type_id.name}'" if record.consultation_type_id else ""
                raise ValidationError(
                    f"A consultation fee already exists for this Department, Designation{type_str}{doc_str}."
                )
