{
	"name": "Giro",
	"version": "1.2",
	"depends": [
		"account", "sale", "stock", "account_voucher", "payment_term_type", "base_sms_gateway_erp"
	], 
	"author": "Suhindra", 
	"category": "Accounting",
	"website": '',
	"installable": True,
	"auto_install": False,
	"application": True,
	'data': ['view/giro.xml',
            'view/invoice.xml',
            'view/sales_order.xml',
            'view/stock_picking.xml',
            'view/menu.xml',
            ],
}