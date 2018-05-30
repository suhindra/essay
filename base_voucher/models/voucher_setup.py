# -*- coding: utf-8 -*-

from openerp import models, fields, api

class VoucherSetup(models.TransientModel):    
    _inherit = 'res.config.settings'
    _name = 'voucher.config.settings'

    backdate = fields.Integer()
    exp_due = fields.Integer()
    backdate_error = fields.Char('Invalid Barcode')
    inv_barcode = fields.Char('Invalid Barcode')
    already_scan_in = fields.Char('Barcode Telah di Scan Masuk')
    already_scan_out = fields.Char('Barcode Telah di Scan Keluar')
    notyet_scan_in = fields.Char('Barcode belum di Scan Masuk')
    required_barcode = fields.Char('Barcode belum di Scan Masuk')


    @api.model
    def get_default_voucher_exception(self, fields):
        conf = self.env['ir.config_parameter']
        return {
            'required_barcode': str(conf.get_param('voucher_exception.required_barcode')),
            'backdate_error': str(conf.get_param('voucher_exception.backdate_error')),
            'inv_barcode': str(conf.get_param('voucher_exception.inv_barcode')),
            'already_scan_in': str(conf.get_param('voucher_exception.already_scan_in')),
            'already_scan_out': str(conf.get_param('voucher_exception.already_scan_out')),
            'notyet_scan_in': str(conf.get_param('voucher_exception.notyet_scan_in')),
            'exp_due': int(conf.get_param('voucher_exception.exp_due')),
            'backdate': int(conf.get_param('voucher_exception.backdate')),
        }

    @api.one
    def set_voucher_exception(self):
        conf = self.env['ir.config_parameter']
        conf.set_param('voucher_exception.required_barcode', str(self.required_barcode))
        conf.set_param('voucher_exception.backdate_error', str(self.backdate_error))
        conf.set_param('voucher_exception.inv_barcode', str(self.inv_barcode))
        conf.set_param('voucher_exception.already_scan_in', str(self.already_scan_in))
        conf.set_param('voucher_exception.already_scan_out', str(self.already_scan_out))
        conf.set_param('voucher_exception.notyet_scan_in', str(self.notyet_scan_in))
        conf.set_param('voucher_exception.backdate', int(self.backdate))
        conf.set_param('voucher_exception.exp_due', int(self.exp_due))
