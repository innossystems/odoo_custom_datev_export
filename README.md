# Odoo Custom DATEV Export Modul

Dieses Odoo-Modul bietet eine einfache Möglichkeit, Daten aus Odoo für den DATEV-Export bereitzustellen. Es unterstützt die beiden Exportmodi **Buchungsstapel** und **Debitoren/Kreditoren**, um Unternehmen einen flexiblen und benutzerfreundlichen Exportprozess zu ermöglichen.

---

## Funktionen

- **Einfacher Export**: Bereitet Daten für DATEV auf und exportiert sie im gewünschten Format.
- **Unterstützte Modi**:
  - **Buchungsstapel** (Modus 21): Für den allgemeinen DATEV-Export.
  - **Debitoren/Kreditoren** (Modus 16): Für spezifische Exportanforderungen.
- **Benutzerdefinierte Filter**: Exportiert Daten basierend auf dem ausgewählten Zeitraum, Rechnungsstatus und anderen Kriterien.
- **CSV-Ausgabe**: Erstellt eine exportierbare CSV-Datei im DATEV-konformen Format.

---

## Anforderungen

Damit das Modul korrekt funktioniert, müssen folgende Voraussetzungen erfüllt sein:

1. **Einstellungen des Unternehmens**:
   - Navigiere zu **Einstellungen → Benutzer & Unternehmen → Unternehmen**.
   - Wähle das gewünschte Unternehmen aus.
   - Stelle sicher, dass folgende Felder ausgefüllt sind:
     - **DATEV Beraternummer** (`l10n_de_datev_consultant_number`).
     - **DATEV Kundennummer** (`l10n_de_datev_client_number`).

2. **Installierte Abhängigkeiten**:
   - Das Modul setzt die Basis-Funktionalität von Odoo voraus. Zusätzliche Abhängigkeiten werden automatisch beim Installieren des Moduls berücksichtigt.

---

## Installation

1. Klonen Sie dieses Repository in Ihr Odoo-Addons-Verzeichnis:
   ```bash
   git clone https://github.com/innossystems/odoo_custom_datev_export.git custom_datev_export
2. Aktualisiere die App-Liste in Odoo:
   - Navigiere zu **Apps → Apps**.
   - Klicke auf **Apps aktualisieren**.
3. Installiere das Modul `Odoo Custom DATEV Export`.

---

## Nutzung

1. Navigiere in Odoo zu **Buchhaltung** -> **Berichtswesen** -> **DATEV Export**.
2. Wähle die gewünschten Kriterien:
   - Start- und Enddatum.
   - Exportmodus (Buchungsstapel oder Debitoren/Kreditoren).
   - Zusätzliche Optionen wie "Nur gebuchte Rechnungen" oder "Gutschriften einschließen".
3. Klicke auf **Exportieren**.
4. Die exportierte Datei wird als Download bereitgestellt.

---

## Unterstützung

Falls Fragen oder Probleme auftreten, stehen wir Ihnen gerne zur Verfügung. Kontaktieren Sie uns über die GitHub-Seite des Repositories oder direkt per E-Mail.

---

## Hinweise

- Ohne die korrekte Konfiguration der **DATEV Beraternummer** und **DATEV Kundennummer** im Unternehmensprofil kann das Tool nicht ordnungsgemäß funktionieren.