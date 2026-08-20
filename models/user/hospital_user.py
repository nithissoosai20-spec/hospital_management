from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HospitalUser(models.Model):
    _name = 'hospital.user'
    _description = 'Hospital User'
    _order = 'name'

    ROLE_GROUPS = {
        'doctor': 'hospital_management.group_hospital_doctor',
        'nurse': 'hospital_management.group_hospital_nurse',
        'receptionist': 'hospital_management.group_hospital_receptionist',
        'pharmacist': 'hospital_management.group_hospital_pharmacist',
        'staff': 'hospital_management.group_hospital_user',
    }

    # =====================================================
    # PERSONAL DETAILS
    # =====================================================

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
        string='Mobile Number'
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
        string='Address'
    )

    # =====================================================
    # ODOO LOGIN ACCOUNT
    # =====================================================

    odoo_user_id = fields.Many2one(
        'res.users',
        string='Odoo User',
        ondelete='set null',
        copy=False,
        readonly=True
    )

    password = fields.Char(
        string='Initial Password',
        password=True,
        store=False,
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

    # =====================================================
    # WORK DETAILS
    # =====================================================

    role_id = fields.Many2one(
        'hospital.role',
        string='Role',
        required=False,
        ondelete='restrict'
    )

    odoo_user_id = fields.Many2one(
        'res.users',
        string='Odoo User',
        readonly=True,
        copy=False,
        ondelete='set null'
    )

    password = fields.Char(
        string='Initial Password',
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

    # =====================================================
    # ACCOUNT STATUS
    # =====================================================

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

    # =====================================================
    # COMPUTE
    # =====================================================

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

    # =====================================================
    # ROLE → ODOO GROUP
    # =====================================================

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
            'billing executive': 'group_hospital_billing',
            'admin': 'group_hospital_admin',
            'administrator': 'group_hospital_admin',
            'hr executive': 'group_hospital_hr',
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



    def _get_role_group(self):
        self.ensure_one()

        if not self.role_id:
            return self.env.ref(
                'hospital_management.group_hospital_user'
            )

        role_key = self.role_id.name.strip().lower()

        xml_id = self.ROLE_GROUPS.get(role_key)

        if not xml_id:
            return self.env.ref(
                'hospital_management.group_hospital_user'
            )

        return self.env.ref(xml_id)

    # =====================================================
    # CREATE ODOO USER
    # =====================================================

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

        role_group = self._get_role_group()

        user_vals = {
            'name': self.name,
            'login': self.login,
            'email': self.email or self.login,
            'password': password,
            'group_ids': [(6, 0, [role_group.id])],
        }

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


    # =====================================================
    # UPDATE ODOO USER GROUP
    # =====================================================

    def _update_odoo_user_group(self):
        self.ensure_one()

        if not self.odoo_user_id:
            return

        group = self._get_odoo_group_for_role()

        self.odoo_user_id.sudo().write({
            'group_ids': [(6, 0, [group.id])],
        })

    # =====================================================
    # UPDATE ODOO USER ACCOUNT
    # =====================================================

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

    # =====================================================
    # ONCHANGE
    # =====================================================

    @api.onchange('role_id')
    def _onchange_role_id(self):
        self.department_id = False
        self.designation_id = False
        self.reporting_to_id = False

    @api.onchange('department_id')
    def _onchange_department_id(self):
        self.designation_id = False
        self.reporting_to_id = False

    # =====================================================
    # AUDIT LOGGING
    # =====================================================

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


    # =====================================================
    # CREATE
    # =====================================================

    @api.model_create_multi
    def create(self, vals_list):

        records = super().create(vals_list)

        for record, vals in zip(records, vals_list):

            password = vals.get('password')

            if not password:
                raise ValidationError(
                    f'Password is required for user "{record.name}".'
                )

            # Create actual Odoo login account
            record._create_odoo_user(password)

            # Remove plain password from hospital.user
            record.sudo().write({
                'password': False,
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


    # =====================================================
    # WRITE
    # =====================================================

    def write(self, vals):

        password = vals.pop('password', False)

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
        # Update actual Odoo login password
        # -------------------------------------------------

        if password:

            for record in self:

                if record.odoo_user_id:

                    record._update_odoo_user_password(
                        password
                    )

                record.sudo().write({
                    'password_last_changed':
                        fields.Datetime.now(),
                })

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

        return result

    # =====================================================
    # VALIDATION
    # =====================================================

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