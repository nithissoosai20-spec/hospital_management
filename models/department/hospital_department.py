from odoo import models, fields


class HospitalDepartment(models.Model):
    _name = 'hospital.department'
    _description = 'Hospital Department'
    _order = 'name'

    name = fields.Char(
        string='Department',
        required=True
    )

    role_ids = fields.Many2many(
        'hospital.role',
        'hospital_role_department_rel',
        'department_id',
        'role_id',
        string='Allowed Roles'
    )


class HospitalDesignation(models.Model):
    _name = 'hospital.designation'
    _description = 'Hospital Designation'
    _order = 'name'

    name = fields.Char(
        string='Designation',
        required=True
    )

    department_id = fields.Many2one(
        'hospital.department',
        string='Department',
        required=True,
        ondelete='cascade'
    )


class HospitalReportingPerson(models.Model):
    _name = 'hospital.reporting.person'
    _description = 'Hospital Reporting Person'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True
    )

    department_id = fields.Many2one(
        'hospital.department',
        string='Department',
        required=True,
        ondelete='cascade'
    )