# -*- coding: utf-8 -*-
# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
import logging
_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
        _inherit = "sale.order.line"

        @api.multi
        def _get_delivered_qty(self):
                """Deduct moves marked to refund."""
                qty = super(SaleOrderLine, self)._get_delivered_qty()
                for move in self.procurement_ids.mapped('move_ids').filtered(
                                lambda r: (r.state == 'done' and
                                                     not r.scrapped and
                                                     r.location_dest_id.usage != "customer" and
                                                     r.to_refund_so)):
                        qty -= move.product_uom._compute_qty_obj(
                                move.product_uom, move.product_uom_qty, self.product_uom)
                return qty

        @api.multi
        def _compute_qty_returned(self):
            for line in self:
                qty = 0
                if line.qty_delivered > 0:
                    qty = line.product_uom_qty - line.qty_delivered
                line.qty_returned = qty

        @api.depends('order_id.name')
        def _compute_qty_refunded(self):
            for line in self:
                qty = 0.0
                inv_obj = line.order_id.mapped('invoice_ids')
                if inv_obj:
                    for inv_no in inv_obj:
                        inv_line_obj = (self.env["account.invoice.line"].search([("invoice_id","=",inv_no.id)]))
                        for inv_line in inv_line_obj:
                            inv_type = inv_line.invoice_id.type            
                            invl_q = inv_line.quantity
                            if (
                                (inv_type == 'out_invoice' and invl_q < 0.0) or
                                (inv_type == 'out_refund' and invl_q > 0.0)
                            ):
                                qty += inv_line.uom_id._compute_qty_obj(
                                    inv_line.uom_id, inv_line.quantity, line.product_uom)
                line.qty_refunded = qty

       


        qty_refunded = fields.Float(compute="_compute_qty_refunded",
                                string='Refunded Qty', copy=False, default=0.0)

        qty_returned = fields.Float(compute="_compute_qty_returned",string='Returned Qty', copy=False, default=0.0)
