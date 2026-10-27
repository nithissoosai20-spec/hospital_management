from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    hospital_role_id = fields.Many2one(
        'hospital.role',
        string='Hospital Role',
        compute='_compute_shift_details',
        store=True,
    )
    expected_shift_hours = fields.Float(
        string='Expected Shift Hours',
        compute='_compute_shift_details',
        store=True,
        help='Standard shift hours based on the employee role (e.g., 5h for Doctors, 7h for Nurses).'
    )
    shift_variance = fields.Float(
        string='Shift Variance',
        compute='_compute_shift_details',
        store=True,
        help='Difference between worked hours and expected shift hours (positive = overtime, negative = early departure).'
    )
    shift_status = fields.Selection([
        ('on_duty', 'Currently Working (On Duty)'),
        ('on_time', 'Completed On Time'),
        ('overtime', 'Overtime / Exceeded Shift'),
        ('early', 'Early Departure / Under Shift'),
    ], string='Shift Timing Status', compute='_compute_shift_details', store=True, default='on_duty')

    shift_status_badge = fields.Char(
        string='Shift Timing Summary',
        compute='_compute_shift_details',
        store=True,
    )
    shift_variance_text = fields.Char(
        string='Variance Text',
        compute='_compute_shift_details',
        store=True,
    )

    def write(self, vals):
        if 'employee_id' in vals and not self.env.su:
            for rec in self:
                if rec.employee_id and vals.get('employee_id') != rec.employee_id.id:
                    raise ValidationError("The employee cannot be modified on an existing attendance record.")
        return super().write(vals)

    @api.depends('employee_id', 'check_in', 'check_out', 'worked_hours')
    def _compute_shift_details(self):
        HospitalUser = self.env['hospital.user'].sudo()
        HospitalRole = self.env['hospital.role'].sudo()

        # Cache role hours mapping
        role_map = {}
        for r in HospitalRole.search([]):
            role_map[r.id] = (r.shift_hours or 8.0, r.id)
            if r.name:
                role_map[r.name.strip().lower()] = (r.shift_hours or 8.0, r.id)

        for rec in self:
            role_id = False
            expected_hours = 8.0

            if rec.employee_id:
                # 1. Match from hospital.user
                domain = [('hr_employee_id', '=', rec.employee_id.id)]
                if rec.employee_id.user_id:
                    domain = ['|', ('hr_employee_id', '=', rec.employee_id.id), ('odoo_user_id', '=', rec.employee_id.user_id.id)]
                h_user = HospitalUser.search(domain, limit=1)

                if h_user and h_user.role_id:
                    role_id = h_user.role_id.id
                    expected_hours = h_user.role_id.shift_hours or 8.0
                else:
                    # Fallback by employee job or designation name
                    job_name = (rec.employee_id.job_id.name or '').strip().lower()
                    if 'doctor' in job_name:
                        expected_hours, role_id = role_map.get('doctor', (5.0, False))
                    elif 'nurse' in job_name:
                        expected_hours, role_id = role_map.get('nurse', (7.0, False))
                    elif 'reception' in job_name:
                        expected_hours, role_id = role_map.get('receptionist', (8.0, False))
                    else:
                        expected_hours = 8.0

            rec.hospital_role_id = role_id
            rec.expected_shift_hours = expected_hours

            # Calculate timing outcome
            exp_display = f"{int(expected_hours)}h" if expected_hours.is_integer() else f"{expected_hours:.1f}h"

            if not rec.check_out:
                rec.shift_variance = 0.0
                rec.shift_status = 'on_duty'
                rec.shift_variance_text = 'On Duty'
                rec.shift_status_badge = f'Currently Working (Expected: {exp_display})'
            else:
                worked = rec.worked_hours or 0.0
                diff = worked - expected_hours
                rec.shift_variance = diff

                abs_diff = abs(diff)
                total_seconds = int(round(abs_diff * 3600))
                diff_h = total_seconds // 3600
                diff_m = (total_seconds % 3600) // 60
                time_str = f'{diff_h}h {diff_m:02d}m'

                # 5-minute tolerance (0.0833 hours)
                if diff > 0.0833:
                    rec.shift_status = 'overtime'
                    rec.shift_variance_text = f'+{time_str} Exceeded'
                    rec.shift_status_badge = f'+{time_str} Overtime (Exceeded Shift)'
                elif diff < -0.0833:
                    rec.shift_status = 'early'
                    rec.shift_variance_text = f'-{time_str} Shortfall'
                    rec.shift_status_badge = f'-{time_str} Early Departure (Under Shift)'
                else:
                    rec.shift_status = 'on_time'
                    rec.shift_variance_text = 'Exact Shift Met'
                    rec.shift_status_badge = 'Completed On Time'
