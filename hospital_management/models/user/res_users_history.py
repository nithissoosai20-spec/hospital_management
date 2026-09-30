from odoo import models, api, fields
from odoo.http import request

class ResUsers(models.Model):
    _inherit = 'res.users'

    def _update_last_login(self):
        res = super(ResUsers, self)._update_last_login()
        for user in self:
            try:
                if request and hasattr(request, 'session'):
                    hospital_user = self.env['hospital.user'].sudo().search([('odoo_user_id', '=', user.id)], limit=1)
                    if hospital_user:
                        history = self.env['hospital.login.history'].sudo().create({
                            'user_id': hospital_user.id,
                            'login_time': fields.Datetime.now()
                        })
                        request.session['hospital_history_id'] = history.id
            except Exception as e:
                pass
        return res
