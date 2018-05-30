# -*- coding: utf-8 -*-
#

from openerp import models, fields, api
import datetime


class Factory(models.Model):
    '''Factory object'''

    _name = "factory"
    _description = __doc__
    _order = "name asc"
    _rec_name = "name"

    name = fields.Char('Pabrik', required=True)
    address = fields.Char('Alamat Pabrik')
    contact = fields.Char('Contact Person')
    description = fields.Char('Deskripsi')
    
