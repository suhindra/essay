# coding: utf-8
# Copyright 2016 Vauxoo (https://www.vauxoo.com) <info@vauxoo.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from openerp import models, fields, api, _
from openerp import exceptions


class ProductCategory(models.Model):
    _inherit = 'product.category'

    due_date = fields.Integer('due date')

