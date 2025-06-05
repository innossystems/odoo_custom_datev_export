# -*- coding: utf-8 -*-
import base64
import csv
import io
import zipfile
import logging
import calendar
from io import StringIO
from collections import defaultdict
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_repr

_logger = logging.getLogger(__name__)

class ExportWizard(models.TransientModel):
    _name = 'export.wizard'
    _description = 'Export Wizard'

    # ==================== HALB-DYNAMISCHE DATUMS-AUSWAHL ====================
    
    selected_month = fields.Selection(
        selection='_get_available_months',
        string='Monat',
        help='Monat für Export (bis aktueller Monat)'
    )
    
    selected_year = fields.Selection(
        selection='_get_available_years', 
        string='Jahr',
        help='Jahr für Export (letzte 3 Jahre)'
    )
    
    # Umschaltung für manuelle Auswahl
    use_date_range = fields.Boolean(
        string='Manueller Datumsbereich',
        default=False,
        help='Aktivieren für Von/Bis-Datumsauswahl (für ältere Zeiträume)'
    )
    
    # Manuelle Datumsauswahl
    start_date = fields.Date(
        string='Von Datum',
        help='Startdatum für Export'
    )
    
    end_date = fields.Date(
        string='Bis Datum', 
        help='Enddatum für Export'
    )
    
    # Info-Anzeige
    date_info = fields.Char(
        string='Gewählter Zeitraum',
        compute='_compute_date_info',
        help='Zeigt den gewählten Zeitraum an'
    )

    # ==================== STANDARD FELDER ====================
    
    # NEUES FELD: Rechnungstyp-Auswahl mit Radio Buttons
    invoice_type_filter = fields.Selection([
        ('all', 'Rechnungen und Gutschriften'),
        ('invoices_only', 'Nur Rechnungen'),
        ('credit_notes_only', 'Nur Gutschriften')
    ], string='Rechnungstyp', default='all', required=True)
    
    export_mode = fields.Selection([
        ('21', 'Buchungsstapel'),
        ('16', 'Debitoren/Kreditoren')
    ], string='Exportmodus', default='21', required=True)
    
    include_attachments = fields.Boolean(string='PDF Rechnungen & document.xml mit exportieren', default=False)
    is_company_only = fields.Boolean(string="Ist Unternehmen", default=True)
    file_name = fields.Char(string="Dateiname", default="EXTF_datev_export.zip")
    file_data = fields.Binary(string="Datei", readonly=True)

    # ==================== HALB-DYNAMISCHE LISTEN ====================
    
    @api.model
    def _get_available_months(self):
        """
        Gibt alle Monate zurück (Jan-Dez)
        Einfacher und praktischer als komplizierte Einschränkungen
        """
        months = [
            ('01', 'Januar'), ('02', 'Februar'), ('03', 'März'),
            ('04', 'April'), ('05', 'Mai'), ('06', 'Juni'),
            ('07', 'Juli'), ('08', 'August'), ('09', 'September'),
            ('10', 'Oktober'), ('11', 'November'), ('12', 'Dezember')
        ]
        
        _logger.info("Verfügbare Monate: Alle (Jan-Dez)")
        return months

    @api.model 
    def _get_available_years(self):
        """
        Gibt die letzten 3 Jahre zurück (inklusive aktuelles Jahr)
        """
        today = date.today()
        current_year = today.year
        
        # Letzte 3 Jahre: aktuelles Jahr + 2 vergangene
        years = []
        for i in range(3):
            year = current_year - i
            years.append((str(year), str(year)))
        
        _logger.info("Verfügbare Jahre (letzte 3): %s", years)
        return years

    # ==================== DEFAULT-WERTE ====================
    
    @api.model
    def default_get(self, fields_list):
        """Setzt letzten Monat als Standard"""
        res = super().default_get(fields_list)
        
        # Letzten Monat als Standard setzen
        last_month = date.today() - relativedelta(months=1)
        
        _logger.info("Setze Standard auf letzten Monat: %s/%s", last_month.month, last_month.year)
        
        if 'selected_month' in fields_list:
            res['selected_month'] = f"{last_month.month:02d}"
            
        if 'selected_year' in fields_list:
            res['selected_year'] = str(last_month.year)
            
        return res

    # ==================== BERECHNETE FELDER ====================
    
    @api.depends('use_date_range', 'selected_month', 'selected_year', 'start_date', 'end_date')
    def _compute_date_info(self):
        """Zeigt den aktuell gewählten Zeitraum an"""
        for record in self:
            if record.use_date_range:
                if record.start_date and record.end_date:
                    record.date_info = f"Von {record.start_date} bis {record.end_date}"
                else:
                    record.date_info = "Bitte Von/Bis-Datum auswählen"
            else:
                if record.selected_month and record.selected_year:
                    months = dict(record._get_available_months())
                    month_name = months.get(record.selected_month, record.selected_month)
                    record.date_info = f"{month_name} {record.selected_year}"
                else:
                    record.date_info = "Bitte Monat und Jahr auswählen"

    # ==================== FORM-LOGIK ====================
    
    @api.onchange('use_date_range')
    def _onchange_use_date_range(self):
        """Umschaltung zwischen Monat/Jahr und manuellem Datumsbereich"""
        if not self.use_date_range:
            # Zurück zu Monat/Jahr: Letzten Monat setzen
            last_month = date.today() - relativedelta(months=1)
            self.selected_month = f"{last_month.month:02d}"
            self.selected_year = str(last_month.year)
            self.start_date = False
            self.end_date = False
        else:
            # Zu manuellem Bereich: Gewählten Monat als Bereich setzen
            if self.selected_month and self.selected_year:
                year = int(self.selected_year)
                month = int(self.selected_month)
                self.start_date = date(year, month, 1)
                last_day = calendar.monthrange(year, month)[1]
                self.end_date = date(year, month, last_day)

    @api.onchange('export_mode')
    def _onchange_export_mode(self):
        """Anpassung bei Exportmodus-Wechsel"""
        if self.export_mode == '16':  # Debitoren/Kreditoren
            self.use_date_range = False
            self.selected_month = False
            self.selected_year = False
            self.start_date = False
            self.end_date = False
            self.invoice_type_filter = 'all'  # Geändert: neues Feld
            self.include_attachments = False
            self.is_company_only = True
        elif self.export_mode == '21':  # Buchungsstapel
            self.invoice_type_filter = 'all'  # Standard: Alle Rechnungstypen
            self.is_company_only = False
            self.include_attachments = True

    # ==================== VALIDIERUNG ====================
    
    @api.constrains('export_mode', 'use_date_range', 'selected_month', 'selected_year', 'start_date', 'end_date')
    def _check_date_requirements(self):
        """Validierung der Datums-Eingaben"""
        for record in self:
            if record.export_mode == '21':
                if record.use_date_range:
                    if not record.start_date or not record.end_date:
                        raise ValidationError(_("Bitte Von- und Bis-Datum angeben."))
                    # Warnung bei sehr alten Daten
                    if record.start_date < date.today() - relativedelta(years=5):
                        _logger.warning("Sehr alter Datumsbereich gewählt: %s", record.start_date)
                else:
                    if not record.selected_month or not record.selected_year:
                        raise ValidationError(_("Bitte Monat und Jahr auswählen."))

    # ==================== DATUMS-BERECHNUNG ====================
    
    def _get_export_date_range(self):
        """Berechnet Start- und Enddatum für Export"""
        self.ensure_one()
        
        if self.use_date_range:
            return self.start_date, self.end_date
        else:
            if not self.selected_month or not self.selected_year:
                raise UserError(_("Bitte Monat und Jahr auswählen."))
            
            year = int(self.selected_year)
            month = int(self.selected_month)
            
            start_date = date(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = date(year, month, last_day)
            
            return start_date, end_date

    # ==================== EXPORT-LOGIK ====================
    
    def action_export(self):
        """Hauptmethode: Erstellt ZIP-Datei mit DATEV-Export"""
        
        # 1. RECHNUNGEN FINDEN
        invoices = self._get_invoices_for_export()
        if not invoices:
            start_date, end_date = self._get_export_date_range()
            raise UserError(_(
                'Keine Rechnungen für den Zeitraum %s bis %s gefunden.\n\n'
                'Tipp: Verwenden Sie "Manueller Datumsbereich" für ältere Zeiträume.'
            ) % (start_date, end_date))

        # 2. ZIP-DATEI ERSTELLEN
        zip_data, file_name = self._create_export_zip(invoices)
        
        # 3. DATEI SPEICHERN UND DOWNLOAD ANBIETEN
        self.file_data = base64.b64encode(zip_data)
        self.file_name = file_name

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=export.wizard&id={self.id}&field=file_data&filename_field=file_name&download=true',
            'target': 'self',
        }

    def _get_invoices_for_export(self):
        """Erstellt Domain-Filter und sucht passende Rechnungen"""
        domain = []
        
        # Datumsfilter (nur für Buchungsstapel)
        if self.export_mode == '21':
            start_date, end_date = self._get_export_date_range()
            domain += [
                ('invoice_date', '>=', start_date), 
                ('invoice_date', '<=', end_date)
            ]
        
        # Status-Filter: Immer nur gebuchte Rechnungen (removed include_posted)
        domain.append(('state', '=', 'posted'))

        # Rechnungstyp-Filter basierend auf neuem Radio Button
        if self.invoice_type_filter == 'invoices_only':
            domain.append(('move_type', '=', 'out_invoice'))
        elif self.invoice_type_filter == 'credit_notes_only':
            domain.append(('move_type', '=', 'out_refund'))
        elif self.invoice_type_filter == 'all':
            domain.append(('move_type', 'in', ['out_invoice', 'out_refund']))

        _logger.info("Rechnungssuche mit Domain: %s", domain)
        invoices = self.env['account.move'].search(domain)
        _logger.info("Gefundene Rechnungen: %d", len(invoices))
        
        return invoices

    def _create_export_zip(self, invoices):
        """Erstellt ZIP-Datei mit allen notwendigen Export-Dateien"""
        buffer = io.BytesIO()
        
        # Verwende gewählten Datumsbereich für Dateinamen
        if self.export_mode == '21':
            start_date, end_date = self._get_export_date_range()
            if start_date.replace(day=1) == end_date.replace(day=calendar.monthrange(end_date.year, end_date.month)[1]):
                # Ganzer Monat
                date_str = f"{start_date.strftime('%Y-%m')}"
            else:
                # Datumsbereich
                date_str = f"{start_date.strftime('%Y-%m-%d')}_bis_{end_date.strftime('%Y-%m-%d')}"
        else:
            date_str = fields.Date.today().strftime('%Y-%m-%d')
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            if self.export_mode == '21':
                # BUCHUNGSSTAPEL-EXPORT
                base_name = 'EXTF_datev_export_Buchungsstapel'
                if self.include_attachments:
                    base_name += '_PDF'

                # Haupt-CSV-Datei (Buchungen)
                zip_file.writestr(
                    f'{base_name}_{date_str}.csv',
                    self._generate_csv_content(invoices)
                )

                # Partner-CSV-Datei (Debitoren) - nur Firmen
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

                # PDF-ANHÄNGE: Bewährte Logik aus funktionierender Version
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
                # DEBITOREN/KREDITOREN-EXPORT
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
        return buffer.read(), f'{base_name}_{date_str}.zip'

    # ==================== KERN-LOGIK: BUCHUNGSSTAPEL ====================
    def _prepare_buchungsstapel(self, invoices):
        """
        KERN-METHODE: Gruppiert Rechnungspositionen nach Erlöskonto
        
        Für jede Rechnung:
        1. Alle Positionen durchgehen
        2. Nach account_id.code gruppieren  
        3. Beträge pro Konto summieren
        4. Pro Konto eine Export-Zeile erstellen
        """
        _logger.info("=== DATEV Buchungsstapel Vorbereitung START ===")
        lines = []
        
        for inv in invoices:
            _logger.info("Verarbeite Rechnung: %s (Gesamtbetrag: %s)", inv.name, inv.amount_total)
            
            # SCHRITT 1: Positionen nach Erlöskonto gruppieren
            account_groups = self._group_invoice_lines_by_account(inv)
            
            # SCHRITT 2: Für jede Kontogruppe eine Export-Zeile erstellen
            for account_code, total_amount in account_groups.items():
                _logger.info("  -> Erstelle Export-Zeile: Konto=%s, Betrag=%s", account_code, total_amount)
                export_line = self._create_datev_line(inv, account_code, total_amount)
                lines.append(export_line)
        
        _logger.info("=== DATEV Buchungsstapel Vorbereitung ENDE: %d Zeilen erstellt ===", len(lines))
        return lines

    def _group_invoice_lines_by_account(self, invoice):
        """
        Gruppiert die Rechnungspositionen einer Rechnung nach Erlöskonto
        
        Returns: dict {account_code: summe_der_beträge}
        """
        account_groups = defaultdict(float)
        
        _logger.info("  Analysiere %d Rechnungspositionen:", len(invoice.invoice_line_ids))
        
        for i, line in enumerate(invoice.invoice_line_ids, 1):
            # Debug-Info für jede Position
            account_code = line.account_id.code if line.account_id else None
            _logger.info("    Position %d: %s | Konto: %s | Betrag: %s", 
                        i, line.name or 'Ohne Name', account_code or 'KEIN KONTO', line.price_total)
            
            # Position ohne Konto überspringen
            if not account_code:
                _logger.warning("    -> Position %d übersprungen (kein Erlöskonto gesetzt)", i)
                continue
            
            # Betrag zur Kontogruppe hinzufügen
            account_groups[account_code] += line.price_total
            _logger.info("    -> Zu Konto %s addiert: %s (Neue Summe: %s)", 
                        account_code, line.price_total, account_groups[account_code])
        
        # Fallback: Falls keine gültigen Positionen gefunden
        if not account_groups:
            _logger.warning("  WARNUNG: Keine Positionen mit Erlöskonto! Verwende Fallback 4400")
            account_groups['4400'] = invoice.amount_total
        
        _logger.info("  Finale Kontogruppen: %s", dict(account_groups))
        return account_groups

    def _create_datev_line(self, invoice, account_code, amount):
        """
        Erstellt eine einzelne DATEV-Export-Zeile
        
        Args:
            invoice: Die Rechnung
            account_code: Das Erlöskonto 
            amount: Der Betrag für dieses Konto
            
        Returns: Liste mit 125 Feldern für DATEV-Export
        """
        array = [''] * 125
        
        # Grunddaten
        array[0] = f"{amount:.2f}".replace('.', ',')  # Umsatz
        array[1] = 'H' if invoice.move_type == 'out_invoice' else 'S'  # Soll/Haben
        array[2] = invoice.currency_id.name or ''  # Währung
        
        # Konten
        array[6] = account_code  # Erlöskonto (gruppiert nach Rechnungspositionen!)
        array[7] = invoice.partner_id.property_account_receivable_id.code or ''  # Debitorenkonto
        
        # Datum und Referenzen
        array[9] = invoice.invoice_date.strftime('%d%m') if invoice.invoice_date else ''  # Belegdatum
        array[10] = invoice.name or ''  # Rechnungsnummer
        array[11] = invoice.invoice_date_due.strftime('%d%m%y') if invoice.invoice_date_due else ''  # Fälligkeit
        
        # Partner-Info
        partner_name = invoice.partner_id.parent_id.name if invoice.partner_id.parent_id else invoice.partner_id.name
        array[13] = partner_name or ''  # Buchungstext
        
        # BELEGLINK: PDF-Anhang Verknüpfung (für ALLE Zeilen einer Rechnung!)
        if invoice.message_main_attachment_id:
            array[19] = f'BEDI "{invoice._l10n_de_datev_get_guid()}"'
        
        return array

    # ==================== CSV-GENERIERUNG ====================
    def _generate_csv_content(self, invoices):
        """Generiert den CSV-Inhalt basierend auf Exportmodus"""
        output = StringIO()
        writer = csv.writer(output, delimiter=';', quotechar="'", quoting=csv.QUOTE_MINIMAL)

        # DATEV-Header schreiben
        self._write_datev_header(writer)

        if self.export_mode == '21':
            # Buchungsstapel: Header + Datenzeilen
            writer.writerow(self._get_buchungsstapel_header())
            writer.writerows(self._prepare_buchungsstapel(invoices))
        elif self.export_mode == '16':
            # Debitoren/Kreditoren: Header + Partner-Daten
            writer.writerow(self._get_partnerliste_header())
            writer.writerows(self._prepare_partner_list(invoices))

        return output.getvalue()

    def _generate_filtered_partner_csv(self, partners):
        """Generiert CSV nur für Partner (ohne DATEV-Header)"""
        output = StringIO()
        writer = csv.writer(output, delimiter=';', quotechar="'", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(self._get_partnerliste_header())

        for partner in partners:
            array = [''] * 243
            array[0] = partner.property_account_receivable_id.code if partner.property_account_receivable_id else ''
            array[1] = partner.name if partner.is_company else ''
            array[3] = '' if partner.is_company else partner.name
            array[6] = '2' if partner.is_company else '1'
            array[9] = partner.vat or ''
            writer.writerow(array)

        return output.getvalue()

    def _prepare_partner_list(self, invoices):
        """Bereitet Partner-Liste für Export vor"""
        partner_ids = invoices.mapped('partner_id').filtered(lambda p: p)
        if self.is_company_only:
            partner_ids = partner_ids.filtered(lambda p: p.is_company)

        lines = []
        for partner in partner_ids:
            array = [''] * 243
            array[0] = partner.property_account_receivable_id.code if partner.property_account_receivable_id else ''
            array[1] = partner.name if partner.is_company else ''
            array[3] = '' if partner.is_company else partner.name
            array[6] = '2' if partner.is_company else '1'
            array[9] = partner.vat or ''
            lines.append(array)
        return lines

    # ==================== DATEV-HEADER UND -FORMAT ====================
    def _write_datev_header(self, writer):
        """Schreibt den DATEV-spezifischen Header"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]
        
        # Verwende gewählten Datumsbereich für Header
        if self.export_mode == '21':
            start_date, end_date = self._get_export_date_range()
            wirtschaftsjahresbeginn = start_date.strftime('%Y') + '0101'
            start_date_formatted = start_date.strftime('%Y%m%d')
            end_date_formatted = end_date.strftime('%Y%m%d')
        else:
            wirtschaftsjahresbeginn = ''
            start_date_formatted = ''
            end_date_formatted = ''

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
        """Generiert XML-Datei für PDF-Anhänge"""
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

    # ==================== DATEV-HEADER-DEFINITIONEN ==================== 
    def _get_buchungsstapel_header(self):
        """Spalten-Header für Buchungsstapel-Export"""
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
        """Spalten-Header für Partner-Export"""
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

    # ==================== LEGACY METHODEN ====================
    def _datev_find_partner_account(self, account, partner):
        """Legacy-Methode für Partner-Konto-Findung (wird aktuell nicht verwendet)"""
        length = (self.env.company.l10n_de_datev_account_length or 4) + 1
        if not account:
            return ''
        if partner and account.account_type in ('asset_receivable', 'liability_payable'):
            prefix = '1' if account.account_type == 'asset_receivable' else '7'
            return str(prefix) + str(partner.id).rjust(length - 1, '0')
        return str(account.code).ljust(length - 1, '0')