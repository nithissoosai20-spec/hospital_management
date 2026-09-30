from odoo import models, fields

class HospitalLabDashboard(models.Model):
    _name = 'hospital.lab.dashboard'
    _description = 'Lab Dashboard'

    name = fields.Char(default='Lab Dashboard', readonly=True)
    total_appointments = fields.Integer(string='Total Lab Appointments', compute='_compute_stats')
    pending_tests = fields.Integer(string='Pending Tests', compute='_compute_stats')

    def _compute_stats(self):
        for rec in self:
            lab_env = self.env['hospital.lab.appointment']
            rec.total_appointments = lab_env.search_count([])
            rec.pending_tests = lab_env.search_count([('state', 'not in', ['completed', 'cancelled'])])
            
    def action_open_lab_reports(self):
        return self.env['ir.actions.act_window']._for_xml_id('hospital_management.action_hospital_lab_appointments')
