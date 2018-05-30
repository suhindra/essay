from openerp import models, api
from datetime import datetime
import time
from openerp import _
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.tools import float_is_zero
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)

class AgedProductXlsx(ReportXlsx):


    def get_productss(self, docs):
        cr = self.env.cr

        if docs['form'][0]['location_id'] and docs['form'][0]['product_categ']:
            cr.execute("select sq.id from stock_quant sq inner join product_product pp on(pp.id=sq.product_id) "
                       " inner join product_template pt on(pt.id=pp.product_tmpl_id and pt.categ_id in %s) "
                       "where sq.location_id in %s and sq.qty > 0 and sq.in_date <=%s", (tuple(docs['form'][0]['product_categ']),
                                                                     tuple(docs['form'][0]['location_id']), docs['form'][0]['from_date']))
        elif docs['form'][0]['location_id']:
            cr.execute("select sq.id from stock_quant sq where sq.location_id in %s and sq.qty > 0 and sq.in_date <=%s",
                       (tuple(docs['form'][0]['location_id']), docs['form'][0]['from_date']))
        elif docs['form'][0]['product_categ']:
            cr.execute("select sq.id from stock_quant sq inner join product_product pp on(pp.id=sq.product_id) "
                       " inner join product_template pt on(pt.id=pp.product_tmpl_id and pt.categ_id in %s)"
                       "where sq.qty > 0  and sq.in_date <=%s", (tuple(docs['form'][0]['product_categ']), docs['form'][0]['from_date']))
        else:
            cr.execute("select id from stock_quant where qty > 0  and in_date <=%s", (docs['form'][0]['from_date'],))
        quant_ids = cr.fetchall()
        quant_id = []
        for i in quant_ids:
            quant_id.append(i[0])
        rec = self.env['stock.quant'].browse(quant_id)
        products = {}
        product_list = []
        for i in rec:
            date1 = datetime.strptime(docs['form'][0]['from_date'], '%Y-%m-%d %H:%M:%S').date()
            if len(i.history_ids) == 1 and i.product_id.id not in product_list:
                product_list.append(i.product_id.id)
                temp = {
                    'product': i.product_id.name,
                    'total_qty': i.qty,
                    'location': i.location_id.name,
                }
                qty = [0, 0, 0, 0, 0]

                date2 = datetime.strptime(i.in_date, '%Y-%m-%d %H:%M:%S').date()
                no_days = (date1 - date2).days
                t1 = 0
                t2 = docs['form'][0]['interval']
                for j in range(0, 5):
                    if no_days >= 4 * docs['form'][0]['interval']:
                        qty[4] += i.qty
                        break
                    elif no_days in range(t1, t2):
                        qty[j] += i.qty
                        break

                    t1 = t2
                    t2 += docs['form'][0]['interval']
                temp['qty'] = qty
                products[i.product_id.id] = temp
            elif len(i.history_ids) == 1 and i.product_id.id in product_list:
                date2 = datetime.strptime(i.in_date, '%Y-%m-%d %H:%M:%S').date()
                no_days = (date1 - date2).days
                t1 = 0
                t2 = docs['form'][0]['interval']
                for j in range(0, 5):
                    if no_days >= 4 * docs['form'][0]['interval']:
                        products[i.product_id.id]['qty'][4] += i.qty
                        products[i.product_id.id]['total_qty'] += i.qty
                        break
                    elif no_days in range(t1, t2):
                        products[i.product_id.id]['qty'][j] += i.qty
                        products[i.product_id.id]['total_qty'] += i.qty
                        break

                    t1 = t2
                    t2 += docs['form'][0]['interval']
        return products

    def generate_xlsx_report(self, workbook, data, obj):
        
        currency = self.env.user.company_id.currency_id.symbol or ''
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 16, 'align': 'vcenter', 'bg_color': '#D3D3D3', 'bold': True})
        format1.set_font_color('#000080')
        format4 = workbook.add_format({'font_size': 12})
        format3 = workbook.add_format({'font_size': 10, 'bold': True})
        format4 = workbook.add_format({'font_size': 10})
        format5 = workbook.add_format({'font_size': 12, 'bold': True, 'bg_color': '#D3D3D3'})
        format1.set_align('center')
        format4.set_align('left')
        format3.set_align('left')
        format4.set_align('center')

        
        products = self.get_productss(data)
        _logger.info(products)
        row = 5
        col = 0
        start = 1
        sheet.merge_range('A2:J3', 'Stock Ageing Report', format1)
        row += 1
        sheet.merge_range(row, col, row, col+2, 'Tanggal Awal Perhitungan :', format4)
        sheet.merge_range(row, col+3, row, col+6, data['form'][0]['from_date'], format4)
        row += 1
        sheet.merge_range(row, col, row, col+2, 'Periode (hari) :', format4)
        sheet.merge_range(row, col+3, row, col+6, data['form'][0]['interval'], format4)
        
        row += 2
        # constructing the table
        sheet.write(row, col, "Products", format5)
        sheet.write(row, col+1, str(start) + " - " + str(int(data['form'][0]['interval'])), format5)
        sheet.write(row, col+2, str(int(data['form'][0]['interval'])+1) + " - " + str((int(data['form'][0]['interval']) * 2)), format5)
        sheet.write(row, col+3, str((int(data['form'][0]['interval']) * 2 )+1) + " - " + str((int(data['form'][0]['interval']) * 3)), format5)
        sheet.write(row, col+4, " < " + str((int(data['form'][0]['interval']) * 3)), format5)
        sheet.write(row, col+5, "Total", format5)
        sheet.write(row, col+6, "Location", format5)
        row += 1
        _logger.info(type(products))


        for item in products:
            sheet.write(row, col, products[item]['product'] or '-',format4)
            sheet.write(row, col+1, products[item]['qty'][1] or '-',format4)
            sheet.write(row, col+2, products[item]['qty'][2] or '-',format4)
            sheet.write(row, col+3, products[item]['qty'][3] or '-',format4)
            sheet.write(row, col+4, products[item]['qty'][4] or '-',format4)
            sheet.write(row, col+5, products[item]['total_qty'] or '-',format4)
            sheet.write(row, col+6, products[item]['location'] or '-',format4)
            row += 1
    
       

AgedProductXlsx('report.product_ageing_report.report_ageing_analysis',
                 'stock.quant')
