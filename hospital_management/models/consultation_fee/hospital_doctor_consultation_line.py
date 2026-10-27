from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HospitalDoctorConsultationLine(models.Model):
    _name = 'hospital.doctor.consultation.line'
    _description = 'Doctor Consultation Type and Fee'
    _order = 'doctor_id, consultation_type_id'

    doctor_id = fields.Many2one(
        'hospital.user',
        string='Doctor',
        required=True,
        ondelete='cascade',
    )

    consultation_type_id = fields.Many2one(
        'hospital.consultation.type',
        string='Consultation Type',
        required=True,
        ondelete='restrict',
    )

    fee = fields.Float(
        string='Doctor Fee (Rs.)',
        required=True,
        default=0.0,
    )

    _check_fee_positive = models.Constraint(
        'CHECK(fee >= 0)',
        'Doctor Fee cannot be negative.',
    )

    @api.onchange('consultation_type_id')
    def _onchange_consultation_type_id(self):
        if self.consultation_type_id and self.doctor_id:
            duplicate = self.doctor_id.consultation_line_ids.filtered(
                lambda l: l.consultation_type_id.id == self.consultation_type_id.id and l._origin.id != self._origin.id
            )
            if duplicate:
                selected_name = self.consultation_type_id.name
                self.consultation_type_id = False
                return {
                    'warning': {
                        'title': 'Already Selected',
                        'message': f"Consultation Type '{selected_name}' is already added for this doctor. Please choose a different type.",
                    }
                }

    @api.constrains('doctor_id', 'consultation_type_id')
    def _check_unique_doctor_consultation(self):
        for rec in self:
            if rec.doctor_id and rec.consultation_type_id:
                duplicate = self.search([
                    ('doctor_id', '=', rec.doctor_id.id),
                    ('consultation_type_id', '=', rec.consultation_type_id.id),
                    ('id', '!=', rec.id),
                ], limit=1)
                if duplicate:
                    raise ValidationError(
                        f"Consultation Type '{rec.consultation_type_id.name}' is already added for this Doctor!"
                    )
