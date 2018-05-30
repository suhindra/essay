from openerp import models, fields, api
from openerp import tools
import openerp.addons.decimal_precision as dp
import time
import logging
from openerp.tools.translate import _
from openerp import netsvc
import datetime
from openerp.exceptions import UserError
from lxml import etree
import requests
import xml.etree.ElementTree as et

_logger = logging.getLogger(__name__)
STATES = [('open', 'Open'), ('close', 'Success'), ('error', 'Error')]


class alisan_sms_blast(models.Model):
    _name = 'alisan.sms.blast'
    _rec_name = 'name'
    _description = 'Alisan Sms Blast'

    name = fields.Char(string="Name")
    alisan_sms_blast_line = fields.One2many('alisan.sms.blast.line', 'alisan_sms_blast_id')    
    text = fields.Text(string="Text", required=True)   

    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}
        default['name'] = '/'
        return super(alisan_sms_blast, self).copy(default=default)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('alisan.sms.blast')
        return super(alisan_sms_blast, self).create(vals) 

    
    @api.multi
    def action_send(self):
    	conf = self.env['ir.config_parameter']
        user_key = str(conf.get_param('sms_gateway.user_key')),
        user_key = str(user_key[0])
        pass_key = str(conf.get_param('sms_gateway.pass_key')),
        pass_key = str(pass_key[0])
        send_sms_api = str(conf.get_param('sms_gateway.send_sms_api')),
        send_sms_api = str(send_sms_api[0])

        
        for x in self.alisan_sms_blast_line:
        	if x.state != 'close':
				isi_pesan = self.text
				url = send_sms_api.format(user_key=str(user_key), pass_key=str(pass_key), phone=str(x.partner_id.mobile), message=str(isi_pesan))
				_logger.info(url)
				response = requests.get(url)
				content = et.fromstring(response.content)
				message = content.find("message")
				text = message.find("text").text
				if text == "Success":
					x.state = 'close'
				else:
					x.state = 'error'
    
    @api.multi
    def action_get_customer(self):
        cst_list = self.env["res.partner"].search([("mobile", "!=", False), ("customer", "=", True), ("active", "=", True)])
        _logger.info(cst_list)
        lines =[]
        if cst_list:
            for val in cst_list:
                line_item = {
                              'state': 'open',
                              'partner_id': val.id,
                        }
                lines += [line_item]
        self.update({'alisan_sms_blast_line': lines})



class alisan_sms_blast_line(models.Model):
    _name = 'alisan.sms.blast.line'
    _description = 'alisan_sms_blast_line'
    
    alisan_sms_blast_id = fields.Many2one('alisan.sms.blast', 'Alisan Sms Blast', help='',readonly=True)
    state = fields.Selection(string="State", selection=STATES, required=True, default="draft")
    partner_id = fields.Many2one('res.partner','Customer', help='Customer',readonly=True)
    

    @api.multi
    def compute_total(self):
        for x in self:
            for item in x.invoice_id:
                delta = datetime.datetime.today() - datetime.datetime.strptime(item.date_due, '%Y-%m-%d')
                if (delta.days < 0) or (x.invoice_residual == 0):
                    x.days_due = 0
                else:    
                    x.days_due = delta.days


   