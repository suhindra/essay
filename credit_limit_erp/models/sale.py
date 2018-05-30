# coding: utf-8

from openerp import models, fields, api, _
from openerp import exceptions
import logging
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import UserError
import datetime
from openerp import tools

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    over_due_approve_by = fields.Many2one('hr.employee','Over Due Approved By')
    recommended_by = fields.Many2one('hr.employee','Recommended By')
    recommended = fields.Boolean('Recommended By SPV FA')
    credit_limit_approve_by = fields.Many2one('hr.employee','Credit Limit Approved By')
    credit_overloaded = fields.Boolean('Is Credit Overloaded?')
    overdue_credit = fields.Boolean('Is Have Overdue Payment?')
    sales_type = fields.Selection([('normal', 'Normal Sales'), ('do', 'DO Sales')],"Sales Type", default="normal", required=True)
    overdue_credit_amount = fields.Float(compute='_get_overdue_credit', string="Late Payments Amount")
    credit_limit = fields.Float(compute='_get_credit_limit', string="Credit Limit")
    credit = fields.Float(compute='_get_credit', string="Total Receivable")
    open_giro_amount = fields.Float(compute='_get_credit', string="Open Giro Amount")
    reject_giro_amount = fields.Float(compute='_get_credit', string="Reject Giro Amount")
    oldest_late_payment = fields.Date(compute='_get_oldest_late_payment', string="Oldest Late Payment")
    over_due_age = fields.Integer(compute='_get_oldest_late_payment', string="Over Due Ages(Day(s))")


    @api.one
    @api.depends('amount_total')
    def _amount_in_words(self):
        self.amount_to_text = amount_to_text_id(self.amount_total, self.pricelist_id.currency_id.symbol)
    
    @api.multi
    def check_limit(self):
        for so in self:
            if so.payment_term_id.payment_type != 'credit':
                return True
            current_so_amounnt = 0
            current_so = self.env['sale.order'].search([('partner_id', '=', so.partner_id.id), ('state', '=', 'sale'), ('invoice_status','!=','invoiced')])
            for value in current_so:
                current_so_amounnt = current_so_amounnt + value.amount_total
            allowed_sale = self.env['res.partner'].with_context(
                {'new_amount': so.amount_total,
                 'new_currency': so.company_id.currency_id.id}).browse(so.partner_id.id).allowed_sale
            if allowed_sale:
                return True
            else:
                if so.credit_overloaded:
                    if so.credit_limit_approve_by.id:
                        pass
                    else:
                        msg = _('Tidak bisa confirm Sale Order karena melampaui credit limit.'
                            '\nCredit Limit : %s') % (so.partner_id.credit_limit)
                        raise exceptions.Warning(msg)

                elif so.overdue_credit:
                    if so.over_due_approve_by.id:
                        pass
                    else:
                        msg = _('Tidak bisa confirm Sale Order karena ada over due payments')
                        raise exceptions.Warning(msg)
                user_id = self.env.uid
                employee_obj = self.env['hr.employee']
                employees = employee_obj.search([('user_id', '=', user_id)])
                if  employees:
                    for record in employees:
                        if ( (so.partner_id.credit_limit + (record.credit_limit_approve_amount * so.partner_id.credit_limit / 100) - (so.partner_id.credit + current_so_amounnt + so.amount_total)) >= 0.0 ):
                            pass
                        else :
                            msg = _('Tidak bisa confirm Sale Order karena akan melampaui credit limit.'
                            '\nCredit Limit : %s') % (so.partner_id.credit_limit)
                return True


    @api.multi
    def check_package(self):
        current_package = self.env['stock.quant.package'].search([('location_id.usage', '=', 'internal')])
        if current_package:
            msg = _('Tidak bisa confirm Sale Order karena ada return bonus yang belum di unpack')
            raise exceptions.Warning(msg)
            
        


    @api.multi
    def action_confirm(self):
        self.check_package()
        self.check_limit()
        return super(SaleOrder, self).action_confirm()


    @api.multi
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        invoice_obj = self.env['account.invoice']
        inv = invoice_obj.search([('origin', '=', self.name)])
        if  inv:
            for record in inv:
                for val in self.giro_sales_order_ids:
                    val.invoice_id = record.id
        return res

        


    @api.multi
    def ignore_credit_overload(self):
        user_id = self.env.uid
        employee_obj = self.env['hr.employee']        

        if self.credit_overloaded:
            current_so_amounnt = 0
            current_so = self.env['sale.order'].search([('partner_id', '=', self.partner_id.id), ('state', '=', 'sale'), ('invoice_status','!=','invoiced')])
            for value in current_so:
                current_so_amounnt = current_so_amounnt + value.amount_total
            employees = employee_obj.search([('user_id', '=', user_id)])
            if  employees:
                for record in employees:
                    if ( (self.partner_id.credit_limit + (record.credit_limit_approve_amount * self.partner_id.credit_limit / 100) - (self.partner_id.credit + current_so_amounnt + self.amount_total)) >= 0.0 ):
                        self.write({'credit_limit_approve_by':record.id})
                    else :
                        msg = _('Credit Limit akun anda tidak cukup untuk Approve')
                        raise exceptions.Warning(msg)
        else:
            msg = _('Sales Order ini tidak membutuhkan Approve')
            raise exceptions.Warning(msg)
        
    @api.multi
    def get_recommend(self):
        user_id = self.env.uid
        employee_obj = self.env['hr.employee']        
        employees = employee_obj.search([('user_id', '=', user_id)])
        if  employees:
            for record in employees:
                if (record.recommend):
                    self.write({'recommended_by':record.id, 'recommended': True})
                else :
                    msg = _('Credit Limit akun anda tidak cukup untuk Approve')
                    raise exceptions.Warning(msg)
        else:
            msg = _('User Tidak Boleh Melakukan Recommended Sales Order')
            raise exceptions.Warning(msg)

    @api.multi
    def get_unrecommend(self):
        user_id = self.env.uid
        employee_obj = self.env['hr.employee']        
        employees = employee_obj.search([('user_id', '=', user_id)])
        if  employees:
            for record in employees:
                if (record.recommend):
                    self.write({'recommended_by':False, 'recommended': False})
                else :
                    msg = _('Credit Limit akun anda tidak cukup untuk Approve')
                    raise exceptions.Warning(msg)
        else:
            msg = _('User Tidak Boleh Melakukan Recommended Sales Order')
            raise exceptions.Warning(msg)

    @api.multi
    def ignore_late_payment(self):
        user_id = self.env.uid
        employee_obj = self.env['hr.employee']
        if self.overdue_credit:
            employees = employee_obj.search([('user_id', '=', user_id)])
            if  employees:
                for record in employees:
                    if ( record.overdue_credit_approve ):
                        self.write({'over_due_approve_by':record.id})
                    else :
                        msg = _('Akun anda tidak memiliki hak untuk Approve')
                        raise exceptions.Warning(msg)
        else:
            msg = _('Sales Order ini tidak membutuhkan Approve')
            raise exceptions.Warning(msg)

    @api.onchange('partner_id')   
    def onchange_sale_partner_id(self):
        self.credit_overloaded = self.partner_id.credit_overloaded
        self.overdue_credit = self.partner_id.overdue_credit
        self.over_due_approve_by = ''
        self.credit_limit_approve_by = ''
        self.user_id = self.partner_id.route_id.salesperson_id.user_id.id


    @api.onchange('amount_total')   
    def onchange_sale_amount_total(self):
        if ( ((self.partner_id.credit_limit - (self.partner_id.credit  + self.amount_total)) < 0.0) and (self.payment_term_id.payment_type == 'credit') ):
            self.credit_overloaded = True
            self.credit_limit_approve_by = ''   

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}

        for order in self:
            group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)
            for line in order.order_line.sorted(key=lambda l: l.qty_to_invoice < 0):
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if group_key not in invoices:
                    inv_data = order._prepare_invoice()
                    invoice = inv_obj.create(inv_data)
                    invoices[group_key] = invoice
                elif group_key in invoices:
                    vals = {}
                    if order.name not in invoices[group_key].origin.split(', '):
                        vals['origin'] = invoices[group_key].origin + ', ' + order.name
                    if order.client_order_ref and order.client_order_ref not in invoices[group_key].name.split(', '):
                        vals['name'] = invoices[group_key].name + ', ' + order.client_order_ref
                    invoices[group_key].write(vals)
                if line.qty_to_invoice > 0:
                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
                elif line.qty_to_invoice < 0 and final:
                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)

        if not invoices:
            raise UserError(_('There is no invoicable line. 1'))

        for invoice in invoices.values():
            if not invoice.invoice_line_ids:
                raise UserError(_('There is no invoicable line. 2'))
            # If invoice is negative, do a refund invoice instead
            if invoice.amount_untaxed < 0:
                invoice.type = 'out_refund'
                for line in invoice.invoice_line_ids:
                    line.quantity = -line.quantity
            # Use additional field helper function (for account extensions)
            for line in invoice.invoice_line_ids:
                line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            invoice.compute_taxes()
            #invoice.signal_workflow('invoice_open')

        return [inv.id for inv in invoices.values()]

    @api.depends('credit_overloaded')
    def _get_overdue_credit(self):
        for sale_order in self:
            today = datetime.date.today()
            sale_order.overdue_credit_amount = 0
            moveline_obj = self.env['account.invoice']
            movelines = moveline_obj.search([('partner_id', '=', sale_order.partner_id.id), ('state', '=', 'open'), ('date_due', '<', today)])
            for inv in movelines:
                if sale_order.overdue_credit:
                    sale_order.overdue_credit_amount = sale_order.overdue_credit_amount + inv.residual

    @api.multi
    def _get_credit(self):
        for sale_order in self:
            sale_order.credit = sale_order.partner_id.credit
            giro_obj = self.env['alisan.giro']
            open_giro_obj = giro_obj.search([('partner_id', '=', sale_order.partner_id.id), ('state', '=', 'open')])
            for open in open_giro_obj:
                sale_order.open_giro_amount = sale_order.open_giro_amount + open.amount

            reject_giro_obj = giro_obj.search([('partner_id', '=', sale_order.partner_id.id), ('state', '=', 'reject')])
            for open in reject_giro_obj:
                sale_order.reject_giro_amount = sale_order.reject_giro_amount + open.amount

    @api.multi
    def _get_oldest_late_payment(self):
        for sale_order in self:
            today = datetime.date.today()
            sale_order.oldest_late_payment = ''
            sale_order.over_due_age = ''
            moveline_obj = self.env['account.move.line']
            movelines = moveline_obj.search([('partner_id', '=', sale_order.partner_id.id), ('debit', '>', 0), ('quantity', '>', 0),('account_id.internal_type', '=', 'receivable'),('move_id.state', '!=', 'draft'), ('reconciled', '=', False), ('date_maturity', '<', today)], limit=1, order='date_maturity asc')
            for line in movelines:
                if sale_order.credit_overloaded:
                    sale_order.oldest_late_payment = line.date_maturity
                    format = '%Y-%m-%d'
                    a = datetime.datetime.strptime(line.date_maturity, format)
                    b = datetime.datetime.strptime(str(today), format)
                    c = b - a
                    _logger.info(type(c.days))
                    sale_order.over_due_age = int(c.days)
            

    @api.multi
    def _get_credit_limit(self):
        for sale_order in self:
            sale_order.credit_limit = sale_order.partner_id.credit_limit

        
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    def _get_to_invoice_qty(self):
        so_obj = self.env['sale.order']
        for line in self:
            if line.order_id.state in ['sale', 'done']:
                if (line.order_id.sales_type == 'do') or (line.product_id.type == 'service'):
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0