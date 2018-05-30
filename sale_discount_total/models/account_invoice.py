from openerp import api, fields, models
import openerp.addons.decimal_precision as dp
import logging
from openerp.tools.float_utils import float_compare
_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice')
    def _compute_amount(self):
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        self.amount_tax = sum(line.amount for line in self.tax_line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax
        self.amount_discount = sum((line.quantity * line.price_unit * line.discount)/100 for line in self.invoice_line_ids)
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.date_invoice)
            amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
            amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign

    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], string='Discount Type',
                                     readonly=True, states={'draft': [('readonly', False)]}, default='percent')
    discount_rate = fields.Float('Discount Amount', digits=(16, 2), readonly=True, states={'draft': [('readonly', False)]})
    amount_discount = fields.Monetary(string='Discount', store=True, readonly=True, compute='_compute_amount',
                                      track_visibility='always')

    @api.onchange('discount_type', 'discount_rate')
    def supply_rate(self):
        for inv in self:
            if inv.discount_type == 'percent':
                for line in inv.invoice_line_ids:
                    line.discount = inv.discount_rate
            else:
                total = discount = 0.0
                for line in inv.invoice_line_ids:
                    currency = line.invoice_id and line.invoice_id.currency_id or None
                    price = line.price_unit
                    taxes = False
                    if line.invoice_line_tax_ids:
                        taxes = line.invoice_line_tax_ids.compute_all(price, currency, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
                        total += taxes['total_excluded'] 

                    else:
                        total += (line.quantity * line.price_unit)
                
                if inv.discount_rate != 0:
                    discount = (inv.discount_rate / total) * 100
                else:
                    discount = inv.discount_rate
                for line in inv.invoice_line_ids:
                    line.discount = discount

    @api.multi
    def compute_invoice_totals(self, company_currency, invoice_move_lines):
        total = 0
        total_currency = 0
        for line in invoice_move_lines:
            if self.currency_id != company_currency:
                currency = self.currency_id.with_context(date=self.date_invoice or fields.Date.context_today(self))
                line['currency_id'] = currency.id
                line['amount_currency'] = currency.round(line['price'])
                line['price'] = currency.compute(line['price'], company_currency)
            else:
                line['currency_id'] = False
                line['amount_currency'] = False
                line['price'] = line['price']
            if self.type in ('out_invoice', 'in_refund'):
                total += line['price']
                total_currency += line['amount_currency'] or line['price']
                line['price'] = - line['price']
            else:
                total -= line['price']
                total_currency -= line['amount_currency'] or line['price']
        return total, total_currency, invoice_move_lines

    @api.multi
    def button_dummy(self):
        self.supply_rate()
        return True

    @api.multi
    def invoice_validate(self):
        move = self.move_id
        journal_id = move.journal_id
        update_posted_orig = journal_id.update_posted
        journal_id.update_posted = True
        move.button_cancel()
        line_id_vals = []
        record_disount = 0
        if self.type == "out_invoice":
            record_disount = 0
            for ol in self.invoice_line_ids:
                record_disount += (ol.discount / 100) * ol.price_unit * ol.quantity
            if record_disount != 0:
                line_id_vals += self.env['account.move.line'].with_context(check_move_validity=False).create({
                            'analytic_account_id': False,
                            'tax_ids': False,
                            'product_uom_id': False,
                            'invoice_id': self.id,
                            'analytic_line_ids': [],
                            'tax_line_id': False,
                            'currency_id': False,
                            "name": "Sale Discount",
                            "account_id": ol.product_id.categ_id.parent_id.property_account_income_categ_id.id,
                            "credit": record_disount,
                            "debit": False,
                            'product_id': False,
                            'date_maturity': False, 
                            "partner_id": self.partner_id.id,
                            'amount_currency': 0,
                            'quantity': 1.0,
                            "move_id": move.id})

                line_id_vals += self.env['account.move.line'].with_context(check_move_validity=False).create({
                            'analytic_account_id': False,
                            'tax_ids': False,
                            'product_uom_id': False,
                            'invoice_id': self.id,
                            'analytic_line_ids': [],
                            'tax_line_id': False,
                            'currency_id': False,
                            "name": "Discount",
                            "account_id": ol.product_id.categ_id.parent_id.property_account_discount_income_id.id,
                            "debit": record_disount,
                            "credit": False,
                            'product_id': False,
                            'date_maturity': False, 
                            "partner_id": self.partner_id.id,
                            'amount_currency': 0,
                            'quantity': 1.0,
                            "move_id": move.id})

        if self.type == "out_refund":
            record_disount = 0
            for ol in self.invoice_line_ids:
                record_disount += (ol.discount / 100) * ol.price_unit * ol.quantity
            if record_disount != 0:
                line_id_vals += self.env['account.move.line'].with_context(check_move_validity=False).create({
                            'analytic_account_id': False,
                            'tax_ids': False,
                            'product_uom_id': False,
                            'invoice_id': self.id,
                            'analytic_line_ids': [],
                            'tax_line_id': False,
                            'currency_id': False,
                            "name": "Sale Discount",
                            "account_id": ol.product_id.categ_id.parent_id.property_account_discount_income_id.id,
                            "debit": record_disount,
                            "credit": False,
                            'product_id': False,
                            'date_maturity': False, 
                            "partner_id": self.partner_id.id,
                            'amount_currency': 0,
                            'quantity': 1.0,
                            "move_id": move.id})

                line_id_vals += self.env['account.move.line'].with_context(check_move_validity=False).create({
                            'analytic_account_id': False,
                            'tax_ids': False,
                            'product_uom_id': False,
                            'invoice_id': self.id,
                            'analytic_line_ids': [],
                            'tax_line_id': False,
                            'currency_id': False,
                            "name": "Discount",
                            "account_id": ol.product_id.categ_id.parent_id.property_account_income_categ_id.id,
                            "credit": record_disount,
                            "debit": False,
                            'product_id': False,
                            'date_maturity': False, 
                            "partner_id": self.partner_id.id,
                            'amount_currency': 0,
                            'quantity': 1.0,
                            "move_id": move.id})

        super(AccountInvoice, self).invoice_validate()
        move.post()

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    discount = fields.Float(string='Discount (%)', digits=(16, 20))
    line_discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], string='Discount Type',
                                     readonly=True, required=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                     default='percent')
    line_discount_rate = fields.Float('Discount Rate', digits_compute=dp.get_precision('Account'),
                                 readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    line_discount = fields.Float(string='Line Discount (%)', digits=dp.get_precision('Discount'), default=0.0)
    line_discount_amount = fields.Float('Discount Rate', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})

   
    @api.model
    def new(self, values=None):
        """
        Apply the linked to a purchase.order.line.discount to the
        account_invoice_line
        """
        values = {} if values is None else values
        account_invoice_line = super(
            AccountInvoiceLine, self).new(values=values)
        if account_invoice_line.purchase_line_id:
            account_invoice_line.discount =\
                account_invoice_line.purchase_line_id.discount
        return account_invoice_line



class account_config_settings(models.TransientModel):
    _inherit = "account.config.settings"

    sale_discount_account = fields.Many2one(
        'account.account',
        string="Default Sale Discount Account")

    purchase_discount_account = fields.Many2one(
        'account.account',
        string="Default Purchase Discount Account")

    @api.model
    def get_default_sale_discount_account_values(self, fields):
        conf = self.env['ir.config_parameter']
        account_account = conf.get_param('discount_account.sale_discount_account')
        
        return {
            'sale_discount_account': int(account_account),
        }

    @api.model
    def get_default_purchase_discount_account_values(self, fields):
        conf = self.env['ir.config_parameter']
        account_account = conf.get_param('discount_account.purchase_discount_account')
        return {
            'purchase_discount_account': int(account_account),
        }


    @api.one
    def set_sale_discount_account_values(self):
        conf = self.env['ir.config_parameter']
        sale_discount_account = 0
        for account in self.sale_discount_account:
            sale_discount_account = account.id
        conf.set_param('discount_account.sale_discount_account', int(sale_discount_account))

    @api.one
    def set_purchase_discount_account_values(self):
        conf = self.env['ir.config_parameter']
        purchase_discount_account = 0
        for account in self.purchase_discount_account:
            purchase_discount_account = account.id
        conf.set_param('discount_account.purchase_discount_account', int(purchase_discount_account))

