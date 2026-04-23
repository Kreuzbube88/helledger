# 📥 Import

HELLEDGER unterstützt den Import von Transaktionen aus **CSV**, **OFX** und **QFX** Dateien.

---

## Import starten

1. Im Menü **Import** auswählen
2. Datei per Drag & Drop oder Klick hochladen
3. Spalten mappen
4. Import starten

---

## CSV-Import

CSV-Dateien werden mit einem **Spalten-Mapping** importiert. Du kannst selbst festlegen, welche Spalte Datum, Betrag und Beschreibung enthält.

**Konfigurierbar:**
- Datumsformat (z. B. `DD.MM.YYYY`, `YYYY-MM-DD`)
- Dezimaltrennzeichen (Komma oder Punkt)
- Standardkategorie (optional)
- Zielkonto

**Beispiel-Format:**
```
Datum;Beschreibung;Betrag
01.04.2026;Gehalt;2500,00
03.04.2026;Miete;-900,00
```

---

## OFX / QFX-Import

OFX- und QFX-Dateien (typische Bankexporte) werden automatisch erkannt und geparst. Kein manuelles Spalten-Mapping notwendig.

---

## Duplikaterkennung

HELLEDGER erkennt bereits importierte Transaktionen anhand von Datum, Betrag und Beschreibung und überspringt Duplikate automatisch. Die Ergebnisseite zeigt:

- ✅ Importiert
- ⚠️ Duplikate gefunden
- ❌ Fehler
