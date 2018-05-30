from openerp import models, fields

class tambah_overdue_sms(models.Model):
    _inherit = 'res.partner'
    _name = 'res.partner'
    
    overdue_sms = fields.Selection([
            ('sale', "Sale"),
            ('purchase', "Purchase")
        ])