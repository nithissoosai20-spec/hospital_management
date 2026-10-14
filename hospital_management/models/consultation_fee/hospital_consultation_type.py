from odoo import models, fields, api


class HospitalConsultationType(models.Model):
    _name = 'hospital.consultation.type'
    _description = 'Hospital Consultation Type'
    _order = 'name asc'

    name = fields.Char(string='Consultation Type', required=True)
    code = fields.Char(string='Code')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100, **kwargs):
        domain = list(domain or kwargs.get('args') or [])
        doctor_id = self.env.context.get('doctor_user_id')
        if doctor_id:
            lines = self.env['hospital.doctor.consultation.line'].search([
                ('doctor_id', '=', doctor_id),
            ])
            existing_ids = lines.mapped('consultation_type_id.id')
            if existing_ids:
                domain.append(('id', 'not in', existing_ids))
        return super().name_search(name=name, domain=domain, operator=operator, limit=limit)

    def action_save(self):
        action = self.env.ref('hospital_management.action_hospital_consultation_types').sudo().read()[0]
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Saved successfully',
                'type': 'success',
                'sticky': False,
                'next': action,
            }
        }

    def action_clear(self):
        for rec in self:
            rec.name = False
            rec.code = False
            rec.description = False
            rec.active = True

    def action_close(self):
        return self.env.ref('hospital_management.action_hospital_consultation_types').sudo().read()[0]
