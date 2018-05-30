from openerp.osv import fields,osv
from openerp import tools

class alisan_receivable_aging_report(osv.osv):
    _name = "alisan.receivable.aging"
    _description = "Receivable Aging"
    _auto = False
    _auto = False
    _rec_name = 'date_invoice'
    _columns = {
        'invoice_id':fields.many2one('account.invoice', 'Invoice'),
        'date_due': fields.date('Due Date'),
        'company_id':fields.many2one('res.company', 'Company'),
        'partner_id':fields.many2one('res.partner', 'Partner'),
        'type':fields.selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Vendor Bill'),
            ('out_refund','Customer Refund'),
            ('in_refund','Vendor Refund'),
        ]),
        'date_invoice':fields.date(string='Invoice Date'),
        'user_id':fields.many2one('res.users', string='Salesperson'),
        'amount_total':fields.float('Amount Total'),
        'giro':fields.float('Giro Covered'),
        }
    
    _order = 'date_invoice desc'
    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'alisan_receivable_aging_report')
        cr.execute("""
            create or replace view alisan_receivable_aging as (
            SELECT 
              i.id,
              i.id as invoice_id,
              i.date_due, 
              i.company_id,
              i.partner_id,
              i.type,
              i.date_invoice,
              i.user_id,
              CASE WHEN i.type = 'out_invoice' THEN i.amount_total
                   WHEN i.type = 'in_invoice' THEN -1 * i.amount_total
                   WHEN i.type = 'out_refund' THEN -1 * i.amount_total
                   WHEN i.type = 'in_refund' THEN i.amount_total
              END as amount_total,
              g.amount as giro
            FROM 
              account_invoice i
            JOIN 
              alisan_giro_invioce g
            ON
              g.invoice_id = i.id
            WHERE 
              i.date_due < current_date 
            AND 
              i.state = 'open'
            AND
              i.type = 'out_invoice')
            """)