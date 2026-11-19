from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HospitalUser(models.Model):
    availability_status = fields.Char(
        string="Availability",
        compute='_compute_availability_status'
    )

    @api.depends('active')
    def _compute_availability_status(self):
        for record in self:
            record.availability_status = 'Available' if record.active else 'Not Available'

    _name = 'hospital.user'
    _description = 'Hospital User'

    login_history_ids = fields.One2many(
        'hospital.login.history',
        'user_id',
        string='Login History'
    )

    def action_close_user_form(self):
        return {'type': 'ir.actions.act_window_close'}

    def action_view_history(self):
        self.ensure_one()
        return {
            'name': 'Login History',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.user',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('hospital_management.view_hospital_user_history_form').id,
            'target': 'new',
        }

    _order = 'name'

    # PERSONAL DETAILS

    name = fields.Char(
        string='Full Name',
        required=True
    )

    employee_id = fields.Char(
        string='Employee ID',
        required=True
    )

    login = fields.Char(
        string='Username',
        required=True
    )

    email = fields.Char(
        string='Email Address'
    )

    mobile = fields.Char(
        string='Mobile Number',
    )

    date_of_birth = fields.Date(
        string='Date of Birth'
    )

    gender = fields.Selection(
        [
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
        ],
        string='Gender'
    )

    address = fields.Text(
        string='Address',
    )

    # ODOO LOGIN ACCOUNT

    password_confirm = fields.Char(
        string='Re-enter Password',
        copy=False
    )

    account_created = fields.Boolean(
        string='Login Account Created',
        compute='_compute_account_created'
    )

    last_login = fields.Datetime(
        string='Last Login',
        related='odoo_user_id.login_date',
        readonly=True,
    )

    password_last_changed = fields.Datetime(
        string='Password Last Changed',
        readonly=True,
        copy=False,
    )

    two_factor_enabled = fields.Boolean(
        string='Two-Factor Authentication',
        compute='_compute_two_factor_enabled',
        readonly=True,
    )

    # WORK DETAILS

    role_id = fields.Many2one(
        'hospital.role',
        string='Role',
        required=False,
        ondelete='restrict'
    )

    is_doctor = fields.Boolean(
        string='Is Doctor',
        compute='_compute_is_doctor',
        store=True,
    )

    consultation_line_ids = fields.One2many(
        'hospital.doctor.consultation.line',
        'doctor_id',
        string='Consultation Types & Fees',
    )

    existing_consultation_type_ids = fields.Many2many(
        'hospital.consultation.type',
        compute='_compute_existing_consultation_types',
        string='Selected Consultation Types',
    )

    @api.depends('consultation_line_ids.consultation_type_id')
    def _compute_existing_consultation_types(self):
        for rec in self:
            rec.existing_consultation_type_ids = rec.consultation_line_ids.mapped('consultation_type_id')

    @api.onchange('consultation_line_ids')
    def _onchange_consultation_line_ids(self):
        self.existing_consultation_type_ids = self.consultation_line_ids.mapped('consultation_type_id')

    @api.depends('role_id', 'role_id.name')
    def _compute_is_doctor(self):
        for rec in self:
            rec.is_doctor = bool(rec.role_id and (rec.role_id.name or '').strip().lower() == 'doctor')

    odoo_user_id = fields.Many2one(
        'res.users',
        string='Odoo User',
        readonly=True,
        copy=False,
        ondelete='set null'
    )

    password = fields.Char(
        string='Password',
        copy=False
    )

    allowed_department_ids = fields.Many2many(
        'hospital.department',
        compute='_compute_allowed_departments',
        string='Allowed Departments'
    )

    department_id = fields.Many2one(
        'hospital.department',
        string='Department',
        required=True,
        ondelete='restrict'
    )

    designation_id = fields.Many2one(
        'hospital.designation',
        string='Designation',
        required=True,
        domain="[('department_id', '=', department_id)]",
        ondelete='restrict'
    )

    reporting_to_id = fields.Many2one(
        'hospital.user',
        string='Reporting To',
        domain="""[
            ('id', '!=', id),
            ('role_id', '=', role_id),
            ('department_id', '=', department_id)
        ]""",
        ondelete='restrict'
    )

    hr_employee_id = fields.Many2one(
        'hr.employee',
        string='HR Employee Record',
        readonly=True,
        copy=False,
        ondelete='set null'
    )


    # ACCOUNT STATUS

    active = fields.Boolean(
        string='Active',
        default=True
    )

    status = fields.Selection(
        [
            ('available', 'Available'),
            ('inactive', 'Inactive'),
            ('operation_theatre', 'Operation Theatre'),
        ],
        string='Status',
        default='available',
        required=True
    )

    # ACCESS & PERMISSIONS (Admin Configurable)
    perm_dashboard = fields.Boolean(
        string='Dashboard',
        default=True,
        help='Allow access to Main Role / Hospital Dashboard'
    )
    perm_appointments = fields.Boolean(
        string='Appointments & Queue',
        default=False,
        help='Allow booking appointments and viewing doctor patient queues'
    )
    perm_patients = fields.Boolean(
        string='Patients Directory',
        default=False,
        help='Allow viewing and managing patient records'
    )
    perm_billing = fields.Boolean(
        string='Billing & Invoices',
        default=False,
        help='Allow viewing and creating patient bills & invoices'
    )
    perm_pharmacy = fields.Boolean(
        string='Pharmacy & Stock',
        default=False,
        help='Allow access to pharmacy items, medicine stock, and dispensing'
    )
    perm_lab = fields.Boolean(
        string='Laboratory & Tests',
        default=False,
        help='Allow viewing lab test requests, entering results, and printing lab reports'
    )
    perm_hr_employees = fields.Boolean(
        string='HR Employees',
        default=False,
        help='Allow viewing and managing hospital staff and employee directory'
    )
    perm_attendance = fields.Boolean(
        string='Staff Attendances',
        default=False,
        help='Allow viewing staff check-in/out records'
    )
    perm_time_off = fields.Boolean(
        string='Time Off / Leaves',
        default=False,
        help='Allow viewing staff leave requests'
    )
    perm_expenses = fields.Boolean(
        string='Staff Expenses',
        default=False,
        help='Allow viewing employee expense claims'
    )
    perm_asset_items = fields.Boolean(
        string='Hospital Assets',
        default=False,
        help='Allow viewing medical equipment and asset inventory'
    )
    perm_asset_requests = fields.Boolean(
        string='Asset Requests & Purchases',
        default=False,
        help='Allow viewing item requests, purchase orders, and supplier invoices'
    )
    perm_masters = fields.Boolean(
        string='Master Data & Configuration',
        default=False,
        help='Allow configuring categories, consultation types, and fee rules'
    )
    perm_users = fields.Boolean(
        string='User Management',
        default=False,
        help='Allow creating hospital users and managing permissions'
    )
    perm_emergency = fields.Boolean(
        string='Emergency Treatment',
        default=False,
        help='Allow viewing and managing Emergency Treatment & Inpatient admissions'
    )

    # ACTION / CAPABILITY PERMISSIONS (Admin Configurable)
    perm_can_delete = fields.Boolean(
        string='Can Delete Records',
        default=False,
        help='Allow permanently deleting hospital records'
    )
    perm_can_approve = fields.Boolean(
        string='Can Approve Requests',
        default=False,
        help='Allow approving leave requests, expense claims, and purchase requests'
    )
    perm_can_collect_cash = fields.Boolean(
        string='Can Collect Cash / Settle Bills',
        default=False,
        help='Allow confirming payments and settling patient bills'
    )
    perm_can_export = fields.Boolean(
        string='Can Export Data (Excel/CSV)',
        default=False,
        help='Allow exporting data from lists and reports to Excel or CSV'
    )


    # COMPUTE

    @api.depends('role_id')
    def _compute_allowed_departments(self):
        for record in self:
            if record.role_id:
                record.allowed_department_ids = record.role_id.department_ids
            else:
                record.allowed_department_ids = False

    @api.depends('odoo_user_id')
    def _compute_account_created(self):
        for record in self:
            record.account_created = bool(record.odoo_user_id)

    @api.depends('odoo_user_id')
    def _compute_two_factor_enabled(self):
        for record in self:
            user = record.odoo_user_id

            if not user:
                record.two_factor_enabled = False
                continue

            if 'totp_enabled' in user._fields:
                record.two_factor_enabled = bool(
                    user.totp_enabled
                )
            else:
                record.two_factor_enabled = False

    # ROLE â†’ ODOO GROUP

    def _get_odoo_group_for_role(self):
        self.ensure_one()

        if not self.role_id:
            return self.env.ref(
                'hospital_management.group_hospital_user'
            )

        role_name = (self.role_id.name or '').strip().lower()

        role_group_map = {
            'doctor': 'group_hospital_doctor',
            'nurse': 'group_hospital_nurse',
            'receptionist': 'group_hospital_receptionist',
            'pharmacist': 'group_hospital_pharmacist',
            'lab technician': 'group_hospital_lab_technician',
            'lab manager': 'group_hospital_lab_technician',
            'lab master': 'group_hospital_lab_technician',
            'billing executive': 'group_hospital_billing',
            'admin': 'group_hospital_admin',
            'administrator': 'group_hospital_admin',
            'hr executive': 'group_hospital_hr',
            'hr manager': 'group_hospital_hr',
            'emergency ward': 'group_hospital_emergency_ward',
            'observation ward': 'group_hospital_emergency_ward',
            'super admin': 'group_hospital_super_admin',
        }
        xml_id = role_group_map.get(role_name)

        if xml_id:
            try:
                return self.env.ref(
                    f'hospital_management.{xml_id}'
                )
            except ValueError:
                pass

        return self.env.ref(
            'hospital_management.group_hospital_user'
        )

    @api.onchange('password')
    def _onchange_password(self):
        if self.password:
            self.password_confirm = self.password

    # CREATE ODOO USER

    def _create_odoo_user(self, password):
        self.ensure_one()

        if self.odoo_user_id:
            return self.odoo_user_id

        if not self.login:
            raise ValidationError(
                'Username / Email is required to create the login account.'
            )

        if not password:
            raise ValidationError(
                'Password is required to create the login account.'
            )

        existing_user = self.env['res.users'].sudo().search(
            [('login', '=', self.login)],
            limit=1
        )

        if existing_user:
            raise ValidationError(
                f'An Odoo user already exists with login: {self.login}'
            )

        role_group = self._get_odoo_group_for_role()

        role_name = (self.role_id.name or '').strip().lower()
        if role_name in ['hr manager', 'hr executive']:
            dashboard_action = self.env.ref('hospital_management.action_hospital_hr_dashboard', raise_if_not_found=False)
        elif role_name == 'receptionist':
            dashboard_action = self.env.ref('hospital_management.action_hospital_reception_dashboard', raise_if_not_found=False)
        elif role_name == 'doctor':
            dashboard_action = self.env.ref('hospital_management.action_hospital_doctor_dashboard', raise_if_not_found=False)
        elif role_name == 'lab technician':
            dashboard_action = self.env.ref('hospital_management.action_hospital_lab_dashboard', raise_if_not_found=False)
        elif role_name == 'pharmacist':
            dashboard_action = self.env.ref('hospital_management.action_hospital_pharmacy_dashboard_form', raise_if_not_found=False)
        elif role_name in ['admin', 'administrator', 'super admin']:
            dashboard_action = self.env.ref('hospital_management.action_hospital_admin_dashboard_window', raise_if_not_found=False)
        else:
            dashboard_action = self.env.ref('hospital_management.action_hospital_dashboard', raise_if_not_found=False)
        action_id = dashboard_action.id if dashboard_action else False

        user_vals = {
            'name': self.name,
            'login': self.login,
            'email': self.email or self.login,
            'password': password,
            'group_ids': [
                (4, self.env.ref('base.group_user').id),
                (4, role_group.id),
            ],
        }
        if action_id:
            user_vals['action_id'] = action_id


        odoo_user = self.env['res.users'].sudo().create(user_vals)

        self.sudo().write({
            'odoo_user_id': odoo_user.id,
        })

        return odoo_user

    def _update_odoo_user_password(self, password):
        self.ensure_one()

        if self.odoo_user_id and password:
            self.odoo_user_id.sudo().write({
                'password': password,
            })


    # -------------------------------------------------
    # PERMISSION DEFAULTS & ROLE MAPPING
    # -------------------------------------------------

    def _get_default_permissions_for_role(self, role_name):
        role_norm = (role_name or '').strip().lower()
        defaults = {
            'perm_dashboard': True,
            'perm_appointments': False,
            'perm_patients': False,
            'perm_billing': False,
            'perm_pharmacy': False,
            'perm_lab': False,
            'perm_hr_employees': False,
            'perm_attendance': False,
            'perm_time_off': False,
            'perm_expenses': False,
            'perm_asset_items': False,
            'perm_asset_requests': False,
            'perm_masters': False,
            'perm_users': False,
            'perm_emergency': False,
            'perm_can_delete': False,
            'perm_can_approve': False,
            'perm_can_collect_cash': False,
            'perm_can_export': False,
        }

        if role_norm in ['admin', 'administrator', 'super admin']:
            for k in defaults:
                defaults[k] = True
        elif role_norm == 'doctor':
            defaults.update({
                'perm_appointments': True,
                'perm_patients': True,
                'perm_lab': True,
                'perm_can_export': True,
            })
        elif role_norm == 'receptionist':
            defaults.update({
                'perm_appointments': True,
                'perm_patients': True,
                'perm_billing': True,
                'perm_emergency': True,
                'perm_can_collect_cash': True,
            })
        elif role_norm in ['emergency ward', 'observation ward']:
            defaults.update({
                'perm_emergency': True,
                'perm_patients': True,
            })
        elif role_norm == 'pharmacist':
            defaults.update({
                'perm_pharmacy': True,
                'perm_billing': True,
                'perm_can_collect_cash': True,
            })
        elif role_norm in ['lab technician', 'lab manager', 'lab master']:
            defaults.update({
                'perm_lab': True,
                'perm_can_export': True,
            })
        elif role_norm in ['hr manager', 'hr executive']:
            defaults.update({
                'perm_hr_employees': True,
                'perm_attendance': True,
                'perm_time_off': True,
                'perm_expenses': True,
                'perm_can_approve': True,
                'perm_can_export': True,
            })
        elif role_norm == 'asset manager':
            defaults.update({
                'perm_asset_items': True,
                'perm_asset_requests': True,
                'perm_can_approve': True,
                'perm_can_export': True,
            })
        return defaults

    def action_reset_permissions(self):
        self.ensure_one()
        role_name = self.role_id.name if self.role_id else ''
        defaults = self._get_default_permissions_for_role(role_name)
        self.write(defaults)
        self._sync_permissions_to_odoo_user()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Permissions Reset',
                'message': f"Permissions for {self.name} have been reset to defaults for role '{role_name}'.",
                'type': 'info',
                'sticky': False,
            }
        }

    # -------------------------------------------------
    # SYNC PERMISSIONS TO ODOO USER (GROUPS & ACTION)
    # -------------------------------------------------

    def _sync_permissions_to_odoo_user(self):
        for rec in self:
            if not rec.odoo_user_id:
                continue

            user = rec.odoo_user_id.sudo()
            group_ids = set()

            # Always Internal User
            internal_user_group = self.env.ref('base.group_user', raise_if_not_found=False)
            if internal_user_group:
                group_ids.add(internal_user_group.id)

            # Primary Role group
            primary_group = rec._get_odoo_group_for_role()
            if primary_group:
                group_ids.add(primary_group.id)

            # Export
            if rec.perm_can_export:
                g = self.env.ref('base.group_allow_export', raise_if_not_found=False)
                if g:
                    group_ids.add(g.id)

            # Billing
            if rec.perm_billing:
                g = self.env.ref('hospital_management.group_hospital_billing', raise_if_not_found=False)
                if g:
                    group_ids.add(g.id)

            # Role-specific access groups are determined by primary role above (_get_odoo_group_for_role).
            # Feature permissions must not cross-contaminate other roles' primary groups.

            # HR Employees
            if rec.perm_hr_employees:
                g = self.env.ref('hr.group_hr_manager' if rec.perm_can_approve else 'hr.group_hr_user', raise_if_not_found=False)
                if g:
                    group_ids.add(g.id)
                g_hr = self.env.ref('hospital_management.group_hospital_hr', raise_if_not_found=False)
                if g_hr:
                    group_ids.add(g_hr.id)

            # Attendance
            if rec.perm_attendance:
                g = self.env.ref('hr_attendance.group_hr_attendance_manager' if rec.perm_can_approve else 'hr_attendance.group_hr_attendance_user', raise_if_not_found=False)
                if g:
                    group_ids.add(g.id)

            # Time Off
            if rec.perm_time_off:
                g = self.env.ref('hr_holidays.group_hr_holidays_manager' if rec.perm_can_approve else 'hr_holidays.group_hr_holidays_user', raise_if_not_found=False)
                if g:
                    group_ids.add(g.id)

            # Expenses
            if rec.perm_expenses:
                g = self.env.ref('hr_expense.group_hr_expense_manager' if rec.perm_can_approve else 'hr_expense.group_hr_expense_team_approver', raise_if_not_found=False)
                if g:
                    group_ids.add(g.id)

            # Asset Items
            if rec.perm_asset_items:
                g = self.env.ref('maintenance.group_equipment_manager', raise_if_not_found=False)
                if g:
                    group_ids.add(g.id)

            # Asset Requests
            if rec.perm_asset_requests:
                g = self.env.ref('hospital_hr_asset.group_hospital_asset_manager', raise_if_not_found=False)
                if g:
                    group_ids.add(g.id)

            # Masters / Users / Admin
            if rec.perm_masters and rec.perm_users:
                g = self.env.ref('hospital_management.group_hospital_admin', raise_if_not_found=False)
                if g:
                    group_ids.add(g.id)

            # Emergency Treatment
            if rec.perm_emergency:
                g = self.env.ref('hospital_management.group_hospital_emergency_ward', raise_if_not_found=False)
                if g:
                    group_ids.add(g.id)

            # Route & Landing Action
            role_name = (rec.role_id.name or '').strip().lower()
            if role_name in ['hr manager', 'hr executive'] or (rec.perm_hr_employees and not any([rec.perm_appointments, rec.perm_patients, rec.perm_pharmacy, rec.perm_lab])):
                dashboard_action = self.env.ref('hospital_management.action_hospital_hr_dashboard', raise_if_not_found=False)
            elif role_name == 'receptionist':
                dashboard_action = self.env.ref('hospital_management.action_hospital_reception_dashboard', raise_if_not_found=False)
            elif role_name == 'doctor':
                dashboard_action = self.env.ref('hospital_management.action_hospital_doctor_dashboard', raise_if_not_found=False)
            elif role_name == 'lab technician':
                dashboard_action = self.env.ref('hospital_management.action_hospital_lab_dashboard', raise_if_not_found=False)
            elif role_name == 'pharmacist':
                dashboard_action = self.env.ref('hospital_management.action_hospital_pharmacy_dashboard_form', raise_if_not_found=False)
            elif role_name in ['admin', 'administrator', 'super admin']:
                dashboard_action = self.env.ref('hospital_management.action_hospital_admin_dashboard_window', raise_if_not_found=False)
            else:
                dashboard_action = self.env.ref('hospital_management.action_hospital_dashboard', raise_if_not_found=False)

            write_vals = {
                'group_ids': [(6, 0, list(group_ids))]
            }
            if dashboard_action:
                write_vals['action_id'] = dashboard_action.id

            user.write(write_vals)

    def _update_odoo_user_group(self):
        self.ensure_one()
        self._sync_permissions_to_odoo_user()

    # -------------------------------------------------
    # HR EMPLOYEE BI-DIRECTIONAL LINK & SYNC
    # -------------------------------------------------

    def _get_or_create_hr_department(self, hospital_department):
        if not hospital_department:
            return False
        HrDepartment = self.env['hr.department'].sudo()
        name = hospital_department.name.strip()
        dept = HrDepartment.search([('name', '=ilike', name)], limit=1)
        if not dept:
            dept = HrDepartment.create({'name': name})
        return dept.id

    def _get_or_create_hr_job(self, hospital_designation, hr_department_id=False):
        if not hospital_designation:
            return False
        HrJob = self.env['hr.job'].sudo()
        name = hospital_designation.name.strip()
        job = HrJob.search([('name', '=ilike', name)], limit=1)
        if not job:
            vals = {'name': name}
            if hr_department_id:
                vals['department_id'] = hr_department_id
            job = HrJob.create(vals)
        return job.id

    def _sync_hr_employee(self):
        HrEmployee = self.env['hr.employee'].sudo()
        for rec in self:
            emp = rec.hr_employee_id
            if not emp and rec.odoo_user_id:
                emp = HrEmployee.search([('user_id', '=', rec.odoo_user_id.id)], limit=1)
            if not emp and rec.login:
                emp = HrEmployee.search([
                    '|',
                    ('work_email', '=', rec.email or rec.login),
                    ('name', '=ilike', rec.name.strip())
                ], limit=1)

            dept_id = rec._get_or_create_hr_department(rec.department_id) if rec.department_id else False
            job_id = rec._get_or_create_hr_job(rec.designation_id, dept_id) if rec.designation_id else False

            vals = {
                'name': rec.name,
                'work_email': rec.email or (rec.odoo_user_id.email if rec.odoo_user_id else rec.login),
                'work_phone': rec.mobile or False,
                'active': rec.active,
            }
            if rec.odoo_user_id:
                vals['user_id'] = rec.odoo_user_id.id
            if dept_id:
                vals['department_id'] = dept_id
            if job_id:
                vals['job_id'] = job_id
            if rec.gender:
                if 'sex' in HrEmployee._fields: vals['sex'] = rec.gender
            if rec.date_of_birth:
                vals['birthday'] = rec.date_of_birth

            if emp:
                emp.write(vals)
            else:
                emp = HrEmployee.create(vals)

            if rec.hr_employee_id != emp:
                rec.sudo().write({'hr_employee_id': emp.id})

    def action_open_hr_employee(self):
        self.ensure_one()
        if not self.hr_employee_id:
            self._sync_hr_employee()
        if not self.hr_employee_id:
            raise ValidationError("No linked HR Employee record found.")
        return {
            'name': 'HR Employee Profile',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee',
            'res_id': self.hr_employee_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


    # UPDATE ODOO USER ACCOUNT

    def _update_odoo_user_account(self, vals):
        self.ensure_one()

        if not self.odoo_user_id:
            return

        update_vals = {}

        if 'name' in vals:
            update_vals['name'] = vals['name']

        if 'email' in vals and vals['email']:
            existing_user = self.env['res.users'].sudo().search([
                ('login', '=', vals['email']),
                ('id', '!=', self.odoo_user_id.id),
            ], limit=1)

            if existing_user:
                raise ValidationError(
                    f'An Odoo login already exists for {vals["email"]}.'
                )

            update_vals['login'] = vals['email']
            update_vals['email'] = vals['email']

        if 'active' in vals:
            update_vals['active'] = vals['active']

        if 'password' in vals and vals['password']:
            update_vals['password'] = vals['password']

        if update_vals:
            self.odoo_user_id.sudo().write(update_vals)

    # ONCHANGE

    @api.onchange('role_id')
    def _onchange_role_id(self):
        self.department_id = False
        self.designation_id = False
        self.reporting_to_id = False
        if self.role_id:
            defaults = self._get_default_permissions_for_role(self.role_id.name)
            for k, v in defaults.items():
                setattr(self, k, v)

    @api.onchange('department_id')
    def _onchange_department_id(self):
        self.designation_id = False
        self.reporting_to_id = False

    # AUDIT LOGGING

    def _create_activity(
        self,
        action,
        description,
        field_name=False,
        previous_value=False,
        new_value=False,
        status='success'
    ):
        Activity = self.env['hospital.user.activity']

        for record in self:

            Activity.create({
                'user_id': record.id,
                'action': action,
                'description': description,
                'performed_by_id': self.env.user.id,
                'activity_date': fields.Datetime.now(),
                'field_name': field_name,
                'previous_value': previous_value,
                'new_value': new_value,
                'status': status,
                'ip_address': self.env.context.get('remote_addr'),
                'user_agent': self.env.context.get('user_agent'),
            })

    # SAVE ACTION  (explicit Save button on the form)

    def action_save_user(self):
        self.ensure_one()
        if self.is_doctor and not self.consultation_line_ids:
            raise ValidationError(
                "Doctor Configuration Incomplete!\n\n"
                "Please add at least one Consultation Type and Fee in the 'Consultation Types & Fees' tab before saving."
            )
        # The user requested to always redirect to the all users page
        action = self.env.ref('hospital_management.action_hospital_users').read()[0]
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Saved successfully',
                'type': 'success',
                'sticky': False,
                'next': action
            }
        }

    # CREATE

    @api.model
    def _validate_password_strength(self, password):
        import re
        if not password:
            return
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not re.search(r"[a-z]", password):
            raise ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r"[A-Z]", password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r"[0-9]", password):
            raise ValidationError("Password must contain at least one number.")
        if not re.search(r"[^a-zA-Z0-9]", password):
            raise ValidationError("Password must contain at least one special symbol.")

    @api.model_create_multi
    def create(self, vals_list):

        records = super().create(vals_list)

        for record, vals in zip(records, vals_list):

            password = vals.get('password')
            password_confirm = vals.get('password_confirm')

            if not password:
                raise ValidationError(
                    f'Password is required for user "{record.name}".'
                )
            if password != password_confirm:
                raise ValidationError("Passwords do not match!")
            self._validate_password_strength(password)

            # Create actual Odoo login account
            record._create_odoo_user(password)

            # Initialize role defaults if permissions were not passed
            if not any(k.startswith('perm_') for k in vals):
                defaults = record._get_default_permissions_for_role(record.role_id.name if record.role_id else '')
                record.sudo().write(defaults)
            record._sync_permissions_to_odoo_user()
            record._sync_hr_employee()

            # Keep synchronized password on hospital.user
            record.sudo().write({
                'password': password,
                'password_confirm': password,
                'password_last_changed': fields.Datetime.now(),
            })

            # Create audit activity
            record._create_activity(
                action='created',
                description=(
                    f'User "{record.name}" was created.'
                ),
                field_name='User',
                previous_value='',
                new_value=(
                    f'Username: {record.login}, '
                    f'Role: {record.role_id.name if record.role_id else ""}, '
                    f'Department: {record.department_id.name if record.department_id else ""}'
                ),
            )

            # Password event
            record._create_activity(
                action='password_changed',
                description=(
                    f'Initial password was created for "{record.name}".'
                ),
                field_name='Password',
                previous_value='',
                new_value='********',
            )

        return records

    # WRITE

    def write(self, vals):

        password = vals.pop('password', False)
        password_confirm = vals.pop('password_confirm', False)

        # -------------------------------------------------
        # Save old values BEFORE update
        # -------------------------------------------------

        tracked_values = {}

        for record in self:

            tracked_values[record.id] = {}

            if 'role_id' in vals:
                tracked_values[record.id]['role_id'] = (
                    record.role_id.name
                    if record.role_id
                    else ''
                )

            if 'department_id' in vals:
                tracked_values[record.id]['department_id'] = (
                    record.department_id.name
                    if record.department_id
                    else ''
                )

            if 'designation_id' in vals:
                tracked_values[record.id]['designation_id'] = (
                    record.designation_id.name
                    if record.designation_id
                    else ''
                )

            if 'reporting_to_id' in vals:
                tracked_values[record.id]['reporting_to_id'] = (
                    record.reporting_to_id.name
                    if record.reporting_to_id
                    else ''
                )

            if 'active' in vals:
                tracked_values[record.id]['active'] = (
                    'Active'
                    if record.active
                    else 'Inactive'
                )

            general_fields = [
                'name',
                'employee_id',
                'login',
                'email',
                'mobile',
                'date_of_birth',
                'gender',
                'address',
            ]

            for field_name in general_fields:

                if field_name in vals:

                    old_value = getattr(record, field_name)

                    if old_value:
                        old_value = str(old_value)

                    tracked_values[record.id][field_name] = (
                        old_value or ''
                    )

        # -------------------------------------------------
        # Update hospital.user
        # -------------------------------------------------

        result = super().write(vals)

        # -------------------------------------------------
        # Sync with actual Odoo login account
        # -------------------------------------------------
        odoo_vals = {}
        if 'name' in vals: odoo_vals['name'] = vals['name']
        if 'login' in vals: odoo_vals['login'] = vals['login']
        if 'email' in vals: odoo_vals['email'] = vals['email']
        if 'active' in vals: odoo_vals['active'] = vals['active']

        if odoo_vals:
            for record in self:
                if record.odoo_user_id:
                    record.odoo_user_id.sudo().write(odoo_vals)

        # -------------------------------------------------
        # Update actual Odoo login password
        # -------------------------------------------------

        new_password = password or password_confirm
        if new_password:
            if password and password_confirm and password != password_confirm:
                raise ValidationError("Passwords do not match!")
            self._validate_password_strength(new_password)

            for record in self:

                if record.odoo_user_id:
                    record._update_odoo_user_password(
                        new_password
                    )
                else:
                    record._create_odoo_user(new_password)

                self.env.cr.execute(
                    "UPDATE hospital_user SET password = %s, password_confirm = %s, password_last_changed = %s WHERE id = %s",
                    (new_password, new_password, fields.Datetime.now(), record.id)
                )
                record.invalidate_recordset(['password', 'password_confirm', 'password_last_changed'])

                record._create_activity(
                    action='password_changed',
                    description=(
                        f'Password changed for "{record.name}".'
                    ),
                    field_name='Password',
                    previous_value='********',
                    new_value='********',
                )

        # -------------------------------------------------
        # Audit changes
        # -------------------------------------------------

        for record in self:

            previous = tracked_values.get(record.id, {})

            # ---------------------------------------------
            # Role
            # ---------------------------------------------

            if 'role_id' in vals:

                old_value = previous.get(
                    'role_id',
                    ''
                )

                new_value = (
                    record.role_id.name
                    if record.role_id
                    else ''
                )

                if old_value != new_value:

                    record._update_odoo_user_group()

                    record._create_activity(
                        action='role_changed',
                        description=(
                            f'Role changed for "{record.name}".'
                        ),
                        field_name='Role',
                        previous_value=old_value,
                        new_value=new_value,
                    )

            # ---------------------------------------------
            # Department
            # ---------------------------------------------

            if 'department_id' in vals:

                old_value = previous.get(
                    'department_id',
                    ''
                )

                new_value = (
                    record.department_id.name
                    if record.department_id
                    else ''
                )

                if old_value != new_value:

                    record._create_activity(
                        action='department_changed',
                        description=(
                            f'Department changed for "{record.name}".'
                        ),
                        field_name='Department',
                        previous_value=old_value,
                        new_value=new_value,
                    )

            # ---------------------------------------------
            # Designation
            # ---------------------------------------------

            if 'designation_id' in vals:

                old_value = previous.get(
                    'designation_id',
                    ''
                )

                new_value = (
                    record.designation_id.name
                    if record.designation_id
                    else ''
                )

                if old_value != new_value:

                    record._create_activity(
                        action='designation_changed',
                        description=(
                            f'Designation changed for "{record.name}".'
                        ),
                        field_name='Designation',
                        previous_value=old_value,
                        new_value=new_value,
                    )

            # ---------------------------------------------
            # Reporting Manager
            # ---------------------------------------------

            if 'reporting_to_id' in vals:

                old_value = previous.get(
                    'reporting_to_id',
                    ''
                )

                new_value = (
                    record.reporting_to_id.name
                    if record.reporting_to_id
                    else ''
                )

                if old_value != new_value:

                    record._create_activity(
                        action='reporting_changed',
                        description=(
                            f'Reporting manager changed for '
                            f'"{record.name}".'
                        ),
                        field_name='Reporting To',
                        previous_value=old_value,
                        new_value=new_value,
                    )

            # ---------------------------------------------
            # Account Status
            # ---------------------------------------------

            if 'active' in vals:

                old_value = previous.get(
                    'active',
                    ''
                )

                new_value = (
                    'Active'
                    if record.active
                    else 'Inactive'
                )

                if old_value != new_value:

                    action = (
                        'activated'
                        if record.active
                        else 'deactivated'
                    )

                    record._create_activity(
                        action=action,
                        description=(
                            f'Account for "{record.name}" was '
                            f'{"activated" if record.active else "deactivated"}.'
                        ),
                        field_name='Account Status',
                        previous_value=old_value,
                        new_value=new_value,
                    )

            # ---------------------------------------------
            # General Information
            # ---------------------------------------------

            general_field_labels = {
                'name': 'Full Name',
                'employee_id': 'Employee ID',
                'login': 'Username',
                'email': 'Email Address',
                'mobile': 'Mobile Number',
                'date_of_birth': 'Date of Birth',
                'gender': 'Gender',
                'address': 'Address',
            }

            for field_name, label in general_field_labels.items():

                if field_name not in vals:
                    continue

                old_value = previous.get(
                    field_name,
                    ''
                )

                new_value = getattr(
                    record,
                    field_name
                )

                if new_value:
                    new_value = str(new_value)

                new_value = new_value or ''

                if old_value == new_value:
                    continue

                record._create_activity(
                    action='updated',
                    description=(
                        f'{label} updated for '
                        f'"{record.name}".'
                    ),
                    field_name=label,
                    previous_value=old_value,
                    new_value=new_value,
                )

        # Sync permissions if role or permissions changed
        perm_keys = [k for k in vals if k.startswith('perm_') or k == 'role_id']
        if perm_keys:
            for record in self:
                record._sync_permissions_to_odoo_user()

        # Sync HR employee if personal or work details changed
        hr_keys = ['name', 'email', 'mobile', 'department_id', 'designation_id', 'active', 'gender', 'date_of_birth', 'role_id']
        if any(k in vals for k in hr_keys):
            for record in self:
                record._sync_hr_employee()

        return result

    # VALIDATION

    @api.constrains('employee_id')
    def _check_employee_id_unique(self):
        for record in self:

            if record.employee_id:

                duplicate = self.search([
                    ('employee_id', '=', record.employee_id),
                    ('id', '!=', record.id),
                ], limit=1)

                if duplicate:
                    raise ValidationError(
                        'Employee ID must be unique.'
                    )

    @api.constrains('login')
    def _check_login_unique(self):
        for record in self:

            if record.login:

                duplicate = self.search([
                    ('login', '=', record.login),
                    ('id', '!=', record.id),
                ], limit=1)

                if duplicate:
                    raise ValidationError(
                        'Username must be unique.'
                    )

    @api.constrains('email')
    def _check_email_unique(self):
        for record in self:

            if record.email:

                duplicate = self.search([
                    ('email', '=', record.email),
                    ('id', '!=', record.id),
                ], limit=1)

                if duplicate:
                    raise ValidationError(
                        'Email address must be unique.'
                    )

    @api.constrains('designation_id', 'department_id')
    def _check_designation_department(self):
        for record in self:

            if (
                record.designation_id
                and record.designation_id.department_id
                != record.department_id
            ):
                raise ValidationError(
                    'The selected designation does not belong '
                    'to the selected department.'
                )

    @api.constrains('reporting_to_id', 'role_id', 'department_id')
    def _check_reporting_to(self):
        for record in self:

            if record.reporting_to_id:

                if record.reporting_to_id == record:
                    raise ValidationError(
                        'A user cannot report to themselves.'
                    )

                if record.reporting_to_id.role_id != record.role_id:
                    raise ValidationError(
                        'Reporting To must have the same role.'
                    )

                if (
                    record.reporting_to_id.department_id
                    != record.department_id
                ):
                    raise ValidationError(
                        'Reporting To must belong to the same department.'
                    )

    @api.constrains('consultation_line_ids', 'role_id')
    def _check_doctor_consultation_lines(self):
        for record in self:
            if record.role_id and (record.role_id.name or '').strip().lower() == 'doctor':
                if not record.consultation_line_ids:
                    raise ValidationError(
                        "Doctor Configuration Incomplete!\n\n"
                        "Please add at least one Consultation Type and Fee in the 'Consultation Types & Fees' tab before saving."
                    )
                type_ids = [line.consultation_type_id.id for line in record.consultation_line_ids if line.consultation_type_id]
                if len(type_ids) != len(set(type_ids)):
                    raise ValidationError(
                        "Duplicate Consultation Types are not allowed for the same doctor. "
                        "Each consultation type must be added only once."
                    )

    def action_close(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create User',
            'res_model': 'hospital.user',
            'view_mode': 'list,form',
            'target': 'current',
        }