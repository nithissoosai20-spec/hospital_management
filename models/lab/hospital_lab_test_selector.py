from odoo import models, fields, api


class HospitalLabTestSelectorLine(models.TransientModel):
    _name = 'hospital.lab.test.selector.line'
    _description = 'Lab Test Selector Line'

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
        string='Category',
        readonly=True
    )
    sample_type = fields.Selection(
        related='test_id.sample_type',
        string='Sample Type',
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

    lab_appointment_id = fields.Many2one(
        'hospital.lab.appointment',
        string='Lab Appointment'
    )

    filter_category = fields.Selection(
        [
            ('hematology', 'Hematology'),
            ('biochemistry', 'Biochemistry'),
            ('microbiology', 'Microbiology'),
            ('pathology', 'Pathology'),
            ('radiology', 'Radiology'),
            ('cardiology', 'Cardiology'),
            ('other', 'Other'),
        ],
        string='Category'
    )

    filter_sample_type = fields.Selection(
        [
            ('blood', 'Blood'),
            ('urine', 'Urine'),
            ('stool', 'Stool'),
            ('swab', 'Swab'),
            ('serum', 'Serum'),
            ('other', 'Other'),
        ],
        string='Sample Type'
    )
    

    line_ids = fields.One2many(
        'hospital.lab.test.selector.line',
        'wizard_id',
        string='Lab Tests'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res['line_ids'] = []
        return res

    @api.onchange('filter_category', 'filter_sample_type')
    def _onchange_filters(self):
        if not self.filter_category and not self.filter_sample_type:
            self.line_ids = [(5, 0, 0)]
            return
            
        domain = [('is_profile', '=', False)]
        if self.filter_category:
            domain.append(('category', '=', self.filter_category))
        if self.filter_sample_type:
            domain.append(('sample_type', '=', self.filter_sample_type))

        tests = self.env['hospital.lab.test'].search(domain)
        
        # Check if the existing lines already match the current filters.
        # If they do, this onchange was triggered by a form reload (e.g. after clicking Select All)
        # and we MUST return early so we don't wipe out the checkboxes.
        if self.line_ids:
            match = True
            for line in self.line_ids:
                if not line.test_id:
                    continue
                if self.filter_category and line.test_id.category != self.filter_category:
                    match = False
                    break
                if self.filter_sample_type and line.test_id.sample_type != self.filter_sample_type:
                    match = False
                    break
            if match:
                return
        
        # Otherwise, the user actually changed the filters, so we load the new tests.
        self.line_ids = [(5, 0, 0)]
        new_lines = []
        for test in tests:
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
        """Add all selected tests to the lab appointment lines."""
        appointment = self.lab_appointment_id
        if not appointment:
            return {'type': 'ir.actions.act_window_close'}

        existing_test_ids = appointment.line_ids.mapped('lab_test_id.id')
        new_lines = []

        for line in self.line_ids.filtered('selected'):
            test = line.test_id
            if test.is_profile:
                for param in test.parameter_ids:
                    if param.id not in existing_test_ids:
                        new_lines.append((0, 0, {'lab_test_id': param.id}))
                        existing_test_ids.append(param.id)
            else:
                if test.id not in existing_test_ids:
                    new_lines.append((0, 0, {'lab_test_id': test.id}))
                    existing_test_ids.append(test.id)

        if new_lines:
            # Reconstruct the list safely for Odoo 17/19 one2many commands
            appointment.write({
                'line_ids': [(4, l.id) for l in appointment.line_ids] + new_lines
            })

        # Return a client action to completely reload the parent view so new lines appear instantly
        return {'type': 'ir.actions.client', 'tag': 'reload'}

