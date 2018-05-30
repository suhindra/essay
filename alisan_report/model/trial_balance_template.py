from openerp import models, fields, api


class alisan_trial_balance_template(models.Model):
    _inherit = 'account.config.settings'
    _name = 'alisan.trial.balance.template'

        


class alisan_trial_balance_template(models.TransientModel):
    _inherit = 'account.config.settings'

    trial_balance_account = fields.Char('Trial Balance Account')


    @api.model
    def get_default_voucher_exception(self, fields):
        conf = self.env['ir.config_parameter']
        return {
            'trial_balance_account': str(conf.get_param('trial_balance.trial_balance_account')),
        }

    @api.one
    def set_voucher_exception(self):
        conf = self.env['ir.config_parameter']
        conf.set_param('trial_balance.trial_balance_account', str(self.trial_balance_account))
    