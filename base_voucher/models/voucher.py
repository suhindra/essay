# -*- coding: utf-8 -*-
#

from openerp import models, fields, api
import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import ValidationError
from openerp.exceptions import Warning
import logging
from lxml import etree


_logger = logging.getLogger(__name__)


class BaseVoucher(models.Model):
    '''Voucher object'''

    _name = "res.voucher"
    _description = "Voucher object"
    _order = "voucher_number asc"
    _rec_name = "voucher_number"

    display_name = fields.Char('Name', compute='_get_display_name', store=True)
    barcode = fields.Char('Barcode')
    input_date = fields.Date('Tanggal Penerbitan')
    voucher_number = fields.Char('No. Voucher')
    cement_type = fields.Many2one('cement.type', 'Tipe Semen')
    factory = fields.Many2one('factory', 'Lokasi Pemuatan')
    web_order_number = fields.Char('No. Web Order')
    uom_id = fields.Many2one('product.uom', 'Standar Satuan')   
    customer_id = fields.Many2one('res.partner', 'Pelanggan', domain=[('customer', '=', True)])
    qty = fields.Integer('Jumlah')
    sales_id = fields.Many2one('res.users', 'Duta Alisan')
    exp_date = fields.Date('Tanggal Kadaluarsa', default=lambda self: self._get_exp_date())
    exp_date_hidden = fields.Date('Tanggal Kadaluarsa', readonly='True')
    backdate = fields.Integer('Backdate Tanggal Penerbitan')
    exp_due = fields.Integer('Expired date')
    warehouse_id = fields.Many2one('stock.warehouse', 'Cabang')
    plate_number = fields.Char('No. Plat')
    driver = fields.Char('Nama Supir')
    nav_integration = fields.Boolean('Nav Integration')
    load_status = fields.Selection([
        ('open', 'Open'), 
        ('in', 'Masuk Pemuatan'), 
        ('out', 'Keluar dari Pemuatan')
    ], 'Status Pemuatan', default='open', readonly='True')
    scan_ids = fields.One2many(
        'res.voucher.scan',
        'voucher_number',
        'Scan History',
        readonly = True
    )
    state = fields.Selection([
        ('draft', "Draft"),
        ('confirmed', "Released"),
        ('done', "Close"),
        ('exp', "Expired"),
        ('cancel', "Canceled"),
    ], default='draft')
    _defaults= {
    'input_date': lambda *a: datetime.datetime.today().strftime('%Y-%m-%d'),
    }

    _sql_constraints = [
        ('barcode_unique', 'unique(barcode)', 'Barcode telah digunakan!'),
        ('voucher_number_unique', 'unique(voucher_number)', 'No. Voucher telah digunakan!')
    ]

    @api.model
    def _get_exp_date(self):
        conf = self.env['ir.config_parameter']
        exp_due = int(conf.get_param('voucher_exception.exp_due')),
        exp_due = int(exp_due[0])
        exp_date = datetime.datetime.today() + datetime.timedelta(days=exp_due)
        return exp_date

    @api.one
    @api.constrains('qty')
    def _check_values(self):
        if self.qty == 0:
            raise Warning('Jumlah Muatan Tidak Bisa "0" ')

    @api.one
    @api.constrains('input_date')
    def _check_due_date(self):
        conf = self.env['ir.config_parameter']
        exp_due = int(conf.get_param('voucher_exception.exp_due')),
        backdate = int(conf.get_param('voucher_exception.backdate')),
        backdate_error = str(conf.get_param('voucher_exception.backdate_error')),
        exp_due = int(exp_due[0])
        backdate = int(backdate[0])
        backdate_error = str(backdate_error[0])
        backdate_date = datetime.datetime.now() - datetime.timedelta(days=backdate)
        if  (   
                datetime.datetime.strptime(self.input_date, DEFAULT_SERVER_DATE_FORMAT).date() > datetime.datetime.now().date()   or 
                datetime.datetime.strptime(self.input_date, DEFAULT_SERVER_DATE_FORMAT).date() < backdate_date.date()   
            ):
            raise ValidationError(backdate_error.format(kwarg=str(backdate)))
        else:

            date_1 = datetime.datetime.strptime(self.input_date, "%Y-%m-%d")
            exp_date = date_1 + datetime.timedelta(days=exp_due)
            vals = {'exp_date_hidden': exp_date}        
            return {'value': vals}    

    @api.onchange('cement_type')   
    def onchange_cement_type(self):
        self.uom_id = self.cement_type.uom_id.id
        
    @api.multi
    def action_confirm(self):
        if self.barcode:
            self.write({'state': 'confirmed'})
        else:
            conf = self.env['ir.config_parameter']
            required_barcode = str(conf.get_param('voucher_exception.required_barcode')),
            required_barcode = str(required_barcode[0])
            raise ValidationError(required_barcode)

    @api.multi
    def action_cancel(self):
        if self.load_status != 'out':
            self.write({'state': 'cancel'})
        else:
            raise ValidationError('Tidak bisa membatalkan Scan Keluar')
    
    @api.multi
    def action_draft(self):
        for line in self.scan_ids:
            line.unlink()
        self.write({'state': 'draft'})

    @api.multi
    def action_done(self):
        self.write({'state': 'done'})

    @api.onchange('warehouse_id')
    def _onchange_warehouse(self):
        res = {}
        if self.warehouse_id:
            usr_id = []
            team_id = []
            a = []
            warehouse = self.warehouse_id.id
            team_obj = self.env['crm.team'].search([('default_warehouse','=',warehouse)])
            for team in team_obj:
                user_obj = self.env['crm.team'].search([('id','=',team.id)]).member_ids
                for user in user_obj:
                    e = user.id
                    usr_id.append(e)

            usr_id = list(set(usr_id))
            res = {
                   'domain': {'sales_id': [('id', 'in', usr_id)]},
            } 
            
        else:
            res = {
                    'domain': {},
            }
        return res 

    @api.one
    def copy(self, default=None):
        default = dict(default or {})
        default.update({
        'barcode': False,'voucher_number': '','web_order_number': '','load_status':'open'
        })
        return super(BaseVoucher, self).copy(default) 

    @api.multi
    def unlink(self):
        for voucher in self:
            if voucher.state not in ('draft'):
               raise Warning('Tidak bisa menghapus voucher jika tidak pada status draft')
        return models.Model.unlink(self)
