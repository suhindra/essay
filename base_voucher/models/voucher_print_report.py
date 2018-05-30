# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError

class VoucherPrintReport(models.TransientModel):    
    _inherit = 'res.config.settings'
    _name = 'voucher.print.report'

    customer_id = fields.Many2one('res.partner', 'Pelanggan', domain=[('customer', '=', True)])
    start_date = fields.Date('Tanggal Awal', required="True")
    end_date = fields.Date('Tanggal Akhir', required="True")

    @api.multi
    def render_html_voucher_report(self, data=None):
        if self.customer_id.id:
            _matching_obj = self.env['res.voucher'].search([('customer_id','=',self.customer_id.id),('input_date','>=',self.start_date),('input_date','<=',self.end_date)])
        else:
            _matching_obj = self.env['res.voucher'].search([('input_date','>=',self.start_date),('input_date','<=',self.end_date)])
        if _matching_obj:
            report_obj = self.env['report']
            return report_obj.get_action(_matching_obj,'base_voucher.voucher_report_template')
        else:
            False

    @api.multi
    def render_pdf_voucher_report(self, data=None):
        if self.customer_id.id:
            _matching_obj = self.env['res.voucher'].search([('customer_id','=',self.customer_id.id),('input_date','>=',self.start_date),('input_date','<=',self.end_date)])
        else:
            _matching_obj = self.env['res.voucher'].search([('input_date','>=',self.start_date),('input_date','<=',self.end_date)])
        if _matching_obj:
            report_obj = self.env['report']
            return report_obj.get_action(_matching_obj,'base_voucher.voucher_report_pdf_template')
        else:
            False

    @api.one
    @api.constrains('customer_id', 'start_date', 'end_date')
    def _check_values(self):
        if self.customer_id.id:
            _matching_obj = self.env['res.voucher'].search([('customer_id','=',self.customer_id.id),('input_date','>=',self.start_date),('input_date','<=',self.end_date)])
            if _matching_obj:
                raise ValidationError('Record not found')