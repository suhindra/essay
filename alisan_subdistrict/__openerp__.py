{
    'name': 'Subdistrict management',
    'version': '1.0',
    'depends': ['base'],
    'author': "Suhindra",
    'maintainer': 'Suhindra',
    'license': "AGPL-3",
    'summary': '''Subdistrict management system''',
    'data': ['views/alisan_subdistrict_view.xml',
             'views/alisan_city_view.xml',
             'views/partner_view.xml',
             'security/ir.model.access.csv'],
    'installable': True,
    'auto_install': False,
}
