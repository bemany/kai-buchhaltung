# Airtable-Schema — Quelle der Wahrheit

Base: **„EÜR 2025 Kai"**. Claude legt alle Tabellen, Felder und Views über den Airtable-MCP-Connector
an (`create_table`, `create_field`, …). Feldnamen sind **ASCII-sicher** gehalten, damit Skripte
(`lexoffice_fetch.py`, `build_euer.py`) und CSV-Header identisch sind.

Konventionen:
- Datum: Airtable-Feldtyp **Date** (ISO `YYYY-MM-DD`). In CSV ebenfalls `YYYY-MM-DD`.
- Beträge: Feldtyp **Currency** (EUR, 2 Nachkommastellen). In CSV Dezimalpunkt, z. B. `1234.50`.
- Jede Faktentabelle hat einen **stabilen, eindeutigen Schlüssel** (für Idempotenz/Dedup beim Re-Run).

---

## Table `Eingangsrechnungen`
Belege/Eingangsrechnungen (aus Lexoffice **und** aus Gmail-Postfächern).

| Feld | Typ | Hinweis |
|------|-----|---------|
| `BelegID` | Single line text | **Schlüssel/unique.** Lexoffice: `lex:<voucherId>`; Gmail: `gmail:<messageId>` |
| `Belegnummer` | Single line text | Rechnungs-/Belegnummer des Lieferanten |
| `Rechnungsdatum` | Date | Ausstellungsdatum |
| `Zahlungsdatum` | Date | maßgeblich für EÜR-Periode (Ist-Prinzip) |
| `Beschreibung` | Single line text | Was wurde gezahlt (Leistung) |
| `Lieferant` | Single line text | An wen gezahlt wurde |
| `Nettobetrag` | Currency | Netto |
| `MwSt_Betrag` | Currency | belastete Vorsteuer |
| `Gesamtbetrag` | Currency | Brutto (= Netto + MwSt) |
| `Waehrung` | Single select | Optionen `EUR` (Default), `USD`, `GBP`, `CHF`, … |
| `Auslandsvermerk` | Single line text | z. B. „Reverse-Charge, Lieferant IE" |
| `Steuerschluessel` | Single select | `19`,`7`,`0`,`RC-13b`,`IG-Erwerb`,`IG-Lieferung`,`stfrei` (s. STEUERSCHLUESSEL.md) |
| `Kategorie` | Single select | EÜR-/Aufwandskonto, z. B. `Wareneinkauf`,`Fremdleistung`,`Buerobedarf`,`Reisekosten`,`Sonstiges` |
| `Quelle` | Single select | `lexoffice`,`gmail-1`,`gmail-2` |
| `Quelle_Link` | URL | Lexoffice-Beleglink bzw. Gmail-Permalink |
| `Beleg_PDF` | Attachment | Original-Beleg (PDF) |
| `Notizen` | Long text | Freitext |

**Views:** „Alle", „Unverknüpft (kein Bank-Match)", „Nach Monat (Zahlungsdatum)", „Nach Steuerschlüssel".
*Reverse-Links* zu den Bankkonten erscheinen automatisch, sobald eine Bankzeile auf einen Beleg verlinkt.

---

## Table `Ausgangsrechnungen`
Eigene Rechnungen aus Lexoffice (erstellt **und** bezahlt 2025).

| Feld | Typ | Hinweis |
|------|-----|---------|
| `LexofficeID` | Single line text | **Schlüssel/unique** (invoice `id`, UUID) |
| `Rechnungsnummer` | Single line text | `voucherNumber` |
| `Rechnungsdatum` | Date | `voucherDate` |
| `Kunde` | Single line text | Kontaktname (aus contacts aufgelöst) |
| `KundenID` | Single line text | Lexoffice `contactId` |
| `Netto` | Currency | `totalNetAmount` |
| `MwSt` | Currency | `totalTaxAmount` |
| `Brutto` | Currency | `totalGrossAmount` |
| `Waehrung` | Single select | `currency` |
| `Steuerschluessel` | Single select | wie oben |
| `Status` | Single select | `open`,`paid`,`overdue`,`voided` |
| `Bezahlt_am` | Date | sofern verfügbar |
| `Quelle_Link` | URL | Lexoffice-Beleglink |
| `Notizen` | Long text | |

**Views:** „Alle", „Bezahlt (Status=paid)", „Nach Monat".

---

## Tables `Bank_TradeRepublic`, `Bank_Sparkasse`, `Bank_C24`
Drei Tabellen mit identischem Schema (eigene Tabelle je Bank — bewusst getrennt).

| Feld | Typ | Hinweis |
|------|-----|---------|
| `ZeilenID` | Single line text | **Schlüssel/unique** = Hash aus Datum+Betrag+Verwendungszweck |
| `Buchungsdatum` | Date | |
| `Wertstellung` | Date | optional |
| `Von_An` | Single line text | Auftraggeber bzw. Empfänger |
| `Verwendungszweck` | Single line text | |
| `Betrag` | Currency | `+` Eingang / `−` Ausgang (Vorzeichen) |
| `Waehrung` | Single select | `EUR` |
| `Saldo` | Currency | laufender Kontostand (falls im Export) |
| `Geschaeftlich` | Single select | `ja`,`nein`,`privat` |
| `Beleg_Eingang` | Link → `Eingangsrechnungen` | Zuordnung Ausgabe ↔ Eingangsbeleg |
| `Beleg_Ausgang` | Link → `Ausgangsrechnungen` | Zuordnung Einnahme ↔ eigene Rechnung |
| `Kategorie` | Single select | EÜR-Zuordnung |
| `Notizen` | Long text | |

**Views:** „Geschäftlich = ja", „Unverknüpft", „Nach Monat".

---

## Table `Lohnjournal_2025`
Manueller Import (Lexware Lohn & Gehalt — **keine API**). Format noch offen (CSV/PDF).

| Feld | Typ | Hinweis |
|------|-----|---------|
| `Monat` | Single line text | `YYYY-MM` |
| `Mitarbeiter` | Single line text | Name/Personalnummer |
| `Bruttolohn` | Currency | |
| `Lohnsteuer` | Currency | |
| `Soli` | Currency | |
| `Kirchensteuer` | Currency | |
| `SV_AN_Anteil` | Currency | Sozialversicherung Arbeitnehmer |
| `SV_AG_Anteil` | Currency | Sozialversicherung Arbeitgeber |
| `Nettolohn` | Currency | Auszahlungsbetrag |
| `AG_Gesamtkosten` | Currency | Brutto + AG-Anteil → **EÜR-Personalaufwand** |
| `Auszahlungsdatum` | Date | |
| `Bank_Ref` | Single line text | ZeilenID der Lohnzahlung (Bank) |
| `Notizen` | Long text | |

---

## Table `Vermietung_Verpachtung` (Anlage V — separat, NICHT im EÜR-Saldo)

| Feld | Typ | Hinweis |
|------|-----|---------|
| `Objekt` | Single line text | Immobilie/Adresse |
| `Mieter` | Single line text | |
| `Monat` | Single line text | `YYYY-MM` |
| `Kaltmiete` | Currency | |
| `Nebenkosten` | Currency | Umlagen |
| `Gesamtmiete` | Currency | |
| `Eingangsdatum` | Date | tatsächlicher Zahlungseingang |
| `Bank_Ref` | Single line text | ZeilenID (Bank) |
| `Werbungskosten` | Currency | optional |
| `Notizen` | Long text | |

---

## Table `EUER_Uebersicht` (angelehnt an amtliche Anlage EÜR 2025)
Wird von `scripts/build_euer.py` berechnet bzw. von Claude befüllt.

| Feld | Typ | Hinweis |
|------|-----|---------|
| `Position` | Single line text | z. B. „Umsatzerlöse (netto)" |
| `Abschnitt` | Single select | `Einnahmen`,`Ausgaben`,`Saldo`,`nachrichtlich` |
| `Betrag` | Currency | |
| `EUER_Zeile` | Single line text | amtliche Zeilennr. zur Orientierung (z. B. „Z. 14") |
| `Berechnung` | Single line text | Formel/Herkunft (z. B. „Σ Ausgangsrechnungen.Netto") |

**Standard-Positionen** (siehe `build_euer.py`):
- Einnahmen: Umsatzerlöse (netto), vereinnahmte USt, sonstige Einnahmen → **Summe Einnahmen**
- Ausgaben: Wareneinkauf/Fremdleistung, Personalkosten (AG_Gesamtkosten), gezahlte Vorsteuer,
  übrige Betriebsausgaben → **Summe Ausgaben**
- **Saldo = Summe Einnahmen − Summe Ausgaben**
- nachrichtlich: Einkünfte V&V (Anlage V) — **nicht** im Saldo
