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
    appointment_id = fields.Many2one('hospital.appointment', string='Appointment')
    line_ids = fields.One2many('patient.medicine.prescription.wizard.line', 'wizard_id', string='Medicines')

    def action_prescribe(self):
        self.ensure_one()
        doctor = self.env['hospital.user'].search([('odoo_user_id', '=', self.env.user.id)], limit=1)
        
        # Link to active consultation appointment
        active_appointment = False
        if self.appointment_id:
            active_appointment = self.appointment_id
        elif self.env.context.get('default_appointment_id'):
            active_appointment = self.env['hospital.appointment'].browse(self.env.context['default_appointment_id'])
        
        if not active_appointment:
            active_appointment = self.env['hospital.appointment'].search([
                ('patient_id', '=', self.patient_id.id),
                ('state', 'in', ['draft', 'booked'])
            ], order='id desc', limit=1)
            
        if not doctor and active_appointment and active_appointment.doctor_id:
            doctor = active_appointment.doctor_id
            
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
            prescription.write({
                'date_prescribed': fields.Datetime.now(),
                'doctor_id': doctor.id if doctor else prescription.doctor_id.id
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

        # Automatically create or update draft Pharmacy Bill for direct Pharmacy fulfillment & payment
        bill = False
        if active_appointment:
            bill = self.env['hospital.pharmacy.bill'].search([
                ('appointment_id', '=', active_appointment.id),
                ('state', '=', 'draft')
            ], limit=1)
        if not bill:
            bill = self.env['hospital.pharmacy.bill'].search([
                ('patient_id', '=', self.patient_id.id),
                ('state', '=', 'draft')
            ], order='id desc', limit=1)

        if not self.line_ids:
            if bill:
                bill.line_ids.unlink()
            return {'type': 'ir.actions.client', 'tag': 'reload'}

        if not bill:
            bill = self.env['hospital.pharmacy.bill'].create({
                'patient_id': self.patient_id.id,
                'customer_type': 'patient',
                'doctor_id': doctor.id if doctor else False,
                'doctor_department_id': doctor.department_id.id if doctor and doctor.department_id else False,
                'appointment_id': active_appointment.id if active_appointment else False,
                'prescription_ids': [(6, 0, [prescription.id])],
                'state': 'draft',
            })
        else:
            bill_vals = {
                'prescription_ids': [(6, 0, [prescription.id])],
            }
            if not bill.appointment_id and active_appointment:
                bill_vals['appointment_id'] = active_appointment.id
            if not bill.doctor_id and doctor:
                bill_vals['doctor_id'] = doctor.id
                if doctor.department_id:
                    bill_vals['doctor_department_id'] = doctor.department_id.id
            bill.write(bill_vals)
            bill.line_ids.unlink()

        # Add medicine items into pharmacy bill
        bill_lines = []
        for line in self.line_ids:
            med = line.medicine_id
            mrp_val = med.total_amount or med.selling_price or med.mrp or 0.0
            m = '1' if line.morning else '0'
            a = '1' if line.afternoon else '0'
            e = '1' if line.evening else '0'
            n = '1' if line.night else '0'
            dosage_str = f"{m}-{a}-{e}-{n}"
            instr_str = 'Before Meal' if line.timing == 'before' else 'After Meal'
            bill_lines.append((0, 0, {
                'stock_id': med.id,
                'medicine_name': med.medicine_name,
                'qty': float(line.qty),
                'mrp': mrp_val,
                'available_stock': med.quantity,
                'batch': med.batch_number or '',
                'expiry': med.expiry_date or '',
                'dosage': dosage_str,
                'instructions': instr_str,
                'cgst_percent': med.cgst or 0.0,
                'sgst_percent': med.sgst or 0.0,
                'igst_percent': med.igst or 0.0,
                'discount': med.discount_percent or 0.0,
            }))
        bill.write({'line_ids': bill_lines})
        bill._compute_amounts()
            
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

