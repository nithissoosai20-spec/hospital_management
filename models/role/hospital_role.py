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

    _sql_constraints = [
        (
            'hospital_role_name_unique',
            'UNIQUE(name)',
            'Role name must be unique.'
        ),
    ]