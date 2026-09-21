{
    'name': 'Hospital Management',
    'version': '2.9',
    'category': 'Healthcare',
    'summary': 'Hospital Management System',
    'author': 'Hospital POC',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'web',
    ],

    'assets': {
        'web.assets_backend': [

            'hospital_management/static/src/xml/list_view_override.xml',
            'hospital_management/static/src/css/reception_dashboard.css',
            'hospital_management/static/src/css/admin_dashboard.css',
            'hospital_management/static/src/css/pharmacy_dashboard.css',
            'hospital_management/static/src/css/doctor_dashboard.css',

            'hospital_management/static/src/global_ui_tweaks.js',
            'hospital_management/static/src/js/hospital_user_form.js',
            'hospital_management/static/src/js/hospital_pharmacy_stock_form.js',
            'hospital_management/static/src/js/number_spinner_field.js',
            'hospital_management/static/src/js/number_spinner_field.xml',
            'hospital_management/static/src/hospital_layout/hospital_layout.js',
            'hospital_management/static/src/hospital_layout/hospital_layout.xml',
            'hospital_management/static/src/hospital_layout/user_company_menu.xml',

            'hospital_management/static/src/css/hospital_layout.css',
            'hospital_management/static/src/css/hospital_appointment.css',
            'hospital_management/static/src/css/hospital_lab.css',

            'hospital_management/static/src/pharmacy_dashboard/pharmacy_dashboard.js',
            'hospital_management/static/src/pharmacy_dashboard/pharmacy_dashboard.xml',

            # Appointment list customization
            'hospital_management/static/src/appointment_list/appointment_list.js',
            'hospital_management/static/src/appointment_list/appointment_search_enter.js',
            'hospital_management/static/src/billing_list/billing_list.js',
            'hospital_management/static/src/billing_list/purchase_list.js',
            'hospital_management/static/src/appointment_list/appointment_list.xml',
        'hospital_management/static/src/js/appointment_form.js',
            'hospital_management/static/src/js/lab_form.js',
            'hospital_management/static/src/js/time_picker.js',



        ],

        'web.assets_frontend': [
            'hospital_management/static/src/css/login.css',
            'hospital_management/static/src/js/clear_hash_on_login.js',
        ],

    },

    'data': [
        'security/hospital_security.xml',
        'security/ir.model.access.csv',



        'data/patient/patient_sequence.xml',
        'data/appointment/appointment_sequence.xml',
        'data/pharmacy/pharmacy_bill_sequence.xml',
        'data/pharmacy/pharmacy_purchase_sequence.xml',
        'data/pharmacy/pharmacy_payment_sequence.xml',
        'data/pharmacy/pharmacy_cron.xml',
        'data/hospital_demo_data.xml',
        'data/master_category_data.xml',
        'data/lab/lab_appointment_sequence.xml',
        'data/lab/lab_test_master_data.xml',
        'data/consultation_fee/consultation_fee_data.xml',

        'views/master/hospital_category_master_views.xml',
        'views/consultation_fee/hospital_consultation_fee_views.xml',

        'views/pharmacy/hospital_pharmacy_stock_views.xml',
        'views/pharmacy/hospital_pharmacy_bill_reports.xml',
        'views/pharmacy/hospital_pharmacy_bill_views.xml',
        'views/pharmacy/hospital_pharmacy_purchase_views.xml',
        'views/pharmacy/hospital_pharmacy_payment_views.xml',
        'views/pharmacy/hospital_pharmacy_purchase_invoice_views.xml',
        'views/pharmacy/hospital_pharmacy_purchase_reports.xml',

        'views/patient/hospital_patient_views.xml',
        'wizard/prescribe_wizard_views.xml',
        'views/appointment/hospital_appointment_views.xml',
        'views/appointment/hospital_doctor_views.xml',
        'views/appointment/hospital_appointment_booking_wizard_views.xml',
        'views/appointment/hospital_appointment_reports.xml',
        'views/lab/hospital_lab_reports.xml',
        'views/lab/hospital_lab_views.xml',
        'views/lab/lab_receipt_wizard_views.xml',
        'views/lab/hospital_lab_test_selector_views.xml',


        'views/user/hospital_user_views.xml',
        'views/user/hospital_user_activity_views.xml',

        'views/dashboard/hospital_lab_dashboard_views.xml',
        'views/dashboard/hospital_reception_actions.xml',
        'views/dashboard/hospital_dashboard_views.xml',
        'views/dashboard/hospital_role_dashboards.xml',
        'views/dashboard/hospital_pharmacy_dashboard.xml',
        'views/dashboard/hospital_pharmacy_dashboard_form.xml',
        'views/dashboard/hospital_doctor_dashboard.xml',

        'views/login/hospital_login.xml',
        'views/login/hospital_web_login.xml',
        'views/login/login_page.xml',

        'views/menus/hospital_menu.xml',



    ],

    'installable': True,
    'application': True,
}