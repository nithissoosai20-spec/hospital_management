from odoo import api, fields, models, _

class HospitalAssetScrap(models.Model):
    _name = 'hospital.asset.scrap'
    _description = 'Asset Scrap'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment', required=True)
    reason = fields.Text(string='Reason')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], string='Status', default='draft')

    def action_validate(self):
        for rec in self:
            if rec.name == 'New':
                rec.name = self.env['ir.sequence'].next_by_code('hospital.asset.scrap.seq') or 'New'
            rec.state = 'done'
            rec.equipment_id.active = False
