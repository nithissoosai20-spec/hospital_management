from odoo import models, fields, api


class HospitalReceptionDashboard(models.Model):
    _name = 'hospital.reception.dashboard'
    _description = 'Hospital Reception Dashboard'

    name = fields.Char(
        string='Dashboard',
        default='Reception Dashboard',
        readonly=True
    )

    # =========================
    # SUMMARY
    # =========================

    total_patients = fields.Integer(
        string='Total Patients',
        compute='_compute_dashboard'
    )

    total_appointments = fields.Integer(
        string='Total Appointments',
        compute='_compute_dashboard'
    )

    today_appointments = fields.Integer(
        string="Today's Appointments",
        compute='_compute_dashboard'
    )

    booked_appointments = fields.Integer(
        string='Booked Appointments',
        compute='_compute_dashboard'
    )

    completed_appointments = fields.Integer(
        string='Completed Appointments',
        compute='_compute_dashboard'
    )

    pending_payments = fields.Integer(
        string='Pending Payments',
        compute='_compute_dashboard'
    )


    # =========================
    # EXTRA INFORMATION
    # =========================

    available_doctors = fields.Integer(
        string='Available Doctors',
        compute='_compute_dashboard'
    )

    inactive_doctors = fields.Integer(
        string='Inactive Doctors',
        compute='_compute_dashboard'
    )

    waiting_patients = fields.Integer(
        string='Waiting Appointments',
        compute='_compute_dashboard'
    )

    cancelled_appointments = fields.Integer(
        string='Cancelled Appointments',
        compute='_compute_dashboard'
    )

    @api.depends()
    def _compute_dashboard(self):

        Patient = self.env['hospital.patient']
        Appointment = self.env['hospital.appointment']
        HospitalUser = self.env['hospital.user']

        today = fields.Date.today()

        for record in self:

            #total appointments

            record.total_appointments = Appointment.search_count([])
            # -------------------------
            # PATIENTS
            # -------------------------

            record.total_patients = Patient.search_count([
                ('active', '=', True)
            ])

            # -------------------------
            # TODAY'S APPOINTMENTS
            # -------------------------

            today_appointments = Appointment.search([
                ('appointment_date', '=', today)
            ])

            record.today_appointments = len(today_appointments)

            # -------------------------
            # BOOKED
            # -------------------------

            record.booked_appointments = Appointment.search_count([
                ('state', '=', 'booked')
            ])

            # -------------------------
            # COMPLETED
            # -------------------------

            record.completed_appointments = Appointment.search_count([
                ('state', '=', 'completed')
            ])

            # -------------------------
            # PENDING PAYMENTS
            # -------------------------

            record.pending_payments = Appointment.search_count([
                ('payment_status', 'in', ['pending', 'partial'])
            ])

            # -------------------------
            # WAITING
            #
            # There is no separate
            # "waiting" state in your
            # appointment model.
            #
            # Draft appointments are
            # treated as waiting.
            # -------------------------

            record.waiting_patients = Appointment.search_count([
                ('state', '=', 'draft')
            ])

            # -------------------------
            # CANCELLED
            # -------------------------

            record.cancelled_appointments = Appointment.search_count([
                ('state', '=', 'cancelled')
            ])

            # -------------------------
            # DOCTORS
            #
            # hospital.user records
            # whose role is Doctor
            # -------------------------

            record.available_doctors = HospitalUser.search_count([
                ('role_id.name', '=', 'Doctor'),
                ('odoo_user_id.active', '=', True)
            ])

            record.inactive_doctors = HospitalUser.search_count([
                ('role_id.name', '=', 'Doctor'),
                ('odoo_user_id.active', '=', False)
            ])