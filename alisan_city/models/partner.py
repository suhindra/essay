from openerp import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    city_id = fields.Many2one('res.alisan.city', 'Kota/Kabupaten')

    @api.one
    @api.onchange('city_id')
    def onchange_city_id(self):
        if self.city_id:
            #self.zip = self.zip_id.name
            self.city = self.city_id.name
            self.state_id = self.city_id.state_id
            self.country_id = self.city_id.state_id.country_id

   