from odoo import models, fields, api


class HospitalAdminDashboard(models.Model):
    _name = 'hospital.admin.dashboard'
    _description = 'Hospital Admin Dashboard'

    name = fields.Char(
        string='Dashboard',
        default='Admin Dashboard',
        readonly=True
    )

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

    patient_count = fields.Integer(
        string='Patients',
        compute='_compute_dashboard'
    )

    appointment_count = fields.Integer(
        string='Appointments',
        compute='_compute_dashboard'
    )

    @api.depends()
    def _compute_dashboard(self):
        User = self.env['hospital.user']
        Patient = self.env['hospital.patient']
        Appointment = self.env['hospital.appointment']

        for record in self:
            users = User.search([])

            record.total_users = len(users)

            record.active_users = len(
                users.filtered(lambda u: u.active)
            )

            record.inactive_users = len(
                users.filtered(lambda u: not u.active)
            )

            record.super_admin_count = len(
                users.filtered(
                    lambda u: u.role_id
                    and u.role_id.name == 'Super Admin'
                )
            )

            record.doctor_count = len(
                users.filtered(
                    lambda u: u.role_id
                    and u.role_id.name == 'Doctor'
                )
            )

            record.receptionist_count = len(
                users.filtered(
                    lambda u: u.role_id
                    and u.role_id.name == 'Receptionist'
                )
            )

            record.patient_count = Patient.search_count([])

            record.appointment_count = Appointment.search_count([])