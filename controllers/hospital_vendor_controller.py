from odoo import http
from odoo.http import request
import json


class HospitalVendorController(http.Controller):
    """Allows pharmacy staff (without Contact/Creation rights) to create pharmacy vendors."""

    @http.route('/hospital/create_vendor', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def create_vendor(self, name, phone=None, email=None, vat=None, street=None, **kwargs):
        if not name or not name.strip():
            return {'success': False, 'error': 'Vendor name is required.'}

        vals = {
            'name': name.strip(),
            'is_pharmacy_vendor': True,
        }
        if phone:
            vals['phone'] = phone.strip()
        if email:
            vals['email'] = email.strip()
        if vat:
            vals['vat'] = vat.strip()
        if street:
            vals['street'] = street.strip()

        try:
            # Use sudo() so pharmacy users without Contact/Creation rights can still create vendors
            partner = request.env['res.partner'].sudo().create(vals)
            return {'success': True, 'id': partner.id, 'name': partner.name}
        except Exception as e:
            return {'success': False, 'error': str(e)}

