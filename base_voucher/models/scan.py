# -*- coding: utf-8 -*-
#

from openerp import models, fields, api
import datetime
import logging
from openerp.exceptions import ValidationError
import requests
import xml.etree.ElementTree as et

_logger = logging.getLogger(__name__)


class VoucherScan(models.Model):
    '''Voucher Scan object'''

    _name = "res.voucher.scan"
    _description = "Voucher Scan object"

    voucher_number = fields.Many2one(
        'res.voucher',
        'No. Voucher',
    )
    type = fields.Selection([
        ('in', "Masuk"),
        ('out', "Keluar"),
        ('cancel', 'Batal Muat')
    ], default='in')
    voucher_number_help = fields.Integer('help')
    web_order_number = fields.Char('No. Web Order')
    barcode = fields.Char('Barcode', store=False)
    customer_id = fields.Many2one('res.partner', 'Pelanggan', store=False)
    sales_id = fields.Many2one('res.users', 'Duta Alisan', store=False)
    warehouse_id = fields.Many2one('stock.warehouse', 'Cabang', store=False)
    cement_type = fields.Many2one('cement.type', 'Tipe Semen', store=False)
    uom_id = fields.Many2one('product.uom', 'Standar Satuan', store=False)
    qty = fields.Integer('Jumlah', store=False)
    input_date = fields.Date('Tanggal Penerbitan', store=False)
    exp_date = fields.Date('Tanggal Kadaluarsa', readonly=True, store=False)
    plate_number = fields.Char('No. Plat', required=True)
    driver = fields.Char('Nama Supir', required=True)
    plate_number_help = fields.Char('No. Plat', store=False)
    driver_help = fields.Char('Nama Supir', store=False)
    factory = fields.Many2one('factory', 'Lokasi Pemuatan', store=False)
    load_status = fields.Selection([
        ('open', 'Open'), 
        ('in', 'Masuk Pemuatan'), 
        ('out', 'Keluar dari Pemuatan')
    ], 'Status Pemuatan', store=False)
    state = fields.Selection([
        ('draft', "Draft"),
        ('confirmed', "Released"),
        ('done', "Close"),
        ('exp', "Expired"),
    ], store=False)
    scan_by = fields.Selection([
        ('dekstop', "Dekstop"),
        ('mobile', "Android"),
    ], default='dekstop')
    



    def onchange_in_barcode(self, cr, uid, ids, barcode, context=None):
        vals = {}
        barcode_obj = self.pool.get('res.voucher')
        _matching_barcode = barcode_obj.search(cr, uid, [('barcode', '=ilike', barcode),('state', '=', 'confirmed'),('load_status', '=', 'open')], context=context)

        if _matching_barcode:
            _matching_obj = barcode_obj.browse(cr, uid, _matching_barcode[0], context=context)
            vals = {
                'value': { 
                    'voucher_number': _matching_obj.id,  
                    'web_order_number': _matching_obj.web_order_number,  
                    'customer_id': _matching_obj.customer_id,  
                    'sales_id': _matching_obj.sales_id,  
                    'cement_type': _matching_obj.cement_type,  
                    'uom_id': _matching_obj.uom_id,  
                    'qty': _matching_obj.qty,
                    'input_date': _matching_obj.input_date,                
                    'exp_date': _matching_obj.exp_date,                
                    'load_status': _matching_obj.load_status,
                    'warehouse_id': _matching_obj.warehouse_id,
                    'voucher_number_help': _matching_obj.id, 
                    'plate_number': _matching_obj.plate_number,
                    'driver': _matching_obj.driver,
                    'plate_number_help': _matching_obj.plate_number,
                    'driver_help': _matching_obj.driver,
                    'factory': _matching_obj.factory,
                }
            }
            

        else:
            vals = {
                'value': { 
                    'voucher_number': '',  
                    'web_order_number': '',  
                    'customer_id': '',  
                    'sales_id': '',  
                    'cement_type': '',  
                    'uom_id': '',  
                    'qty': '',
                    'input_date': '',
                    'exp_date': '',
                    'load_status': '',
                    'barcode': '',
                    'warehouse_id': '',
                    'voucher_number_help': '', 
                    'plate_number': '',
                    'driver': '',
                    'plate_number_help': '',
                    'driver_help': '',
                    'factory': '',
                },
                'warning': {
                    'title': 'Barcode',
                    'message': 'Data Tidak Ditemukan',
                }
            }

        return vals

    @api.multi
    def action_confirm_scan_in(self):
        new_driver=self.driver
        new_plate_number = self.plate_number
        new_web_order_number = self.web_order_number
        new_voucher_number = self.voucher_number_help
        voucher_obj = self.env['res.voucher'].search([('id', '=', new_voucher_number),('state', '=', 'confirmed'),('load_status', '=', 'open')])
        if  voucher_obj:
            for record in voucher_obj:
                record.write({'load_status': 'in', 'driver':new_driver, 'web_order_number':new_web_order_number, 'plate_number':new_plate_number})
            scan_obj = self.env['res.voucher.scan']
            scan_obj.create({'voucher_number': new_voucher_number, 'type': 'in', 'scan_by': 'dekstop', 'driver':new_driver})
            barcode_obj = self.env['res.voucher']
            _matching_obj = barcode_obj.search([('id', '=', self.voucher_number_help)])
            report_obj = self.env['report']
            return report_obj.get_action(_matching_obj,'base_voucher.voucher_validation_report_template')

    def action_scan_in(self, cr, uid, ids, context=None):
        context = context or {}
        scan_obj = self.browse(cr, uid, ids[0], context)
        new_barcode=scan_obj.barcode
        new_driver=scan_obj.driver
        new_web_order_number=scan_obj.web_order_number
        new_plate_number=scan_obj.plate_number
        new_voucher_number = scan_obj.voucher_number_help
        _matching_barcode = self.pool.get('res.voucher.scan').search(cr, uid, [('voucher_number','=', new_voucher_number),('type', '=', 'in')], context=context)
        if _matching_barcode:
            _matching_cancel_barcode = self.pool.get('res.voucher.scan').search(cr, uid, [('voucher_number','=', new_voucher_number),('type', '=', 'cancel')], context=context)
            if _matching_cancel_barcode:
                scan_obj.create({'voucher_number': new_voucher_number, 'type': 'in', 'driver':new_driver})
                voucher_obj = self.pool.get('res.voucher')
                voucher_obj.write(cr, uid, [new_voucher_number], {'load_status': 'in', 'driver':new_driver, 'web_order_number':new_web_order_number, 'plate_number':new_plate_number}, context=context)
            else:
                raise ValidationError("Barcode %s Sudah di scan Masuk" %new_voucher_number)
                return False



    def onchange_out_barcode(self, cr, uid, ids, barcode, context=None):
        vals = {}
        barcode_obj = self.pool.get('res.voucher')
        _matching_barcode = barcode_obj.search(cr, uid, [('barcode', '=ilike', barcode),('state', '=', 'confirmed'),('load_status', '=', 'in')], context=context)

        if _matching_barcode:

            _matching_obj = barcode_obj.browse(cr, uid, _matching_barcode[0], context=context)
            vals = {
                'value': { 
                    'voucher_number': _matching_obj.id,  
                    'web_order_number': _matching_obj.web_order_number,  
                    'customer_id': _matching_obj.customer_id,  
                    'sales_id': _matching_obj.sales_id,  
                    'cement_type': _matching_obj.cement_type,  
                    'uom_id': _matching_obj.uom_id,  
                    'qty': _matching_obj.qty,
                    'input_date': _matching_obj.input_date,                
                    'exp_date': _matching_obj.exp_date,                
                    'load_status': _matching_obj.load_status,
                    'warehouse_id': _matching_obj.warehouse_id,
                    'voucher_number_help': _matching_obj.id, 
                    'plate_number': _matching_obj.plate_number,
                    'driver': _matching_obj.driver,
                    'plate_number_help': _matching_obj.plate_number,
                    'driver_help': _matching_obj.driver,
                    'factory': _matching_obj.factory,

                }
            }

        else:
            vals = {
                'value': { 
                    'voucher_number': '',  
                    'web_order_number': '',  
                    'customer_id': '',  
                    'sales_id': '',  
                    'cement_type': '',  
                    'uom_id': '',  
                    'qty': '',
                    'input_date': '',
                    'exp_date': '',
                    'load_status': '',
                    'barcode': '',
                    'warehouse_id': '',
                    'voucher_number_help': '',
                    'plate_number': '',
                    'driver': '',
                    'factory': '',
                },
                'warning': {
                    'title': 'Barcode',
                    'message': 'Data Tidak Ditemukan',
                }
            }

        return vals

    def onchange_cancel_out_barcode(self, cr, uid, ids, barcode, context=None):
        vals = {}
        barcode_obj = self.pool.get('res.voucher')
        _matching_barcode = barcode_obj.search(cr, uid, [('barcode', '=ilike', barcode),('state', '=', 'confirmed'),('load_status', '=', 'in')], context=context)

        if _matching_barcode:

            _matching_obj = barcode_obj.browse(cr, uid, _matching_barcode[0], context=context)
            vals = {
                'value': { 
                    'voucher_number': _matching_obj.id,  
                    'web_order_number': _matching_obj.web_order_number,  
                    'customer_id': _matching_obj.customer_id,  
                    'sales_id': _matching_obj.sales_id,  
                    'cement_type': _matching_obj.cement_type,  
                    'uom_id': _matching_obj.uom_id,  
                    'qty': _matching_obj.qty,
                    'input_date': _matching_obj.input_date,                
                    'exp_date': _matching_obj.exp_date,                
                    'load_status': _matching_obj.load_status,
                    'warehouse_id': _matching_obj.warehouse_id,
                    'voucher_number_help': _matching_obj.id, 
                    'plate_number': _matching_obj.plate_number,
                    'driver': _matching_obj.driver,
                    'plate_number_help': _matching_obj.plate_number,
                    'driver_help': _matching_obj.driver,
                    'factory': _matching_obj.factory,

                }
            }

        else:
            vals = {
                'value': { 
                    'voucher_number': '',  
                    'web_order_number': '',  
                    'customer_id': '',  
                    'sales_id': '',  
                    'cement_type': '',  
                    'uom_id': '',  
                    'qty': '',
                    'input_date': '',
                    'exp_date': '',
                    'load_status': '',
                    'barcode': '',
                    'warehouse_id': '',
                    'voucher_number_help': '',
                    'plate_number': '',
                    'driver': '',
                    'factory': '',
                },
                'warning': {
                    'title': 'Barcode',
                    'message': 'Voucher Belum Scan Masuk Atau Sudah Scan Keluar',
                }
            }

        return vals

    @api.multi
    def action_scan_out(self):
        new_driver=self.driver
        new_plate_number=self.plate_number
        new_voucher_number = self.voucher_number_help
        _matching_barcode = self.env['res.voucher.scan'].search([('voucher_number','=', new_voucher_number),('type', '=', 'out')])
        if _matching_barcode:
            raise ValidationError("Barcode %s Sudah di scan Keluar")
            return False
        _matching_barcode.create({'voucher_number': new_voucher_number, 'type': 'out', 'driver':new_driver})

        barcode_obj = self.env['res.voucher']
        voucher_obj = barcode_obj.search([('id', '=', new_voucher_number)])
        if  voucher_obj:
            for record in voucher_obj:
                record.write({'load_status': 'out', 'state':'done'})

        _matching_obj = barcode_obj.browse(voucher_obj.id)
        
        customer = _matching_obj.customer_id.name
        no_voucher = _matching_obj.voucher_number
        scan_out_date = _matching_obj.write_date
        _logger.info(voucher_obj)
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        date_field1 = datetime.datetime.strptime(scan_out_date, DATETIME_FORMAT)
        scan_out_date = date_field1 + datetime.timedelta(hours=7)
        cement_type = _matching_obj.cement_type.name
        qty = _matching_obj.qty
        driver = _matching_obj.driver
        plate_number = _matching_obj.plate_number
        phone = _matching_obj.customer_id.mobile
        #phone = "082138036540"

        conf = self.env['ir.config_parameter']
        sms_template = str(conf.get_param('sms_gateway.sms_template')),
        sms_template = str(sms_template[0])

        user_key = str(conf.get_param('sms_gateway.user_key')),
        user_key = str(user_key[0])

        pass_key = str(conf.get_param('sms_gateway.pass_key')),
        pass_key = str(pass_key[0])

        send_sms_api = str(conf.get_param('sms_gateway.send_sms_api')),
        send_sms_api = str(send_sms_api[0])

        status_sms_api = str(conf.get_param('sms_gateway.status_sms_api')),
        status_sms_api = str(status_sms_api[0])

        #sms notifikation

        credit_api = str(conf.get_param('sms_gateway.credit_api')),
        credit_api = str(credit_api[0])

        credit_limit = int(conf.get_param('sms_gateway.credit_limit')),
        credit_limit = int(credit_limit[0])

        notification_number = str(conf.get_param('sms_gateway.notification_number')),
        notification_number = str(notification_number[0])

        notification_text = str(conf.get_param('sms_gateway.notification_text')),
        notification_text = str(notification_text[0])

        isi_pesan = sms_template.format(customer=str(customer), no_voucher=str(no_voucher), scan_out_date=str(scan_out_date), cement_type=str(cement_type), qty=str(qty), driver=str(driver), plate_number=str(plate_number))

        url = send_sms_api.format(user_key=str(user_key), pass_key=str(pass_key), phone=str(phone), message=str(isi_pesan))
        
        response = requests.get(url)
        content = et.fromstring(response.content)
        message = content.find("message")
        text = message.find("text").text
        if text == "Success":
            message_id = message.find("messageId").text
            to = message.find("to").text
            status = message.find("status").text
            sms_log = self.env['res.sms.gateway.log']
            sms_log.create({'sending_status': 'Sending', 'message_id': message_id, 'to': to, 'voucher_number':new_voucher_number, 'message':isi_pesan, 'text':text})
        else:
            to = phone
            status = message.find("status").text
            sms_log = self.env['res.sms.gateway.log']
            sms_log.create({'sending_status': 'Error', 'to': to, 'voucher_number':new_voucher_number, 'message':isi_pesan, 'text':text})

        url_credit = credit_api.format(user_key=str(user_key), pass_key=str(pass_key), phone=str(phone))
        response_credit = requests.get(url_credit)
        content = et.fromstring(response_credit.content)
        credit = content.find("credit")
        value = credit.find("value").text
        value = int(value)
        _logger.warning(value)
        _logger.warning(credit_limit)
        if value < credit_limit:
            send_notif = send_sms_api.format(user_key=str(user_key), pass_key=str(pass_key), phone=str(notification_number), message=str(notification_text))
            response = requests.get(send_notif)
            content = et.fromstring(response.content)
            message = content.find("message")
            text = message.find("text").text
            if text == "Success":
                message_id = message.find("messageId").text
                to = message.find("to").text
                status = message.find("status").text
                sms_log = self.env['res.sms.gateway.log']
                sms_log.create({'sending_status': 'Sending', 'message_id': message_id, 'to': to, 'message':notification_text, 'text':text})
            else:
                to = phone
                status = message.find("status").text
                sms_log = self.env['res.sms.gateway.log']
                sms_log.create({'sending_status': 'Error', 'to': to,  'message':notification_text, 'text':text})

    @api.multi
    def action_scan_cancel_load(self):
        new_driver=self.driver
        new_plate_number=self.plate_number
        new_voucher_number = self.voucher_number_help
        _matching_barcode = self.env['res.voucher.scan'].search([('voucher_number','=', new_voucher_number),('type', '=', 'out')])
        if _matching_barcode:
            raise ValidationError("Barcode %s Sudah di scan Keluar")
            return False
        _matching_barcode.create({'voucher_number': new_voucher_number, 'type': 'cancel', 'driver':new_driver})

        barcode_obj = self.env['res.voucher']
        voucher_obj = barcode_obj.search([('id', '=', new_voucher_number)])
        if  voucher_obj:
            for record in voucher_obj:
                record.write({'load_status': 'open', 'state':'confirmed'})


    
    
    @api.model
    def action_scan(self, barcode, type):
        conf = self.env['ir.config_parameter']
        inv_barcode = str(conf.get_param('voucher_exception.inv_barcode')),
        inv_barcode = str(inv_barcode[0])
        vals = {
                'warning' : inv_barcode
        }
        if type == 'in':
            barcode_obj = self.env['res.voucher']
            _matching_barcode = barcode_obj.search([('barcode', '=ilike', barcode), ('state', '=', 'confirmed'), ('load_status', '=', 'open')])
            if _matching_barcode:
                _matching_obj = barcode_obj.browse(_matching_barcode.id)
                vals = {
                        'voucher_number': _matching_obj.voucher_number,
                        'web_order_number': _matching_obj.web_order_number,
                        'customer_id': _matching_obj.customer_id.name,
                        'sales_id': _matching_obj.sales_id.name,
                        'cement_type': _matching_obj.cement_type.name,
                        'uom_id': _matching_obj.uom_id.name,
                        'qty': _matching_obj.qty,
                        'input_date': _matching_obj.input_date,
                        'exp_date': _matching_obj.exp_date,
                        'load_status': _matching_obj.load_status,
                        'warehouse_id': _matching_obj.warehouse_id.name,
                        'voucher_number_help': _matching_obj.id,
                        'plate_number': _matching_obj.plate_number,
                        'driver': _matching_obj.driver,
                        'status':'true',
                    }
                
            else:
                _exceptions_obj = barcode_obj.search([('barcode', '=ilike', barcode), ('load_status', '=', 'in')])
                if _exceptions_obj:
                    _matching_obj = barcode_obj.browse(_exceptions_obj.id)
                    conf = self.env['ir.config_parameter']
                    already_scan_in = str(conf.get_param('voucher_exception.already_scan_in')),
                    already_scan_in = str(already_scan_in[0])
                    vals = {
                        'voucher_number': _matching_obj.voucher_number,
                        'web_order_number': _matching_obj.web_order_number,
                        'customer_id': _matching_obj.customer_id.name,
                        'sales_id': _matching_obj.sales_id.name,
                        'cement_type': _matching_obj.cement_type.name,
                        'uom_id': _matching_obj.uom_id.name,
                        'qty': _matching_obj.qty,
                        'input_date': _matching_obj.input_date,
                        'exp_date': _matching_obj.exp_date,
                        'load_status': _matching_obj.load_status,
                        'warehouse_id': _matching_obj.warehouse_id.name,
                        'voucher_number_help': _matching_obj.id,
                        'plate_number': _matching_obj.plate_number,
                        'driver': _matching_obj.driver,
                        'status':'false',
                        'warning' : already_scan_in.format(kwarg=str(barcode)),
                    }

        if type == 'out':
            barcode_obj = self.env['res.voucher']
            _matching_barcode = barcode_obj.search([('barcode', '=ilike', barcode), ('state', '=', 'confirmed'), ('load_status', '=', 'in')])
            _matching_open_barcode = barcode_obj.search([('barcode', '=ilike', barcode), ('state', '=', 'confirmed'), ('load_status', '=', 'open')])
            if _matching_barcode:
                _matching_obj = barcode_obj.browse(_matching_barcode.id)
                vals = {
                    'voucher_number': _matching_obj.voucher_number,
                    'web_order_number': _matching_obj.web_order_number,
                    'customer_id': _matching_obj.customer_id.name,
                    'sales_id': _matching_obj.sales_id.name,
                    'cement_type': _matching_obj.cement_type.name,
                    'uom_id': _matching_obj.uom_id.name,
                    'qty': _matching_obj.qty,
                    'input_date': _matching_obj.input_date,
                    'exp_date': _matching_obj.exp_date,
                    'load_status': _matching_obj.load_status,
                    'warehouse_id': _matching_obj.warehouse_id.name,
                    'voucher_number_help': _matching_obj.id,
                    'plate_number': _matching_obj.plate_number,
                    'driver': _matching_obj.driver,
                    'status':'True',
                    }
            elif _matching_open_barcode:
                conf = self.env['ir.config_parameter']
                notyet_scan_in = str(conf.get_param('voucher_exception.notyet_scan_in')),
                notyet_scan_in = str(notyet_scan_in[0])
                _matching_obj = barcode_obj.browse(_matching_open_barcode.id)
                vals = {
                    'voucher_number': _matching_obj.voucher_number,
                    'web_order_number': _matching_obj.web_order_number,
                    'customer_id': _matching_obj.customer_id.name,
                    'sales_id': _matching_obj.sales_id.name,
                    'cement_type': _matching_obj.cement_type.name,
                    'uom_id': _matching_obj.uom_id.name,
                    'qty': _matching_obj.qty,
                    'input_date': _matching_obj.input_date,
                    'exp_date': _matching_obj.exp_date,
                    'load_status': _matching_obj.load_status,
                    'warehouse_id': _matching_obj.warehouse_id.name,
                    'voucher_number_help': _matching_obj.id,
                    'plate_number': _matching_obj.plate_number,
                    'driver': _matching_obj.driver,
                    'status':'false',
                    'warning' : notyet_scan_in.format(kwarg=str(barcode)),
                }
            else:
                _exceptions_obj = barcode_obj.search([('barcode', '=ilike', barcode), ('load_status', '=', 'out')])
                if _exceptions_obj:
                    conf = self.env['ir.config_parameter']
                    already_scan_out = str(conf.get_param('voucher_exception.already_scan_out')),
                    already_scan_out = str(already_scan_out[0])
                    _matching_obj = barcode_obj.browse(_exceptions_obj.id)
                    vals = {
                        'voucher_number': _matching_obj.voucher_number,
                        'web_order_number': _matching_obj.web_order_number,
                        'customer_id': _matching_obj.customer_id.name,
                        'sales_id': _matching_obj.sales_id.name,
                        'cement_type': _matching_obj.cement_type.name,
                        'uom_id': _matching_obj.uom_id.name,
                        'qty': _matching_obj.qty,
                        'input_date': _matching_obj.input_date,
                        'exp_date': _matching_obj.exp_date,
                        'load_status': _matching_obj.load_status,
                        'warehouse_id': _matching_obj.warehouse_id.name,
                        'voucher_number_help': _matching_obj.id,
                        'plate_number': _matching_obj.plate_number,
                        'driver': _matching_obj.driver,
                        'status':'false',
                        'warning' : already_scan_out.format(kwarg=str(barcode)),
                    }

        return vals
    
    @api.model
    def validate_scan(self, id, voucher_number_help, barcode, type, plat_num, driver):
        vals = {}
        if type == 'in':
            voucher_obj = self.env['res.voucher'].search([('barcode', '=ilike', barcode), ('state', '=', 'confirmed'), ('load_status', '=', 'open')])
            if  voucher_obj:
                if plat_num != "" and driver != "":
                    for record in voucher_obj:
                        record.write({'load_status': 'in', 'driver':driver, 'plate_number':plat_num})
                    scan_obj = self.env['res.voucher.scan']
                    scan_obj.create({'barcode': barcode, 'voucher_number': voucher_number_help, 'type': 'in', 'driver':driver, 'plate_number':plat_num, 'scan_by': 'mobile'})
                    vals = {
                            'voucher_number': voucher_obj.voucher_number,
                            'web_order_number': voucher_obj.web_order_number,
                            'customer_id': voucher_obj.customer_id.name,
                            'sales_id': voucher_obj.sales_id.name,
                            'cement_type': voucher_obj.cement_type.name,
                            'uom_id': voucher_obj.uom_id.name,
                            'qty': voucher_obj.qty,
                            'input_date': voucher_obj.input_date,
                            'exp_date': voucher_obj.exp_date,
                            'load_status': voucher_obj.load_status,
                            'warehouse_id': voucher_obj.warehouse_id.name,
                            'voucher_number_help': voucher_obj.id,
                            'plate_number': voucher_obj.plate_number,
                            'driver': voucher_obj.driver,
                            'status':'True',
                        }
                else:
                    vals = {
                            'voucher_number': voucher_obj.voucher_number,
                            'web_order_number': voucher_obj.web_order_number,
                            'customer_id': voucher_obj.customer_id.name,
                            'sales_id': voucher_obj.sales_id.name,
                            'cement_type': voucher_obj.cement_type.name,
                            'uom_id': voucher_obj.uom_id.name,
                            'qty': voucher_obj.qty,
                            'input_date': voucher_obj.input_date,
                            'exp_date': voucher_obj.exp_date,
                            'load_status': voucher_obj.load_status,
                            'warehouse_id': voucher_obj.warehouse_id.name,
                            'voucher_number_help': voucher_obj.id,
                            'plate_number': voucher_obj.plate_number,
                            'driver': voucher_obj.driver,
                            'status':'False',
                            'warning' : 'Data Kendaraan Harus Diisi!!',
                        }
 
        if type == 'out':
            voucher_obj = self.env['res.voucher'].search([('barcode', '=ilike', barcode), ('state', '=', 'confirmed'), ('load_status', '=', 'in')])
            for record in voucher_obj:
                record.write({'load_status': 'out', 'state': 'done'})
            scan_obj = self.env['res.voucher.scan']
            scan_obj.create({'barcode': barcode, 'voucher_number': voucher_number_help, 'type': 'out', 'driver':driver, 'plate_number':plat_num, 'scan_by': 'mobile'})
            vals = {
                            'voucher_number': voucher_obj.voucher_number,
                            'web_order_number': voucher_obj.web_order_number,
                            'customer_id': voucher_obj.customer_id.name,
                            'sales_id': voucher_obj.sales_id.name,
                            'cement_type': voucher_obj.cement_type.name,
                            'uom_id': voucher_obj.uom_id.name,
                            'qty': voucher_obj.qty,
                            'input_date': voucher_obj.input_date,
                            'exp_date': voucher_obj.exp_date,
                            'load_status': voucher_obj.load_status,
                            'warehouse_id': voucher_obj.warehouse_id.name,
                            'voucher_number_help': voucher_obj.id,
                            'plate_number': voucher_obj.plate_number,
                            'driver': voucher_obj.driver,
                            'status':'True',
                        }

        return vals