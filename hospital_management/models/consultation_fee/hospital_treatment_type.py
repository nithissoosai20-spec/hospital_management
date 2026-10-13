from odoo import models, fields


class HospitalTreatmentType(models.Model):
    _name = 'hospital.treatment.type'
    _description = 'Hospital Treatment Type'
    _order = 'name asc'

    name = fields.Char(string='Treatment Type', required=True)
    code = fields.Char(string='Code')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)

