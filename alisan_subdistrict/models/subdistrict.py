# -*- coding: utf-8 -*-
#

from openerp import models, fields, api


class AlisanSubdistrict(models.Model):
    '''subdistrict completion object'''

    _name = "res.alisan.subdistrict"
    _description = __doc__
    _order = "name asc"
    _rec_name = "display_name"

    display_name = fields.Char('Name', compute='_get_display_name', store=True)
    name = fields.Char('Subdistrict Name', required=True)
    zip = fields.Char('ZIP', required=True)
    code = fields.Char('Subdistrict Code', size=64,
                       help="The official code for the Subdistrict")
    city_id = fields.Many2one('res.alisan.city', 'City', required=True)

    @api.one
    @api.depends(
        'name',)
    def _get_display_name(self):
        if self.name:
            name = self.name
        self.display_name = name