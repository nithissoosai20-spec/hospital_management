from odoo import models, fields

class HospitalLabSubtestWizard(models.TransientModel):
    _name = 'hospital.lab.subtest.wizard'
    _description = 'Select Sub-Tests'

    lab_appointment_id = fields.Many2one('hospital.lab.appointment', string='Lab Appointment')
    appointment_line_id = fields.Many2one('hospital.lab.appointment.line', string='Source Line')
    line_ids = fields.One2many('hospital.lab.subtest.wizard.line', 'wizard_id', string='Sub Tests')

    def action_add_subtests(self):
        self.ensure_one()
        
        # Generate data for new lines
        new_lines_data = []
        for line in self.line_ids.filtered(lambda l: l.selected):
            existing = self.env['hospital.lab.appointment.line'].search([
                ('lab_appointment_id', '=', self.lab_appointment_id.id),
                ('subtest_id', '=', line.subtest_id.id)
            ])
            if not existing:
                new_lines_data.append({
                    'lab_appointment_id': self.lab_appointment_id.id,
                    'lab_test_id': line.lab_test_id.id,
                    'subtest_id': line.subtest_id.id,
                    'name': False,
                    'unit': line.subtest_id.unit,
                    'normal_range_display': line.subtest_id.normal_range_display,
                    'normal_range_min': line.subtest_id.normal_range_min,
                    'normal_range_max': line.subtest_id.normal_range_max,
                    'is_parameter': True
                })
        
        if new_lines_data:
            appointment = self.lab_appointment_id
            lines = list(appointment.line_ids.sorted(key=lambda r: (r.sequence, r.id)))
            
            seq = 10
            for line in lines:
                line.sequence = seq
                seq += 10
                if line.id == self.appointment_line_id.id:
                    for data in new_lines_data:
                        data['sequence'] = seq
                        self.env['hospital.lab.appointment.line'].create(data)
                        seq += 10
                        
        return {'type': 'ir.actions.client', 'tag': 'reload'}

class HospitalLabSubtestWizardLine(models.TransientModel):
    _name = 'hospital.lab.subtest.wizard.line'
    _description = 'Sub-Test Wizard Line'

    wizard_id = fields.Many2one('hospital.lab.subtest.wizard')
    subtest_id = fields.Many2one('hospital.lab.subtest', string='Sub Test')
    lab_test_id = fields.Many2one('hospital.lab.test', string='Main Test')
    selected = fields.Boolean(string='Select')
