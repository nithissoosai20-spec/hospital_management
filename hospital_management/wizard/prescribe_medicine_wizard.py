from odoo import models, fields, api

class PrescribeMedicineWizard(models.TransientModel):
    _name = 'patient.medicine.prescription.wizard'
    _description = 'Prescribe Medicine Wizard'

    @api.model
    def default_get(self, fields_list):
        res = super(PrescribeMedicineWizard, self).default_get(fields_list)
        if 'patient_id' in res or self.env.context.get('default_patient_id'):
            patient_id = res.get('patient_id') or self.env.context.get('default_patient_id')
            prescription = self.env['hospital.prescription'].search([
                ('patient_id', '=', patient_id),
                ('state', '=', 'draft')
            ], limit=1)
            
            if prescription:
                lines = []
                for line in prescription.line_ids:
                    lines.append((0, 0, {
                        'medicine_id': line.medicine_id.id,
                        'qty': line.qty,
                        'morning': line.morning,
                        'afternoon': line.afternoon,
                        'evening': line.evening,
                        'night': line.night,
                        'timing': line.timing,
                    }))
                if lines:
                    res['line_ids'] = lines
        return res


    patient_id = fields.Many2one('hospital.patient', string='Patient', required=True)
    line_ids = fields.One2many('patient.medicine.prescription.wizard.line', 'wizard_id', string='Medicines')

    def action_prescribe(self):
        self.ensure_one()
        doctor = self.env['hospital.user'].search([('odoo_user_id', '=', self.env.user.id)], limit=1)
        
        prescription = self.env['hospital.prescription'].search([
            ('patient_id', '=', self.patient_id.id),
            ('state', '=', 'draft')
        ], limit=1)
        
        if not prescription:
            if not self.line_ids:
                return {'type': 'ir.actions.client', 'tag': 'reload'}
            prescription = self.env['hospital.prescription'].create({
                'patient_id': self.patient_id.id,
                'doctor_id': doctor.id if doctor else False,
                'state': 'draft'
            })
        else:
            # Clear existing lines to replace with the new ones from the wizard
            prescription.line_ids.unlink()
            from odoo import fields
            prescription.write({'date_prescribed': fields.Datetime.now()})
            
        for line in self.line_ids:
            self.env['hospital.prescription.line'].create({
                'prescription_id': prescription.id,
                'medicine_id': line.medicine_id.id,
                'qty': line.qty,
                'morning': line.morning,
                'afternoon': line.afternoon,
                'evening': line.evening,
                'night': line.night,
                'timing': line.timing
            })
            
        return {'type': 'ir.actions.client', 'tag': 'reload'}
            
        doctor = self.env['hospital.user'].search([('odoo_user_id', '=', self.env.user.id)], limit=1)
        
        prescription = self.env['hospital.prescription'].create({
            'patient_id': self.patient_id.id,
            'doctor_id': doctor.id if doctor else False,
            'state': 'draft'
        })
        
        for line in self.line_ids:
            self.env['hospital.prescription.line'].create({
                'prescription_id': prescription.id,
                'medicine_id': line.medicine_id.id,
                'qty': line.qty,
                'morning': line.morning,
                'afternoon': line.afternoon,
                'evening': line.evening,
                'night': line.night,
                'timing': line.timing
            })
            
        return {'type': 'ir.actions.client', 'tag': 'reload'}


class PrescribeMedicineWizardLine(models.TransientModel):
    _name = 'patient.medicine.prescription.wizard.line'
    _description = 'Prescribe Medicine Wizard Line'

    wizard_id = fields.Many2one('patient.medicine.prescription.wizard', string='Wizard')
    
    medicine_id = fields.Many2one('hospital.pharmacy.stock', string='Medicine', required=True)
    
    qty = fields.Integer(string='Qty', default=1, required=True)
    
    morning = fields.Boolean(string='Morning')
    afternoon = fields.Boolean(string='Afternoon')
    evening = fields.Boolean(string='Evening')
    night = fields.Boolean(string='Night')
    
    timing = fields.Selection([
        ('before', 'Before Meal'),
        ('after', 'After Meal')
    ], string='Instructions', default='after')

