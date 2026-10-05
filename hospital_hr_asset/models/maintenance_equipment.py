from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

class HospitalAssetServiceLog(models.Model):
    _name = 'hospital.asset.service.log'
    _description = 'Asset Service Log'

    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment', required=True, ondelete='cascade')
    date = fields.Date(string='Service Date', default=fields.Date.context_today)
    issue = fields.Char(string='Issue / Fixed', required=True)
    amount_paid = fields.Float(string='Amount Paid')



class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    # Un-compute owner_user_id from hr_maintenance to make it fully writable manually
    owner_user_id = fields.Many2one('res.users', string='Owner', compute='_compute_owner_user_id_override', inverse='_inverse_owner_user_id', store=True, readonly=False)

    def _compute_owner_user_id_override(self):
        pass

    def _inverse_owner_user_id(self):
        pass



    _inherit = 'maintenance.equipment'

    # 1. Product Specs
    specs = fields.Text(string='Specifications')
    make = fields.Char(string='Make / Manufacturer')

    # 2. Purchase & Vendor
    purchase_date = fields.Date(string='Date of Purchase')
    discount = fields.Float(string='Discount (%)')
    vendor_gst = fields.Char(string='Vendor GST', related='partner_id.vat', readonly=True)

    # 3. Warranty & Service
    guaranty_details = fields.Text(string='Guaranty Details')
    service_type = fields.Selection([
        ('free', 'Free Service'),
        ('paid', 'Paid Service')
    ], string='Service Version', default='free')
    service_contact = fields.Char(string='Service Contact Number')
    service_log_ids = fields.One2many('hospital.asset.service.log', 'equipment_id', string='Service Logs')

    # 4. Lifecycle & Age
    installed_date = fields.Date(string='Installed Date')
    expected_lifetime_years = fields.Integer(string='Expected Lifetime (Years)', default=5)
    age_years = fields.Float(string='Age (Years)', compute='_compute_age_years', store=True)
    
    
    allocation_log_ids = fields.One2many('hospital.asset.allocation.log', 'equipment_id', string='Allocation Logs')

    @api.model_create_multi
    def create(self, vals_list):
        records = super(MaintenanceEquipment, self).create(vals_list)
        for record in records:
            if record.owner_user_id:
                self.env['hospital.asset.allocation.log'].create({
                    'equipment_id': record.id,
                    'user_id': record.owner_user_id.id,
                    'status': 'active'
                })
        return records

    def write(self, vals):
        for record in self:
            if 'owner_user_id' in vals:
                old_user = record.owner_user_id
                new_user_id = vals.get('owner_user_id')
                if new_user_id != (old_user.id if old_user else False):
                    # Close existing active allocation
                    active_logs = self.env['hospital.asset.allocation.log'].search([
                        ('equipment_id', '=', record.id),
                        ('status', '=', 'active')
                    ])
                    active_logs.write({
                        'status': 'returned',
                        'date_returned': fields.Datetime.now()
                    })
                    
                    # Open new allocation
                    if new_user_id:
                        self.env['hospital.asset.allocation.log'].create({
                            'equipment_id': record.id,
                            'user_id': new_user_id,
                            'status': 'active'
                        })
            
            # Phase 4 Link: If marked for scrap, auto-create draft scrap order
            if vals.get('asset_status') == 'scrap' and record.asset_status != 'scrap':
                self.env['hospital.asset.scrap'].create({
                    'equipment_id': record.id,
                    'reason': 'Auto-generated Draft: Asset tagged as Scrap for Resale / Lifetime Expired',
                    'state': 'draft'
                })

        return super(MaintenanceEquipment, self).write(vals)

    
    def action_custom_save(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Equipments',
            'res_model': 'maintenance.equipment',
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_custom_cancel(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Equipments',
            'res_model': 'maintenance.equipment',
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_custom_clear(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Equipment',
            'res_model': 'maintenance.equipment',
            'view_mode': 'form',
            'target': 'current',
        }

    asset_status = fields.Selection([
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('scrap', 'Scrap for Resale')
    ], string='Asset Status', default='active', tracking=True)

    @api.depends('installed_date')
    def _compute_age_years(self):
        for record in self:
            if record.installed_date:
                delta = relativedelta(fields.Date.today(), record.installed_date)
                record.age_years = delta.years + (delta.months / 12.0)
            else:
                record.age_years = 0.0

    @api.model
    def _cron_auto_scrap_assets(self):
        assets = self.search([('asset_status', '=', 'active'), ('installed_date', '!=', False)])
        for asset in assets:
            delta = relativedelta(fields.Date.today(), asset.installed_date)
            exact_years = delta.years + (delta.months / 12.0) + (delta.days / 365.25)
            if exact_years >= asset.expected_lifetime_years:
                asset.write({
                    'asset_status': 'scrap',
                    'scrap_date': fields.Date.today()
                })
