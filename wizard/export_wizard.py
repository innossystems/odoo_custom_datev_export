# -*- coding: utf-8 -*-
import base64
import csv
import io
import zipfile
from io import StringIO
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import float_repr

class ExportWizard(models.TransientModel):
    _name = 'export.wizard'
    _description = 'Export Wizard'

    start_date = fields.Date(string='Startdatum')
    end_date = fields.Date(string='Enddatum')
    include_posted = fields.Boolean(string='Nur gebuchte Rechnungen', default=True)
    include_customer_invoices = fields.Boolean(string='Nur Kundenrechnungen', default=True)
    include_credit_notes = fields.Boolean(string='Gutschriften einschließen', default=True)
    export_mode = fields.Selection([
        ('21', 'Buchungsstapel'),
        ('16', 'Debitoren/Kreditoren')
    ], string='Exportmodus', default='21', required=True)
    include_attachments = fields.Boolean(string='PDF Rechnungen & document.xml mit exportieren', default=False)
    is_company_only = fields.Boolean(string="Ist Unternehmen", default=True)
    file_name = fields.Char(string="Dateiname", default="EXTF_datev_export.zip")
    file_data = fields.Binary(string="Datei", readonly=True)

    @api.onchange('export_mode')
    def _onchange_export_mode(self):
        if self.export_mode == '16':  # Debitoren/Kreditoren
            self.start_date = False
            self.end_date = False
            self.include_posted = False
            self.include_customer_invoices = False
            self.include_credit_notes = False
            self.include_attachments = False
            self.is_company_only = True
        if self.export_mode == '21': # Buchungsstapel
            self.include_posted = True
            self.include_customer_invoices = True
            self.include_credit_notes = True
            self.is_company_only = False

    @api.constrains('export_mode', 'start_date', 'end_date')
    def _check_required_dates_for_buchungsstapel(self):
        for rec in self:
            if rec.export_mode == '21' and (not rec.start_date or not rec.end_date):
                raise ValidationError(_("Für Buchungsstapel-Exporte müssen Startdatum und Enddatum angegeben sein."))

    def action_export(self):
        domain = []
        if self.export_mode == '21':
            if not self.start_date or not self.end_date:
                raise UserError(_('Bitte Start- und Enddatum angeben für Buchungsstapel-Export.'))
            domain += [('invoice_date', '>=', self.start_date), ('invoice_date', '<=', self.end_date)]
            if self.include_posted:
                domain.append(('state', '=', 'posted'))
        else:
            if self.include_posted:
                domain.append(('state', '=', 'posted'))

        invoice_types = []
        if self.include_customer_invoices:
            invoice_types.append('out_invoice')
        if self.include_credit_notes:
            invoice_types.append('out_refund')
        if invoice_types:
            domain.append(('move_type', 'in', invoice_types))

        invoices = self.env['account.move'].search(domain)
        if not invoices:
            raise UserError(_('Keine Rechnungen für die ausgewählten Kriterien gefunden.'))

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            date_str = fields.Date.today().strftime('%Y-%m-%d')

            if self.export_mode == '21':
                # ---------------- Buchungsstapel + Partnerliste ----------------
                base_name = 'EXTF_datev_export_Buchungsstapel'
                if self.include_attachments:
                    base_name += '_PDF'

                zip_file.writestr(
                    f'{base_name}_{date_str}.csv',
                    self._generate_csv_content(invoices)
                )

                filtered_partners = invoices.mapped('partner_id').filtered(
                    lambda p: (
                        p and
                        p.property_account_receivable_id and
                        p.property_account_receivable_id.code and
                        p.is_company
                    )
                )
                if filtered_partners:
                    zip_file.writestr(
                        f'EXTF_datev_export_Debitoren_Kreditoren_Buchungsstapel_{date_str}.csv',
                        self._generate_filtered_partner_csv(filtered_partners)
                    )

                if self.include_attachments:
                    attachments = invoices.filtered(lambda m: m.message_main_attachment_id)
                    documents = []
                    for invoice in attachments:
                        attachment = invoice.message_main_attachment_id
                        zip_file.writestr(attachment.name, attachment.raw)
                        documents.append({
                            'guid': invoice._l10n_de_datev_get_guid(),
                            'filename': attachment.name,
                            'type': 2 if invoice.is_sale_document() else 1 if invoice.is_purchase_document() else None,
                        })
                    if documents:
                        zip_file.writestr('document.xml', self._generate_document_xml(documents))

            else:
                # ---------------- Debitoren/Kreditoren (Modus 16) ----------------
                base_name = 'EXTF_datev_export_Debitoren_Kreditoren'
                partners = invoices.mapped('partner_id')
                if self.is_company_only:
                    partners = partners.filtered(lambda p: p.is_company)
                if not partners:
                    raise UserError(_('Keine passenden Partner für Debitoren/Kreditoren-Export gefunden.'))

                zip_file.writestr(
                    f'{base_name}_{date_str}.csv',
                    self._generate_filtered_partner_csv(partners)
                )

        buffer.seek(0)
        self.file_data = base64.b64encode(buffer.read())
        self.file_name = f'{base_name}_{date_str}.zip'

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=export.wizard&id={self.id}&field=file_data&filename_field=file_name&download=true',
            'target': 'self',
        }

    def _generate_csv_content(self, invoices):
        output = StringIO()
        writer = csv.writer(output, delimiter=';', quotechar="'", quoting=csv.QUOTE_MINIMAL)

        self._write_datev_header(writer)

        if self.export_mode == '21':
            writer.writerow(self._get_buchungsstapel_header())
            writer.writerows(self._prepare_buchungsstapel(invoices))
        elif self.export_mode == '16':
            writer.writerow(self._get_partnerliste_header())
            writer.writerows(self._prepare_partner_list(invoices))

        return output.getvalue()
    

    def _generate_filtered_partner_csv(self, partners):
        output = StringIO()
        writer = csv.writer(output, delimiter=';', quotechar="'", quoting=csv.QUOTE_MINIMAL)

        writer.writerow(self._get_partnerliste_header())

        for partner in partners:
            array = [''] * 243
            # array[0] = self._datev_find_partner_account(partner.property_account_receivable_id, partner)
            array[0] = partner.property_account_receivable_id.code if partner.property_account_receivable_id else ''
            array[1] = partner.name if partner.is_company else ''
            array[3] = '' if partner.is_company else partner.name
            array[6] = '2' if partner.is_company else '1'
            array[9] = partner.vat or ''
            writer.writerow(array)

        return output.getvalue()

    def _write_datev_header(self, writer):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]
        wirtschaftsjahresbeginn = self.start_date.strftime('%Y') + '0101' if self.start_date else ''
        start_date_formatted = self.start_date.strftime('%Y%m%d') if self.start_date else ''
        end_date_formatted = self.end_date.strftime('%Y%m%d') if self.end_date else ''

        export_mode = self.export_mode
        satzart_bezeichner = 'Buchungsstapel' if export_mode == '21' else 'Debitoren/Kreditoren'
        satzart_nummer = '13' if export_mode == '21' else '5'

        writer.writerow([
            '"EXTF"', 700, export_mode,
            satzart_bezeichner, satzart_nummer,
            timestamp, '', '', '', '',
            str(self.env.company.l10n_de_datev_consultant_number or ''),
            str(self.env.company.l10n_de_datev_client_number or ''),
            wirtschaftsjahresbeginn,
            str(self.env.company.l10n_de_datev_account_length or ''),
            start_date_formatted, end_date_formatted,
            '', '', '', '',
            0, self.env.company.currency_id.name,
            '', '', '', '', '', '', '', '', ''
        ])

    def _generate_document_xml(self, documents):
        lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<DocumentList>']
        now = fields.Datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        lines.append(f'  <DateCreated>{now}</DateCreated>')
        for doc in documents:
            lines.append('  <Document>')
            lines.append(f'    <GUID>{doc["guid"]}</GUID>')
            lines.append(f'    <Filename>{doc["filename"]}</Filename>')
            if doc['type']:
                lines.append(f'    <DocumentType>{doc["type"]}</DocumentType>')
            lines.append('  </Document>')
        lines.append('</DocumentList>')
        return '\n'.join(lines)

    def _get_buchungsstapel_header(self):
        return [
            'Umsatz (ohne Soll/Haben-Kz)', 'Soll/Haben-Kennzeichen', 'WKZ Umsatz', 'Kurs', 'Basis-Umsatz', 'WKZ Basis-Umsatz',
            'Konto', 'Gegenkonto (ohne BU-Schlüssel)', 'BU-Schlüssel', 'Belegdatum', 'Belegfeld 1', 'Belegfeld 2', 'Skonto',
            'Buchungstext', 'Postensperre', 'Diverse Adressnummer', 'Geschäftspartnerbank', 'Sachverhalt', 'Zinssperre',
            'Beleglink', 'Beleginfo - Art 1', 'Beleginfo - Inhalt 1', 'Beleginfo - Art 2', 'Beleginfo - Inhalt 2',
            'Beleginfo - Art 3', 'Beleginfo - Inhalt 3', 'Beleginfo - Art 4', 'Beleginfo - Inhalt 4',
            'Beleginfo - Art 5', 'Beleginfo - Inhalt 5', 'Beleginfo - Art 6', 'Beleginfo - Inhalt 6',
            'Beleginfo - Art 7', 'Beleginfo - Inhalt 7', 'Beleginfo - Art 8', 'Beleginfo - Inhalt 8', 'KOST1 - Kostenstelle',
            'KOST2 - Kostenstelle', 'Kost-Menge', 'EU-Land u. UStID (Bestimmung)', 'EU-Steuersatz (Bestimmung)',
            'Abw. Versteuerungsart', 'Sachverhalt L+L', 'Funktionsergänzung L+L', 'BU 49 Hauptfunktionstyp', 'BU 49 Hauptfunktionsnummer',
            'BU 49 Funktionsergänzung', 'Zusatzinformation - Art 1', 'Zusatzinformation- Inhalt 1', 'Zusatzinformation - Art 2',
            'Zusatzinformation- Inhalt 2', 'Zusatzinformation - Art 3', 'Zusatzinformation- Inhalt 3', 'Zusatzinformation - Art 4',
            'Zusatzinformation- Inhalt 4', 'Zusatzinformation - Art 5', 'Zusatzinformation- Inhalt 5', 'Zusatzinformation - Art 6',
            'Zusatzinformation- Inhalt 6', 'Zusatzinformation - Art 7', 'Zusatzinformation- Inhalt 7', 'Zusatzinformation - Art 8',
            'Zusatzinformation- Inhalt 8', 'Zusatzinformation - Art 9', 'Zusatzinformation- Inhalt 9', 'Zusatzinformation - Art 10',
            'Zusatzinformation- Inhalt 10', 'Zusatzinformation - Art 11', 'Zusatzinformation- Inhalt 11', 'Zusatzinformation - Art 12',
            'Zusatzinformation- Inhalt 12', 'Zusatzinformation - Art 13', 'Zusatzinformation- Inhalt 13', 'Zusatzinformation - Art 14',
            'Zusatzinformation- Inhalt 14', 'Zusatzinformation - Art 15', 'Zusatzinformation- Inhalt 15', 'Zusatzinformation - Art 16',
            'Zusatzinformation- Inhalt 16', 'Zusatzinformation - Art 17', 'Zusatzinformation- Inhalt 17', 'Zusatzinformation - Art 18',
            'Zusatzinformation- Inhalt 18', 'Zusatzinformation - Art 19', 'Zusatzinformation- Inhalt 19', 'Zusatzinformation - Art 20',
            'Zusatzinformation- Inhalt 20', 'Stück', 'Gewicht', 'Zahlweise', 'Forderungsart', 'Veranlagungsjahr', 'Zugeordnete Fälligkeit',
            'Skontotyp', 'Auftragsnummer', 'Buchungstyp', 'USt-Schlüssel (Anzahlungen)', 'EU-Land (Anzahlungen)', 'Sachverhalt L+L (Anzahlungen)',
            'EU-Steuersatz (Anzahlungen)', 'Erlöskonto (Anzahlungen)', 'Herkunft-Kz', 'Buchungs GUID', 'KOST-Datum', 'SEPA-Mandatsreferenz',
            'Skontosperre', 'Gesellschaftername', 'Beteiligtennummer', 'Identifikationsnummer', 'Zeichnernummer', 'Postensperre bis',
            'Bezeichnung SoBil-Sachverhalt', 'Kennzeichen SoBil-Buchung', 'Festschreibung', 'Leistungsdatum', 'Datum Zuord. Steuerperiode',
            'Fälligkeit', 'Generalumkehr (GU)', 'Steuersatz', 'Land', 'Abrechnungsreferenz', 'BVV-Position', 'EU-Land u. UStID (Ursprung)',
            'EU-Steuersatz (Ursprung)', 'Abw. Skontokonto',
        ]

    def _get_partnerliste_header(self):
        return [
            'Konto', 'Name (Adressattyp Unternehmen)', 'Unternehmensgegenstand', 'Name (Adressattyp natürl. Person)',
            'Vorname (Adressattyp natürl. Person)', 'Name (Adressattyp keine Angabe)', 'Adressattyp', 'Kurzbezeichnung',
            'EU-Land', 'EU-UStID', 'Anrede', 'Titel/Akad. Grad', 'Adelstitel', 'Namensvorsatz', 'Adressart', 'Straße',
            'Postfach', 'Postleitzahl', 'Ort', 'Land', 'Versandzusatz', 'Adresszusatz', 'Abweichende Anrede', 'Abw. Zustellbezeichnung 1',
            'Abw. Zustellbezeichnung 2', 'Kennz. Korrespondenzadresse', 'Adresse Gültig von', 'Adresse Gültig bis', 'Telefon',
            'Bemerkung (Telefon)', 'Telefon GL', 'Bemerkung (Telefon GL)', 'E-Mail', 'Bemerkung (E-Mail)', 'Internet',
            'Bemerkung (Internet)', 'Fax', 'Bemerkung (Fax)', 'Sonstige', 'Bemerkung (Sonstige)', 'Bankleitzahl 1',
            'Bankbezeichnung 1', 'Bank-Kontonummer 1', 'Länderkennzeichen 1', 'IBAN-Nr. 1', 'Leerfeld', 'SWIFT-Code 1',
            'Abw. Kontoinhaber 1', 'Kennz. Hauptbankverb. 1', 'Bankverb 1 Gültig von', 'Bankverb 1 Gültig bis', 'Bankleitzahl 2',
            'Bankbezeichnung 2', 'Bank-Kontonummer 2', 'Länderkennzeichen 2', 'IBAN-Nr. 2', 'Leerfeld', 'SWIFT-Code 2',
            'Abw. Kontoinhaber 2', 'Kennz. Hauptbankverb. 2', 'Bankverb 2 Gültig von', 'Bankverb 2 Gültig bis', 'Bankleitzahl 3',
            'Bankbezeichnung 3', 'Bank-Kontonummer 3', 'Länderkennzeichen 3', 'IBAN-Nr. 3', 'Leerfeld', 'SWIFT-Code 3',
            'Abw. Kontoinhaber 3', 'Kennz. Hauptbankverb. 3', 'Bankverb 3 Gültig von', 'Bankverb 3 Gültig bis', 'Bankleitzahl 4',
            'Bankbezeichnung 4', 'Bank-Kontonummer 4', 'Länderkennzeichen 4', 'IBAN-Nr. 4', 'Leerfeld', 'SWIFT-Code 4',
            'Abw. Kontoinhaber 4', 'Kennz. Hauptbankverb. 4', 'Bankverb 4 Gültig von', 'Bankverb 4 Gültig bis', 'Bankleitzahl 5',
            'Bankbezeichnung 5', 'Bank-Kontonummer 5', 'Länderkennzeichen 5', 'IBAN-Nr. 5', 'Leerfeld', 'SWIFT-Code 5',
            'Abw. Kontoinhaber 5', 'Kennz. Hauptbankverb. 5', 'Bankverb 5 Gültig von', 'Bankverb 5 Gültig bis', 'Leerfeld',
            'Briefanrede', 'Grußformel', 'Kunden-/Lief.-Nr.', 'Steuernummer', 'Sprache', 'Ansprechpartner', 'Vertreter',
            'Sachbearbeiter', 'Diverse-Konto', 'Ausgabeziel', 'Währungssteuerung', 'Kreditlimit (Debitor)', 'Zahlungsbedingung',
            'Fälligkeit in Tagen (Debitor)', 'Skonto in Prozent (Debitor)', 'Kreditoren-Ziel 1 Tg.', 'Kreditoren-Skonto 1 %',
            'Kreditoren-Ziel 2 Tg.', 'Kreditoren-Skonto 2 %', 'Kreditoren-Ziel 3 Brutto Tg.', 'Kreditoren-Ziel 4 Tg.',
            'Kreditoren-Skonto 4 %', 'Kreditoren-Ziel 5 Tg.', 'Kreditoren-Skonto 5 %', 'Mahnung', 'Kontoauszug', 'Mahntext 1',
            'Mahntext 2', 'Mahntext 3', 'Kontoauszugstext', 'Mahnlimit Betrag', 'Mahnlimit %', 'Zinsberechnung', 'Mahnzinssatz 1',
            'Mahnzinssatz 2', 'Mahnzinssatz 3', 'Lastschrift', 'Leerfeld', 'Mandantenbank', 'Zahlungsträger', 'Indiv. Feld 1',
            'Indiv. Feld 2', 'Indiv. Feld 3', 'Indiv. Feld 4', 'Indiv. Feld 5', 'Indiv. Feld 6', 'Indiv. Feld 7', 'Indiv. Feld 8',
            'Indiv. Feld 9', 'Indiv. Feld 10', 'Indiv. Feld 11', 'Indiv. Feld 12', 'Indiv. Feld 13', 'Indiv. Feld 14',
            'Indiv. Feld 15', 'Abweichende Anrede (Rechnungsadresse)', 'Adressart (Rechnungsadresse)', 'Straße (Rechnungsadresse)',
            'Postfach (Rechnungsadresse)', 'Postleitzahl (Rechnungsadresse)', 'Ort (Rechnungsadresse)', 'Land (Rechnungsadresse)',
            'Versandzusatz (Rechnungsadresse)', 'Adresszusatz (Rechnungsadresse)', 'Abw. Zustellbezeichnung 1 (Rechnungsadresse)',
            'Abw. Zustellbezeichnung 2 (Rechnungsadresse)', 'Adresse Gültig von (Rechnungsadresse)', 'Adresse Gültig bis (Rechnungsadresse)',
            'Bankleitzahl 6', 'Bankbezeichnung 6', 'Bank-Kontonummer 6', 'Länderkennzeichen 6', 'IBAN-Nr. 6', 'Leerfeld',
            'SWIFT-Code 6', 'Abw. Kontoinhaber 6', 'Kennz. Hauptbankverb. 6', 'Bankverb 6 Gültig von', 'Bankverb 6 Gültig bis',
            'Bankleitzahl 7', 'Bankbezeichnung 7', 'Bank-Kontonummer 7', 'Länderkennzeichen 7', 'IBAN-Nr. 7', 'Leerfeld',
            'SWIFT-Code 7', 'Abw. Kontoinhaber 7', 'Kennz. Hauptbankverb. 7', 'Bankverb 7 Gültig von', 'Bankverb 7 Gültig bis',
            'Bankleitzahl 8', 'Bankbezeichnung 8', 'Bank-Kontonummer 8', 'Länderkennzeichen 8', 'IBAN-Nr. 8', 'Leerfeld',
            'SWIFT-Code 8', 'Abw. Kontoinhaber 8', 'Kennz. Hauptbankverb. 8', 'Bankverb 8 Gültig von', 'Bankverb 8 Gültig bis',
            'Bankleitzahl 9', 'Bankbezeichnung 9', 'Bank-Kontonummer 9', 'Länderkennzeichen 9', 'IBAN-Nr. 9', 'Leerfeld',
            'SWIFT-Code 9', 'Abw. Kontoinhaber 9', 'Kennz. Hauptbankverb. 9', 'Bankverb 9 Gültig von', 'Bankverb 9 Gültig bis',
            'Bankleitzahl 10', 'Bankbezeichnung 10', 'Bank-Kontonummer 10', 'Länderkennzeichen 10', 'IBAN-Nr. 10', 'Leerfeld',
            'SWIFT-Code 10', 'Abw. Kontoinhaber 10', 'Kennz. Hauptbankverb. 10', 'Bankverb 10 Gültig von', 'Bankverb 10 Gültig bis',
            'Nummer Fremdsystem', 'Insolvent', 'SEPA-Mandatsreferenz 1', 'SEPA-Mandatsreferenz 2', 'SEPA-Mandatsreferenz 3',
            'SEPA-Mandatsreferenz 4', 'SEPA-Mandatsreferenz 5', 'SEPA-Mandatsreferenz 6', 'SEPA-Mandatsreferenz 7',
            'SEPA-Mandatsreferenz 8', 'SEPA-Mandatsreferenz 9', 'SEPA-Mandatsreferenz 10', 'Verknüpftes OPOS-Konto',
            'Mahnsperre bis', 'Lastschriftsperre bis', 'Zahlungssperre bis', 'Gebührenberechnung', 'Mahngebühr 1', 'Mahngebühr 2',
            'Mahngebühr 3', 'Pauschalenberechnung', 'Verzugspauschale 1', 'Verzugspauschale 2', 'Verzugspauschale 3',
            'Alternativer Suchname', 'Status', 'Anschrift manuell geändert (Korrespondenzadresse)', 'Anschrift individuell (Korrespondenzadresse)',
            'Anschrift manuell geändert (Rechnungsadresse)', 'Anschrift individuell (Rechnungsadresse)', 'Fristberechnung bei Debitor',
            'Mahnfrist 1', 'Mahnfrist 2', 'Mahnfrist 3', 'Letzte Frist',
        ]

    def _prepare_buchungsstapel(self, invoices):
        lines = []
        for inv in invoices:
            array = [''] * 125
            array[0] = f"{inv.amount_total:.2f}".replace('.', ',')
            array[1] = 'H' if inv.move_type == 'out_invoice' else 'S'
            array[2] = inv.currency_id.name or ''
            array[6] = '4400'
            array[7] = inv.partner_id.property_account_receivable_id.code or ''
            array[9] = inv.invoice_date.strftime('%d%m') if inv.invoice_date else ''
            array[10] = inv.name or ''
            array[11] = inv.invoice_date_due.strftime('%d%m%y') if inv.invoice_date_due else ''
            array[13] = inv.partner_id.parent_id.name if inv.partner_id.parent_id else inv.partner_id.name or ''
            if inv.message_main_attachment_id:
                array[19] = f'BEDI "{inv._l10n_de_datev_get_guid()}"'
            lines.append(array)
        return lines

    def _prepare_partner_list(self, invoices):
        partner_ids = invoices.mapped('partner_id').filtered(lambda p: p)
        # Filtere nur Firmen, wenn angehakt
        if self.is_company_only:
            partner_ids = partner_ids.filtered(lambda p: p.is_company)

        lines = []
        for partner in partner_ids:
            array = [''] * 243
            # array[0] = self._datev_find_partner_account(partner.property_account_receivable_id.code, partner)
            array[0] = partner.property_account_receivable_id.code if partner.property_account_receivable_id else ''
            array[1] = partner.name if partner.is_company else ''
            array[3] = '' if partner.is_company else partner.name
            array[6] = '2' if partner.is_company else '1'
            array[9] = partner.vat or ''
            lines.append(array)
        return lines

    def _datev_find_partner_account(self, account, partner):
        length = (self.env.company.l10n_de_datev_account_length or 4) + 1
        if not account:
            return ''
        if partner and account.account_type in ('asset_receivable', 'liability_payable'):
            prefix = '1' if account.account_type == 'asset_receivable' else '7'
            return str(prefix) + str(partner.id).rjust(length - 1, '0')
        return str(account.code).ljust(length - 1, '0')