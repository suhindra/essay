from openerp.osv import fields,osv
from openerp import tools

class alisan_trial_balance_report(osv.osv):
    _name = "alisan.trial.balance"
    _description = "Trial Balance"
    _auto = False
    _rec_name = 'date'
    _columns = {
            'account_id':fields.many2one('account.account', string='COA', type='row'),
            'amount_total':fields.float(string='Amount'),
            'date':fields.float(string='Date'),
            'year':fields.char(string='Year', type='col'),
            'month':fields.char(string='Month', type='col'),
            'day':fields.char(string='Day', type='col'),
            }
    
    _order = 'date desc'            
    def init(self, cr):
            tools.sql.drop_view_if_exists(cr, 'alisan_trial_balance_report')
            cr.execute("""
                    create or replace view alisan_trial_balance as (
                    SELECT 
                        a.account_id,
                        a.id,
                        a.date,
                        (a.debit - a.credit) as amount_total,
                        EXTRACT(YEAR FROM a.date) as year,
                        EXTRACT(MONTH FROM a.date) as month,
                        EXTRACT(DAY FROM a.date) as day
                    FROM 
                        account_move_line a)
                    """)