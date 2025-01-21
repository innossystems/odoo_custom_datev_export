import base64
import csv
from io import StringIO
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
from datetime import datetime


_logger = logging.getLogger(__name__)

class ExportWizard(models.TransientModel):
    _name = 'export.wizard'
    _description = 'Export Wizard'

    start_date = fields.Date(string='Startdatum', required=True)
    end_date = fields.Date(string='Enddatum', required=True)
    include_posted = fields.Boolean(string='Nur gebuchte Rechnungen', default=True)
    include_customer_invoices = fields.Boolean(string='Nur Kundenrechnungen', default=True)
    include_credit_notes = fields.Boolean(string='Gutschriften einschließen', default=True)
    export_mode = fields.Selection([
        ('21', 'Buchungsstapel'),
        ('16', 'Debitoren/Kreditoren')
    ], string='Exportmodus', default='21', required=True)
    file_name = fields.Char(string="Dateiname", default="EXTF_datev_export.csv")
    file_data = fields.Binary(string="Datei", readonly=True)

    def action_export(self):
        # Debug: Log alle relevanten Informationen für das Debugging
        _logger.info("Startdatum: %s", self.start_date)
        _logger.info("Enddatum: %s", self.end_date)
        _logger.info("Consultant Number: %s", self.env.company.l10n_de_datev_consultant_number)
        _logger.info("Type of Consultant Number: %s", type(self.env.company.l10n_de_datev_consultant_number))

        # Filter basierend auf Benutzerauswahl aufbauen
        domain = [('invoice_date', '>=', self.start_date), ('invoice_date', '<=', self.end_date)]
        if self.include_posted:
            domain.append(('state', '=', 'posted'))  # Nur gebuchte Rechnungen

        # Auswahl von Rechnungstypen basierend auf Benutzerauswahl
        invoice_types = []
        if self.include_customer_invoices:
            invoice_types.append('out_invoice')  # Kundenrechnungen
        if self.include_credit_notes:
            invoice_types.append('out_refund')  # Gutschriften

        if invoice_types:
            domain.append(('move_type', 'in', invoice_types))  # Filtere nach Rechnungstypen

        # Suche nach Rechnungen mit dynamischem Filter
        invoices = self.env['account.move'].search(domain)

        if not invoices:
            raise UserError('Keine Rechnungen für die ausgewählten Kriterien gefunden.')

        # Definition von Exportmodi
        Buchungsstapel = '21'
        debitoren_kreditoren = '16'

        # Zeitstempel
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]
        wirtschaftsjahresbeginn = self.start_date.strftime('%Y') + '0101'
        start_date_formatted = self.start_date.strftime('%Y%m%d')
        end_date_formatted = self.end_date.strftime('%Y%m%d')
        festschreibung = 0


        # CSV-Datei erstellen
        file_content = StringIO()
        writer = csv.writer(file_content, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # Erste Zeile schreiben mit dynamischem Exportmodus
        export_mode = self.export_mode  # Aktueller Modus aus der Auswahl
        writer.writerow(['"EXTF"', 700, export_mode,
                         'Buchungsstapel' if export_mode == '21' else 'Debitoren/Kreditoren',
                         '13' if export_mode == '21' else '5', 
                         timestamp, 
                         '', '', '', '',
                         str(self.env.company.l10n_de_datev_consultant_number or ''),
                         str(self.env.company.l10n_de_datev_client_number or ''), 
                         wirtschaftsjahresbeginn, 
                         str(self.env.company.l10n_de_datev_account_length or ''), 
                         start_date_formatted, 
                         end_date_formatted,
                         '', '', '', '', 
                         festschreibung, 
                         self.env.company.currency_id.display_name, 
                         '', '', '', '', '', '', '', '', ''
                        ])

        # Zweite Zeile mit Spaltenüberschriften basierend auf Exportmodus
        if export_mode == '21':  # Buchungsstapel
            writer.writerow([
            'Umsatz', 'Soll-/Haben-Kennzeichen', 'WKZ Umsatz', 'Kurs', 'Basis-Umsatz',
            'WKZ Basis-Umsatz', 'Konto', 'Gegenkonto (ohne BU-Schlüssel)', 'BU-Schlüssel',
            'Belegdatum', 'Belegfeld 1', 'Belegfeld 2', 'Skonto', 'Buchungstext',
            'Postensperre', 'Diverse Adressnummer', 'Geschäftspartnerbank', 'Sachverhalt',
            'Zinssperre', 'Beleglink', 'Beleginfo- Art 1', 'Beleginfo- Inhalt 1',
            'Beleginfo- Art 2', 'Beleginfo- Inhalt 2', 'Beleginfo- Art 3', 'Beleginfo- Inhalt 3',
            'Beleginfo- Art 4', 'Beleginfo- Inhalt 4', 'Beleginfo- Art 5', 'Beleginfo- Inhalt 5',
            'Beleginfo- Art 6', 'Beleginfo- Inhalt 6', 'Beleginfo- Art 7', 'Beleginfo- Inhalt 7',
            'Beleginfo- Art 8', 'Beleginfo- Inhalt 8', 'KOST1 - Kostenstelle',
            'KOST2 - Kostenstelle', 'Kost-Menge', 'EU-Land u. UStID', 'EU-Steuersatz',
            'Abw. Versteuerungsart', 'Sachverhalt L+L', 'Funktionsergänzung L+L',
            'BU 49 Hauptfunktionstyp', 'BU 49 Hauptfunktionsnummer', 'BU 49 Zeilenwert',
            'Zusatzinformation - Art 1', 'Zusatzinformation - Inhalt 1',
            'Zusatzinformation - Art 2', 'Zusatzinformation - Inhalt 2',
            'Zusatzinformation - Art 3', 'Zusatzinformation - Inhalt 3',
            'Zusatzinformation - Art 4', 'Zusatzinformation - Inhalt 4',
            'Zusatzinformation - Art 5', 'Zusatzinformation - Inhalt 5',
            'Zusatzinformation - Art 6', 'Zusatzinformation - Inhalt 6',
            'Zusatzinformation - Art 7', 'Zusatzinformation - Inhalt 7',
            'Zusatzinformation - Art 8', 'Zusatzinformation - Inhalt 8',
            'Zusatzinformation - Art 9', 'Zusatzinformation - Inhalt 9',
            'Zusatzinformation - Art 10', 'Zusatzinformation - Inhalt 10',
            'Zusatzinformation - Art 11', 'Zusatzinformation - Inhalt 11',
            'Zusatzinformation - Art 12', 'Zusatzinformation - Inhalt 12',
            'Zusatzinformation - Art 13', 'Zusatzinformation - Inhalt 13',
            'Zusatzinformation - Art 14', 'Zusatzinformation - Inhalt 14',
            'Zusatzinformation - Art 15', 'Zusatzinformation - Inhalt 15',
            'Zusatzinformation - Art 16', 'Zusatzinformation - Inhalt 16',
            'Zusatzinformation - Art 17', 'Zusatzinformation - Inhalt 17',
            'Zusatzinformation - Art 18', 'Zusatzinformation - Inhalt 18',
            'Zusatzinformation - Art 19', 'Zusatzinformation - Inhalt 19',
            'Zusatzinformation - Art 20', 'Zusatzinformation - Inhalt 20',
            'Stück', 'Gewicht', 'Zahlweise', 'Forderungsart', 'Veranlagungsjahr',
            'Zugeordnete Fälligkeit', 'Skontotyp', 'Auftragsnummer', 'Buchungstyp',
            'USt-Schlüssel (Anzahlungen)', 'EU-Land (Anzahlungen)',
            'Sachverhalt L+L (Anzahlungen)', 'EU-Steuersatz (Anzahlungen)',
            'Erlöskonto (Anzahlungen)', 'Herkunft-Kz', 'Leerfeld', 'KOST-Datum',
            'SEPA-Mandatsreferenz', 'Skontosperre', 'Gesellschaftername',
            'Beteiligtennummer', 'Identifikationsnummer', 'Zeichnernummer',
            'Postensperre bis', 'Bezeichnung SoBil-Sachverhalt',
            'Kennzeichen SoBil-Buchung', 'Festschreibung'
        ])
        elif export_mode == '16':  # Debitoren/Kreditoren
            writer.writerow([
                'Konto', 'Name (Adressatentyp Unternehmen)', 'Unternehmensgegenstand', 'Name (Adressatentyp natürl. Person)', 'Vorname (Adressatentyp natürl. Person)', 'Name (Adressatentyp keine Angabe)', 'Adressatentyp', 'Kurzbezeichnung', 'EU-Mitgliedstaat', 'EU-USt-IdNr.', 'Anrede', 'Titel / Akad. Grad', 'Adelstitel', 'Namensvorsatz', 'Adressart', 'Straße', 'Postfach', 'Postleitzahl', 'Ort', 'Land', 'Versandzusatz', 'Adresszusatz', 'Abweichende Anrede', 'Abw. Zustellbezeichnung 1', 'Abw. Zustellbezeichnung 2', 'Kennz. Korrespondenzadresse', 'Adresse Gültig von', 'Adresse Gültig bis', 'Telefon', 'Bemerkung (Telefon)', 'Telefon Geschäftsleitung', 'Bemerktung (Telefon GL)', 'E-Mail', 'Bemerkung (E-Mail)', 'Internet', 'Bemerkung (Internet)', 'Fax', 'Bemerkung (Fax)', 'Sonstige', 'Bemerkung (Sonstige 1)', 'Bankleitzahl 1', 'Bankbezeichung 1', 'Bankkonto-Nummer 1', 'Länderkennzeichen 1', 'IBAN-Nr. 1', 'Leerfeld', 'SWIFT-Code 1', 'Abw. Kontoinhaber 1', 'Kennz. Hauptbankverb. 1', 'Bankverb. 1 Gültig von', 'Bankverb. 1 Gültig bis', 'Bankleitzahl 2', 'Bankbezeichung 2', 'Bankkonto-Nummer 2', 'Länderkennzeichen 2', 'IBAN-Nr. 2', 'Leerfeld', 'SWIFT-Code 2', 'Abw. Kontoinhaber 2', 'Kennz. Hauptbankverb. 2', 'Bankverb. 2 Gültig von', 'Bankverb. 2 Gültig bis', 'Bankleitzahl 3', 'Bankbezeichung 3', 'Bankkonto-Nummer 3', 'Länderkennzeichen 3', 'IBAN-Nr. 3', 'Leerfeld', 'SWIFT-Code 3', 'Abw. Kontoinhaber 3', 'Kennz. Hauptbankverb. 3', 'Bankverb. 3 Gültig von', 'Bankverb. 3 Gültig bis', 'Bankleitzahl 4', 'Bankbezeichung 4', 'Bankkonto-Nummer 4', 'Länderkennzeichen 4', 'IBAN-Nr. 4', 'Leerfeld', 'SWIFT-Code 4', 'Abw. Kontoinhaber 4', 'Kennz. Hauptbankverb. 4', 'Bankverb. 4 Gültig von', 'Bankverb. 4 Gültig bis', 'Bankleitzahl 5', 'Bankbezeichung 5', 'Bankkonto-Nummer 5', 'Länderkennzeichen 5', 'IBAN-Nr. 5', 'Leerfeld', 'SWIFT-Code 5', 'Abw. Kontoinhaber 5', 'Kennz. Hauptbankverb. 5', 'Bankverb. 5 Gültig von', 'Bankverb. 5 Gültig bis', 'Leerfeld', 'Briefanrede', 'Grußformel', 'Kundennummer', 'Steuernummer', 'Sprache', 'Ansprechpartner', 'Vertreter', 'Sachbearbeiter', 'Diverse-Konto', 'Ausgabeziel', 'Währungssteuerung', 'Kreditlimit (Debitor)', 'Zahlungsbedingung', 'Fälligkeit in Tagen (Debitor)', 'Skonto in Prozent (Debitor)', 'Kreditoren-Ziel 1 (Tage)', 'Kreditoren-Skonto 1 (%)', 'Kreditoren-Ziel 2 (Tage)', 'Kreditoren-Skonto 2 (%)', 'Kreditoren-Ziel 3 Brutto (Tage)', 'Kreditoren-Ziel 4 (Tage)', 'Kreditoren-Skonto 4 (%)', 'Kreditoren-Ziel 5 (Tage)', 'Kreditoren-Skonto 5 (%)', 'Mahnung', 'Kontoauszug', 'Mahntext 1', 'Mahntext 2', 'Mahntext 3', 'Kontoauszugstest', 'Mahnlimit Betrag', 'Mahnlimit %', 'Zinsberechnung', 'Mahnzinssatz 1', 'Mahnzinssatz 2', 'Mahnzinssatz 3', 'Lastschrift', 'Leerfeld', 'Mandantenbank', 'Zahlungsträger', 'Indiv. Feld 1', 'Indiv. Feld 2', 'Indiv. Feld 3', 'Indiv. Feld 4', 'Indiv. Feld 5', 'Indiv. Feld 6', 'Indiv. Feld 7', 'Indiv. Feld 8', 'Indiv. Feld 9', 'Indiv. Feld 10', 'Indiv. Feld 11', 'Indiv. Feld 12', 'Indiv. Feld 13', 'Indiv. Feld 14', 'Indiv. Feld 15', 'Abweichende Anrede (Rechnungsadresse)', 'Adressart (Rechnungsadresse)', 'Straße (Rechnungsadresse)', 'Postfach (Rechnungsadresse)', 'Postleitzahl (Rechnungsadresse)', 'Ort (Rechnungsadresse)', 'Land (Rechnungsadresse)', 'Versandzusatz (Rechnungsadresse)', 'Adresszusatz (Rechnungsadresse)', 'Abw. Zustellbezeichung 1 (Rechnungsadresse)', 'Abw. Zustellbezeichung 2 (Rechnungsadresse)', 'Adresse Gültig von (Rechnungsadresse)', 'Adresse Gültig bis (Rechnungsadresse)', 'Bankleitzahl 6', 'Bankbezeichung 6', 'Bankkonto-Nummer 6', 'Länderkennzeichen 6', 'IBAN-Nr. 6', 'Leerfeld', 'SWIFT-Code 6', 'Abw. Kontoinhaber 6', 'Kennz. Hauptbankverb. 6', 'Bankverb. 6 Gültig von', 'Bankverb. 6 Gültig bis', 'Bankleitzahl 7', 'Bankbezeichung 7', 'Bankkonto-Nummer 7', 'Länderkennzeichen 7', 'IBAN-Nr. 7', 'Leerfeld', 'SWIFT-Code 7', 'Abw. Kontoinhaber 7', 'Kennz. Hauptbankverb. 7', 'Bankverb. 7 Gültig von', 'Bankverb. 7 Gültig bis', 'Bankleitzahl 8', 'Bankbezeichung 8', 'Bankkonto-Nummer 8', 'Länderkennzeichen 8', 'IBAN-Nr. 8', 'Leerfeld', 'SWIFT-Code 8', 'Abw. Kontoinhaber 8', 'Kennz. Hauptbankverb. 8', 'Bankverb. 8 Gültig von', 'Bankverb. 8 Gültig bis', 'Bankleitzahl 9', 'Bankbezeichung 9', 'Bankkonto-Nummer 9', 'Länderkennzeichen 9', 'IBAN-Nr. 9', 'Leerfeld', 'SWIFT-Code 9', 'Abw. Kontoinhaber 9', 'Kennz. Hauptbankverb. 9', 'Bankverb. 9 Gültig von', 'Bankverb. 9 Gültig bis', 'Bankleitzahl 10', 'Bankbezeichung 10', 'Bankkonto-Nummer 10', 'Länderkennzeichen 10', 'IBAN-Nr. 10', 'Leerfeld', 'SWIFT-Code 10', 'Abw. Kontoinhaber 10', 'Kennz. Hauptbankverb. 10', 'Bankverb. 10 Gültig von', 'Bankverb. 10 Gültig bis', 'Nummer Fremdsystem', 'Insolvent', 'SEPA-Mandatsreferenz 1', 'SEPA-Mandatsreferenz 2', 'SEPA-Mandatsreferenz 3', 'SEPA-Mandatsreferenz 4', 'SEPA-Mandatsreferenz 5', 'SEPA-Mandatsreferenz 6', 'SEPA-Mandatsreferenz 7', 'SEPA-Mandatsreferenz 8', 'SEPA-Mandatsreferenz 9', 'SEPA-Mandatsreferenz 10', 'Verknüpftes OPOS-Konto', 'Mahnsperre bis', 'Lastschriftsperre bis', 'Zahlungssperre bis', 'Gebührenberechnung', 'Mahngebühr 1', 'Mahngebühr 2', 'Mahngebühr 3', 'Pauschalenberechnung', 'Verzugspauschale 1', 'Verzugspauschale 2', 'Verzugspauschale 3', 'Alternativer Suchname', 'Status', 'Anschrift manuell geändert (Korrespondenzadresse)', 'Anschrift individuell (Korrespondenzadresse)', 'Anschrift manuell geändert (Rechnungsadresse)', 'Anschrift individuell (Rechnungsadresse)', 'Fristberechnung bei Debitor', 'Mahnfrist 1', 'Mahnfrist 2', 'Mahnfrist 3', 'Letzte Frist'
            ])

        # Zeilen für jede Rechnung schreiben
        for inv in invoices:
            writer.writerow([
                f"{inv.amount_total:.2f}".replace('.', ','),  # Betrag mit Komma formatieren
                "H" if inv.move_type == 'out_invoice' else "S",  # Soll-/Haben-Kennzeichen basierend auf move_type
                inv.currency_id.name or '', '','','',
                '4400',
                inv.partner_id.property_account_receivable_id.code or '', 
                '',
                inv.invoice_date.strftime('%d%m') if inv.invoice_date else '',
                inv.name or '',
                inv.invoice_date_due.strftime('%d%m%y') if inv.invoice_date_due else '',
                '',
                inv.partner_id.name or '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
                '',
            ])

        # CSV-Daten in Base64 kodieren
        file_content.seek(0)
        csv_data = file_content.read().encode('utf-8')
        file_content.close()

        self.file_data = base64.b64encode(csv_data)
        self.file_name = f'EXTF_datev_export_{fields.Date.today()}.csv'

        # Datei zum Download bereitstellen
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=export.wizard&id={self.id}&field=file_data&filename_field=file_name&download=true',
            'target': 'self',
        }
