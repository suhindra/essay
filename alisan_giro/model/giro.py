from openerp import models, fields, api
from openerp import tools
import openerp.addons.decimal_precision as dp
import time
import logging
from openerp.tools.translate import _
from openerp import netsvc
import datetime
import requests
import xml.etree.ElementTree as et
from openerp.exceptions import UserError
from babel.numbers import format_currency

_logger = logging.getLogger(__name__)
STATES = [('draft', 'Masuk'), ('open', 'Gantung'), ('close', 'Cair'), ('reject', 'Tolak')]


class alisan_giro(models.Model):
    _name = 'alisan.giro'
    _rec_name = 'name'
    _description = 'Giro'

    name = fields.Char('Number', help='Nomor Giro', states={'draft': [('readonly', False)]})
    due_date = fields.Date('Due Date', help='', states={'draft': [('readonly', False)]})
    receive_date = fields.Date('Receive Date', help='',
                                    states={'draft': [('readonly', False)]})
    clearing_date = fields.Date('Clearing Date', help='',
                                     states={'draft': [('readonly', False)]})
    amount = fields.Float('Amount', help='', states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', 'Partner', help='',
                                  states={'draft': [('readonly', False)]})
    journal_id = fields.Many2one('account.journal', 'Bank Journal', domain=[('type', '=', 'bank')], help='',
                                  states={'draft': [('readonly', False)]})
    giro_invoice_ids = fields.One2many('alisan.giro_invioce', 'giro_id',
                                        states={'draft': [('readonly', False)]})
    giro_line_sum = fields.Integer('Total', compute='compute_total')

    giro_amount_remain = fields.Integer('Sisa', compute='compute_remain')
    bank_name = fields.Char('Bank Name')


    type = fields.Selection([
        ('payment', 'Payment'),
        ('receipt', 'Receipt')],
        "Type",
        required=True, states={'draft': [('readonly', False)]})
    invoice_type = fields.Char('Invoice Type', states={'draft': [('readonly', False)]})
    state = fields.Selection(string="State", selection=STATES, required=True, default="draft")
    
    _sql_constraints = [('name_uniq', 'unique(name)', _('Nomor Giro tidak boleh sama'))]
    
    def _cek_total(self, cr, uid, ids, context=None):
        inv_total = 0.0
        for giro in self.browse(cr, uid, ids, context=context):
            for gi in giro.giro_invoice_ids:
                inv_total += gi.amount
            
            if giro.amount == inv_total:
                return True
        
        return False  

    def compute_total(self):
        for item in self.giro_invoice_ids:
            self.giro_line_sum += item.amount

    def compute_remain(self):
        self.giro_amount_remain = self.amount - self.giro_line_sum
    
    @api.multi
    def action_cancel(self):
        self.write({'state': STATES[0][0]})
    
    @api.multi
    def action_confirm(self):
        self.write({'state': STATES[1][0]})

    @api.multi
    def action_reject(self):
        self.write({'state': STATES[3][0]})
        
    def action_clearing(self, cr, uid, ids, context=None):        
        data = {'state': STATES[2][0],
                'clearing_date': time.strftime("%Y-%m-%d %H:%M:%S")}
        self.write(cr, uid, ids, data, context=context)
    
    @api.onchange('type')
    def on_change_type(self):
        inv_type = 'in_invoice'
        if self.type == 'payment':
            inv_type = 'in_invoice'
        elif self.type == 'receipt':
            inv_type = 'out_invoice'
        self.invoice_type = inv_type


class alisan_giro_invoice(models.Model):
    _name = 'alisan.giro_invioce'
    _description = 'Giro vs Invoice'
    
    giro_id = fields.Many2one('alisan.giro', 'Giro', help='')
    invoice_id = fields.Many2one('account.invoice', 'Invoice',
                                  help='Invoice to be paid',
                                  domain=[('state', '=', 'open')])

    sales_order_id = fields.Many2one('sale.order', 'Sales Order',
                                  domain=[('state', '=', 'open'), ('state', '=', 'sale')])
    # 'amount_invoice': fields.related("invoice_id", "residual",
    #             relation="account.invoice",
    #             type="float", string="Invoice Amount", store=True),
    amount_invoice = fields.Float('Invoice Amount')
    amount = fields.Float('Amount Allocated')
    
    @api.onchange('invoice_id')
    def on_change_invoice_id(self):
        self.amount_invoice = self.invoice_id.residual


class account_invoice(models.Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'
    
    giro_invoice_ids = fields.One2many('alisan.giro_invioce', 'invoice_id', string="Giro")


class sales_order(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'
    
    
    giro_sales_order_ids = fields.One2many('alisan.giro_invioce', 'sales_order_id', string="Giro")

    @api.multi
    def _prepare_invoice(self):
        
        self.ensure_one()
        giro_sales_lines = []
        for giro in self.giro_sales_order_ids:
            giro_sales_lines.append([4, giro.id])
            
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))
        invoice_vals = {
            'name': self.client_order_ref or '',
            'origin': self.name,
            'type': 'out_invoice',
            'account_id': self.partner_invoice_id.property_account_receivable_id.id,
            'partner_id': self.partner_invoice_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'comment': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': self.company_id.id,
            'user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id,
            'giro_invoice_ids': giro_sales_lines
        }
        return invoice_vals


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    def _default_location_source(self):
        # retrieve picking type from context; if none this returns an empty recordset
        picking_type_id = self._context.get('default_picking_type_id')
        picking_type = self.env['stock.picking.type'].browse(picking_type_id)
        return picking_type.default_location_src_id
    def _default_location_destination(self):
        # retrieve picking type from context; if none this returns an empty recordset
        picking_type_id = self._context.get('default_picking_type_id')
        picking_type = self.env['stock.picking.type'].browse(picking_type_id)
        return picking_type.default_location_dest_id

    location_id = fields.Many2one('stock.location', required=True, string="Source Location Zone", readonly=False, default=_default_location_source, states={})
    location_dest_id = fields.Many2one('stock.location', required=True,string="Destination Location Zone", readonly=False, default=_default_location_destination, states={})

    def do_new_transfer(self, cr, uid, ids, context=None):       
        pack_op_obj = self.pool['stock.pack.operation']
        data_obj = self.pool['ir.model.data']
        for pick in self.browse(cr, uid, ids, context=context):

            so_obj = self.pool.get('sale.order')
            _matching_so = so_obj.search(cr, uid, [('name', '=', pick.group_id.name)], context=context)
            if _matching_so:

                if pick.picking_type_id.name == 'Delivery Orders':
                    conf = self.pool.get('ir.config_parameter')

                    send_shipped = bool(conf.get_param(cr, uid, 'sms_gateway.send_shipped')),
                    
                    if bool(send_shipped[0]):
                        sms_template = str(conf.get_param(cr, uid, 'sms_gateway.shipped_sms_template')),
                        sms_template = str(sms_template[0])

                        user_key = str(conf.get_param(cr, uid, 'sms_gateway.user_key')),
                        user_key = str(user_key[0])

                        pass_key = str(conf.get_param(cr, uid, 'sms_gateway.pass_key')),
                        pass_key = str(pass_key[0])

                        send_sms_api = str(conf.get_param(cr, uid, 'sms_gateway.send_sms_api')),
                        send_sms_api = str(send_sms_api[0])
                        
                        order_line = ''
                        for x in pick.pack_operation_product_ids:
                            order_line += str(x.product_id.categ_id.name) + ' qty ' + str(x.qty_done)+ ' ' + str(x.product_uom_id.name) + ', '

                        isi_pesan = sms_template.format(customer=str(pick.partner_id.name), order_number=str(pick.name), order_line=str(order_line), order_total=str(format_currency( pick.amount_total, 'IDR', locale='id_ID' )))
                        
                        url = send_sms_api.format(user_key=str(user_key), pass_key=str(pass_key), phone=str(pick.partner_id.mobile), message=str(isi_pesan))
                        response = requests.get(url)
                        content = et.fromstring(response.content)
                        message = content.find("message")
                        text = message.find("text").text
                        if text == "Success":
                            message_id = message.find("messageId").text
                            to = message.find("to").text
                            status = message.find("status").text
                            sms_log = self.pool.get('res.sms.gateway.log')
                            sms_log.create(cr, uid, {'sending_status': 'Sending', 'message_id': message_id, 'to': to, 'source_document':pick.name, 'message':isi_pesan, 'text':text})
                        else:
                            sms_log = self.pool.get('res.sms.gateway.log')
                            sms_log.create(cr, uid, {'sending_status': 'Error', 'source_document':pick.name, 'message':isi_pesan})

                _matching_so_obj = so_obj.browse(cr, uid, _matching_so[0], context=context)

                invoice_obj = self.pool.get('account.invoice')
                _matching_inv = invoice_obj.search(cr, uid, [('origin', '=', pick.group_id.name)], context=context)

                _matching_obj = False
                if _matching_so_obj.sales_type == 'do':
                    if _matching_inv:
                        _matching_obj = invoice_obj.browse(cr, uid, _matching_inv[0], context=context)
                    else:
                        raise UserError(_('Harus Buat Invoice'))                

                allocated_giro = 0
                if _matching_obj:
                    for amount in _matching_obj.giro_invoice_ids:
                        allocated_giro = allocated_giro + amount.amount
                to_delete = []
                if not pick.move_lines and not pick.pack_operation_ids:
                    raise UserError(_('Please create some Initial Demand or Mark as Todo and create some Operations. '))
                # In draft or with no pack operations edited yet, ask if we can just do everything
                if pick.state == 'draft' or all([x.qty_done == 0.0 for x in pick.pack_operation_ids]):
                    # If no lots when needed, raise error
                    picking_type = pick.picking_type_id
                    if (picking_type.use_create_lots or picking_type.use_existing_lots):
                        total_pick = 0
                        for pack in pick.pack_operation_ids:
                            total_pick = total_pick + (pack.sale_price * pack.product_qty)
                            if pack.product_id and pack.product_id.tracking != 'none':
                                raise UserError(_('Some products require lots, so you need to specify those first!'))
                        if total_pick > allocated_giro:
                            if _matching_so_obj.sales_type == 'do':
                                raise UserError(_('Melebihi jaminan'))

                    view = data_obj.xmlid_to_res_id(cr, uid, 'stock.view_immediate_transfer')
                    wiz_id = self.pool['stock.immediate.transfer'].create(cr, uid, {'pick_id': pick.id}, context=context)
                    return {
                         'name': _('Immediate Transfer?'),
                         'type': 'ir.actions.act_window',
                         'view_type': 'form',
                         'view_mode': 'form',
                         'res_model': 'stock.immediate.transfer',
                         'views': [(view, 'form')],
                         'view_id': view,
                         'target': 'new',
                         'res_id': wiz_id,
                         'context': context,
                     }

                # Check backorder should check for other barcodes
                if self.check_backorder(cr, uid, pick, context=context):
                    view = data_obj.xmlid_to_res_id(cr, uid, 'stock.view_backorder_confirmation')
                    wiz_id = self.pool['stock.backorder.confirmation'].create(cr, uid, {'pick_id': pick.id}, context=context)
                    return {
                             'name': _('Create Backorder?'),
                             'type': 'ir.actions.act_window',
                             'view_type': 'form',
                             'view_mode': 'form',
                             'res_model': 'stock.backorder.confirmation',
                             'views': [(view, 'form')],
                             'view_id': view,
                             'target': 'new',
                             'res_id': wiz_id,
                             'context': context,
                         }
                total_pick = 0
                for operation in pick.pack_operation_ids:
                    total_pick = total_pick + (operation.sale_price * operation.qty_done)
                    if operation.qty_done < 0:
                        raise UserError(_('No negative quantities allowed'))
                    if operation.qty_done > 0:
                        pack_op_obj.write(cr, uid, operation.id, {'product_qty': operation.qty_done}, context=context)
                    else:
                        to_delete.append(operation.id)
                if total_pick > allocated_giro:
                    if _matching_so_obj.sales_type == 'do':
                        raise UserError(_('Melebihi jaminan'))
                if to_delete:
                    pack_op_obj.unlink(cr, uid, to_delete, context=context)
            else:
                to_delete = []
                if not pick.move_lines and not pick.pack_operation_ids:
                    raise UserError(_('Please create some Initial Demand or Mark as Todo and create some Operations. '))
                # In draft or with no pack operations edited yet, ask if we can just do everything
                if pick.state == 'draft' or all([x.qty_done == 0.0 for x in pick.pack_operation_ids]):
                    # If no lots when needed, raise error
                    picking_type = pick.picking_type_id
                    if (picking_type.use_create_lots or picking_type.use_existing_lots):
                        for pack in pick.pack_operation_ids:
                            if pack.product_id and pack.product_id.tracking != 'none':
                                raise UserError(_('Some products require lots, so you need to specify those first!'))
                    view = data_obj.xmlid_to_res_id(cr, uid, 'stock.view_immediate_transfer')
                    wiz_id = self.pool['stock.immediate.transfer'].create(cr, uid, {'pick_id': pick.id}, context=context)
                    return {
                         'name': _('Immediate Transfer?'),
                         'type': 'ir.actions.act_window',
                         'view_type': 'form',
                         'view_mode': 'form',
                         'res_model': 'stock.immediate.transfer',
                         'views': [(view, 'form')],
                         'view_id': view,
                         'target': 'new',
                         'res_id': wiz_id,
                         'context': context,
                     }

                # Check backorder should check for other barcodes
                if self.check_backorder(cr, uid, pick, context=context):
                    view = data_obj.xmlid_to_res_id(cr, uid, 'stock.view_backorder_confirmation')
                    wiz_id = self.pool['stock.backorder.confirmation'].create(cr, uid, {'pick_id': pick.id}, context=context)
                    return {
                             'name': _('Create Backorder?'),
                             'type': 'ir.actions.act_window',
                             'view_type': 'form',
                             'view_mode': 'form',
                             'res_model': 'stock.backorder.confirmation',
                             'views': [(view, 'form')],
                             'view_id': view,
                             'target': 'new',
                             'res_id': wiz_id,
                             'context': context,
                         }
                for operation in pick.pack_operation_ids:
                    if operation.qty_done < 0:
                        raise UserError(_('No negative quantities allowed'))
                    if operation.qty_done > 0:
                        pack_op_obj.write(cr, uid, operation.id, {'product_qty': operation.qty_done}, context=context)
                    else:
                        to_delete.append(operation.id)
                if to_delete:
                    pack_op_obj.unlink(cr, uid, to_delete, context=context)
        self.do_transfer(cr, uid, ids, context=context)
        return

class stock_backorder_confirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    @api.multi
    def _process(self, cancel_backorder=False):     
        self.ensure_one()
        so_obj = self.env['sale.order']
        _matching_so = so_obj.search([('name', '=', self.pick_id.group_id.name)])
        if _matching_so:
            allocated_giro = 0
            if _matching_so.sales_type == 'do':
                inv_obj = self.env['account.invoice']
                inv = inv_obj.search([('origin', '=', self.pick_id.group_id.name)])

                if  inv:
                    for record in inv.giro_invoice_ids:
                        allocated_giro = allocated_giro + record.amount

            total_pick = 0
            for pack in self.pick_id.pack_operation_ids:
                if pack.qty_done > 0:
                    pack.product_qty = pack.qty_done
                    total_pick = total_pick + (pack.sale_price * pack.qty_done)
                else:
                    pack.unlink()
            if total_pick > allocated_giro:
                if _matching_so.sales_type == 'do':
                    raise UserError(_('Melebihi jaminan back order'))
            self.pick_id.do_transfer()
            if cancel_backorder:
                backorder_pick = self.env['stock.picking'].search([('backorder_id', '=', self.pick_id.id)])
                backorder_pick.action_cancel()
                self.pick_id.message_post(body=_("Back order <em>%s</em> <b>cancelled</b>.") % (backorder_pick.name))

        else:
            for pack in self.pick_id.pack_operation_ids:
                if pack.qty_done > 0:
                    pack.product_qty = pack.qty_done
                else:
                    pack.unlink()
            self.pick_id.do_transfer()
            if cancel_backorder:
                backorder_pick = self.env['stock.picking'].search([('backorder_id', '=', self.pick_id.id)])
                backorder_pick.action_cancel()
                self.pick_id.message_post(body=_("Back order <em>%s</em> <b>cancelled</b>.") % (backorder_pick.name))



class stock_pack_operation(models.Model):
    _inherit = 'stock.pack.operation'

    @api.depends('product_id')
    def _compute_sale_price(self):
        so_obj = self.env['sale.order.line']
        _matching_so = so_obj.search([('product_id', '=', self.product_id.id), ('order_id.name', '=', self.picking_id.group_id.name)])
        sale_price = 0
        for ms in _matching_so:
            if _matching_so:
                sale_price = ms.price_subtotal / ms.product_uom_qty

            self.update({
                'sale_price': sale_price,
            })

    sale_price = fields.Integer('Sale Price', store=True, compute='_compute_sale_price')


    @api.depends('product_uom_qty', 'discount', 'line_discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        for line in self:
            line_discount_price = line.price_unit * (1 - (line.line_discount or 0.0) / 100.0)
            price = line_discount_price * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

