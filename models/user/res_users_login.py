from odoo import models, fields
from odoo.exceptions import AccessDenied


class ResUsersLoginTracking(models.Model):
    """
    Extends res.users to capture login events and log them
    to hospital.user.activity so admins can see when each
    hospital user last logged in and a full login history.
    """
    _inherit = 'res.users'

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

