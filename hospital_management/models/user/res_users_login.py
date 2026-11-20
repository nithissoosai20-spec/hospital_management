from odoo import models, fields, api
from odoo.exceptions import AccessDenied


class ResUsersLoginTracking(models.Model):
    """
    Extends res.users to capture login events and log them
    to hospital.user.activity so admins can see when each
    hospital user last logged in and a full login history.
    Also handles manual IM presence (online/away/busy/offline).
    """
    _inherit = 'res.users'

    manual_im_status = fields.Selection(
        selection_add=[('online', 'Online')],
        ondelete={'online': 'set null'}
    )

    @api.depends("manual_im_status", "presence_ids.status")
    def _compute_im_status(self):
        for user in self:
            if user.manual_im_status:
                user.im_status = user.manual_im_status
            elif user.presence_ids.status and user.presence_ids.status != "offline":
                user.im_status = user.presence_ids.status
            else:
                user.im_status = "online"

    @api.model
    def get_current_user_designation(self):
        user = self.env.user
        h_user = self.env['hospital.user'].sudo().search([('odoo_user_id', '=', user.id)], limit=1)
        designation = ''
        if h_user:
            if h_user.role_id and h_user.role_id.name:
                designation = h_user.role_id.name
            elif h_user.designation_id and h_user.designation_id.name:
                designation = h_user.designation_id.name
        if not designation:
            if user.has_group('hospital_management.group_hospital_super_admin'):
                designation = 'Super Admin'
            elif user.has_group('hospital_management.group_hospital_admin'):
                designation = 'Administrator'
            elif user.has_group('hospital_management.group_hospital_doctor'):
                designation = 'Doctor'
            elif user.has_group('hospital_management.group_hospital_receptionist'):
                designation = 'Receptionist'
            elif user.has_group('hospital_management.group_hospital_pharmacist'):
                designation = 'Pharmacist'
            elif user.has_group('hospital_management.group_hospital_lab_technician'):
                designation = 'Lab Technician'
            elif user.has_group('hospital_management.group_hospital_hr'):
                designation = 'HR Manager'
        return designation

    def _check_credentials(self, password, env):
        """
        Override Odoo's credential check to log login events.

        How it works:
        - super()._check_credentials() either returns (success)
          or raises AccessDenied (failure).
        - If it returns → we log login_success.
        - If it raises → we log login_failed, then re-raise.

        The try/except around logging ensures that even if
        activity logging fails, the actual login is not blocked.
        """

        try:
            # ── Attempt the actual login ──────────────────────
            result = super()._check_credentials(password, env)

            # ── Login SUCCESS ──────────────────────────────────
            try:
                self.sudo()._log_hospital_login(success=True)
            except Exception:
                # Never break login if logging fails
                pass

            return result

        except AccessDenied:

            # ── Login FAILED ───────────────────────────────────
            try:
                self.sudo()._log_hospital_login(success=False)
            except Exception:
                pass

            raise

    # HELPERS

    def _log_hospital_login(self, success=True):
        """
        Find the hospital.user linked to this res.users record
        and create a hospital.user.activity log entry.
        """
        for odoo_user in self:

            hospital_user = self.env['hospital.user'].sudo().search(
                [('odoo_user_id', '=', odoo_user.id)],
                limit=1
            )

            if not hospital_user:
                # This Odoo user has no hospital.user profile → skip
                continue

            action = 'login_success' if success else 'login_failed'
            status = 'success' if success else 'failed'

            description = (
                f'User "{hospital_user.name}" logged in successfully.'
                if success
                else f'Failed login attempt for user "{hospital_user.name}".'
            )

            self.env['hospital.user.activity'].sudo().create({
                'user_id': hospital_user.id,
                'action': action,
                'description': description,
                'performed_by_id': odoo_user.id,
                'activity_date': fields.Datetime.now(),
                'status': status,
            })


class ResPartnerImStatus(models.Model):
    _inherit = 'res.partner'

    @api.depends("user_ids.manual_im_status", "user_ids.presence_ids.status")
    def _compute_im_status(self):
        for partner in self:
            statuses = []
            for u in partner.user_ids:
                if u.manual_im_status:
                    statuses.append(u.manual_im_status)
                elif u.presence_ids.status and u.presence_ids.status != 'offline':
                    statuses.append(u.presence_ids.status)
                else:
                    statuses.append('online')
            if 'online' in statuses:
                partner.im_status = 'online'
            elif 'away' in statuses:
                partner.im_status = 'away'
            elif 'busy' in statuses:
                partner.im_status = 'busy'
            elif 'offline' in statuses:
                partner.im_status = 'offline'
            else:
                partner.im_status = 'online'


import logging
_logger = logging.getLogger(__name__)

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        _logger.warning(">>> HOSPITAL IR.HTTP SESSION_INFO CALLED! <<<")
        result = super().session_info()
        user = self.env.user
        h_user = self.env['hospital.user'].sudo().search([('odoo_user_id', '=', user.id)], limit=1)
        designation = ''
        if h_user:
            if h_user.role_id and h_user.role_id.name:
                designation = h_user.role_id.name
            elif h_user.designation_id and h_user.designation_id.name:
                designation = h_user.designation_id.name
        if not designation:
            if user.has_group('hospital_management.group_hospital_super_admin'):
                designation = 'Super Admin'
            elif user.has_group('hospital_management.group_hospital_admin'):
                designation = 'Administrator'
            elif user.has_group('hospital_management.group_hospital_doctor'):
                designation = 'Doctor'
            elif user.has_group('hospital_management.group_hospital_receptionist'):
                designation = 'Receptionist'
            elif user.has_group('hospital_management.group_hospital_pharmacist'):
                designation = 'Pharmacist'
            elif user.has_group('hospital_management.group_hospital_lab_technician'):
                designation = 'Lab Technician'
            elif user.has_group('hospital_management.group_hospital_hr'):
                designation = 'HR Manager'
        result['hospital_user_designation'] = designation
        result['user_designation'] = designation
        _logger.warning(">>> HOSPITAL IR.HTTP DESIGNATION: %s <<<", designation)
        return result


