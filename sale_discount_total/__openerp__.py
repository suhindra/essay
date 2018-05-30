{
    'name': 'Sale Discount',
    'version': '1.0',
    'category': 'Sales Management',
    'author': 'Suhindra',

    'description': """
manage discount on total amount in Sale.
        as an specific amount or percentage
""",
    'depends': ['sale',
                'account',
                'purchase'
                ],
    'data': [
        'views/sale_view.xml',
        'views/purchase_view.xml',
        'views/account_invoice_view.xml',
        'views/invoice_report.xml',
        'views/sale_order_report.xml',
        'views/discount_setting.xml',
        'views/product_view.xml',

    ],
    'demo': [
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
