from odoo import api, fields, models

class MaintenanceTeam(models.Model):
    _inherit = 'maintenance.team'

    def action_custom_save(self):
        action = self.env.ref('maintenance.maintenance_team_action_settings').sudo().read()[0]
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Record saved successfully!',
                'type': 'success',
                'sticky': False,
                'next': action
            }
        }

    def action_custom_clear(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
