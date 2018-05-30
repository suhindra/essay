# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import requests
import xml.etree.ElementTree as et
from babel.numbers import format_currency

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    @api.multi
    def action_confirm(self):
        for order in self:
            order.state = 'sale'
            conf = self.env['ir.config_parameter']

            send_ordered = bool(conf.get_param('sms_gateway.send_ordered')),
            
            if bool(send_ordered[0]):
                sms_template = str(conf.get_param('sms_gateway.ordered_sms_template')),
                sms_template = str(sms_template[0])

                user_key = str(conf.get_param('sms_gateway.user_key')),
                user_key = str(user_key[0])

                pass_key = str(conf.get_param('sms_gateway.pass_key')),
                pass_key = str(pass_key[0])

                send_sms_api = str(conf.get_param('sms_gateway.send_sms_api')),
                send_sms_api = str(send_sms_api[0])
                order_line = ''
                for x in self.order_line:
                    order_line += str(x.product_id.default_code) + ' qty ' + str(x.product_uom_qty)+ ' ' + str(x.product_uom.name) + ', '

                isi_pesan = sms_template.format(customer=str(self.partner_id.name), order_number=str(self.name), order_line=str(order_line), order_total=str(format_currency( self.amount_total, 'IDR', locale='id_ID' )))
                url = send_sms_api.format(user_key=str(user_key), pass_key=str(pass_key), phone=str(self.partner_id.mobile), message=str(isi_pesan))
                response = requests.get(url)
                content = et.fromstring(response.content)
                message = content.find("message")
                text = message.find("text").text
                if text == "Success":
                    message_id = message.find("messageId").text
                    to = message.find("to").text
                    status = message.find("status").text
                    sms_log = self.env['res.sms.gateway.log']
                    sms_log.create({'sending_status': 'Sending', 'message_id': message_id, 'to': to, 'source_document':self.name, 'message':isi_pesan, 'text':text})
                else:
                    sms_log = self.env['res.sms.gateway.log']
                    sms_log.create({'sending_status': 'Error', 'source_document':self.name, 'message':isi_pesan})


            if self.env.context.get('send_email'):
                self.force_quotation_send()
            order.order_line._action_procurement_create()
            if not order.project_id:
                for line in order.order_line:
                    if line.product_id.invoice_policy == 'cost':
                        order._create_analytic_account()
                        break
        if self.env['ir.values'].get_default('sale.config.settings', 'auto_done_setting'):
            self.action_done()
        return True

