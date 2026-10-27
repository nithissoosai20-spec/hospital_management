from odoo import models, fields, api


class HospitalReceptionDashboard(models.Model):
    _name = 'hospital.reception.dashboard'
    _inherit = ['hospital.staff.self.service.mixin']
    _description = 'Hospital Reception Dashboard'

    name = fields.Char(
        string='Dashboard',
        default='Reception Dashboard',
        readonly=True
    )

    # SUMMARY

    total_patients = fields.Integer(
        string='Total Patients',
        compute='_compute_dashboard'
    )

    total_appointments = fields.Integer(
        string='Total Appointments',
        compute='_compute_dashboard'
    )

    today_patients = fields.Integer(
        string="Today's Patients",
        compute='_compute_dashboard'
    )

    today_appointments = fields.Integer(
        string="Today's Appointments",
        compute='_compute_dashboard'
    )

    today_token_patients = fields.Integer(
        string="Today's Token Patients",
        compute='_compute_dashboard'
    )

    today_lab_tests = fields.Integer(
        string="Today's Lab Tests",
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

    # EXTRA INFORMATION

    available_doctors = fields.Integer(
        string='Available Doctors',
        compute='_compute_dashboard'
    )

    inactive_doctors = fields.Integer(
        string='Inactive Doctors',
        compute='_compute_dashboard'
    )

    doctor_status_ids = fields.Many2many(
        'hospital.user',
        compute='_compute_dashboard',
        string='Doctors'
    )


    waiting_patients = fields.Integer(
        string='Waiting Appointments',
        compute='_compute_dashboard'
    )

    cancelled_appointments = fields.Integer(
        string='Cancelled Appointments',
        compute='_compute_dashboard'
    )

    # DASHBOARD COMPUTATION

    @api.depends()
    def _compute_dashboard(self):

        Patient = self.env['hospital.patient']
        Appointment = self.env['hospital.appointment']
        HospitalUser = self.env['hospital.user']
        LabAppointment = self.env['hospital.lab.appointment']

        today = fields.Date.today()
        tomorrow = fields.Date.add(today, days=1)

        for record in self:

            # TOTAL PATIENTS TILL NOW

            record.total_patients = Patient.search_count([
                ('active', '=', True)
            ])

            # TODAY PATIENTS
            #
            # Patients registered/created today

            record.today_patients = Patient.search_count([
                ('create_date', '>=', today),
                ('create_date', '<', tomorrow),
            ])

            # TODAY APPOINTMENTS

            today_appointments = Appointment.search([
                ('appointment_date', '=', today)
            ])

            record.today_appointments = len(
                today_appointments
            )

            # TOTAL APPOINTMENTS

            record.total_appointments = Appointment.search_count([])

            # TODAY TOKEN PATIENTS
            #
            # Today's appointments that have a token

            record.today_token_patients = Appointment.search_count([
                ('appointment_date', '=', today),
                ('token_generated', '=', True),
            ])

            # TODAY LAB TESTS
            #
            # Count individual lab tests selected today,
            # not just the number of lab appointments.

            today_lab_appointments = LabAppointment.search([
                ('appointment_date', '=', today),
            ])

            record.today_lab_tests = sum(
                len(lab.line_ids)
                for lab in today_lab_appointments
            )

            # BOOKED APPOINTMENTS

            record.booked_appointments = Appointment.search_count([
                ('state', '=', 'booked')
            ])

            # COMPLETED APPOINTMENTS

            record.completed_appointments = Appointment.search_count([
                ('state', '=', 'completed')
            ])

            # PENDING PAYMENTS

            record.pending_payments = Appointment.search_count([
                ('payment_status', 'in', ['pending', 'partial'])
            ])

            # WAITING PATIENTS
            #
            # Your appointment model does not have a separate
            # waiting state, so draft appointments are treated
            # as waiting.

            record.waiting_patients = Appointment.search_count([
                ('state', '=', 'draft')
            ])

            # CANCELLED APPOINTMENTS

            record.cancelled_appointments = Appointment.search_count([
                ('state', '=', 'cancelled')
            ])

            # AVAILABLE DOCTORS
            #
            # hospital.user records whose role is Doctor
            # and whose linked Odoo user is active.

            record.available_doctors = HospitalUser.search_count([
                ('role_id.name', '=', 'Doctor'),
                ('odoo_user_id.active', '=', True)
            ])

            # INACTIVE DOCTORS

            record.inactive_doctors = HospitalUser.search_count([
                ('role_id.name', '=', 'Doctor'),
                ('odoo_user_id.active', '=', False)
            ])

            # DOCTOR LIST
            record.doctor_status_ids = HospitalUser.search([
                ('role_id.name', '=', 'Doctor')
            ]).ids