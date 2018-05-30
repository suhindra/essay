{
    'name': 'Voucher management',
    'version': '1.0',
    'depends': ['base',
                'stock',
                'sale',
                'alisan_customer_geotag',
                'alisan_city',
                'alisan_subdistrict',
                'sales_team',],
    'author': "Suhindra",
    'maintainer': 'Suhindra',
    'license': "AGPL-3",
    'summary': '''Voucher management system''',
    'data': ['views/base_voucher_view.xml',
            'views/base_voucher_barcode_view.xml',
            'views/voucher_scan_in.xml',
            'views/voucher_scan_out.xml',
            'views/voucher_scan_cancel_load.xml',
            'views/voucher_setup_view.xml',
            'views/cement_type_view.xml',
            'views/factory_view.xml',
            'views/inherit_report_layouts.xml',
            'views/voucher_print_report.xml',
            'views/menu.xml',
            'report/voucher_report_template.xml',
            'report/voucher_report_pdf_template.xml',
            'report/voucher_validation_report_template.xml',
            ],
    'installable': True,
    'auto_install': False,
}
