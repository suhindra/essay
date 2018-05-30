from openerp import models, fields, api


class AlisanCity(models.Model):
    '''City/locations completion object'''

    _name = "res.alisan.city"
    _description = __doc__
    _order = "name asc"
    _rec_name = "display_name"

    display_name = fields.Char('Name', compute='_get_display_name', store=True)
    name = fields.Char('City Name', required=True)
    code = fields.Char('City Code', size=64,
                       help="The official code for the city")
    state_id = fields.Many2one('res.country.state', 'State', required=True)

    @api.one
    @api.depends(
        'name')
    def _get_display_name(self):
        if self.name:
            name = self.name
        self.display_name = name