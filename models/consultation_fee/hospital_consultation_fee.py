from odoo import models, fields, api


class HospitalConsultationFee(models.Model):
    _name = 'hospital.consultation.fee'
    _description = 'Hospital Consultation Fee'
    _order = 'department_id, designation_id'

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

    _sql_constraints = [
        (
            'unique_department_designation',
            'unique(department_id, designation_id)',
            'A consultation fee already exists for this Department and Designation.'
        ),
        (
            'positive_amount',
            'CHECK(amount >= 0)',
            'Consultation Fee cannot be negative.'
        ),
    ]

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
                raise models.ValidationError(
                    'The selected Designation does not belong to the selected Department.'
                )

    def action_save(self):
        """
        Dummy method to trigger form save.
        In Odoo, clicking a type="object" button automatically saves the record first.
        """
        return True
