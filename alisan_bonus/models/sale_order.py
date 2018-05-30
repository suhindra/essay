from openerp import api, fields, models
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

 


