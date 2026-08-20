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

        # Handle Login button
        if request.httprequest.method == 'POST':

            email = (kwargs.get('email') or '').strip()
            password = kwargs.get('password') or ''

            if not email or not password:
                error = 'Please enter email and password.'

            else:

                credential = {
                    'login': email,
                    'password': password,
                    'type': 'password',
                }

                try:
                    request.session.authenticate(
                        request.env,
                        credential,
                    )

                    # Authentication succeeded
                    user = request.env.user

                    self._log_activity(
                        user=user,
                        action='login_success',
                        status='success',
                        description='User logged in successfully.',
                    )

                    return request.redirect('/web')

                except AccessDenied:

                    # Try to identify the account that attempted login
                    user = request.env['res.users'].sudo().search(
                        [('login', '=', email)],
                        limit=1,
                    )

                    self._log_activity(
                        user=user if user else None,
                        action='login_failed',
                        status='failed',
                        description='Invalid email or password.',
                    )

                    error = 'Invalid email or password.'

        return request.render(
            'hospital_management.login_page',
            {
                'error': error,
            }
        )