# -*- coding: utf-8 -*-

from openerp import models, fields, api

class SmsGatewaySetup(models.TransientModel):    
    _inherit = 'res.config.settings'
    _name = 'sms.gateway.config.settings'

    
    sms_template = fields.Text('Template SMS')
    user_key = fields.Char('User Key')
    pass_key = fields.Char('Pass Key')
    send_sms_api = fields.Char('Send SMS API')
    status_sms_api = fields.Char('SMS Status API')
    credit_api = fields.Char('SMS Credit API')
    credit_status = fields.Char('Credit Status')
    active_status = fields.Char('Active Status')
    notification_number = fields.Char('SMS Status API')
    notification_text = fields.Text('SMS Status API')
    credit_limit = fields.Integer('SMS Status API')


    @api.model
    def get_default_sms_gateway_setup(self, fields):
        conf = self.env['ir.config_parameter']
        return {
            'credit_api': str(conf.get_param('sms_gateway.credit_api')),
            'credit_limit': int(conf.get_param('sms_gateway.credit_limit')),
            'notification_number': str(conf.get_param('sms_gateway.notification_number')),
            'notification_text': str(conf.get_param('sms_gateway.notification_text')),
            'sms_template': str(conf.get_param('sms_gateway.sms_template')),
            'user_key': str(conf.get_param('sms_gateway.user_key')),
            'pass_key': str(conf.get_param('sms_gateway.pass_key')),
            'send_sms_api': str(conf.get_param('sms_gateway.send_sms_api')),
            'status_sms_api': str(conf.get_param('sms_gateway.status_sms_api')),
        }

    @api.one
    def set_sms_gateway(self):
        conf = self.env['ir.config_parameter']
        conf.set_param('sms_gateway.credit_api', str(self.credit_api))
        conf.set_param('sms_gateway.credit_limit', int(self.credit_limit))
        conf.set_param('sms_gateway.notification_number', str(self.notification_number))
        conf.set_param('sms_gateway.notification_text', str(self.notification_text))
        conf.set_param('sms_gateway.sms_template', str(self.sms_template))
        conf.set_param('sms_gateway.user_key', str(self.user_key))
        conf.set_param('sms_gateway.pass_key', str(self.pass_key))
        conf.set_param('sms_gateway.send_sms_api', str(self.send_sms_api))
        conf.set_param('sms_gateway.status_sms_api', str(self.status_sms_api))
