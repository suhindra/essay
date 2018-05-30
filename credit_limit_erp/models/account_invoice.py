# coding: utf-8
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from openerp import models, api, fields, _ 
from openerp import exceptions
import datetime
import logging
_logger = logging.getLogger(__name__)

class AccontInvoice(models.Model):

    _inherit = 'account.invoice'

    over_due_age = fields.Integer(compute='_get_oldest_late_payment', string="Over Due Ages(Day(s))")

    @api.multi
    def check_limit_credit(self):
        for invoice in self:
            return True

    @api.multi
    def _get_oldest_late_payment(self):
        today = datetime.date.today()
        for invoice in self:
            invoice.over_due_age = ''
            format = '%Y-%m-%d'
            if invoice.date_due:                
                a = datetime.datetime.strptime(invoice.date_due, format)
                b = datetime.datetime.strptime(str(today), format)
                c = b - a
                if (b > a) and (invoice.state == 'open'):
                    invoice.over_due_age = int(c.days)
                else:
                    invoice.over_due_age = int(c.days)



