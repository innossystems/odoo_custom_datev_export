# 🧾 Odoo Custom DATEV Export Modul

> **Ein professionelles Odoo-Modul für nahtlosen DATEV-Export**

Dieses Odoo-Modul bietet eine intuitive und leistungsstarke Lösung für den Export von Buchhaltungsdaten im DATEV-Format. Es wurde speziell für deutsche Unternehmen entwickelt, die ihre Odoo-Daten effizient an DATEV-Systeme übertragen möchten.

---

## ⚠️ **Beta-Version**
**Achtung:** Dieses Plugin befindet sich noch im Beta-Stadium. Bitte testen Sie es zunächst in einer Testumgebung, bevor Sie es produktiv einsetzen. Nutzung auf eigene Gefahr!

---

## 📁 **Vereinfachte Modul-Struktur**

```
custom_datev_export/
├── __init__.py                    # Wizard importieren
├── __manifest__.py               # Modul-Definition
├── README.md                     # Diese Dokumentation
├── security/
│   └── ir.model.access.csv       # Zugriffsrechte
├── views/
│   └── export_wizard_view.xml    # Einzige View-Datei
└── wizard/
    ├── __init__.py               # Wizard initialisieren
    └── export_wizard.py          # Haupt-Export-Logik
```

## ✨ **Hauptfunktionen**

### 📊 **Zwei Export-Modi**
- **🔸 Buchungsstapel (Modus 21)**: Vollständiger Export aller Buchungen mit intelligenter Gruppierung nach Erlöskonten
- **🔸 Debitoren/Kreditoren (Modus 16)**: Spezialisierter Export für Kundenstammdaten

### 🎯 **Erweiterte Filter-Optionen**
- **📅 Flexible Zeitraumauswahl**: 
  - Schnelle Monatsauswahl für die letzten 3 Jahre
  - Benutzerdefinierte Datumsbereiche für spezielle Anforderungen
- **📋 Intelligente Rechnungsfilter**:
  - Alle Kundenbelege (Rechnungen + Gutschriften)
  - Nur Kundenrechnungen
  - Nur Kundengutschriften
- **🔗 PDF-Anhänge**: Automatische Verknüpfung von Rechnungs-PDFs mit DATEV-Beleglinks

### 🚀 **Technische Highlights**
- **💡 Intelligente Kontogruppierung**: Rechnungen werden automatisch nach Erlöskonten aufgeteilt
- **📎 Vollständige Anhang-Integration**: PDFs und XML-Dokumente werden zur ZIP-Datei hinzugefügt
- **🎨 Benutzerfreundliche Oberfläche**: Intuitive Radio-Buttons und dynamische Feldanzeige
- **✅ DATEV-konforme Ausgabe**: Standardkonforme CSV-Dateien mit korrekten Headern

---

## 🔧 **Systemanforderungen**

### **Odoo-Version**
- Odoo 18.0+
- Community oder Enterprise Edition

### **Erforderliche Module**
- `account` (Buchhaltung)
- `base` (Basis-Framework)

### **Python-Abhängigkeiten**
```python
# Standardbibliotheken (bereits in Odoo enthalten)
import csv
import zipfile
import base64
from datetime import datetime
from dateutil.relativedelta import relativedelta
```

---

## ⚙️ **Konfiguration**

### **1. DATEV-Stammdaten konfigurieren**

Navigiere zu: **Einstellungen → Benutzer & Unternehmen → Unternehmen**

**Erforderliche Felder:**
| Feld | Beschreibung | Beispiel |
|------|--------------|----------|
| **DATEV Beraternummer** | Ihre offizielle DATEV-Beraternummer | `12345` |
| **DATEV Kundennummer** | Ihre DATEV-Kundennummer | `67890` |
| **Kontolänge** | Standardlänge der Kontonummern | `4` |

> ⚠️ **Wichtig:** Ohne diese Angaben funktioniert der Export nicht korrekt!

### **2. Zugriffsrechte**

Das Modul verwendet standardmäßig die Buchhaltungsberechtigungen:
- **Buchhalter**: Vollzugriff auf Export-Funktionen
- **Buchhaltungsmanager**: Vollzugriff auf alle Features

---

## 🚀 **Installation**

### **Schritt 1: Repository klonen**
```bash
cd /path/to/odoo/addons
git clone https://github.com/innossystems/odoo_custom_datev_export.git custom_datev_export
```

### **Schritt 2: Odoo-Installation**
1. Starte Odoo im Developer-Modus
2. Navigiere zu **Apps → Apps aktualisieren**
3. Suche nach "**Custom DATEV Export**"
4. Klicke auf **Installieren**

### **Schritt 3: Konfiguration prüfen**
Stelle sicher, dass alle DATEV-Stammdaten korrekt eingegeben wurden (siehe Konfiguration).

---

## 📖 **Verwendung**

### **Export starten**
### Der Benutzer muss Mitglied der Gruppe account.group_account_manager / Buchhaltung / Abrechnungsadministrator sein
1. **Navigiere zu**: `Buchhaltung → Berichtswesen → DATEV Export`
2. **Wähle Exportmodus**:
   - 🔸 **Buchungsstapel**: Für Buchungsexport
   - 🔸 **Debitoren/Kreditoren**: Für Stammdatenexport

### **Zeitraum festlegen**
**Option A: Schnellauswahl**
- Wähle **Monat** und **Jahr** aus den Dropdown-Listen
- Standard: Vorheriger Monat

**Option B: Benutzerdefiniert**
- Aktiviere "**Benutzerdefinierter Datumsbereich**"
- Setze **Von-Datum** und **Bis-Datum**

### **Filter konfigurieren**
**Rechnungstyp auswählen:**
- 🔘 **Rechnungen und Gutschriften** *(Standard)*
- 🔘 **Nur Rechnungen**
- 🔘 **Nur Gutschriften**

**Optionale Einstellungen:**
- ☑️ **PDF-Rechnungen anhängen**: Fügt PDF-Dateien zur ZIP hinzu
- ☑️ **Nur Unternehmen**: Filtert nur Firmen-Partner *(bei Debitoren/Kreditoren)*

### **Export durchführen**
Klicke auf **Exportieren** → ZIP-Datei wird automatisch heruntergeladen

---

## 📁 **Export-Struktur**

### **Buchungsstapel-Export**
```
EXTF_datev_export_Buchungsstapel_2024-01.zip
├── EXTF_datev_export_Buchungsstapel_2024-01.csv
├── EXTF_datev_export_Debitoren_Kreditoren_Buchungsstapel_2024-01.csv
├── Rechnung_001.pdf (optional)
├── Rechnung_002.pdf (optional)
└── document.xml (optional)
```

### **Debitoren/Kreditoren-Export**
```
EXTF_datev_export_Debitoren_Kreditoren_2024-01-15.zip
└── EXTF_datev_export_Debitoren_Kreditoren_2024-01-15.csv
```

---

## 🔍 **Besondere Features**

### **Intelligente Rechnungsaufteilung**
Rechnungen mit mehreren Positionen werden automatisch nach Erlöskonten gruppiert:

**Beispiel:**
```
Rechnung R001 (150€):
├── Position 1: 100€ → Konto 4400 (Verkauf)
└── Position 2: 50€ → Konto 4500 (Service)

DATEV-Export:
├── Zeile 1: 100€, Konto 4400, Beleglink "BEDI abc-123"
└── Zeile 2: 50€, Konto 4500, Beleglink "BEDI abc-123"
```

### **PDF-Belegverknüpfung**
- Automatische GUID-Generierung für jede Rechnung
- `document.xml` verknüpft PDFs mit DATEV-Buchungen
- Alle Zeilen einer Rechnung teilen sich die gleiche Beleglink-ID

---

## 📋 **Changelog**

### **Version 1.0.4**
- ✨ Vereinfachte Modul-Struktur (40% weniger Dateien)
- 🔄 Entfernung redundanter Actions und Views
- 🧹 Code-Bereinigung und Performance-Optimierung
- ✅ 100% gleiche Funktionalität bei schlankerem Code

### **Version 1.0-beta**
- ✨ Initiale Veröffentlichung
- ✅ Buchungsstapel-Export mit Kontogruppierung
- ✅ Debitoren/Kreditoren-Export
- ✅ PDF-Anhang-Funktionalität
- ✅ Flexible Zeitraumauswahl
- ✅ Radio-Button-Interface für Rechnungstypen

---

## 📜 **Lizenz**

Dieses Projekt steht unter der **AGPL-3.0 Lizenz**. Weitere Details finden Sie in der [LICENSE](LICENSE) Datei.

---

*Letzte Aktualisierung: Juni 2025*