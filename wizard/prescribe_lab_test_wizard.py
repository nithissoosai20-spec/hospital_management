from odoo import models, fields, api

class PrescribeLabTestWizard(models.TransientModel):
    _name = 'patient.lab.test.wizard'
    _description = 'Prescribe Lab Test Wizard'

    patient_id = fields.Many2one('hospital.patient', string='Patient', required=True)
    test_ids = fields.Many2many('hospital.lab.test', string='Lab Tests')

    def action_prescribe(self):
        self.ensure_one()
        if not self.test_ids:
            return {'type': 'ir.actions.act_window_close'}
            
        doctor = self.env['hospital.user'].search([('odoo_user_id', '=', self.env.user.id)], limit=1)
        
        # Create draft lab appointment
        lab_appointment = self.env['hospital.lab.appointment'].create({
            'patient_id': self.patient_id.id,
            'doctor_id': doctor.id if doctor else False,
            'state': 'draft',
            'appointment_date': fields.Datetime.now()
        })
        
        for test in self.test_ids:
            self.env['hospital.lab.appointment.line'].create({
                'lab_appointment_id': lab_appointment.id,
                'lab_test_id': test.id
            })
            
        return {'type': 'ir.actions.act_window_close'}

