# -*- coding: utf-8 -*-

import json
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp import api, fields, models, _
from openerp.tools import float_is_zero, float_compare
from openerp.tools.misc import formatLang

from openerp.exceptions import UserError, RedirectWarning, ValidationError

import openerp.addons.decimal_precision as dp

import logging

_logger = logging.getLogger(__name__)



class AccountInvoice(models.Model):
    _inherit = "account.invoice"


    @api.multi
    def invoice_validate(self):
        for invoice in self:
            #refuse to validate a vendor bill/refund if there already exists one with the same reference for the same partner,
            #because it's probably a double encoding of the same bill/refund
            so_obj = self.env['sale.order'].search([('name', '=', self.origin)])
            if so_obj.sales_type == 'normal':
                if invoice.type == 'out_invoice':
                    barcode_arrival = self.env['scan_line_salesshipment'].search([('scan_line_stockpicking_id.origin', '=', self.origin), ('state','=','arrival_true')])
                    barcode_takeaway = self.env['scan_line_salesshipment'].search([('scan_line_stockpicking_id.origin', '=', self.origin), ('state','=','takeaway')])
                    if barcode_arrival or barcode_takeaway:
                        pass
                    else:
                        raise UserError(_("Belum scan barcode terima atau take away"))
                        
            if invoice.type in ('in_invoice', 'in_refund') and invoice.reference:
                if self.search([('type', '=', invoice.type), ('reference', '=', invoice.reference), ('company_id', '=', invoice.company_id.id), ('commercial_partner_id', '=', invoice.commercial_partner_id.id), ('id', '!=', invoice.id)]):
                    raise UserError(_("Duplicated vendor reference detected. You probably encoded twice the same vendor bill/refund."))
        return self.write({'state': 'open'})
