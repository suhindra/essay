from openerp import models, fields, api

class ResVoucher(models.Model):
    _inherit = 'res.voucher'

    sms_ids = fields.One2many(
        'res.sms.gateway.log',
        'voucher_number',
        'SMS History',
        readonly = True
    )