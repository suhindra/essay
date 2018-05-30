# coding: utf-8

from openerp import api, fields, models


class InheritedCrmSaseSection(models.Model):

    _inherit = "crm.team"

    default_warehouse = fields.Many2one('stock.warehouse',
                                        string='Default Warehouse',
                                        help='In this field can be '
                                        'defined a default warehouse for '
                                        'the related users to the sales team.')


class WarehouseDefault(models.Model):
    """If you inherit from this model and add a field called warehouse_id into
    the model itself then the default value for such model will be the one
    setted into the sales team.
    """

    _auto = False
    _name = "default.warehouse"

    @api.model
    def default_get(self, fields_list):
        """Force that if model has a field called warehouse_id the default
        value is the one in the sales team in the user setted
        """
        defaults = super(WarehouseDefault,
                         self).default_get(fields_list)
        res_users_obj = self.env['res.users']
        user_brw = res_users_obj.browse(self._uid)
        
        return defaults