# -*- coding: utf-8 -*-
#

from openerp import models, fields, api
import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import ValidationError
from openerp.exceptions import Warning
import logging
import requests
import xml.etree.ElementTree as et


_logger = logging.getLogger(__name__)


class BaseSmsGatewayLog(models.Model):
    '''SMS Gateway object'''

    _name = "res.sms.gateway.log"
    _description = "SMS Gateway Log object"
    _order = "message_id asc"    

    display_name = fields.Char('Name', compute='_get_display_name', store=True)
    message_id = fields.Char('ID Pesan')
    message = fields.Char('Isi Pesan')
    to = fields.Char('Nomor tujuan')
    text = fields.Char('Keterangan')
    voucher_number = fields.Many2one(
        'res.voucher',
        'No. Voucher',
    )
    sending_status = fields.Selection([
        ('Sent', "Sent"),
        ('Sending', "Sending"),
        ('Error', "Error"),
    ], default='Sending')

    @api.model 
    def automated_action_method(self):
        active_ids = self._context.get('active_ids')
        for active_id in active_ids:
            sms_log_obj = self.env['res.sms.gateway.log']
            _matching_obj = sms_log_obj.browse(active_id)
            message_id = _matching_obj.message_id
            sending_status = _matching_obj.sending_status
            if sending_status == "Sending":
                conf = self.env['ir.config_parameter']
                user_key = str(conf.get_param('sms_gateway.user_key')),
                user_key = str(user_key[0])
                pass_key = str(conf.get_param('sms_gateway.pass_key')),
                pass_key = str(pass_key[0])
                status_sms_api = str(conf.get_param('sms_gateway.status_sms_api')),
                status_sms_api = str(status_sms_api[0])
                url = status_sms_api.format(user_key=str(user_key), pass_key=str(pass_key), message_id=str(message_id))
                response = requests.get(url)    
                content = et.fromstring(response.content)
                message = content.find("message")
                status = message.find("status").text
                id = message.find("id").text
                if id:
                    sms_obj = sms_log_obj.search([('id', '=', active_id)])
                    if  sms_obj:
                        for record in sms_obj:
                            record.write({'sending_status': 'Sent'})
                _logger.info(url)      
        return True

    @api.multi
    def action_resend_sms(self):        
        voucher_number = self.voucher_number.voucher_number
        voucher_number_id = self.voucher_number.id
        barcode_obj = self.env['res.voucher']
        voucher_obj = barcode_obj.search([('voucher_number', '=ilike', voucher_number)])
        _matching_obj = barcode_obj.browse(voucher_obj.id)
        customer = _matching_obj.customer_id.name
        no_voucher = _matching_obj.voucher_number
        scan_out_date = _matching_obj.write_date
        cement_type = _matching_obj.cement_type.name
        qty = _matching_obj.qty
        driver = _matching_obj.driver
        plate_number = _matching_obj.plate_number
        phone = _matching_obj.customer_id.mobile
        conf = self.env['ir.config_parameter']
        sms_template = str(conf.get_param('sms_gateway.sms_template')),
        sms_template = str(sms_template[0])

        user_key = str(conf.get_param('sms_gateway.user_key')),
        user_key = str(user_key[0])

        pass_key = str(conf.get_param('sms_gateway.pass_key')),
        pass_key = str(pass_key[0])

        send_sms_api = str(conf.get_param('sms_gateway.send_sms_api')),
        send_sms_api = str(send_sms_api[0])

        status_sms_api = str(conf.get_param('sms_gateway.status_sms_api')),
        status_sms_api = str(status_sms_api[0])

        isi_pesan = sms_template.format(customer=str(customer), no_voucher=str(no_voucher), scan_out_date=str(scan_out_date), cement_type=str(cement_type), qty=str(qty), driver=str(driver), plate_number=str(plate_number))

        url = send_sms_api.format(user_key=str(user_key), pass_key=str(pass_key), phone=str(phone), message=str(isi_pesan))
    
        response = requests.get(url)
        content = et.fromstring(response.content)
        message = content.find("message")
        text = message.find("text").text
        if text == "Success":
            message_id = message.find("messageId").text
            to = message.find("to").text
            status = message.find("status").text
            sms_log = self.env['res.sms.gateway.log']
            sms_log.create({'sending_status': 'Sending', 'message_id': message_id, 'to': to, 'voucher_number':voucher_number_id, 'message':isi_pesan, 'text':text})
        else:
            to = phone
            status = message.find("status").text
            sms_log = self.env['res.sms.gateway.log']
            sms_log.create({'sending_status': 'Error', 'to': to, 'voucher_number':voucher_number_id, 'message':isi_pesan, 'text':text})
        return True