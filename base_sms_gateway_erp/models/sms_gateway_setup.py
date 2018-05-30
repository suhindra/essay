# -*- coding: utf-8 -*-

from openerp import models, fields, api

class SmsGatewaySetup(models.TransientModel):    
    _inherit = 'res.config.settings'
    _name = 'sms.gateway.config.settings'

    
    ordered_sms_template = fields.Text('Ordered SMS Template')
    delivery_sms_template = fields.Text('On Delivery SMS Template')
    take_away_sms_template = fields.Text('On Take Away SMS Template')
    arrival_true_sms_template = fields.Text('On Delivery Arrived SMS Template')
    invoiced_sms_template = fields.Text('Invoiced SMS Template')
    shipped_sms_template = fields.Text('Shippped SMS Template')
    payment_overdue_sms_template = fields.Text('Payment Overdue Template')
    user_key = fields.Char('User Key')
    pass_key = fields.Char('Pass Key')
    interval_number = fields.Char('Interval Number')
    repeat_interval_number = fields.Char('Repeat Interval Number')
    send_sms_api = fields.Char('Send SMS API')
    send_ordered = fields.Boolean('Sent a Sale Order Notification')
    send_invoiced = fields.Boolean('Sent a Invoice Notification')
    send_shipped = fields.Boolean('Sent a Shipppement Notification')


    @api.model
    def get_default_sms_gateway_setup(self, fields):
        conf = self.env['ir.config_parameter']
        return {
            'send_sms_api': str(conf.get_param('sms_gateway.send_sms_api')),
            'repeat_interval_number': str(conf.get_param('sms_gateway.repeat_interval_number')),
            'interval_number': str(conf.get_param('sms_gateway.interval_number')),
            'payment_overdue_sms_template': str(conf.get_param('sms_gateway.payment_overdue_sms_template')),
            'delivery_sms_template': str(conf.get_param('sms_gateway.delivery_sms_template')),
            'take_away_sms_template': str(conf.get_param('sms_gateway.take_away_sms_template')),
            'arrival_true_sms_template': str(conf.get_param('sms_gateway.arrival_true_sms_template')),
            'ordered_sms_template': str(conf.get_param('sms_gateway.ordered_sms_template')),
            'invoiced_sms_template': str(conf.get_param('sms_gateway.invoiced_sms_template')),
            'shipped_sms_template': str(conf.get_param('sms_gateway.shipped_sms_template')),
            'user_key': str(conf.get_param('sms_gateway.user_key')),
            'pass_key': str(conf.get_param('sms_gateway.pass_key')),
            'send_ordered': bool(conf.get_param('sms_gateway.send_ordered')),
            'send_invoiced': bool(conf.get_param('sms_gateway.send_invoiced')),
            'send_shipped': bool(conf.get_param('sms_gateway.send_shipped')),
        }

    @api.one
    def set_sms_gateway(self):
        conf = self.env['ir.config_parameter']
        conf.set_param('sms_gateway.send_sms_api', str(self.send_sms_api))
        conf.set_param('sms_gateway.repeat_interval_number', str(self.repeat_interval_number))
        conf.set_param('sms_gateway.interval_number', str(self.interval_number))
        conf.set_param('sms_gateway.payment_overdue_sms_template', str(self.payment_overdue_sms_template))
        conf.set_param('sms_gateway.delivery_sms_template', str(self.delivery_sms_template))
        conf.set_param('sms_gateway.take_away_sms_template', str(self.take_away_sms_template))
        conf.set_param('sms_gateway.arrival_true_sms_template', str(self.arrival_true_sms_template))
        conf.set_param('sms_gateway.ordered_sms_template', str(self.ordered_sms_template))
        conf.set_param('sms_gateway.invoiced_sms_template', str(self.invoiced_sms_template))
        conf.set_param('sms_gateway.shipped_sms_template', str(self.shipped_sms_template))
        conf.set_param('sms_gateway.user_key', str(self.user_key))
        conf.set_param('sms_gateway.pass_key', str(self.pass_key))
        conf.set_param('sms_gateway.send_ordered', bool(self.send_ordered))
        conf.set_param('sms_gateway.send_invoiced', bool(self.send_invoiced))
        conf.set_param('sms_gateway.send_shipped', bool(self.send_shipped))
