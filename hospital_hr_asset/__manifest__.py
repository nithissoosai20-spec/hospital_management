{
    'name': 'Hospital HR & Asset Management',
    'version': '19.0.1.0.0',
    'category': 'Healthcare',
    'summary': 'Hospital-specific HR and Asset Management customizations',
    'author': 'Sathya Technologies',
    'depends': [
        'hospital_management',
        'hr',
        'mail',
        'maintenance',
    ],
    'data': [
        'security/security.xml',
        'data/cron_scrap_assets.xml',
        'data/sequence.xml',
        'security/ir.model.access.csv',
        'views/maintenance_equipment_views.xml',
        'views/hospital_asset_request_views.xml',
        'views/hospital_asset_replacement_views.xml',
        'views/asset_inventory_views.xml',
        'views/hospital_hr_menu.xml',
        'views/asset_scrap_views.xml',
        'views/asset_invoice_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'hospital_hr_asset/static/src/js/hospital_asset_item_form.js',
        ],
    },
}
