from odoo import models, fields, api


class HospitalAdminDashboard(models.Model):
    _name = 'hospital.admin.dashboard'
    _description = 'Hospital Admin Dashboard'

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

    total_revenue = fields.Float(
        string='Total Revenue',
        compute='_compute_dashboard'
    )


    # COMPUTE

    @api.depends()
    def _compute_dashboard(self):

        User = self.env['hospital.user']
        Patient = self.env['hospital.patient']
        Appointment = self.env['hospital.appointment']
        LabAppointment = self.env['hospital.lab.appointment']

        today = fields.Date.today()

        tomorrow = fields.Date.add(
            today,
            days=1
        )

        for record in self:

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
                ('create_date', '>=', today),
                ('create_date', '<', tomorrow),
            ])

            # TOTAL APPOINTMENTS

            record.appointment_count = Appointment.search_count([])

            # TODAY APPOINTMENTS

            record.today_appointments = Appointment.search_count([
                ('appointment_date', '=', today),
            ])

            # TODAY TOKEN PATIENTS

            record.today_token_patients = Appointment.search_count([
                ('appointment_date', '=', today),
                ('token_generated', '=', True),
            ])

            # TODAY LAB TESTS

            today_lab_appointments = LabAppointment.search([
                ('appointment_date', '=', today),
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
            ])

            lab_total = 0.0

            for lab in paid_lab_appointments:

                lab_total += lab.amount or 0.0

            record.lab_revenue = lab_total
            record.total_revenue = consultation_total + lab_total