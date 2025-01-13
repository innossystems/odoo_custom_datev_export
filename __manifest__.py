
{
    'name': 'Datev Export',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'CSV Export für Datev',
    'author': 'Innos Systems',
    'depends': ['account'],
    'data': [
        'views/export_wizard_view.xml',
        'views/account_move_view.xml',
    ],
    'installable': True,
    'application': False,
}