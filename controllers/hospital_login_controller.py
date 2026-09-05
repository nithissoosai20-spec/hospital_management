from odoo import http, fields
from odoo.http import request
from odoo.addons.web.controllers.session import Session

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
                
        return res

    @http.route('/web/session/logout', type='http', auth='none', readonly=True)
    def logout(self, redirect='/odoo'):
        history_id = request.session.get('hospital_history_id')
        if history_id:
            try:
                history = request.env['hospital.login.history'].sudo().browse(history_id)
                if history.exists():
                    history.sudo().write({'logout_time': fields.Datetime.now()})
            except Exception:
                pass
                
        return super(HospitalSession, self).logout(redirect=redirect)
