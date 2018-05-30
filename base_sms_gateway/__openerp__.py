{
    'name': 'SMS Gateway management',
    'version': '1.0',
    'depends': ['base', 'base_action_rule', 'base_voucher', 'sale', 'alisan_customer_geotag'],
    'author': "Suhindra",
    'maintainer': 'Suhindra',
    'license': "AGPL-3",
    'summary': '''SMS Gateway management system''',
    'data': [
                'views/sms_gateway_log_view.xml',
                'views/sms_gateway_setup_view.xml',
                'views/voucher_sms_history.xml',
                'views/customer_mobile_tree_view.xml',
                'views/menu.xml',
            ],
    'installable': True,
    'auto_install': False,
}
