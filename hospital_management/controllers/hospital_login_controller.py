from odoo import http, fields
from odoo.http import request
from odoo.addons.web.controllers.session import Session
from odoo.addons.web.controllers.home import Home
from odoo.addons.web.controllers.database import Database
from odoo.addons.mail.controllers.im_status import ImStatusController

def get_user_hospital_designation(env, user):
    designation = ''
    h_user = env['hospital.user'].sudo().search([('odoo_user_id', '=', user.id)], limit=1)
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

class HospitalDatabase(Database):

    @http.route('/web/database/selector', type='http', auth="none")
    def selector(self, **kw):
        return request.redirect('/web/login?db=new_project_db', 303)

    @http.route('/web/database/manager', type='http', auth="none")
    def manager(self, **kw):
        return request.redirect('/web/login?db=new_project_db', 303)

class HospitalSession(Session):

    @http.route('/web/session/authenticate', type='jsonrpc', auth="none", readonly=False)
    def authenticate(self, db, login, password, base_location=None):
        res = super(HospitalSession, self).authenticate(db, login, password, base_location=base_location)
        
        if request.session.uid:
            # Login successful
            user = request.env['res.users'].sudo().browse(request.session.uid)
            hospital_user = request.env['hospital.user'].sudo().search([('odoo_user_id', '=', user.id)], limit=1)
            
            if hospital_user:
                history = request.env['hospital.login.history'].sudo().create({
                    'user_id': hospital_user.id,
                    'login_time': fields.Datetime.now()
                })
                request.session['hospital_history_id'] = history.id

            # Set user online in presence & manual_im_status
            try:
                now = fields.Datetime.now()
                user.sudo().write({'manual_im_status': 'online'})
                presence = request.env['mail.presence'].sudo().search([('user_id', '=', user.id)], limit=1)
                if presence:
                    presence.sudo().write({'status': 'online', 'last_poll': now, 'last_presence': now})
                else:
                    request.env['mail.presence'].sudo().create({'user_id': user.id, 'status': 'online', 'last_poll': now, 'last_presence': now})
            except Exception:
                pass

            if isinstance(res, dict):
                desig = get_user_hospital_designation(request.env, user)
                res['hospital_user_designation'] = desig
                res['user_designation'] = desig
                
        return res

    @http.route('/web/session/get_session_info', type='jsonrpc', auth='user', readonly=True)
    def get_session_info(self):
        res = super(HospitalSession, self).get_session_info()
        if isinstance(res, dict) and request.session.uid:
            user = request.env['res.users'].sudo().browse(request.session.uid)
            desig = get_user_hospital_designation(request.env, user)
            res['hospital_user_designation'] = desig
            res['user_designation'] = desig
        return res

    @http.route('/hospital/get_my_designation', type='jsonrpc', auth='user', readonly=True)
    def get_my_designation(self):
        if request.session.uid:
            user = request.env['res.users'].sudo().browse(request.session.uid)
            desig = get_user_hospital_designation(request.env, user)
            return {'designation': desig}
        return {'designation': ''}

    @http.route('/web/session/logout', type='http', auth='none', readonly=True)
    def logout(self, redirect='/web/login'):
        if request.session.uid:
            try:
                user = request.env['res.users'].sudo().browse(request.session.uid)
                user.sudo().write({'manual_im_status': 'offline'})
                presence = request.env['mail.presence'].sudo().search([('user_id', '=', user.id)], limit=1)
                if presence:
                    presence.sudo().write({'status': 'offline'})
            except Exception:
                pass

        history_id = request.session.get('hospital_history_id')
        if history_id:
            try:
                history = request.env['hospital.login.history'].sudo().browse(history_id)
                if history.exists():
                    history.sudo().write({'logout_time': fields.Datetime.now()})
            except Exception:
                pass
                
        request.session.logout(keep_db=True)
        request.session.db = 'new_project_db'
        return request.redirect('/web/login?db=new_project_db', 303)


class HospitalImStatusController(ImStatusController):

    @http.route("/mail/set_manual_im_status", methods=["POST"], type="jsonrpc", auth="user")
    def set_manual_im_status(self, status):
        if status not in ["online", "away", "busy", "offline"]:
            raise ValueError(f"Unexpected IM status {status}")
        user = request.env.user
        user.sudo().write({'manual_im_status': status})
        now = fields.Datetime.now()
        presence = request.env['mail.presence'].sudo().search([('user_id', '=', user.id)], limit=1)
        if presence:
            presence.sudo().write({
                'status': status,
                'last_poll': now,
                'last_presence': now,
            })
        else:
            request.env['mail.presence'].sudo().create({
                'user_id': user.id,
                'status': status,
                'last_poll': now,
                'last_presence': now,
            })
        
        user.partner_id.sudo()._compute_im_status()
        user._bus_send(
            "bus.bus/im_status_updated",
            {
                "debounce": False,
                "im_status": status,
                "presence_status": status,
                "partner_id": user.partner_id.id,
            },
            subchannel="presence",
        )
        return {'status': status, 'im_status': status}


class HospitalHome(Home):

    def _login_redirect(self, uid, redirect=None):
        env_sudo = request.env['res.users'].sudo().env
        user = env_sudo['res.users'].browse(uid)

        action = None
        h_user = env_sudo['hospital.user'].search([('odoo_user_id', '=', user.id)], limit=1)
        if h_user and h_user.role_id:
            rname = (h_user.role_id.name or '').strip().lower()
            if rname in ['hr manager', 'hr executive']:
                action = env_sudo.ref('hospital_management.action_hospital_hr_dashboard', raise_if_not_found=False)
            elif rname == 'receptionist':
                action = env_sudo.ref('hospital_management.action_hospital_reception_dashboard', raise_if_not_found=False)
            elif rname == 'doctor':
                action = env_sudo.ref('hospital_management.action_hospital_doctor_dashboard', raise_if_not_found=False)
            elif rname in ['lab technician', 'lab manager']:
                action = env_sudo.ref('hospital_management.action_hospital_lab_dashboard', raise_if_not_found=False)
            elif rname == 'pharmacist':
                action = env_sudo.ref('hospital_management.action_hospital_pharmacy_dashboard_form', raise_if_not_found=False)
            elif rname in ['admin', 'administrator', 'super admin']:
                action = env_sudo.ref('hospital_management.action_hospital_admin_dashboard_window', raise_if_not_found=False)

        # Fallback to user groups if hospital.user record is not configured
        if not action:
            if user.has_group('hospital_management.group_hospital_super_admin') or user.has_group('hospital_management.group_hospital_admin'):
                action = env_sudo.ref('hospital_management.action_hospital_admin_dashboard_window', raise_if_not_found=False)
            elif user.has_group('hospital_management.group_hospital_doctor'):
                action = env_sudo.ref('hospital_management.action_hospital_doctor_dashboard', raise_if_not_found=False)
            elif user.has_group('hospital_management.group_hospital_receptionist'):
                action = env_sudo.ref('hospital_management.action_hospital_reception_dashboard', raise_if_not_found=False)
            elif user.has_group('hospital_management.group_hospital_lab_technician'):
                action = env_sudo.ref('hospital_management.action_hospital_lab_dashboard', raise_if_not_found=False)
            elif user.has_group('hospital_management.group_hospital_pharmacist'):
                action = env_sudo.ref('hospital_management.action_hospital_pharmacy_dashboard_form', raise_if_not_found=False)
            elif user.has_group('hospital_management.group_hospital_hr'):
                action = env_sudo.ref('hospital_management.action_hospital_hr_dashboard', raise_if_not_found=False)

        if not action:
            action = user.action_id
            if action and action._name == 'ir.actions.server':
                action = env_sudo.ref('hospital_management.action_hospital_admin_dashboard_window', raise_if_not_found=False)

        if not action:
            action = env_sudo.ref('hospital_management.action_hospital_admin_dashboard_window', raise_if_not_found=False)

        # Always redirect to role Dashboard on login so users land on Dashboard as their first page
        if action:
            try:
                action_sudo = action.sudo()
                if action_sudo._name in ('ir.actions.act_window', 'ir.actions.client'):
                    if action_sudo.path:
                        return f"/odoo/{action_sudo.path}"
                    return f"/odoo/action-{action_sudo.id}"
            except Exception:
                pass

        return super()._login_redirect(uid, redirect=redirect)

    @http.route()
    def web_client(self, s_action=None, **kw):
        res = super().web_client(s_action=s_action, **kw)
        if hasattr(res, 'qcontext') and res.qcontext and 'session_info' in res.qcontext and request.session.uid:
            user = request.env['res.users'].sudo().browse(request.session.uid)
            desig = get_user_hospital_designation(request.env, user)
            res.qcontext['session_info']['hospital_user_designation'] = desig
            res.qcontext['session_info']['user_designation'] = desig
        return res
