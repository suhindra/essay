from openerp import models, fields


class ResAlisanCity(models.Model):

    _inherit = 'res.alisan.city'

    alisan_subdistrict_ids = fields.One2many('res.alisan.subdistrict', 'city_id', 'Subdistricts')
