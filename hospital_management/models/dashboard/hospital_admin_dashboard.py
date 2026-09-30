from odoo import models, fields, api
from datetime import timedelta


class HospitalAdminDashboard(models.Model):
    _name = 'hospital.admin.dashboard'
    _description = 'Hospital Admin Dashboard'


    date_filter = fields.Selection([
        ('today', 'Today'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('q1', 'Quarter-1'),
        ('q2', 'Quarter-2'),
        ('q3', 'Quarter-3'),
        ('q4', 'Quarter-4'),
        ('year', 'Yearly'),
    ], string='Filter', default='today')

    name = fields.Char(
        string='Dashboard',
        default='Admin Dashboard',
        readonly=True
    )

    # USER SUMMARY

    total_users = fields.Integer(
        string='Total Users',
        compute='_compute_dashboard'
    )

    active_users = fields.Integer(
        string='Active Users',
        compute='_compute_dashboard'
    )

    inactive_users = fields.Integer(
        string='Inactive Users',
        compute='_compute_dashboard'
    )

    super_admin_count = fields.Integer(
        string='Super Admins',
        compute='_compute_dashboard'
    )

    doctor_count = fields.Integer(
        string='Doctors',
        compute='_compute_dashboard'
    )

    receptionist_count = fields.Integer(
        string='Receptionists',
        compute='_compute_dashboard'
    )

    # PATIENT / APPOINTMENT SUMMARY

    patient_count = fields.Integer(
        string='Total Patients',
        compute='_compute_dashboard'
    )

    appointment_count = fields.Integer(
        string='Total Appointments',
        compute='_compute_dashboard'
    )

    today_patients = fields.Integer(
        string="Today's Patients",
        compute='_compute_dashboard'
    )

    total_patients = fields.Integer(
        string='Total Patients Till Now',
        compute='_compute_dashboard'
    )

    today_token_patients = fields.Integer(
        string="Today's Token Patients",
        compute='_compute_dashboard'
    )

    today_appointments = fields.Integer(
        string="Today's Appointments",
        compute='_compute_dashboard'
    )

    today_lab_tests = fields.Integer(
        string="Today's Lab Tests",
        compute='_compute_dashboard'
    )

    # REVENUE

    consultation_revenue = fields.Float(
        string='Consultation Revenue',
        compute='_compute_dashboard'
    )

    lab_revenue = fields.Float(
        string='Lab Revenue',
        compute='_compute_dashboard'
    )

    pharmacy_collection = fields.Float(string='Pharmacy Collection', compute='_compute_dashboard')
    stock_total = fields.Integer(string='Total Medicines', compute='_compute_dashboard')
    stock_low = fields.Integer(string='Low Stock', compute='_compute_dashboard')
    stock_out = fields.Integer(string='Out of Stock', compute='_compute_dashboard')
    stock_expired = fields.Integer(string='Expired Stock', compute='_compute_dashboard')

    total_revenue = fields.Float(
        string='Total Revenue',
        compute='_compute_dashboard'
    )



    # PHARMACY PAYMENTS
    pharmacy_pending_payments = fields.Float(string='Pending Payments', compute='_compute_dashboard')
    pharmacy_paid_payments = fields.Float(string='Paid Payments', compute='_compute_dashboard')
    pharmacy_upcoming_payments = fields.Float(string='Upcoming Payments', compute='_compute_dashboard')


    @api.onchange('date_filter')
    def _onchange_date_filter(self):
        self._compute_dashboard()


    def action_filter_today(self):
        self.sudo().date_filter = 'today'
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_filter_weekly(self):
        self.sudo().date_filter = 'weekly'
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_filter_monthly(self):
        self.sudo().date_filter = 'monthly'
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_filter_q1(self):
        self.sudo().date_filter = 'q1'
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_filter_q2(self):
        self.sudo().date_filter = 'q2'
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_filter_q3(self):
        self.sudo().date_filter = 'q3'
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_filter_q4(self):
        self.sudo().date_filter = 'q4'
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_filter_year(self):
        self.sudo().date_filter = 'year'
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    # COMPUTE

    @api.depends('date_filter')
    def _compute_dashboard(self):

        User = self.env['hospital.user']
        Patient = self.env['hospital.patient'].sudo()
        Appointment = self.env['hospital.appointment'].sudo()
        LabAppointment = self.env['hospital.lab.appointment'].sudo()

        for record in self:
            today = fields.Date.context_today(record)
            if record.date_filter == 'today':
                start_date = today
                end_date = today + timedelta(days=1)
            elif record.date_filter == 'weekly':
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=7)
            elif record.date_filter == 'monthly':
                start_date = today.replace(day=1)
                next_month = today.replace(day=28) + timedelta(days=4)
                end_date = next_month - timedelta(days=next_month.day - 1)
            elif record.date_filter == 'q1':
                start_date = today.replace(month=1, day=1)
                end_date = today.replace(month=4, day=1)
            elif record.date_filter == 'q2':
                start_date = today.replace(month=4, day=1)
                end_date = today.replace(month=7, day=1)
            elif record.date_filter == 'q3':
                start_date = today.replace(month=7, day=1)
                end_date = today.replace(month=10, day=1)
            elif record.date_filter == 'q4':
                start_date = today.replace(month=10, day=1)
                end_date = today.replace(year=today.year + 1, month=1, day=1)
            elif record.date_filter == 'year':
                start_date = today.replace(month=1, day=1)
                end_date = today.replace(year=today.year + 1, month=1, day=1)
            else:
                start_date = today
                end_date = today + timedelta(days=1)


            # USERS

            users = User.search([])

            record.total_users = len(users)

            record.active_users = len(
                users.filtered(
                    lambda user: user.active
                )
            )

            record.inactive_users = len(
                users.filtered(
                    lambda user: not user.active
                )
            )

            record.super_admin_count = len(
                users.filtered(
                    lambda user:
                    user.role_id
                    and user.role_id.name == 'Super Admin'
                )
            )

            record.doctor_count = len(
                users.filtered(
                    lambda user:
                    user.role_id
                    and user.role_id.name == 'Doctor'
                )
            )

            record.receptionist_count = len(
                users.filtered(
                    lambda user:
                    user.role_id
                    and user.role_id.name == 'Receptionist'
                )
            )

            # TOTAL PATIENTS

            record.patient_count = Patient.search_count([])

            record.total_patients = Patient.search_count([])

            # TODAY PATIENTS

            record.today_patients = Patient.search_count([
                ('create_date', '>=', start_date),
                ('create_date', '<', end_date),
            ])

            # TOTAL APPOINTMENTS

            record.appointment_count = Appointment.search_count([])

            # TODAY APPOINTMENTS

            record.today_appointments = Appointment.search_count([
                ('appointment_date', '>=', start_date),
                ('appointment_date', '<', end_date),
            ])

            # TODAY TOKEN PATIENTS

            record.today_token_patients = Appointment.search_count([
                ('appointment_date', '>=', start_date),
                ('appointment_date', '<', end_date),
                ('token_generated', '=', True),
            ])

            # TODAY LAB TESTS

            today_lab_appointments = LabAppointment.search([
                ('appointment_date', '>=', start_date),
                ('appointment_date', '<', end_date),
            ])

            record.today_lab_tests = sum(
                len(lab.line_ids)
                for lab in today_lab_appointments
            )

            # CONSULTATION REVENUE
            #
            # Paid consultation appointments only.

            paid_appointments = Appointment.search([
                ('payment_status', '=', 'paid'),
                ('appointment_date', '>=', start_date),
                ('appointment_date', '<', end_date),
            ])

            consultation_total = 0.0

            for appointment in paid_appointments:

                consultation_total += (
                    appointment.net_amount or 0.0
                )

            record.consultation_revenue = consultation_total
            # LAB REVENUE
            #
            # Paid lab appointments only.

            paid_lab_appointments = LabAppointment.search([
                ('payment_status', '=', 'paid'),
                ('appointment_date', '>=', start_date),
                ('appointment_date', '<', end_date),
            ])

            lab_total = 0.0

            for lab in paid_lab_appointments:

                lab_total += lab.amount or 0.0

            record.lab_revenue = lab_total

            # PHARMACY COLLECTION (Billing)
            pharmacy_bills = self.env['hospital.pharmacy.bill'].sudo().search([
                ('state', '=', 'paid'),
                ('bill_date', '>=', start_date),
                ('bill_date', '<', end_date),
            ])
            record.pharmacy_collection = sum(bill.total_amount for bill in pharmacy_bills)

            # UPDATE TOTAL REVENUE
            record.total_revenue = consultation_total + lab_total + record.pharmacy_collection

            # STOCK SUMMARY
            Stock = self.env['hospital.pharmacy.stock'].sudo()
            record.stock_total = Stock.search_count([])
            record.stock_low = Stock.search_count([('stock_status', '=', 'low')])
            record.stock_out = Stock.search_count([('stock_status', '=', 'out')])
            record.stock_expired = Stock.search_count([('stock_status', '=', 'expired')])


            # PHARMACY PAYMENTS
            record.pharmacy_upcoming_payments = 0.0
            PurchaseInvoice = self.env['hospital.pharmacy.purchase.invoice'].sudo()
            invoices = PurchaseInvoice.search([
                ('invoice_date', '>=', start_date),
                ('invoice_date', '<', end_date),
            ])

            pending = 0.0
            paid = 0.0

            for inv in invoices:
                # Invoice payments show as pending (what is owed)
                pending += inv.balance_amount or 0.0
                # Payment success amount show as paid
                paid += inv.paid_amount or 0.0

            record.pharmacy_pending_payments = pending
            record.pharmacy_paid_payments = paid


    def action_create_user(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create User',
            'res_model': 'hospital.user',
            'view_mode': 'form',
            'target': 'current',
        }