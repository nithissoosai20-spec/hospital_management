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

        # Also create draft Lab Bill for direct Lab fulfillment & payment
        lab_bill = self.env['hospital.lab.bill'].create({
            'patient_id': self.patient_id.id,
            'admission_type': 'with_admission',
            'doctor_id': doctor.id if doctor else False,
            'doctor_department_id': doctor.department_id.id if doctor and doctor.department_id else False,
            'lab_appointment_id': lab_appointment.id,
            'state': 'draft',
        })
        bill_lines = []
        for test in self.test_ids:
            bill_lines.append((0, 0, {
                'lab_test_id': test.id,
                'test_name': test.name,
                'test_code': test.code or '',
                'category_name': test.lab_category_id.name if test.lab_category_id else '',
                'price': test.price or 0.0,
                'discount': 0.0,
                'total_amount': test.price or 0.0,
            }))
        lab_bill.write({'line_ids': bill_lines})
            
        return {'type': 'ir.actions.act_window_close'}

