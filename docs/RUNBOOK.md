# RUNBOOK — EÜR 2025 für Kai

> 👉 **Ohne Technik-Vorkenntnisse?** Nutze stattdessen die einfache
> **[Anleitung für Kai](ANLEITUNG-FUER-KAI.md)**. Dieses RUNBOOK ist die technische Detailfassung.

Dieses Playbook arbeitet Kai (bzw. Claude in Kais Session) Schritt für Schritt ab. Es ist auf
**mehrere Sessions** ausgelegt, weil (a) die zwei Gmail-Postfächer nacheinander verbunden werden und
(b) zwischendurch manuelle Exporte (Bank, Lohn) gebraucht werden. Jeder Schritt ist **idempotent** —
ein erneuter Lauf überspringt bereits Erfasstes.

Datenablage: **Airtable** (Base „EÜR 2025 Kai"). Schema: `docs/SCHEMA.md`.

---

## Session 0 — Setup (einmalig)

1. **Airtable-Base anlegen (manuell durch Kai):** Account auf airtable.com, **leere** Base „EÜR 2025 Kai",
   Airtable-Connector in der Claude-Session verbinden + Base autorisieren.
2. **Tabellen anlegen (durch Claude via Connector):**
   > Prompt an Claude: *„Lege in der Base ‚EÜR 2025 Kai' alle Tabellen, Felder und Views exakt nach
   > `docs/SCHEMA.md` an. Nutze die Airtable-MCP-Tools (`create_table`, `create_field`). Single-Select-
   > Optionen und Feldtypen wie dokumentiert."*
   - Reihenfolge: zuerst `Eingangsrechnungen` und `Ausgangsrechnungen` (Link-Ziele), dann die drei
     `Bank_*`-Tabellen (mit Link-Feldern `Beleg_Eingang`/`Beleg_Ausgang`), dann `Lohnjournal_2025`,
     `Vermietung_Verpachtung`, `EUER_Uebersicht`.
   - Standard-Tabelle, die Airtable beim Base-Anlegen erzeugt, danach löschen oder ignorieren.
3. **Lexoffice-Key setzen:** `export LEXOFFICE_API_KEY=...` (nicht committen). Netzfreigabe zu
   `api.lexoffice.io` sicherstellen.
4. **Gmail-Label vorbereiten:** In **beiden** Postfächern Label `EÜR-2025-erfasst` anlegen
   (Claude: `create_label`). Wird beim ersten Postfach in Session 1/2 erledigt.

---

## Session 1 — Lexoffice (read-only API)

Skript: `scripts/lexoffice_fetch.py` (schreibt kanonische CSV nach `data/`).

```bash
pip install -r scripts/requirements.txt
python scripts/lexoffice_fetch.py --what contacts  --out data        # Kontakte-Cache (Vorlauf)
python scripts/lexoffice_fetch.py --what sales      --year 2025 --out data   # Ausgangsrechnungen
python scripts/lexoffice_fetch.py --what purchases  --year 2025 --out data   # Eingangsbelege
# oder alles auf einmal:
python scripts/lexoffice_fetch.py --what all --year 2025 --out data
```

Erzeugt:
- `data/contacts.csv` (Lookup contactId → Name)
- `data/ausgangsrechnungen.csv` (Status open/paid/overdue/voided, Jahr 2025)
- `data/eingangsrechnungen_lexoffice.csv` (Quelle = `lexoffice`)

**Nach Airtable schreiben (durch Claude via Connector):**
> *„Lies `data/ausgangsrechnungen.csv` und upserte die Zeilen in die Tabelle `Ausgangsrechnungen`
> (Schlüssel `LexofficeID`: existiert → update, sonst create). Gleiches für
> `data/eingangsrechnungen_lexoffice.csv` → `Eingangsrechnungen` (Schlüssel `BelegID`)."*
Dedup über den Schlüssel verhindert Doppelzeilen bei Re-Run.

---

## Session 2 — Gmail Postfach A (Belege)

1. Connector auf **Postfach A** verbinden. Label `EÜR-2025-erfasst` anlegen, falls noch nicht vorhanden.
2. Belege suchen (Claude `search_threads`), Beispiel-Query:
   ```
   has:attachment after:2024/12/31 before:2026/01/01 -label:EÜR-2025-erfasst
   (Rechnung OR Invoice OR Beleg OR Quittung OR Receipt)
   ```
3. Pro Treffer: Beleg-Daten extrahieren (Lieferant, Datum, Netto/MwSt/Brutto, Steuerschlüssel) →
   in `Eingangsrechnungen` upserten mit:
   - `BelegID = gmail:<messageId>`, `Quelle = gmail-1`, `Quelle_Link =` Gmail-Permalink,
   - PDF als `Beleg_PDF` (Attachment).
4. **Erst nach erfolgreichem Eintrag** das Label setzen (`label_message`/`label_thread` mit der ID von
   `EÜR-2025-erfasst`). → Mail wird bei künftigen Läufen übersprungen.
5. **Doppelte Idempotenz:** Falls eine Mail ohne Label, aber mit bereits existierender `BelegID`
   auftaucht (z. B. Session-Abbruch), per `BelegID` deduplizieren statt neu anlegen.

➡️ **PAUSE / Sessionwechsel:** Connector auf Postfach B umstellen.

---

## Session 3 — Gmail Postfach B (Belege)

Identisch zu Session 2, aber `Quelle = gmail-2`. Eigenes Label `EÜR-2025-erfasst` im Postfach B.

---

## Session 4 — Manuelle Importe (keine API)

1. **Bankumsätze:** CSV-Export aus Trade Republic, Sparkasse, C24 herunterladen → je Datei in die
   passende `Bank_*`-Tabelle importieren. `ZeilenID` = Hash aus Datum+Betrag+Verwendungszweck
   (Dedup). `Geschaeftlich` (ja/nein/privat) setzen — nur `ja`-Zeilen sind EÜR-relevant.
   - Tipp: `scripts/build_euer.py --hash-bank data/bank_*.csv` erzeugt stabile ZeilenIDs (s. Skript).
2. **Lohnjournal:** Export aus „Lexware Lohn & Gehalt" (Format noch zu klären, CSV bevorzugt) →
   Tabelle `Lohnjournal_2025`. `AG_Gesamtkosten` = Bruttolohn + SV_AG_Anteil (EÜR-Personalaufwand).
3. **Mieteinnahmen (Anlage V):** aus Bankeingängen / Mietverträgen → `Vermietung_Verpachtung`.
   **Nicht** in den EÜR-Saldo einrechnen.

---

## Session 5 — Verknüpfung & Aggregation

1. **Bank ↔ Beleg/Rechnung matchen:** Claude verknüpft `Bank_*`-Zeilen (Geschaeftlich=ja) mit
   `Eingangsrechnungen`/`Ausgangsrechnungen` über Betrag + Datum (±Toleranz) + Name. Treffer →
   Link-Feld `Beleg_Eingang`/`Beleg_Ausgang` setzen, im Beleg ggf. `Zahlungsdatum` nachtragen.
2. **EÜR-Übersicht berechnen:**
   ```bash
   python scripts/build_euer.py --data data --out data/euer_uebersicht.csv
   ```
   Liest `eingangsrechnungen*.csv`, `ausgangsrechnungen.csv`, `lohnjournal.csv` und schreibt die
   Positionen. Danach durch Claude in Tabelle `EUER_Uebersicht` upserten.
3. **Plausibilität:** Saldo = Summe Einnahmen − Summe Ausgaben. V&V separat (nachrichtlich).
4. **Abschluss:** Ergebnis mit Steuerberater abstimmen. CSV/Excel-Export aus Airtable für den StB.

---

## Idempotenz-Regeln (gelten überall)

| Quelle | Schlüssel | Übersprungen bei Re-Run, wenn … |
|--------|-----------|-------------------------------|
| Lexoffice | `LexofficeID` / `BelegID=lex:<id>` | Schlüssel existiert bereits → update statt create |
| Gmail | `BelegID=gmail:<messageId>` + Label `EÜR-2025-erfasst` | Mail trägt Label **oder** BelegID existiert |
| Bank | `ZeilenID` (Hash) | Hash existiert bereits |

> Reihenfolge-Abhängigkeiten: Sessions 1–3 sind unabhängig (außer Kontakte-Vorlauf in S1).
> Session 5 setzt voraus, dass 1–4 abgeschlossen sind.
