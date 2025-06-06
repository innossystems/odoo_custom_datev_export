# Odoo Custom DATEV Export

Dieses Odoo-Modul bietet eine einfache Möglichkeit, Daten aus Odoo für den DATEV-Export bereitzustellen. Es unterstützt die beiden Exportmodi Buchungsstapel und Debitoren/Kreditoren, um Unternehmen einen flexiblen und benutzerfreundlichen Exportprozess zu ermöglichen.

## 🚀 Features

- **Einfacher Export**: Bereitet Daten für DATEV auf und exportiert sie im gewünschten Format
- **Buchungsstapel (Modus 21)**: Für den allgemeinen DATEV-Export
- **Debitoren/Kreditoren (Modus 16)**: Für spezifische Exportanforderungen
- **Benutzerdefinierte Filter**: Exportiert Daten basierend auf dem ausgewählten Zeitraum, Rechnungsstatus und anderen Kriterien
- **CSV-Ausgabe**: Erstellt eine exportierbare CSV-Datei im DATEV-konformen Format

## 📋 Voraussetzungen

Damit das Modul korrekt funktioniert, müssen folgende Voraussetzungen erfüllt sein:

### Einstellungen des Unternehmens
Navigiere zu **Einstellungen → Benutzer & Unternehmen → Unternehmen** und stelle sicher, dass folgende Felder ausgefüllt sind:

- **DATEV Beraternummer** (`l10n_de_datev_consultant_number`) - 7-stellige Nummer
- **DATEV Kundennummer** (`l10n_de_datev_client_number`) - 1-5 stellige Nummer

### Installierte Abhängigkeiten
- `base` - Odoo Basis-Modul
- `account` - Buchhaltungs-Modul
- `l10n_de` - Deutsche Lokalisierung

## 🛠️ Installation

1. **Repository klonen:**
   ```bash
   git clone https://github.com/innossystems/odoo_custom_datev_export.git custom_datev_export
   ```

2. **Modul in Odoo-Addons-Verzeichnis platzieren**

3. **App-Liste aktualisieren:**
   - Navigiere zu **Apps → Apps**
   - Klicke auf **Apps aktualisieren**

4. **Modul installieren:**
   - Suche nach "Odoo Custom DATEV Export"
   - Klicke auf **Installieren**

## 💼 Verwendung

1. **DATEV Export aufrufen:**
   - Navigiere zu **Buchhaltung → Berichtswesen → DATEV Export**

2. **Export-Parameter wählen:**
   - **Start- und Enddatum** festlegen
   - **Exportmodus** wählen (Buchungsstapel oder Debitoren/Kreditoren)
   - **Zusätzliche Optionen** wie "Nur gebuchte Rechnungen" oder "Gutschriften einschließen"

3. **Export starten:**
   - Klicke auf **Exportieren**
   - Die exportierte Datei wird als Download bereitgestellt

## 📁 Projektstruktur

```
custom_datev_export/
├── __manifest__.py              # Modul-Manifest
├── __init__.py                  # Haupt-Init
├── README.md                    # Diese Datei
│
├── models/                      # Alle Model-Dateien
│   ├── __init__.py
│   └── export_wizard.py         # Haupt-Wizard (Kern-Funktionalität)
│
├── views/                       # View-Definitionen
│   ├── export_wizard_view.xml   # Wizard-Views
│   └── menu_items.xml          # Menü-Definitionen
│
├── utils/                       # Hilfsfunktionen
│   ├── __init__.py
│   ├── datev_formatter.py      # DATEV-Formatierung
│   ├── csv_helper.py           # CSV-Hilfsfunktionen
│   └── validation.py           # Validierungen
│
├── security/                    # Sicherheits-Konfiguration
│   ├── ir.model.access.csv     # Zugriffsrechte
│   └── security_groups.xml     # Benutzergruppen
│
├── data/                        # Stammdaten
│   └── sequence_data.xml       # Sequenzen
│
├── tests/                       # Test-Dateien
│   ├── __init__.py
│   └── test_export_wizard.py   # Unit Tests
│
└── static/description/          # Modul-Beschreibung
    └── icon.png                # Modul-Icon
```

## 🔧 Konfiguration

### Benutzergruppen
Das Modul definiert zwei Benutzergruppen:

- **DATEV Export User**: Kann DATEV-Exporte durchführen
- **DATEV Export Manager**: Vollzugriff auf Konfiguration und Export

### Sicherheit
- Multi-Company-Unterstützung
- Rollenbasierte Zugriffskontrolle
- Sichere Datenvalidierung

## 🧪 Tests

Das Modul enthält umfassende Tests:

```bash
# Tests ausführen
python -m pytest tests/
```

**Test-Abdeckung:**
- Wizard-Erstellung und -Validierung
- DATEV-Formatierung
- Unternehmens-Konfiguration
- Datumsbereich-Validierung

## 🔄 Migration

Falls Sie von der alten Struktur migrieren:

1. **Sicherung erstellen** des aktuellen Moduls
2. **Schrittweise Migration:**
   - Dateien in neue Verzeichnisse verschieben
   - Imports anpassen
   - Tests durchführen
3. **Funktionalität testen** nach jeder Änderung

## ⚠️ Wichtige Hinweise

- Ohne die korrekte Konfiguration der DATEV Beraternummer und DATEV Kundennummer im Unternehmensprofil kann das Tool nicht ordnungsgemäß funktionieren
- Das Modul erfordert eine deutsche Lokalisierung (SKR03/SKR04)
- Exportdateien sollten vor dem Import in DATEV geprüft werden

## 🆘 Support

Falls Fragen oder Probleme auftreten:

- **GitHub Issues**: [Repository Issues](https://github.com/innossystems/odoo_custom_datev_export/issues)
- **E-Mail Support**: Kontaktieren Sie uns über die GitHub-Seite

## 📄 Lizenz

Dieses Modul steht unter der LGPL-3 Lizenz.

## 🏗️ Entwicklung

### Beitragen
1. Fork das Repository
2. Erstelle einen Feature-Branch
3. Implementiere deine Änderungen
4. Füge Tests hinzu
5. Erstelle einen Pull Request

### Code-Qualität
- Befolge die Odoo-Entwicklungsrichtlinien
- Schreibe Tests für neue Features
- Dokumentiere deine Änderungen

---

**Entwickelt von [Innos Systems](https://github.com/innossystems)**