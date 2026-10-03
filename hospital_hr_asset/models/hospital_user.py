from odoo import api, models

class HospitalUser(models.Model):
    _inherit = 'hospital.user'

    def _sync_to_hr_employee(self):
        for record in self:
            if not record.odoo_user_id:
                continue

            hr_employee = self.env['hr.employee'].sudo().search([('user_id', '=', record.odoo_user_id.id)], limit=1)

            hr_dept = False
            if record.department_id:
                hr_dept = self.env['hr.department'].sudo().search([('name', '=', record.department_id.name)], limit=1)
                if not hr_dept:
                    hr_dept = self.env['hr.department'].sudo().create({'name': record.department_id.name})
            
            hr_job = False
            if record.designation_id:
                hr_job = self.env['hr.job'].sudo().search([('name', '=', record.designation_id.name)], limit=1)
                if not hr_job:
                    hr_job = self.env['hr.job'].sudo().create({'name': record.designation_id.name})

            parent_emp = False
            if record.reporting_to_id and record.reporting_to_id.odoo_user_id:
                parent_emp = self.env['hr.employee'].sudo().search([('user_id', '=', record.reporting_to_id.odoo_user_id.id)], limit=1)

            vals = {
                'name': record.name,
                'work_email': record.email,
                'work_phone': record.mobile,
                'sex': record.gender,
                'birthday': record.date_of_birth,
                'department_id': hr_dept.id if hr_dept else False,
                'job_id': hr_job.id if hr_job else False,
                'parent_id': parent_emp.id if parent_emp else False,
                'active': record.active,
            }

            if hr_employee:
                hr_employee.write(vals)
            else:
                vals['user_id'] = record.odoo_user_id.id
                self.env['hr.employee'].sudo().create(vals)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_to_hr_employee()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._sync_to_hr_employee()
        return res

    def _get_odoo_group_for_role(self):
        self.ensure_one()

        role_name = (self.role_id.name or '').strip().lower()

        if role_name == 'hr manager':
            return self.env.ref(
                'hospital_management.group_hospital_hr'
            )

        if role_name == 'asset manager':
            return self.env.ref(
                'hospital_hr_asset.group_hospital_asset_manager'
            )

        return super()._get_odoo_group_for_role()