from odoo import models, fields


class HospitalUserActivity(models.Model):
    _name = 'hospital.user.activity'
    _description = 'Hospital User Activity'
    _order = 'activity_date desc, id desc'

    # =====================================================
    # USER
    # =====================================================

    user_id = fields.Many2one(
        'hospital.user',
        string='User',
        required=True,
        ondelete='cascade'
    )

    # =====================================================
    # ACTIVITY INFORMATION
    # =====================================================

    action = fields.Selection(
        [
            ('created', 'User Created'),
            ('updated', 'User Updated'),
            ('role_changed', 'Role Changed'),
            ('department_changed', 'Department Changed'),
            ('designation_changed', 'Designation Changed'),
            ('reporting_changed', 'Reporting Manager Changed'),
            ('activated', 'Account Activated'),
            ('deactivated', 'Account Deactivated'),
            ('password_changed', 'Password Changed'),
            ('password_reset', 'Password Reset'),
            ('login_success', 'Login Successful'),
            ('login_failed', 'Login Failed'),
            ('logout', 'Logout'),
        ],
        string='Action',
        required=True
    )

    description = fields.Text(
        string='Description',
        required=True
    )

    # =====================================================
    # AUDIT INFORMATION
    # =====================================================

    performed_by_id = fields.Many2one(
        'res.users',
        string='Performed By',
        required=True,
        default=lambda self: self.env.user,
        ondelete='restrict'
    )

    activity_date = fields.Datetime(
        string='Date / Time',
        required=True,
        default=fields.Datetime.now
    )

    # =====================================================
    # CHANGE INFORMATION
    # =====================================================

    field_name = fields.Char(
        string='Changed Field'
    )

    previous_value = fields.Text(
        string='Previous Value'
    )

    new_value = fields.Text(
        string='New Value'
    )

    # =====================================================
    # RESULT
    # =====================================================

    status = fields.Selection(
        [
            ('success', 'Success'),
            ('failed', 'Failed'),
        ],
        string='Status',
        required=True,
        default='success'
    )

    # =====================================================
    # REQUEST INFORMATION
    # =====================================================

    ip_address = fields.Char(
        string='IP Address'
    )

    user_agent = fields.Char(
        string='User Agent'
    )

    metadata = fields.Text(
        string='Metadata'
    )
