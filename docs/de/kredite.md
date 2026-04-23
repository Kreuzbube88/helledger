# 🏦 Kredite

Unter **Kredite** verwaltest du Verbraucher- und Immobilienkredite mit vollständigem Tilgungsplan.

---

## Kredittypen

| Typ | Beschreibung |
|-----|--------------|
| **Verbraucherkredit** | Klassischer Ratenkredit |
| **Immobilienkredit** | Hypothek mit Kaufpreis, Eigenkapital und Grundschuld |

---

## Kredit anlegen

HELLEDGER berechnet automatisch den fehlenden Wert, wenn du **3 von 4** Feldern ausfüllst:

- Darlehensbetrag
- Zinssatz (p.a.)
- Monatliche Rate
- Laufzeit (Monate)

---

## Tilgungsplan

Der **Tilgungsplan** zeigt monatlich:

| Spalte | Beschreibung |
|--------|--------------|
| Monat / Datum | Buchungsdatum |
| Rate | Gesamte monatliche Zahlung |
| Zinsen | Zinsanteil der Rate |
| Tilgung | Tilgungsanteil |
| Sondertilgung | Einmalige oder regelmäßige Sonderzahlungen |
| Restschuld | Verbleibende Schuld nach Buchung |

Der Plan kann als **CSV** exportiert werden.

---

## Sondertilgungen

Unter dem Tab **Sondertilgungen** kannst du zusätzliche Zahlungen erfassen:

- **Einmalig** — zu einem bestimmten Datum
- **Wiederkehrend** — mit Intervall und optionalem Enddatum

**Effekte:**
- **Laufzeit verkürzen** — Rate bleibt gleich, Laufzeit sinkt
- **Rate reduzieren** — Laufzeit bleibt gleich, Rate sinkt

---

## KPIs

| KPI | Beschreibung |
|-----|--------------|
| Zinsen gesamt | Gesamtzinskosten über die Laufzeit |
| Gesamt gezahlt | Summe aller Zahlungen |
| Zinsen gespart | Ersparnis durch Sondertilgungen |
| Monate gespart | Verkürzung der Laufzeit |
| Aktueller Saldo | Heutige Restschuld |
| Voraussichtl. Abzahlung | Geschätztes Abzahlungsdatum |

---

## Automatische Fixkosten-Verknüpfung

Beim Anlegen eines Kredits wird automatisch eine Fixkosten-Kategorie erstellt. Die monatliche Rate wird über die Fixkosten-Verwaltung gebucht. Nach dem Markieren als "abbezahlt" wird die Kategorie archiviert.
