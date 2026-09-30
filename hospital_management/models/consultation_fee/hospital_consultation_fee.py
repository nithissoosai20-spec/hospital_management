from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HospitalConsultationFee(models.Model):
    _name = 'hospital.consultation.fee'
    _description = 'Hospital Consultation Fee'
    _order = 'department_id, designation_id'

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = 'Consultation Fee'

    _constraints = [
        models.Constraint(
            'unique(department_id, designation_id)',
            'A consultation fee already exists for this Department and Designation.',
        ),
        models.Constraint(
            'CHECK(amount >= 0)',
            'Consultation Fee cannot be negative.',
        ),
    ]

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
        # Implicitly saves in Odoo.
        pass

    def action_clear(self):
        for rec in self:
            rec.department_id = False
            rec.designation_id = False
            rec.amount = 0.0
            rec.active = True

    def action_close(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Consultation Fees',
            'res_model': 'hospital.consultation.fee',
            'view_mode': 'list,form',
            'target': 'current',
        }


    @api.onchange('department_id')
    def _onchange_department_id(self):
        self.designation_id = False

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

    def action_save(self):
        """
        Dummy method to trigger form save.
        In Odoo, clicking a type="object" button automatically saves the record first.
        """
        return True
