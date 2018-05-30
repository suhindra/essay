# -*- coding: utf-8 -*-
# Copyright (c) 2014 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, exceptions, _, api
import logging
_logger = logging.getLogger(__name__)


class Report(models.Model):
    _inherit = 'report'

    @api.model
    def print_document(self, record_ids, report_name, html=None, data=None):
        """ Print a document, do not return the document file """
        document = self.with_context(must_skip_send_to_printer=True).get_pdf(
            record_ids, report_name, html=html, data=data)
        report = self._get_report_from_name(report_name)
        behaviour = report.behaviour()[report.id]
        printer = behaviour['printer']
        if not printer:
            raise exceptions.Warning(
                _('No printer configured to print this report.')
            )
        return printer.print_document(report, record_ids, document, report.report_type, record_ids)

    @api.multi
    def _can_print_report(self, behaviour, printer, document):
        """Predicate that decide if report can be sent to printer

        If you want to prevent `get_pdf` to send report you can set
        the `must_skip_send_to_printer` key to True in the context
        """
        if self.env.context.get('must_skip_send_to_printer'):
            return False
        if behaviour['action'] == 'server' and printer and document:
            return True
        return False

    @api.v7
    def get_pdf(self, cr, uid, ids, report_name, html=None,
                data=None, context=None):
        """ Generate a PDF and returns it.

        If the action configured on the report is server, it prints the
        generated document as well.
        """
        document = super(Report, self).get_pdf(cr, uid, ids, report_name,
                                               html=html, data=data,
                                               context=context)
        report = self._get_report_from_name(cr, uid, report_name)
        behaviour = report.behaviour()[report.id]
        printer = behaviour['printer']
        job_count=self.pool.get('printing.job').search(cr, uid, [('name','=',str(report.name) + str(ids))], offset=0, limit=None, order=None, context=None, count=True)
        
        can_print_report = self._can_print_report(cr, uid, ids,
                                                  behaviour, printer, document,
                                                  context=context)
        if can_print_report:
            printer.print_document(report, ids, document, report.report_type)
        if (job_count < report.max_print) or (report.print_limit_exception.id == uid):
            return document
        else:
            return False

    @api.v8
    def get_pdf(self, docids, report_name, html=None, data=None):
        return self._model.get_pdf(self._cr, self._uid,
                                   docids, report_name,
                                   html=html, data=data, context=self._context)
