# -*- coding: utf-8 -*-
#

from openerp import models, fields, api
import datetime


class CementType(models.Model):
    '''vehicle completion object'''

    _name = "cement.type"
    _description = __doc__
    _order = "name asc"
    _rec_name = "name"

    name = fields.Char('Tipe Semen', required=True)
    uom_id = fields.Many2one('product.uom', 'Standar Satuan')
