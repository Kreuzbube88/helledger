# 📅 Fixkosten

Fixkosten sind regelmäßige Buchungen, die HELLEDGER automatisch jeden Monat als Transaktionen anlegt.

---

## Typen

| Typ | Beschreibung |
|-----|--------------|
| **Einnahme** | Regelmäßiges Einkommen (z. B. Gehalt) |
| **Ausgabe** | Wiederkehrende Ausgabe (z. B. Miete, Strom, Abos) |
| **Sparüberweisung** | Automatischer Transfer von einem Konto auf ein Sparkonto |

---

## Intervalle

Fixkosten können mit verschiedenen Buchungsintervallen angelegt werden:

| Intervall | Buchung |
|-----------|---------|
| Monatlich | Jeden Monat |
| Quartalsweise | Jan, Apr, Jul, Okt |
| Halbjährlich | Jan, Jul |
| Jährlich | Einmal pro Jahr |

---

## Reserveansicht

Für nicht-monatliche Fixkosten (z. B. jährliche Versicherung) berechnet HELLEDGER automatisch den **monatlichen Rücklagenanteil**. Die Reserveansicht zeigt, wie viel pro Monat zurückgelegt werden sollte.

---

## Automatische Buchung

HELLEDGER bucht Fixkosten automatisch beim Laden des Dashboards für den aktuellen Monat. Bereits gebuchte Monate werden nicht doppelt gebucht.

---

## Ablaufwarnung

Fixkosten mit einem **Enddatum** zeigen im Dashboard eine Warnung, wenn sie innerhalb der nächsten 30 Tage auslaufen.

---

## Sparüberweisung einrichten

1. Typ **Sparüberweisung** wählen
2. **Quellkonto** (z. B. Fixkosten-Konto) auswählen
3. **Zielkonto** (Sparkonto) auswählen
4. Betrag und Startdatum festlegen

Die Sparquote im Dashboard und der Monatsansicht wird automatisch auf Basis aller aktiven Sparüberweisungen berechnet.
