# coding: utf-8
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from datetime import timedelta
import datetime
from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    grace_payment_days = fields.Float(
        'Days grace payment',
        help='Days grace payment')

    credit_overloaded = fields.Boolean(
        compute='_get_credit_overloaded',
        string="Credit Overloaded", type='Boolean')
    overdue_credit = fields.Boolean(
        compute='_get_overdue_credit', string="Late Payments", type='Boolean')
    allowed_sale = fields.Boolean(
        compute='get_allowed_sale', string="Allowed Sales", type='Boolean')
    open_giro_amount = fields.Float(compute='_get_credit', string="Open Giro Amount")
    reject_giro_amount = fields.Float(compute='_get_credit', string="Reject Giro Amount")
    oldest_late_payment = fields.Date(compute='_get_oldest_late_payment', string="Oldest Late Payment")
    over_due_age = fields.Integer(compute='_get_oldest_late_payment', string="Over Due Ages(Day(s))")
    overdue_credit_amount = fields.Float(compute='_get_overdue_credit', string="Late Payments Amount")
    
    @api.multi
    def _get_overdue_credit(self):
        today = datetime.date.today()
        self.overdue_credit_amount = 0
        moveline_obj = self.env['account.invoice']
        movelines = moveline_obj.search([('partner_id', '=', self.id), ('state', '=', 'open'), ('date_due', '<', today)])
        for inv in movelines:
            if self.credit_overloaded:
                self.overdue_credit_amount = self.overdue_credit_amount + inv.residual

    @api.multi
    def _get_oldest_late_payment(self):
        today = datetime.date.today()
        for partner in self:
            partner.oldest_late_payment = ''
            partner.over_due_age = ''
            moveline_obj = self.env['account.move.line']
            movelines = moveline_obj.search([('partner_id', '=', partner.id), ('debit', '>', 0), ('quantity', '>', 0),('account_id.internal_type', '=', 'receivable'),('move_id.state', '!=', 'draft'), ('reconciled', '=', False), ('date_maturity', '<', today)], limit=1, order='date_maturity asc')
            for line in movelines:
                if partner.credit_overloaded:
                    partner.oldest_late_payment = line.date_maturity
                    format = '%Y-%m-%d'
                    a = datetime.datetime.strptime(line.date_maturity, format)
                    b = datetime.datetime.strptime(str(today), format)
                    c = b - a
                    _logger.info(type(c.days))
                    partner.over_due_age = int(c.days)
    
    @api.multi
    def _get_credit(self):
        for partner in self:
            giro_obj = self.env['alisan.giro']
            open_giro_obj = giro_obj.search([('partner_id', '=', partner.id), ('state', '=', 'open')])
            for open in open_giro_obj:
                partner.open_giro_amount = partner.open_giro_amount + open.amount

            reject_giro_obj = giro_obj.search([('partner_id', '=', partner.id), ('state', '=', 'reject')])
            for open in reject_giro_obj:
                partner.reject_giro_amount = partner.reject_giro_amount + open.amount


    @api.multi
    def _get_credit_overloaded(self):
        for partner in self:
            context = self.env.context or {}
            currency_obj = self.env['res.currency']
            res_company = self.env['res.company']
            imd_obj = self.env['ir.model.data']
            company_id = imd_obj.get_object_reference(
                'base', 'main_company')[1]
            company = res_company.browse(company_id)
            new_amount = context.get('new_amount', 0.0)
            new_currency = context.get('new_currency', False)
            if new_currency:
                from_currency = currency_obj.browse(new_currency)
            else:
                from_currency = company.currency_id
            new_amount_currency = from_currency.compute(
                new_amount, company.currency_id)

            new_credit = partner.credit + new_amount_currency
            partner.credit_overloaded = new_credit > partner.credit_limit

    @api.multi
    def _get_overdue_credit(self):
        for partner in self:
            _logger.info(partner.id)
            moveline_obj = self.env['account.move.line']
            movelines = moveline_obj.search(
                [('partner_id', '=', partner.id),
                 ('account_id.internal_type', '=', 'receivable'),
                 ('debit', '>', 0),
                 ('quantity', '>', 0),
                 ('move_id.state', '!=', 'draft'),
                 ('reconciled', '=', False)])
            # credit = 0.0
            debit_maturity, credit_maturity = 0.0, 0.0
            for line in movelines:
                if line.date_maturity and line.partner_id.grace_payment_days:
                    maturity = fields.Datetime.from_string(
                        line.date_maturity)
                    grace_payment_days = timedelta(
                        days=line.partner_id.grace_payment_days)
                    limit_day = maturity + grace_payment_days
                    limit_day = limit_day.strftime("%Y-%m-%d")

                elif line.date_maturity:
                    _logger.info(line.date_maturity)
                    limit_day = line.date_maturity
                else:
                    limit_day = fields.Date.today()
                if limit_day < fields.Date.today():
                    # credit and debit maturity sums all aml
                    # with late payments
                    debit_maturity += line.debit
                credit_maturity += line.credit
                # credit += line.credit
            balance_maturity = debit_maturity - credit_maturity
            partner.overdue_credit = balance_maturity > 0.0
            

    @api.multi
    def get_allowed_sale(self):
        for partner in self:
            partner.allowed_sale = not partner.credit_overloaded and \
                not partner.overdue_credit

    @api.multi
    def get_allowed_sale(self):
        for partner in self:
            partner.allowed_sale = not partner.credit_overloaded and \
                not partner.overdue_credit
