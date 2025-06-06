{
    'name': 'Custom DATEV Export',
    'version': '1.0.4',
    'depends': ['base', 'account'],
    'external_dependencies': {
        'python': ['dateutil'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/export_wizard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}