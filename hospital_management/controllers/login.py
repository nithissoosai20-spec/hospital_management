from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied


class HospitalLoginController(http.Controller):

    def _log_activity(
        self,
        user=None,
        action='login_failed',
        status='failed',
        description=None,
    ):
        """Create a hospital user activity record."""

        try:
            vals = {
                'user_id': user.id if user else False,
                'action': action,
                'status': status,
                'description': description or '',
                'ip_address': request.httprequest.remote_addr or '',
                'user_agent': request.httprequest.user_agent.string or '',
            }

            request.env['hospital.user.activity'].sudo().create(vals)

        except Exception:
            # Activity logging must never prevent login.
            request.env.cr.rollback()

    @http.route(
        '/login',
        type='http',
        auth='public',
        methods=['GET', 'POST'],
        website=False,
    )
    def login_page(self, **kwargs):

        # Already logged in
        if request.session.uid:
            return request.redirect('/web')

        error = None

        # Handle login
        if request.httprequest.method == 'POST':

            username = (kwargs.get('username') or '').strip()
            password = kwargs.get('password') or ''

            if not username or not password:

                error = 'Please enter username and password.'

            else:

                credential = {
                    'login': username,
                    'password': password,
                    'type': 'password',
                }

                try:

                    request.session.authenticate(
                        request.env,
                        credential,
                    )

                    # Authentication succeeded
                    odoo_user = request.env.user

                    # Find corresponding hospital user
                    hospital_user = request.env[
                        'hospital.user'
                    ].sudo().search(
                        [
                            (
                                'odoo_user_id',
                                '=',
                                odoo_user.id,
                            )
                        ],
                        limit=1,
                    )

                    self._log_activity(
                        user=hospital_user,
                        action='login_success',
                        status='success',
                        description=(
                            'User logged in successfully.'
                        ),
                    )

                    return request.redirect('/web')

                except AccessDenied:

                    # Find hospital user by username
                    hospital_user = request.env[
                        'hospital.user'
                    ].sudo().search(
                        [
                            ('login', '=', username),
                        ],
                        limit=1,
                    )

                    self._log_activity(
                        user=hospital_user if hospital_user else None,
                        action='login_failed',
                        status='failed',
                        description=(
                            'Invalid username or password.'
                        ),
                    )

                    error = 'Invalid username or password.'

        return request.render(
            'hospital_management.login_page',
            {
                'error': error,
            }
        )