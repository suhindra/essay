# coding: utf-8
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from datetime import timedelta
from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    credit_limit_approve_amount = fields.Integer(string="Approve Credit Overloaded (%)")
    overdue_credit_approve = fields.Boolean(string="Approve Late Payment")
    recommend = fields.Boolean(string="Recommend SO")

