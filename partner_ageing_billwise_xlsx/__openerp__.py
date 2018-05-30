{
    'name': 'Aged Partner Balance Excel',
    'version': '9.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Aged Partner Balance in Excel Format',
    'description': """
    This module provides an excel report of aged partner balance.
    """,
    'author': 'Suhindra',
    'maintainer': 'Suhindra',
    'depends': ['report_xlsx', 'account_accountant'],
    'data': [
             'views/report_aged_partner_billwise.xml',
            ],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
