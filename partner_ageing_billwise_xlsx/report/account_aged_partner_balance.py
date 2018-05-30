# -*- coding: utf-8 -*-

import time
from datetime import datetime
from openerp import _
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.tools import float_is_zero
from dateutil.relativedelta import relativedelta


class AgedBillwiseXlsx(ReportXlsx):
    def _get_billwise_move_lines(self, account_type, date_from, target_move, period_length):
        periods = {}
        start = datetime.strptime(date_from, "%Y-%m-%d")
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            periods[str(i)] = {
                'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        res = []
        total = []
        cr = self.env.cr
        user_company = self.env.user.company_id.id
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type))
        #build the reconciliation clause to see what partner needs to be printed
        reconciliation_clause = '(l.reconciled IS FALSE)'
        cr.execute('SELECT debit_move_id, credit_move_id FROM account_partial_reconcile where create_date > %s', (date_from,))
        reconciled_after_date = []
        for row in cr.fetchall():
            reconciled_after_date += [row[0], row[1]]
        if reconciled_after_date:
            reconciliation_clause = '(l.reconciled IS FALSE OR l.id IN %s)'
            arg_list += (tuple(reconciled_after_date),)
        arg_list += (date_from, user_company)
        query = '''
            SELECT DISTINCT l.partner_id, UPPER(res_partner.name)
            FROM account_move_line AS l left join res_partner on l.partner_id = res_partner.id, account_account, account_move am
            WHERE (l.account_id = account_account.id)
                AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.internal_type IN %s)
                AND ''' + reconciliation_clause + '''
                AND (l.date <= %s)
                AND l.company_id = %s
            ORDER BY UPPER(res_partner.name)'''
        cr.execute(query, arg_list)

        partners = cr.dictfetchall()
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners if partner['partner_id']]
        lines = dict((partner['partner_id'] or False, []) for partner in partners)
        if not partner_ids:
            return [], [], []

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}
        query = '''SELECT l.id
                FROM account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND (COALESCE(l.date_maturity,l.date) > %s)\
                    AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                AND (l.date <= %s)
                AND l.company_id = %s'''
        cr.execute(query, (tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, user_company))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = line.balance
            if line.balance == 0:
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.create_date[:10] <= date_from:
                    line_amount += partial_line.amount
            for partial_line in line.matched_credit_ids:
                if partial_line.create_date[:10] <= date_from:
                    line_amount -= partial_line.amount
            undue_amounts[partner_id] += line_amount
            lines[partner_id].append({
                'line': line,
                'amount': line_amount,
                'period': 6,
                })
        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date_maturity,l.date)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
            args_list += (date_from, user_company)

            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    AND l.company_id = %s'''
            cr.execute(query, args_list)
            partners_amount = {}
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            for line in self.env['account.move.line'].browse(aml_ids):
                partner_id = line.partner_id.id or False
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = line.balance
                if line.balance == 0:
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.create_date[:10] <= date_from:
                        line_amount += partial_line.amount
                for partial_line in line.matched_credit_ids:
                    if partial_line.create_date[:10] <= date_from:
                        line_amount -= partial_line.amount

                partners_amount[partner_id] += line_amount
                lines[partner_id].append({
                    'line': line,
                    'amount': line_amount,
                    'period': i + 1,
                    })
            history.append(partners_amount)
        for partner in partners:
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            if partner['partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                undue_amt = undue_amounts[partner['partner_id']]

            total[6] = total[6] + undue_amt
            values['direction'] = undue_amt
            if not float_is_zero(values['direction'], precision_rounding=self.env.user.company_id.currency_id.rounding):
                at_least_one_amount = True

            for i in range(5):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)], precision_rounding=self.env.user.company_id.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
            ## Add for total
            total[(i + 1)] += values['total']
            values['partner_id'] = partner['partner_id']
            if partner['partner_id']:
                browsed_partner = self.env['res.partner'].browse(partner['partner_id'])
                values['name'] = browsed_partner.name and len(browsed_partner.name) >= 45 and browsed_partner.name[0:40] + '...' or browsed_partner.name
                values['trust'] = False
            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False
            if at_least_one_amount:
                res.append(values)

        return res, total, lines

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

        sheet.merge_range('A2:J3', 'Aged Partner Balance', format1)
        row = 5
        col = 0

        if data['form']['result_selection'] == 'customer':
            account_type = ['receivable']
        elif data['form']['result_selection'] == 'supplier':
            account_type = ['payable']
        else:
            account_type = ['payable', 'receivable']
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
        target_move = data['form'].get('target_move', 'all')
        movelines, total, dummy = self._get_billwise_move_lines(account_type,
                                                                date_from, target_move,
                                                                data['form']['period_length'])
        for partner in dummy:
            for line in dummy[partner]:
                line['intervals'] = {
                    '0': 0,
                    '1': 0,
                    '2': 0,
                    '3': 0,
                    '4': 0,
                    '5': 0,
                    'total': 0
                }
                line['intervals'][str(line['period'] - 1)] = line['amount']
                line['intervals']['total'] += line['amount']

        form = data['form']
        sheet.merge_range(row, col, row, col+2, 'Tanggal Awal Perhitungan :', format4)
        sheet.merge_range(row, col+3, row, col+6, form['date_from'], format4)
        row += 1
        sheet.merge_range(row, col, row, col+2, 'Periode (hari) :', format4)
        sheet.merge_range(row, col+3, row, col+6, form['period_length'], format4)
        row += 1
        account_type = ""
        if form['result_selection'] == 'customer':
            account_type += "AR"
        elif form['result_selection'] == 'supplier':
            account_type += "AP"
        elif form['result_selection'] == 'customer_supplier':
            account_type += "AR & AP"
        target_move = ""
        if form['target_move'] == 'all':
            target_move += "All Entries"
        elif form['result_selection'] == 'posted':
            target_move += "All Posted Entries"
        sheet.merge_range(row, col, row, col+2, "Partner's :", format4)
        sheet.merge_range(row, col + 3, row, col + 6, account_type, format4)
        
        row += 2
        # constructing the table
        sheet.write(row, col, "Nomor Dokumen", format5)
        sheet.write(row, col+1, "Partners", format5)
        sheet.write(row, col+2, "Tipe", format5)
        sheet.write(row, col+3, "Posting Date", format5)
        sheet.write(row, col+4, "Due Date", format5)
        sheet.write(row, col+5, "Original Amount", format5)
        sheet.write(row, col+6, "Aging per today", format5)
        sheet.write(row, col+7, "Residual", format5)
        sheet.write(row, col+8, "Cover Giro", format5)
        sheet.write(row, col+9, "Not Due", format5)
        sheet.write(row, col+10, form['4']['name'], format5)
        sheet.write(row, col+11, form['3']['name'], format5)
        sheet.write(row, col+12, form['2']['name'], format5)
        sheet.write(row, col+13, form['1']['name'], format5)
        sheet.write(row, col+14, form['0']['name'], format5)
        sheet.write(row, col+15, "Total", format5)

        row += 2
        for partner in movelines:
            for line in dummy[partner['partner_id']]:
                if line['amount'] != 0:
                    sheet.write(row, col, line['line'].invoice_id.number or line['line'].move_id.name, format4)
                    sheet.write(row, col + 1,
                                line['line'].invoice_id.partner_id.name or line['line'].partner_id.name,
                                format4)
                    sheet.write(row, col + 2,
                                line['line'].invoice_id.account_id.name or line['line'].account_id.name,
                                format4)
                    sheet.write(row, col + 3,
                                line['line'].invoice_id.date_invoice or line['line'].date,
                                format4)
                    sheet.write(row, col + 4,
                                line['line'].invoice_id.date_due or line['line'].date_maturity,
                                format4)
                    sheet.write(row, col + 5,
                                line['line'].invoice_id.amount_total or line['intervals'].get('total'),
                                format4)
                    sheet.write(row, col + 6,
                                line['line'].invoice_id.over_due_age,
                                format4)
                    sheet.write(row, col + 7,
                                line['intervals'].get('total') or  "-",
                                format4)
                    giro_allocated = 0
                    for giro in line['line'].invoice_id.giro_invoice_ids:
                        giro_allocated += giro.amount
                    sheet.write(row, col + 8,
                                giro_allocated or '-',
                                format4)
                    sheet.write(row, col + 9,
                                line['intervals'].get('5') or '-',
                                format4)
                    sheet.write(row, col + 10,
                                line['intervals'].get('4') or '-',
                                format4)
                    sheet.write(row, col + 11,
                                line['intervals'].get('3') or '-',
                                format4)
                    sheet.write(row, col + 12,
                                line['intervals'].get('2') or '-',
                                format4)
                    sheet.write(row, col + 13,
                                line['intervals'].get('1') or '-',
                                format4)
                    sheet.write(row, col + 14,
                                line['intervals'].get('0') or '-',
                                format4)
                    sheet.write(row, col + 15,
                                line['intervals'].get('total')  or '-',
                                format4)
                    row += 1


AgedBillwiseXlsx('report.partner_ageing_billwise_xlsx.partner_balance_xlsx.xlsx',
                 'account.aged.trial.balance.xls')
