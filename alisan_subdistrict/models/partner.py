from openerp import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    subdistrict_id = fields.Many2one('res.alisan.subdistrict', 'Kecamatan')

    @api.one
    @api.onchange('subdistrict_id')
    def onchange_subdistrict_id(self):
        if self.subdistrict_id:
            self.zip = self.subdistrict_id.zip
            self.city = self.subdistrict_id.city_id.name
            self.city_id = self.subdistrict_id.city_id
            self.state_id = self.subdistrict_id.city_id.state_id
            self.country_id = self.subdistrict_id.city_id.state_id.country_id


   