from odoo import models, fields, api


class HospitalDoctorDashboard(models.Model):
    _name = 'hospital.doctor.dashboard'
    _description = 'Hospital Doctor Dashboard'

    name = fields.Char(
        string='Dashboard',
        default='Doctor Dashboard',
        readonly=True
    )

    my_appointments = fields.Integer(
        string='My Appointments',
        compute='_compute_dashboard'
    )

    today_appointments = fields.Integer(
        string="Today's Appointments",
        compute='_compute_dashboard'
    )

    completed_appointments = fields.Integer(
        string='Completed',
        compute='_compute_dashboard'
    )

    pending_appointments = fields.Integer(
        string='Pending',
        compute='_compute_dashboard'
    )

    my_patients = fields.Integer(
        string='My Patients',
        compute='_compute_dashboard'
    )

    @api.depends()
    def _compute_dashboard(self):
        Appointment = self.env['hospital.appointment']

        hospital_user = self.env['hospital.user'].search(
            [('odoo_user_id', '=', self.env.user.id)],
            limit=1
        )

        for record in self:
            if not hospital_user:
                record.my_appointments = 0
                record.today_appointments = 0
                record.completed_appointments = 0
                record.pending_appointments = 0
                record.my_patients = 0
                continue

            appointments = Appointment.search([
                ('doctor_id', '=', hospital_user.id)
            ])

            today = fields.Date.today()

            record.my_appointments = len(appointments)

            record.today_appointments = len(
                appointments.filtered(
                    lambda a: a.appointment_date == today
                )
            )

            record.completed_appointments = len(
                appointments.filtered(
                    lambda a: a.state == 'completed'
                )
            )

            record.pending_appointments = len(
                appointments.filtered(
                    lambda a: a.state in ('draft', 'booked')
                )
            )

            record.my_patients = len(
                appointments.mapped('patient_id')
            )