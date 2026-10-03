{
    'name': 'Hospital HR & Asset Management',
    'version': '19.0.1.0.0',
    'category': 'Healthcare',
    'summary': 'Hospital-specific HR and Asset Management customizations',
    'depends': [
        'hospital_management',
        'hr',
        'maintenance',
    ],
    'data': [
        'security/security.xml',
        'views/hospital_hr_menu.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
