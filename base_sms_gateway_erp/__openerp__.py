{
    'name': 'SMS Gateway management',
    'version': '1.0',
    'depends': ['base', 'base_action_rule', 'sale','alisan_shipmentbarcode'],
    'author': "Suhindra",
    'maintainer': 'Suhindra',
    'license': "AGPL-3",
    'summary': '''SMS Gateway management system''',
    'data': [
                'views/sms_gateway_setup_view.xml',
                'views/sms_gateway_log_view.xml',
                'views/customer_mobile_tree_view.xml',
                'views/sms_blast_view.xml',
            ],
    'installable': True,
    'auto_install': False,
}
