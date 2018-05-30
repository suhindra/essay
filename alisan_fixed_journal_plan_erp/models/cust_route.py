from openerp import api, fields, models, _

class cust_route(models.Model): 
    _name = 'fjp.route'
    _description = "Rute Kunjungan"
    _rec_name = 'route_code'
  
    route_code = fields.Char(string="Rute Code",required=True)
    salesperson_id = fields.Many2one('hr.employee', string='Duta Alisan', required=True)
    description = fields.Char(
                     string="Deskripsi Rute Kunjungan",)
        
    
class cust_partner(models.Model): 
    _inherit = 'res.partner'
    
    route_id = fields.Many2one('fjp.route', 'Rute Kunjungan')

    
