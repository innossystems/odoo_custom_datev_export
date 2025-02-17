
{
    'name': 'Datev Export',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'CSV Export für Datev',
    'license': 'LGPL-3',
    'author': 'Innos Systems',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/export_wizard_view.xml',
        'views/account_move_view.xml',
    ],
    'installable': True,
    'application': False,
}