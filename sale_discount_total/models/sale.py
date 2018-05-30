from openerp import api, fields, models
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends('order_line.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = amount_discount = amount_undiscount = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                amount_discount += line.discount_amount + line.line_discount_amount
                amount_undiscount += line.product_uom_qty * line.price_unit

            order.update({
                'amount_undiscount': order.pricelist_id.currency_id.round(amount_undiscount),
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_discount': order.pricelist_id.currency_id.round(amount_discount),
                'amount_total': amount_untaxed + amount_tax,
            })

    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], string='Discount type',
                                     readonly=True, required= True,states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                     default='percent')
    discount_rate = fields.Float('Discount Rate', digits_compute=dp.get_precision('Account'),
                                 readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all',
                                     track_visibility='always')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all',
                                 track_visibility='always')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all',
                                   track_visibility='always')
    amount_undiscount = fields.Monetary(string='Undiscount Amount', store=True, readonly=True, compute='_amount_all',
                                     track_visibility='always')
    amount_discount = fields.Monetary(string='Total Discount', store=True, readonly=True, compute='_amount_all',
                                      digits_compute=dp.get_precision('Account'), track_visibility='always')


    @api.onchange('discount_type', 'discount_rate', 'order_line')
    def supply_rate(self):
        for order in self:
            if order.discount_type == 'percent':
                for line in order.order_line:
                    total = round((line.product_uom_qty * line.price_unit))
                    total_before_header_disc = total - line.line_discount_amount
                    header_discount_amount = (total_before_header_disc * order.discount_rate)/100
                    line.discount_amount = header_discount_amount
                    if total != 0:
                        line.discount = (1 -((total_before_header_disc - header_discount_amount) / total ))*100
                    else:
                        line.discount = 0


            else:
                for line in order.order_line:
                    total = 0.0
                    total += round((line.product_uom_qty * line.price_unit))
                    total_before_header_disc = total - line.line_discount_amount
                    if order.discount_rate != 0:
                        header_discount_amount = total / order.amount_undiscount * round(order.discount_rate)
                        line.discount_amount = header_discount_amount
                        line.discount = (1-((total_before_header_disc - header_discount_amount)/total))*100.00  
                    else:
                        line.discount_amount = 0.00
                        line.discount = 0.00
                

    @api.multi
    def _prepare_invoice(self,):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals.update({
            'discount_type': self.discount_type,
            'discount_rate': self.discount_rate,
        })
        return invoice_vals

    @api.multi
    def button_dummy(self):
        self.supply_rate()
        return True

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    discount = fields.Float(string='Discount (%)',digits=dp.get_precision('Discount'), default=0.0)
    line_discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], string='Discount Type',
                                     readonly=True, required=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                     default='percent')
    line_discount_rate = fields.Float('Discount Rate', digits=dp.get_precision('Account'),
                                 readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    line_discount = fields.Float(string='Line Discount (%)', digits=dp.get_precision('Discount'), default=0.0)
    line_discount_amount = fields.Float('Line Amount Discount', digits_compute=dp.get_precision('Account'),
                                 readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    discount_amount = fields.Float('Amount Discount', digits=(16, 20),
                                 readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})


    @api.onchange('line_discount_type', 'line_discount_rate', 'product_uom_qty', 'discount', 'line_discount', 'price_unit',)
    def supply_rate(self):
        for line in self:
            if line.line_discount_type == 'percent':
                line.line_discount = line.line_discount_rate
                line.line_discount_amount = (line.line_discount_rate/100.00) * (line.product_uom_qty * line.price_unit)
            else:
                total = discount = 0.0
                total += round((line.product_uom_qty * line.price_unit))
                if line.line_discount_rate != 0:
                    discount = (line.line_discount_rate / total) * 100
                else:
                    discount = line.line_discount_rate
                line.line_discount = discount
                line.line_discount_amount = (discount/100.00) * total


    @api.onchange('line_discount_type')
    def reset_rate(self):
        for line in self:
            line.line_discount_rate = 0.00

class ProductCategory(models.Model):
    _inherit = "product.category"

    property_account_discount_income_id = fields.Many2one('account.account', company_dependent=True,
        string="Discount Income Account", 
        domain=[('deprecated', '=', False)],
        help="This account will be used for invoices to value sales.")
    property_account_discount_expense_id = fields.Many2one('account.account', company_dependent=True,
        string="Discount Expense Account",
        domain=[('deprecated', '=', False)],
        help="This account will be used for invoices to value expenses.")

class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.multi
    def get_product_discount_accounts(self):
        return {
            'income': self.categ_id.parent_id.property_account_discount_income_id,
            'expense': self.categ_id.parent_id.property_account_discount_expense_id
        }

