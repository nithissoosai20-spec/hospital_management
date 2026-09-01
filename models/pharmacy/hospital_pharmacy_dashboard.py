from odoo import models, fields, api


class HospitalPharmacyDashboard(models.Model):
    _name = 'hospital.pharmacy.dashboard'
    _description = 'Hospital Pharmacy Dashboard'

    name = fields.Char(
        string='Dashboard',
        default='Pharmacy Dashboard',
        readonly=True
    )

    total_medicines = fields.Integer(
        string='Total Medicines',
        compute='_compute_dashboard'
    )

    low_stock = fields.Integer(
        string='Low Stock',
        compute='_compute_dashboard'
    )

    out_of_stock = fields.Integer(
        string='Out of Stock',
        compute='_compute_dashboard'
    )

    today_bills = fields.Integer(
        string="Today's Bills",
        compute='_compute_dashboard'
    )

    today_revenue = fields.Float(
        string="Today's Revenue",
        compute='_compute_dashboard'
    )

    pending_bills = fields.Integer(
        string='Pending Bills',
        compute='_compute_dashboard'
    )

    @api.depends()
    def _compute_dashboard(self):
        Stock = self.env['hospital.pharmacy.stock']
        Bill = self.env['hospital.pharmacy.bill']
        today = fields.Date.today()

        for record in self:
            all_stock = Stock.search([])
            record.total_medicines = len(all_stock)
            record.low_stock = len(
                all_stock.filtered(lambda s: s.stock_status in ('low', 'critical'))
            )
            record.out_of_stock = len(
                all_stock.filtered(lambda s: s.stock_status == 'out')
            )

            today_bills = Bill.search([
                ('create_date', '>=', fields.Datetime.to_datetime(today)),
            ])
            record.today_bills = len(today_bills)
            record.today_revenue = sum(
                b.total_amount for b in today_bills if b.state == 'paid'
            )
            record.pending_bills = Bill.search_count([('state', '=', 'draft')])

    def action_view_total_medicines(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Total Medicines',
            'res_model': 'hospital.pharmacy.stock',
            'view_mode': 'list,form',
            'domain': [],
        }

    def action_view_low_stock(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Low Stock Medicines',
            'res_model': 'hospital.pharmacy.stock',
            'view_mode': 'list,form',
            'domain': [('quantity', '<=', 50), ('quantity', '>', 0)],
        }

    def action_view_out_of_stock(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Out of Stock Medicines',
            'res_model': 'hospital.pharmacy.stock',
            'view_mode': 'list,form',
            'domain': [('quantity', '<=', 0)],
        }

    def action_view_today_bills(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Today Bills',
            'res_model': 'hospital.pharmacy.bill',
            'view_mode': 'list,form',
            'domain': [('create_date', '>=', fields.Date.context_today(self))],
        }

    def action_view_today_revenue(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Today Revenue',
            'res_model': 'hospital.pharmacy.bill',
            'view_mode': 'list,form',
            'domain': [('create_date', '>=', fields.Date.context_today(self)), ('state', '=', 'paid')],
        }

    def action_view_pending_bills(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pending Bills',
            'res_model': 'hospital.pharmacy.bill',
            'view_mode': 'list,form',
            'domain': [('state', '=', 'draft')],
        }
