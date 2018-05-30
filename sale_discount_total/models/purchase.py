from openerp import api, fields, models
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.depends('order_line.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = amount_discount = amount_undiscount = 0.0
            for line in order.order_line:
                amount_undiscount += line.price_subtotal
                if (amount_discount > 0) and (line.taxes_id) :
                    amount_tax += (amount_undiscount - amount_discount)/10
                else:
                    amount_tax += line.price_tax
            
            amount_discount += (order.discount_rate * amount_undiscount / 100)
            order.update({
                'amount_undiscount': order.currency_id.round(amount_undiscount),
                'amount_untaxed': order.currency_id.round(amount_undiscount - amount_discount),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_discount': order.currency_id.round(amount_discount),
                'amount_total': (amount_undiscount - amount_discount) + amount_tax,
            })

    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], string='Discount type',
                                     required= True,states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                     default='percent')
    discount_rate = fields.Float('Discount Rate', digits_compute=dp.get_precision('Account'),
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
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
        if (self.partner_id) and (self.discount_rate > 0) and (self.order_line):
            self._amount_all()
        return True

    @api.multi
    def button_dummy(self):
        self.supply_rate()
        return True
                

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    discount = fields.Float(string='Discount (%)', digits=(16, 20), default=0.0)
    line_discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], string='Discount Type',
                                     required=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                     default='percent')
    line_discount_rate = fields.Float('Discount Rate', digits=dp.get_precision('Account'),
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    line_second_discount_rate = fields.Float('Second Discount Rate', digits=dp.get_precision('Account'),
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    line_discount = fields.Float(string='Line Discount (%)', digits=dp.get_precision('Discount'), default=0.0)
    line_discount_amount = fields.Float('Line Amount Discount', digits_compute=dp.get_precision('Account'),
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    discount_amount = fields.Float('Amount Discount', digits=(16, 20),
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})

    @api.depends('discount')
    def _compute_amount(self):
        prices = {}
        for line in self:
            if line.discount:
                prices[line.id] = line.price_unit
                line.price_unit *= (1 - line.discount / 100.0)
            super(PurchaseOrderLine, line)._compute_amount()
            if line.discount:
                line.price_unit = prices[line.id]

    @api.multi
    def _get_stock_move_price_unit(self):
        """Get correct price with discount replacing current price_unit
        value before calling super and restoring it later for assuring
        maximum inheritability.
        """
        if self.discount:
            price_unit = self.price_unit
            self.price_unit *= (100 - self.discount) / 100
        price = super(PurchaseOrderLine, self)._get_stock_move_price_unit()
        if self.discount:
            self.price_unit = price_unit
        return price


    @api.onchange('line_discount_type', 'line_discount_rate','line_second_discount_rate', 'line_discount_amount', 'product_qty', 'discount', 'line_discount', 'price_unit',)
    def supply_rate(self):
        for line in self:
            if line.line_discount_type == 'percent':
                line.discount = line.line_discount_rate
                if line.product_qty > 0:
                    first_discount = (line.line_discount_rate/100.00) * (line.product_qty * (line.price_unit - (line.price_tax / line.product_qty)))
                    second_discount = (line.line_second_discount_rate/100.00) * (line.product_qty * ((line.price_unit - (line.price_tax / line.product_qty))) - first_discount)
                    line.line_discount_amount = first_discount + second_discount

            else:
                total = discount = 0.0
                total += round((line.product_qty * (line.price_unit - (line.price_tax / line.product_qty))))
                if line.line_discount_rate != 0:
                    discount = (line.line_discount_rate / total) * 100
                else:
                    discount = line.line_discount_rate
                line.discount = discount
                line.line_discount_amount = (discount/100.00) * total


    @api.onchange('line_discount_type')
    def reset_rate(self):
        for line in self:
            line.line_discount_rate = 0.00
