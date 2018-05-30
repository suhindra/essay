from openerp import models, fields, api


class AgeingAnalysis(models.Model):
    _name = 'product.ageing'

    from_date = fields.Datetime(string="Starting Date", required=True)
    location_id = fields.Many2many('stock.location', string="Location")
    product_categ = fields.Many2many('product.category', string="Category")
    interval = fields.Integer(string="Interval(days)", default=30, required=True)

    @api.model
    def check_report(self, data):
        """Redirects to the report with the values obtained from the wizard
                'data['form']':  date duration"""
        rec = self.browse(data)
        data = {}
        data['form'] = rec.read(['from_date', 'location_id', 'product_categ', 'interval'])
        return self._print_report(data)


    def _print_report(self, data):
        res = {}
       
        return {
            'name': 'Report Product Ageing',
            'type': 'ir.actions.report.xml',
            'report_name': 'product_ageing_report.report_ageing_analysis',
            'datas': data
        }