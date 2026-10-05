from odoo import api, fields, models

class AssetAllocationLog(models.Model):
    _name = 'hospital.asset.allocation.log'
    _description = 'Asset Allocation Log'

    equipment_id = fields.Many2one('maintenance.equipment', required=True)
    user_id = fields.Many2one('res.users', string="Assigned To", required=True)
    assigned_by = fields.Many2one('res.users', default=lambda self: self.env.uid)
    date_assigned = fields.Datetime(default=fields.Datetime.now)
    date_returned = fields.Datetime(readonly=True)
    return_condition = fields.Text(string="Condition on Return")
    status = fields.Selection([
        ('active', 'Currently Assigned'),
        ('returned', 'Returned')
    ], default='active')
