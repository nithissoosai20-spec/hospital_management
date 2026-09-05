from odoo import models, fields, api

class HospitalLoginHistory(models.Model):
    _name = 'hospital.login.history'
    _description = 'User Login History'
    _order = 'login_time desc'

    user_id = fields.Many2one('hospital.user', string='User', required=True, ondelete='cascade')
    name = fields.Char(related='user_id.name', string='Name', store=True)
    employee_id = fields.Char(related='user_id.employee_id', string='Employee ID', store=True)
    
    login_time = fields.Datetime(string='Login Time', required=True, default=fields.Datetime.now)
    logout_time = fields.Datetime(string='Logout Time')
