# coding: utf-8
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Credit Limit - ERP",
    "version": "9.0.0.1.0",
    "author": "Suhindra",
    "license": "LGPL-3",
    'summary': '''Credit Limit management system''',
    "depends": [
        "base",
        "stock",
        "alisan_giro",
        "account",
        "sale",
        "product",
        "hr",
        "payment_term_type"],
    "data": [
        "views/invoice_workflow.xml",
        "views/partner_view.xml",
        "views/sales_order.xml",
        "views/product_category.xml",
        "views/employee_view.xml",
        "views/account_invoice.xml",
    ],
    "installable": True,
    'auto_install': False,
}
