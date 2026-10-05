from odoo import api, fields, models

class MaintenanceTeam(models.Model):
    _inherit = 'maintenance.team'

    def action_custom_save(self):
        # The form is inherently saved when type="object" is clicked in Odoo 16+
        return self.env.ref('maintenance.maintenance_team_action_settings').sudo().read()[0]

    def action_custom_clear(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
