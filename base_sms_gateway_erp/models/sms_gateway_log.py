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
from babel.numbers import format_currency


_logger = logging.getLogger(__name__)


class BaseSmsGatewayLog(models.Model):
    '''SMS Gateway object'''

    _name = "res.sms.gateway.log"
    _description = "SMS Gateway Log object"
    _order = "message_id asc"    

    display_name = fields.Char('Name', compute='_get_display_name', store=True)
    message_id = fields.Char('Message ID')
    message = fields.Text('Message')
    to = fields.Char('Nomor tujuan')
    text = fields.Char('Keterangan')
    source_document = fields.Char('Source Document')
    sending_status = fields.Selection([
        ('Sent', "Sent"),
        ('Sending', "Sending"),
        ('Error', "Error"),
    ], default='Sending')
    

    @api.model
    def action_send_notif_sms(self):
        today = datetime.date.today()
        conf = self.env['ir.config_parameter']
        user_key = str(conf.get_param('sms_gateway.user_key')),
        user_key = str(user_key[0])

        pass_key = str(conf.get_param('sms_gateway.pass_key')),
        pass_key = str(pass_key[0])
        
        interval_number = str(conf.get_param('sms_gateway.interval_number')),
        interval_number = str(interval_number[0])

        interval_number = interval_number.split('&')

        repeat_interval_number = str(conf.get_param('sms_gateway.repeat_interval_number')),
        repeat_interval_number = int(repeat_interval_number[0])

        send_sms_api = str(conf.get_param('sms_gateway.send_sms_api')),
        send_sms_api = str(send_sms_api[0])
        invoice = self.env['account.invoice']
        invoice_obj = invoice.search([('partner_id.overdue_sms','=','sale'), ('state', '=', 'open'), ('due_date_sales', '<', datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')), ('type', '=', 'out_invoice'), ('giro_invoice_ids','=',False)])
        if invoice_obj:
            giro = 0
            for record in invoice_obj:
                for giro in record.giro_invoice_ids:
                    amount_allocated += giro.amount_allocated
                if ((record.residual - amount_allocated) > 0):
                    if record.due_date_sales and record.partner_id.mobile:
                        a = datetime.datetime.strptime(record.due_date_sales, '%Y-%m-%d %H:%M:%S')
                        b = datetime.datetime.strptime(str(today), '%Y-%m-%d')
                        c = b - a
                        
                        for day in interval_number:                        
                            if int(c.days) == int(day):
                                sms_template = str(conf.get_param('sms_gateway.payment_overdue_sms_template')),
                                sms_template = str(sms_template[0])

                                write_date = record.due_date_sales
                                DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
                                date_field1 = datetime.datetime.strptime(write_date, DATETIME_FORMAT)
                                write_date = date_field1 + datetime.timedelta(hours=7)

                                isi_pesan = sms_template.format(customer=str(record.partner_id.name), invoice_number=str(record.number), date_due=str(write_date), total=str(format_currency( record.residual - amount_allocated, 'IDR', locale='id_ID' )))
                                url = send_sms_api.format(user_key=str(user_key), pass_key=str(pass_key), phone=str(record.partner_id.mobile), message=str(isi_pesan))
                                response = requests.get(url)
                                content = et.fromstring(response.content)
                                message = content.find("message")
                                text = message.find("text").text
                                if text == "Success":
                                    message_id = message.find("messageId").text
                                    to = message.find("to").text
                                    status = message.find("status").text
                                    sms_log = self.env['res.sms.gateway.log']
                                    sms_log.create({'sending_status': 'Sent', 'message_id': message_id, 'to': to, 'source_document':record.number, 'message':isi_pesan, 'text':text})
                                else:
                                    sms_log = self.env['res.sms.gateway.log']
                                    sms_log.create({'sending_status': 'Error', 'source_document':record.number, 'message':isi_pesan})

                        if (int(c.days)%int(repeat_interval_number)) == 0:
                            sms_template = str(conf.get_param('sms_gateway.payment_overdue_sms_template')),
                            sms_template = str(sms_template[0])

                            write_date = record.due_date_sales
                            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
                            date_field1 = datetime.datetime.strptime(write_date, DATETIME_FORMAT)
                            write_date = date_field1 + datetime.timedelta(hours=7)

                            isi_pesan = sms_template.format(customer=str(record.partner_id.name), invoice_number=str(record.number), date_due=str(write_date), total=str(format_currency( record.residual - amount_allocated, 'IDR', locale='id_ID' )))
                            url = send_sms_api.format(user_key=str(user_key), pass_key=str(pass_key), phone=str(record.partner_id.mobile), message=str(isi_pesan))
                            response = requests.get(url)
                            content = et.fromstring(response.content)
                            message = content.find("message")
                            text = message.find("text").text
                            if text == "Success":
                                message_id = message.find("messageId").text
                                to = message.find("to").text
                                status = message.find("status").text
                                sms_log = self.env['res.sms.gateway.log']
                                sms_log.create({'sending_status': 'Sent', 'message_id': message_id, 'to': to, 'source_document':record.number, 'message':isi_pesan, 'text':text})
                            else:
                                sms_log = self.env['res.sms.gateway.log']
                                sms_log.create({'sending_status': 'Error', 'source_document':record.number, 'message':isi_pesan})
                        
                        
                    
            

    @api.multi
    def action_resend_sms(self):
        conf = self.env['ir.config_parameter']
        user_key = str(conf.get_param('sms_gateway.user_key')),
        user_key = str(user_key[0])

        pass_key = str(conf.get_param('sms_gateway.pass_key')),
        pass_key = str(pass_key[0])
        
        send_sms_api = str(conf.get_param('sms_gateway.send_sms_api')),
        send_sms_api = str(send_sms_api[0])

        isi_pesan = self.message
        url = send_sms_api.format(user_key=str(user_key), pass_key=str(pass_key), phone=str(self.to), message=str(isi_pesan))
        response = requests.get(url)
        content = et.fromstring(response.content)
        message = content.find("message")
        text = message.find("text").text
        if text == "Success":
            message_id = message.find("messageId").text
            to = message.find("to").text
            status = message.find("status").text
            sms_log = self.env['res.sms.gateway.log']
            sms_log.create({'sending_status': 'Sent', 'message_id': message_id, 'to': to, 'source_document':self.source_document, 'message':isi_pesan, 'text':text})
            self.write({'sending_status': 'Sent(Resend)'})
        else:
            sms_log = self.env['res.sms.gateway.log']
            sms_log.create({'sending_status': 'Error', 'source_document':self.source_document, 'message':isi_pesan})
            self.write({'sending_status': 'Error(Resend)'})