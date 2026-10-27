from odoo import models, fields, api
from odoo.exceptions import ValidationError
import pytz


class HospitalStaffSelfServiceMixin(models.AbstractModel):
    _name = 'hospital.staff.self.service.mixin'
    _description = 'Hospital Staff Self-Service Mixin'

    my_employee_id = fields.Many2one(
        'hr.employee',
        compute='_compute_self_service',
        string='My Employee Record'
    )
    my_attendance_state = fields.Selection(
        [('checked_in', 'Checked In'), ('checked_out', 'Checked Out')],
        compute='_compute_self_service',
        string='Attendance State'
    )
    my_check_in_time = fields.Char(
        compute='_compute_self_service',
        string='Check-in Time'
    )

    def _compute_self_service(self):
        for rec in self:
            emp = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
            rec.my_employee_id = emp
            if emp:
                state = emp.sudo().attendance_state or 'checked_out'
                rec.my_attendance_state = state
                last_att = emp.sudo().last_attendance_id
                if last_att and not last_att.check_out and last_att.check_in:
                    user_tz = self.env.user.tz or 'Asia/Kolkata'
                    utc_dt = last_att.check_in
                    try:
                        local_tz = pytz.timezone(user_tz)
                        local_dt = pytz.utc.localize(utc_dt).astimezone(local_tz)
                        rec.my_check_in_time = local_dt.strftime('%I:%M %p')
                    except Exception:
                        rec.my_check_in_time = str(utc_dt)[11:16]
                else:
                    rec.my_check_in_time = False
            else:
                rec.my_attendance_state = 'checked_out'
                rec.my_check_in_time = False

    def action_toggle_attendance(self):
        emp = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        if not emp:
            raise ValidationError("No HR Employee record linked to your user account. Please contact Administrator.")

        emp.sudo()._attendance_action_change()
        now_checked_in = emp.sudo().attendance_state == 'checked_in'

        status_text = "Checked In" if now_checked_in else "Checked Out"
        msg_type = 'success' if now_checked_in else 'warning'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': f'Attendance: {status_text}',
                'message': f'You have successfully {status_text.lower()} at {fields.Datetime.now().strftime("%I:%M %p")}.',
                'type': msg_type,
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'}
            }
        }

    def action_request_leave(self):
        emp = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        return {
            'name': 'Apply for Leave',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_employee_id': emp.id if emp else False,
            }
        }

    def action_submit_expense(self):
        emp = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        return {
            'name': 'Submit Expense Claim',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.expense',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_employee_id': emp.id if emp else False,
            }
        }

