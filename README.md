# kai-buchhaltung — EÜR 2025

Werkzeugkasten zur Aufbereitung der **Einnahmenüberschussrechnung (EÜR) 2025** für Kai.

> **Wichtig:** Dieses Repo ist ein **Runbook + Skripte**. Es führt die Buchhaltung nicht selbst aus,
> sondern wird von **Kai in seiner eigenen Claude-Cloud-Session mit seinen eigenen Connectoren**
> (Gmail, Airtable, Lexoffice-API-Key) abgearbeitet. Datenablage ist **Airtable**.

## Architektur in einem Bild

```
 Lexoffice REST API ──┐
 (Public API Key)     │   scripts/lexoffice_fetch.py ──► data/*.csv ─┐
                      │                                              │
 Gmail Postfach A ────┤   Claude (MCP Gmail-Connector) ─────────────┤
 Gmail Postfach B ────┘   + Label "EÜR-2025-erfasst"                │
                                                                    ▼
 Bank-CSV (TR/Sparkasse/C24) ─────────────► manueller Import ──►  AIRTABLE Base "EÜR 2025 Kai"
 Lohnjournal (Lexware Lohn&Gehalt, kein API) ► manueller Import ─►  (Claude legt Tables/Felder/Views
 Mieteinnahmen (Anlage V) ────────────────► manueller Import ──►   via MCP-Connector selbst an)
                                                                    │
                                          scripts/build_euer.py ◄───┘  ──► EUER_Uebersicht
```

## Quickstart (für Kai)

1. **Airtable vorbereiten** (einmalig, manuell):
   - Kostenlosen Account auf airtable.com anlegen.
   - Eine **leere** Base anlegen, z. B. „EÜR 2025 Kai" (Standard-Tabelle kann bleiben, wird ersetzt/ignoriert).
   - In der Claude-Session den **Airtable-Connector** verbinden und für diese Base autorisieren.
   - Danach Claude bitten: *„Lege die Tabellen laut `docs/SCHEMA.md` an."* → Claude erstellt
     Tables, Felder und Views komplett selbst über den Connector. Du musst nichts manuell bauen.
2. **Lexoffice-Key bereitstellen:** Public-API-Key im Lexware/Lexoffice-Konto erzeugen
   (Einstellungen → Public API) und in der Session als Env-Variable setzen:
   `export LEXOFFICE_API_KEY=...` — **nicht ins Repo schreiben**.
3. **Gmail:** Beide Postfächer werden nacheinander verbunden (zwei Sessions, siehe Runbook).
4. **Runbook abarbeiten:** `docs/RUNBOOK.md` Schritt für Schritt folgen.

## Inhalt

| Pfad | Zweck |
|------|-------|
| `docs/RUNBOOK.md` | Schritt-für-Schritt-Playbook (das Hauptdokument für Kais Session) |
| `docs/SCHEMA.md` | Tabellen-, Feld- und View-Definitionen (Quelle der Wahrheit) |
| `docs/STEUERSCHLUESSEL.md` | Referenz der Steuerschlüssel/USt-Sätze |
| `scripts/lexoffice_fetch.py` | Holt Ausgangsrechnungen, Eingangsbelege, Kontakte aus der Lexoffice-API |
| `scripts/build_euer.py` | Aggregiert die Tabellen zur EÜR-Übersicht + Bank-Matching-Hilfe |
| `scripts/airtable_scaffold.py` | Optionale Referenz zum Base-Aufbau (primär macht das Claude via MCP) |
| `data/` | Kanonische Zwischendaten (CSV/JSON), gitignored |

## Steuerliche Grundannahmen

- **Regelbesteuert** (keine Kleinunternehmerregelung §19) → volle MwSt-/Vorsteuer-/Steuerschlüssel-Logik.
- **EÜR = Zufluss-/Abfluss-Prinzip** (Ist): maßgeblich ist i. d. R. das **Zahlungsdatum**, nicht das Rechnungsdatum.
- **Vermietung & Verpachtung** (§21 EStG) gehört in die **Anlage V**, **nicht** in den EÜR-Saldo.
  Das Blatt `Vermietung_Verpachtung` wird separat geführt und nur nachrichtlich ausgewiesen.
- **Lohn/Gehalt** ist über die Lexoffice **Public API nicht abrufbar** → manueller Export aus
  „Lexware Lohn & Gehalt".

> Dies ist keine Steuerberatung. Ergebnisse vor Abgabe mit einem Steuerberater abstimmen.

## Sicherheit

- `LEXOFFICE_API_KEY` und Airtable-Token ausschließlich als Env-Variablen in Kais Umgebung halten.
- `data/`-Inhalte (enthalten personenbezogene/steuerliche Daten) sind via `.gitignore` vom Commit ausgeschlossen.

## Offene Punkte (TODO)

- [ ] **Lohnjournal-Quelle/-Format** final klären (CSV vs. PDF aus Lexware Lohn & Gehalt).
- [ ] **V&V-Details**: Objekte, Mietverträge, Werbungskosten (Kai liefert Kontext nach).
- [ ] **Konkrete Gmail-Adressen** der zwei Postfächer + Belegkriterien/Absenderliste.
- [ ] Versteuerungsart (Ist/Soll) bestätigen — Default Ist.
