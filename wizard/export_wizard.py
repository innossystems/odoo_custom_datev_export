import base64
import csv
from io import StringIO
from odoo import models, fields, api
from odoo.exceptions import UserError


class ExportWizard(models.TransientModel):
    _name = 'export.wizard'
    _description = 'Export Wizard'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    file_name = fields.Char(string="File Name", default="EXTF_datev_export.csv")
    file_data = fields.Binary(string="File", readonly=True)

    def action_export(self):
        # Suche nach Rechnungen im angegebenen Zeitraum
        invoices = self.env['account.move'].search([
            ('invoice_date', '>=', self.start_date),
            ('invoice_date', '<=', self.end_date),
            ('move_type', '=', 'out_invoice'),  # Nur Kundenrechnungen
            ('state', '=', 'posted'),          # Nur gebuchte Rechnungen
        ])

        if not invoices:
            raise UserError('No invoices found for the selected period.')

        # CSV-Datei erstellen
        file_content = StringIO()
        writer = csv.writer(file_content, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)  # CSV mit Semikolon als Trenner
        writer.writerow(['EXTF - Betrag Gesamt', '510 Spalte', '21 Spalte', '', '','Rechnungsdatum', 'Rechnungsnummer', 'Kontoname'])
        writer.writerow(['Umsatz', 'Soll/Haben', 'WKZ Umsatz', 'Konto', 'Gegenkonto','Belegdatum', 'Belegfeld', 'Buchungstext'])

        for inv in invoices:
            writer.writerow([
                f"{inv.amount_total:.2f}".replace('.', ','),  # Betrag mit Komma formatieren
                'H',
                inv.currency_id.name,
                inv.l10n_de_datev_main_account_id.code,
                inv.partner_id.property_account_receivable_id.code,
                inv.invoice_date.strftime('%d%m'),
                inv.name,
                inv.partner_id.name or '',
            ])

        file_content.seek(0)
        csv_data = file_content.read().encode('utf-8')
        file_content.close()

        self.file_data = base64.b64encode(csv_data)
        self.file_name = f'EXTF_datev_export_{fields.Date.today()}.csv'

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=export.wizard&id={self.id}&field=file_data&filename_field=file_name&download=true',
            'target': 'self',
        }