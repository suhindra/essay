# -*- coding: utf-8 -*-
from openerp import models, fields, api
from lxml import etree
import datetime
import requests
import xml.etree.ElementTree as et

import logging
_logger = logging.getLogger(__name__)

class scan_line_salesshipment(models.Model):
    _inherit = "scan_line_salesshipment"

    @api.model
    def create(self, vals):
        rec = super(scan_line_salesshipment, self).create(vals)
        if rec.state == 'deliver':
            conf = self.env['ir.config_parameter']
            sms_template = str(conf.get_param('sms_gateway.delivery_sms_template')),
            sms_template = str(sms_template[0])
            if sms_template and rec.partnername.mobile:
                user_key = str(conf.get_param('sms_gateway.user_key')),
                user_key = str(user_key[0])
                pass_key = str(conf.get_param('sms_gateway.pass_key')),
                pass_key = str(pass_key[0])
                send_sms_api = str(conf.get_param('sms_gateway.send_sms_api')),
                send_sms_api = str(send_sms_api[0])

                create_date = rec.create_date
                DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
                date_field1 = datetime.datetime.strptime(create_date, DATETIME_FORMAT)
                create_date = date_field1 + datetime.timedelta(hours=7)

                isi_pesan = sms_template.format(customer=str(rec.partnername.name), shippment_number=str(rec.scan_line_stockpicking_id.name), schedule_date=str(create_date))
                url = send_sms_api.format(user_key=str(user_key), pass_key=str(pass_key), phone=str(rec.partnername.mobile), message=str(isi_pesan))
                response = requests.get(url)
                content = et.fromstring(response.content)
                message = content.find("message")
                text = message.find("text").text
                if text == "Success":
                    message_id = message.find("messageId").text
                    to = message.find("to").text
                    status = message.find("status").text
                    sms_log = self.env['res.sms.gateway.log']
                    sms_log.create({'sending_status': 'Sent', 'message_id': message_id, 'to': to, 'source_document':rec.scan_line_stockpicking_id.name, 'message':isi_pesan, 'text':text})
                else:
                    sms_log = self.env['res.sms.gateway.log']
                    sms_log.create({'sending_status': 'Error', 'source_document':rec.scan_line_stockpicking_id.name, 'message':isi_pesan})

        if rec.state == 'takeaway':
            _logger.info('take_away')
            conf = self.env['ir.config_parameter']
            sms_template = str(conf.get_param('sms_gateway.take_away_sms_template')),
            sms_template = str(sms_template[0])
            if sms_template and rec.partnername.mobile:
                user_key = str(conf.get_param('sms_gateway.user_key')),
                user_key = str(user_key[0])
                pass_key = str(conf.get_param('sms_gateway.pass_key')),
                pass_key = str(pass_key[0])
                send_sms_api = str(conf.get_param('sms_gateway.send_sms_api')),
                send_sms_api = str(send_sms_api[0])

                create_date = rec.create_date
                DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
                date_field1 = datetime.datetime.strptime(create_date, DATETIME_FORMAT)
                create_date = date_field1 + datetime.timedelta(hours=7)

                isi_pesan = sms_template.format(customer=str(rec.partnername.name), shippment_number=str(rec.scan_line_stockpicking_id.name), schedule_date=str(create_date))
                url = send_sms_api.format(user_key=str(user_key), pass_key=str(pass_key), phone=str(rec.partnername.mobile), message=str(isi_pesan))
                response = requests.get(url)
                content = et.fromstring(response.content)
                message = content.find("message")
                text = message.find("text").text
                if text == "Success":
                    message_id = message.find("messageId").text
                    to = message.find("to").text
                    status = message.find("status").text
                    sms_log = self.env['res.sms.gateway.log']
                    sms_log.create({'sending_status': 'Sent', 'message_id': message_id, 'to': to, 'source_document':rec.scan_line_stockpicking_id.name, 'message':isi_pesan, 'text':text})
                else:
                    sms_log = self.env['res.sms.gateway.log']
                    sms_log.create({'sending_status': 'Error', 'source_document':rec.scan_line_stockpicking_id.name, 'message':isi_pesan})

        if rec.state == 'arrival_true':
            _logger.info('take_away')
            conf = self.env['ir.config_parameter']
            sms_template = str(conf.get_param('sms_gateway.arrival_true_sms_template')),
            sms_template = str(sms_template[0])
            if sms_template and rec.partnername.mobile:
                user_key = str(conf.get_param('sms_gateway.user_key')),
                user_key = str(user_key[0])
                pass_key = str(conf.get_param('sms_gateway.pass_key')),
                pass_key = str(pass_key[0])
                send_sms_api = str(conf.get_param('sms_gateway.send_sms_api')),
                send_sms_api = str(send_sms_api[0])

                create_date = rec.create_date
                DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
                date_field1 = datetime.datetime.strptime(create_date, DATETIME_FORMAT)
                create_date = date_field1 + datetime.timedelta(hours=7)

                isi_pesan = sms_template.format(customer=str(rec.partnername.name), shippment_number=str(rec.scan_line_stockpicking_id.name), schedule_date=str(create_date))
                url = send_sms_api.format(user_key=str(user_key), pass_key=str(pass_key), phone=str(rec.partnername.mobile), message=str(isi_pesan))
                response = requests.get(url)
                content = et.fromstring(response.content)
                message = content.find("message")
                text = message.find("text").text
                if text == "Success":
                    message_id = message.find("messageId").text
                    to = message.find("to").text
                    status = message.find("status").text
                    sms_log = self.env['res.sms.gateway.log']
                    sms_log.create({'sending_status': 'Sent', 'message_id': message_id, 'to': to, 'source_document':rec.scan_line_stockpicking_id.name, 'message':isi_pesan, 'text':text})
                else:
                    sms_log = self.env['res.sms.gateway.log']
                    sms_log.create({'sending_status': 'Error', 'source_document':rec.scan_line_stockpicking_id.name, 'message':isi_pesan})

        return rec