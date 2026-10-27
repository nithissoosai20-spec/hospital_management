from odoo import models, fields

class HospitalHrDashboard(models.Model):
    _name = 'hospital.hr.dashboard'
    _inherit = ['hospital.staff.self.service.mixin']
    _description = 'Hospital HR Dashboard'

    name = fields.Char(default='HR Dashboard', readonly=True)
    total_employees = fields.Integer(string='Total Employees', compute='_compute_stats')
    total_departments = fields.Integer(string='Departments', compute='_compute_stats')
    today_attendances = fields.Integer(string='Present Today', compute='_compute_stats')
    pending_leaves = fields.Integer(string='Pending Leaves', compute='_compute_stats')
    pending_expenses = fields.Integer(string='Pending Expenses', compute='_compute_stats')

    def _compute_stats(self):
        for rec in self:
            try:
                rec.total_employees = self.env['hr.employee'].search_count([])
            except Exception:
                rec.total_employees = 0

            try:
                rec.total_departments = self.env['hr.department'].search_count([])
            except Exception:
                rec.total_departments = 0

            try:
                today = fields.Date.context_today(self)
                rec.today_attendances = self.env['hr.attendance'].search_count([
                    ('check_in', '>=', str(today))
                ])
            except Exception:
                rec.today_attendances = 0

            try:
                rec.pending_leaves = self.env['hr.leave'].search_count([
                    ('state', 'in', ['confirm', 'validate1'])
                ])
            except Exception:
                rec.pending_leaves = 0

            try:
                rec.pending_expenses = self.env['hr.expense'].search_count([
                    ('state', 'in', ['reported', 'submitted', 'draft'])
                ])
            except Exception:
                rec.pending_expenses = 0

