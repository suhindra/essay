# -*- coding: utf-8 -*-

from openerp import models, fields, api

class SmsGatewayCheckStatus(models.Model):
    _name = 'sms.gateway.check.status'
    name = fields.Char(required=True)
    numberOfUpdates = fields.Integer('Number of updates', help='The number of times the scheduler has run and updated this field')
    lastModified = fields.Date('Last updated')
