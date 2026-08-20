{
    'name': 'Hospital Management',
    'version': '19.0.1.0.0',
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
            'hospital_management/static/src/hospital_layout/hospital_layout.js',
            'hospital_management/static/src/hospital_layout/hospital_layout.xml',
            'hospital_management/static/src/css/hospital_layout.css',
        ],

        'web.assets_frontend': [
            'hospital_management/static/src/css/login.css',
        ],

    },

    'data': [
        'security/hospital_security.xml',
        'security/ir.model.access.csv',

        
        'data/patient/patient_sequence.xml',
        'data/appointment/appointment_sequence.xml',
        'data/hospital_demo_data.xml',
        'data/lab/lab_appointment_sequence.xml',
        'data/lab/lab_test_master_data.xml',

       
        'views/patient/hospital_patient_views.xml',
        'views/appointment/hospital_appointment_views.xml',
        'views/lab/hospital_lab_views.xml',

        'views/user/hospital_user_views.xml',
        'views/user/hospital_user_activity_views.xml',
        
        'views/dashboard/hospital_role_dashboards.xml',
        
        'views/login/hospital_login.xml',
        'views/login/login_page.xml',

        'views/menus/hospital_menu.xml',
        

        
    ],

    'installable': True,
    'application': True,
}