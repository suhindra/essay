# -*- coding: utf-8 -*-
{
    'name': "Alisan Fixed Journal Plan ERP",

    'summary': """Digunakan untuk input data FJP Customer per salesperson ERP
        """,

    'description': """
      Digunakan untuk input data FJP Customer per salesperson ERP
    """,

    'author': "Suhindra",
    'website': "http://www.alisancatur.com/",
    'maintainer': "Suhindra",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'version': '9.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale','crm'],
    "installable":True,
    "auto_install":False,
    # always loaded
    'data': [
        
        'views/partner_view.xml',
        'views/cust_route_view.xml',
        'views/menu.xml',
    ],
}
