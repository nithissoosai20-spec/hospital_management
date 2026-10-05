from odoo import models, fields, api

class HospitalAssetReplacementWizard(models.TransientModel):
    _name = 'hospital.asset.replacement.wizard'
    _description = 'Asset Replacement Wizard'

    request_id = fields.Many2one('maintenance.request', required=True)
    broken_equipment_id = fields.Many2one('maintenance.equipment', related='request_id.equipment_id', string='Broken Asset')
    user_id = fields.Many2one('res.users', related='request_id.owner_user_id', string='Staff Member')
    
    new_equipment_id = fields.Many2one('maintenance.equipment', string='Replacement Asset', required=True, domain="[('asset_status', '=', 'active'), ('owner_user_id', '=', False)]")

    def action_assign_replacement(self):
        self.ensure_one()
        # 1. Unassign the broken asset
        if self.broken_equipment_id:
            self.broken_equipment_id.write({
                'owner_user_id': False,
                'asset_status': 'maintenance'
            })
            self.request_id.message_post(body=f"Broken asset {self.broken_equipment_id.name} unassigned and put under maintenance.")
        
        # 2. Assign the new asset
        if self.new_equipment_id:
            self.new_equipment_id.write({
                'owner_user_id': self.user_id.id
            })
            self.request_id.message_post(body=f"Replacement asset {self.new_equipment_id.name} allocated to user {self.user_id.name}.")
        
        # 3. Update the request
        self.request_id.write({
            'stage_id': self.env.ref('maintenance.stage_3').id # Repaired / Closed
        })



class MaintenanceRequest(models.Model):

    maintenance_type = fields.Selection([
        ('corrective', 'Broken / Repair Needed'),
        ('preventive', 'Routine Service / Checkup')
    ], string='Maintenance Type', default='corrective')

    _inherit = 'maintenance.request'

    owner_user_id = fields.Many2one('res.users', string='Created by User', compute='_compute_owner_user_id_override', inverse='_inverse_owner_user_id', store=True, readonly=False)

    def _compute_owner_user_id_override(self):
        pass

    def _inverse_owner_user_id(self):
        pass



    def action_submit_request(self):
        action = self.env.ref('hospital_hr_asset.action_hospital_my_asset_requests').sudo().read()[0]
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Request Submitted',
                'message': 'Your asset request has been submitted successfully!',
                'type': 'success',
                'sticky': False,
                'next': action,
            }
        }

    def action_cancel_request(self):
        return self.env.ref('hospital_hr_asset.action_hospital_my_asset_requests').sudo().read()[0]
