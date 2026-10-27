from odoo import models, fields
from odoo.exceptions import ValidationError


class HospitalRole(models.Model):
    _name = 'hospital.role'
    _description = 'Hospital Role'
    _order = 'name'

    name = fields.Char(
        string='Role',
        required=True
    )

    active = fields.Boolean(
        string='Active',
        default=True
    )

    department_ids = fields.Many2many(
        'hospital.department',
        'hospital_role_department_rel',
        'role_id',
        'department_id',
        string='Departments'
    )

    shift_hours = fields.Float(
        string='Standard Shift Hours',
        default=8.0,
        help='Standard required shift duration in hours for this role (e.g. 5.0 for Doctors, 7.0 for Nurses).'
    )

    def write(self, vals):
        res = super().write(vals)
        if 'shift_hours' in vals:
            attendances = self.env['hr.attendance'].sudo().search([('hospital_role_id', 'in', self.ids)])
            if attendances:
                attendances._compute_shift_details()
        return res

    _unique_role_name = models.Constraint(
        'UNIQUE(name)',
        'Role name must be unique.',
    )
