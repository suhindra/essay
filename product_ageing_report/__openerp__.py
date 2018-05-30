{
    'name': "Stock Ageing Analysis",
    'version': '9.0.1.0.0',
    'summary': """Product Ageing Analysis With Filterations""",
    'description': """With this module, we can perform stock ageing analysis with optional filters such
                as location, category, etc.""",
    'author': "Suhindra",
    'maintainer': 'Suhindra',
    'category': 'Stock',
    'depends': ['product', 'stock', 'report_xlsx'],
    'data': [
             'security/ir.model.access.csv',
             'wizard/product_ageing.xml',
             'report/report_ageing_products.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
