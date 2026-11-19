from odoo import models, fields, api


class HospitalLabTestSelectorLine(models.TransientModel):
    _name = 'hospital.lab.test.selector.line'
    _description = 'Lab Test Selector Line'
    _order = 'selected desc, id asc'

    wizard_id = fields.Many2one(
        'hospital.lab.test.selector',
        string='Wizard',
        ondelete='cascade'
    )
    test_id = fields.Many2one(
        'hospital.lab.test',
        string='Lab Test'
    )
    test_code = fields.Char(
        related='test_id.code',
        string='Code',
        readonly=True
    )
    category = fields.Selection(
        related='test_id.category',
        string='Old Category',
        readonly=True
    )
    lab_category_id = fields.Many2one(
        related='test_id.lab_category_id',
        string='Category',
        readonly=True
    )
    sample_type = fields.Selection(
        related='test_id.sample_type',
        string='Old Sub Category',
        readonly=True
    )
    lab_sub_category_id = fields.Many2one(
        related='test_id.lab_sub_category_id',
        string='Sub Category',
        readonly=True
    )
    price = fields.Float(
        related='test_id.price',
        string='Price',
        readonly=True
    )
    selected = fields.Boolean(
        string='Select',
        default=False
    )


class HospitalLabTestSelector(models.TransientModel):
    _name = 'hospital.lab.test.selector'
    _description = 'Lab Test Selector Wizard'

    patient_id = fields.Many2one('hospital.patient', string='Patient')
    lab_appointment_id = fields.Many2one(
        'hospital.lab.appointment',
        string='Lab Appointment'
    )

    filter_lab_category_id = fields.Many2one(
        'hospital.category.master',
        string='Category',
        domain="[('category_type', '=', 'lab_category')]"
    )

    filter_lab_sub_category_id = fields.Many2one(
        'hospital.category.master',
        string='Sub Category',
        domain="[('category_type', '=', 'lab_sub_category')]"
    )

    line_ids = fields.One2many(
        'hospital.lab.test.selector.line',
        'wizard_id',
        string='Test Lines'
    )


    @api.onchange('filter_lab_category_id', 'filter_lab_sub_category_id')
    def _onchange_filters(self):
        domain = []
        if self.filter_lab_category_id:
            domain.append(('lab_category_id', '=', self.filter_lab_category_id.id))
        if self.filter_lab_sub_category_id:
            domain.append(('lab_sub_category_id', '=', self.filter_lab_sub_category_id.id))

        tests = self.env['hospital.lab.test'].search(domain)
        
        # Keep currently selected tests even if they don't match the filter!
        selected_test_ids = [line.test_id.id for line in self.line_ids if line.selected and line.test_id]
        
        self.line_ids = [(5, 0, 0)]
        new_lines = []
        
        # Add retained selected tests
        for test_id in selected_test_ids:
            new_lines.append((0, 0, {
                'test_id': test_id,
                'selected': True,
            }))
            
        # Add filtered tests that aren't already in new_lines
        for test in tests:
            if test.id not in selected_test_ids:
                new_lines.append((0, 0, {
                    'test_id': test.id,
                    'selected': False,
                }))
                
        self.line_ids = new_lines

    def action_select_all(self):
        self.ensure_one()
        self.line_ids.write({'selected': True})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Lab Tests',
            'res_model': 'hospital.lab.test.selector',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': dict(self.env.context),
        }

    def action_deselect_all(self):
        self.ensure_one()
        self.line_ids.write({'selected': False})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Lab Tests',
            'res_model': 'hospital.lab.test.selector',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': dict(self.env.context),
        }

    def action_add_selected(self):
        selected_lines = self.line_ids.filtered('selected')
        
        # Find or create appointment
        appointment = False
        if self.lab_appointment_id:
            appointment = self.lab_appointment_id
        elif self.patient_id:
            appointment = self.env['hospital.lab.appointment'].search([
                ('patient_id', '=', self.patient_id.id),
                ('state', '=', 'draft')
            ], limit=1)
            
            if not appointment:
                if not selected_lines:
                    return {'type': 'ir.actions.act_window_close'}
                
                # Check for active consultation to link bidirectionally!
                active_h_appt = self.env['hospital.appointment'].search([
                    ('patient_id', '=', self.patient_id.id),
                    ('state', 'in', ['draft', 'booked'])
                ], order='id desc', limit=1)
                
                doctor = self.env['hospital.user'].search([('odoo_user_id', '=', self.env.user.id)], limit=1)
                if not doctor and active_h_appt and active_h_appt.doctor_id:
                    doctor = active_h_appt.doctor_id

                appointment = self.env['hospital.lab.appointment'].create({
                    'patient_id': self.patient_id.id,
                    'doctor_id': doctor.id if doctor else False,
                    'hospital_appointment_id': active_h_appt.id if active_h_appt else False,
                    'state': 'draft',
                    'payment_status': 'pending',
                    'payment_mode': 'none',
                    'appointment_date': fields.Datetime.now()
                })
            else:
                # Link to active consultation if not linked
                if not appointment.hospital_appointment_id:
                    active_h_appt = self.env['hospital.appointment'].search([
                        ('patient_id', '=', self.patient_id.id),
                        ('state', 'in', ['draft', 'booked'])
                    ], order='id desc', limit=1)
                    if active_h_appt:
                        appointment.hospital_appointment_id = active_h_appt.id
                if not appointment.doctor_id:
                    doctor = self.env['hospital.user'].search([('odoo_user_id', '=', self.env.user.id)], limit=1)
                    if not doctor and appointment.hospital_appointment_id and appointment.hospital_appointment_id.doctor_id:
                        doctor = appointment.hospital_appointment_id.doctor_id
                    if doctor:
                        appointment.doctor_id = doctor.id
                        
        if not appointment:
            return {'type': 'ir.actions.act_window_close'}

        # Clear existing lines to replace with current selection
        appointment.line_ids.unlink()
        appointment.write({'appointment_date': fields.Date.today()})

        new_lines = []
        existing_test_ids = []
        
        # Group selected tests by category
        from collections import defaultdict
        tests_by_category = defaultdict(list)
        for line in selected_lines:
            tests_by_category[line.test_id.lab_category_id].append(line.test_id)
            
        for category, tests in tests_by_category.items():
            if category:
                new_lines.append((0, 0, {'name': category.name, 'display_type': 'line_section', 'is_parameter': False}))
            elif len(tests_by_category) > 1 or tests_by_category.get(False):
                # If there are tests without category, add an 'Others' section
                new_lines.append((0, 0, {'name': 'Others', 'display_type': 'line_section', 'is_parameter': False}))
                
            for test in tests:
                if test.id not in existing_test_ids:
                    new_lines.append((0, 0, {'lab_test_id': test.id, 'is_parameter': False}))
                    existing_test_ids.append(test.id)
                
                if test.is_profile:
                    for param in test.with_context(active_test=False).parameter_ids:
                        if param.id not in existing_test_ids:
                            new_lines.append((0, 0, {'lab_test_id': param.id, 'is_parameter': True}))
                            existing_test_ids.append(param.id)

        if new_lines:
            appointment.write({'line_ids': new_lines})

        # Automatically create or sync draft Lab Bill so it appears directly in Lab User login (Lab Billing)
        patient_rec = self.patient_id or appointment.patient_id
        if patient_rec:
            doctor_rec = appointment.doctor_id
            if not doctor_rec:
                doctor_rec = self.env['hospital.user'].search([('odoo_user_id', '=', self.env.user.id)], limit=1)

            lab_bill = False
            if appointment.hospital_appointment_id:
                lab_bill = self.env['hospital.lab.bill'].search([
                    ('appointment_id', '=', appointment.hospital_appointment_id.id),
                    ('state', '=', 'draft')
                ], limit=1)
            if not lab_bill and appointment.id:
                lab_bill = self.env['hospital.lab.bill'].search([
                    ('lab_appointment_id', '=', appointment.id),
                    ('state', '=', 'draft')
                ], limit=1)
            if not lab_bill:
                lab_bill = self.env['hospital.lab.bill'].search([
                    ('patient_id', '=', patient_rec.id),
                    ('state', '=', 'draft')
                ], order='id desc', limit=1)

            main_tests = [line.test_id for line in selected_lines if line.test_id]

            if not main_tests:
                if lab_bill:
                    lab_bill.line_ids.unlink()
            else:
                if not lab_bill:
                    lab_bill = self.env['hospital.lab.bill'].create({
                        'patient_id': patient_rec.id,
                        'admission_type': 'with_admission',
                        'doctor_id': doctor_rec.id if doctor_rec else False,
                        'doctor_department_id': doctor_rec.department_id.id if doctor_rec and doctor_rec.department_id else False,
                        'appointment_id': appointment.hospital_appointment_id.id if appointment.hospital_appointment_id else False,
                        'lab_appointment_id': appointment.id,
                        'state': 'draft',
                    })
                else:
                    bill_vals = {
                        'lab_appointment_id': appointment.id,
                    }
                    if not lab_bill.doctor_id and doctor_rec:
                        bill_vals['doctor_id'] = doctor_rec.id
                        if doctor_rec.department_id:
                            bill_vals['doctor_department_id'] = doctor_rec.department_id.id
                    if not lab_bill.appointment_id and appointment.hospital_appointment_id:
                        bill_vals['appointment_id'] = appointment.hospital_appointment_id.id
                    lab_bill.write(bill_vals)
                    lab_bill.line_ids.unlink()

                bill_lines = []
                for t in main_tests:
                    bill_lines.append((0, 0, {
                        'lab_test_id': t.id,
                        'test_name': t.name,
                        'test_code': t.code or '',
                        'category_name': t.lab_category_id.name if t.lab_category_id else '',
                        'price': t.price or 0.0,
                        'discount': 0.0,
                        'total_amount': t.price or 0.0,
                    }))
                lab_bill.write({'line_ids': bill_lines})

        # Always reload to refresh the underlying view (patient dashboard or lab appointment)
        return {'type': 'ir.actions.client', 'tag': 'reload'}
