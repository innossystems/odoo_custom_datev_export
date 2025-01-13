import base64
import csv
from datetime import datetime
from io import StringIO
from odoo import models, fields, api

class ExportWizard(models.TransientModel):
    _name = 'export.wizard'
    _description = 'Export Wizard'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    file_name = fields.Char(string="File Name", default="invoice_export.csv")
    file_data = fields.Binary(string="File")

    def action_export(self):
        invoices = self.env['account.move'].search([
            ('invoice_date', '>=', self.start_date),
            ('invoice_date', '<=', self.end_date),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', '=', 'not_paid'),
        ])

        file_content = StringIO()
        writer = csv.writer(file_content, delimiter=',')
        writer.writerow(['Invoice Number', 'Invoice Date', 'Customer', 'Amount Total', 'Status'])

        for inv in invoices:
            writer.writerow([
                inv.name,
                inv.invoice_date,
                inv.partner_id.name,
                inv.amount_total,
                inv.payment_state,
            ])

        file_content.seek(0)
        self.file_data = base64.b64encode(file_content.read().encode('utf-8'))
        self.file_name = f'invoice_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'export.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }