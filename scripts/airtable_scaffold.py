#!/usr/bin/env python3
"""OPTIONALE Referenz: Airtable-Base-Schema als Daten + optionaler Aufbau via Meta-API.

Im Normalfall baut **Claude die Tabellen über den Airtable-MCP-Connector** (create_table /
create_field) direkt anhand von docs/SCHEMA.md. Dieses Skript ist nur eine maschinenlesbare
Referenz desselben Schemas und kann die Base alternativ über die Airtable Metadata-API anlegen.

Modi:
    python scripts/airtable_scaffold.py                 # Schema als Übersicht ausgeben (Default)
    python scripts/airtable_scaffold.py --json          # Schema als JSON ausgeben
    python scripts/airtable_scaffold.py --create        # via Meta-API anlegen (Env nötig)

Für --create:
    AIRTABLE_TOKEN    Personal Access Token mit Scope schema.bases:write
    AIRTABLE_BASE_ID  ID der (leeren) Base, z. B. appXXXXXXXXXXXXXX
"""
from __future__ import annotations

import argparse
import json
import os
import sys

EUR = {"name": "EUR", "symbol": "€", "precision": 2}

STEUERSCHLUESSEL = ["19", "7", "0", "RC-13b", "IG-Erwerb", "IG-Lieferung", "stfrei"]
WAEHRUNGEN = ["EUR", "USD", "GBP", "CHF"]

# Feldtyp-Kürzel: t=single line text, l=long text, d=date, c=currency, s=single select, u=url, a=attachment
def f(name, kind, options=None):
    return {"name": name, "kind": kind, "options": options or {}}

SCHEMA = {
    "Eingangsrechnungen": [
        f("BelegID", "t"), f("Belegnummer", "t"), f("Rechnungsdatum", "d"),
        f("Zahlungsdatum", "d"), f("Beschreibung", "t"), f("Lieferant", "t"),
        f("Nettobetrag", "c"), f("MwSt_Betrag", "c"), f("Gesamtbetrag", "c"),
        f("Waehrung", "s", WAEHRUNGEN), f("Auslandsvermerk", "t"),
        f("Steuerschluessel", "s", STEUERSCHLUESSEL),
        f("Kategorie", "s", ["Wareneinkauf", "Fremdleistung", "Buerobedarf",
                             "Reisekosten", "Sonstiges"]),
        f("Quelle", "s", ["lexoffice", "gmail-1", "gmail-2"]),
        f("Quelle_Link", "u"), f("Beleg_PDF", "a"), f("Notizen", "l"),
    ],
    "Ausgangsrechnungen": [
        f("LexofficeID", "t"), f("Rechnungsnummer", "t"), f("Rechnungsdatum", "d"),
        f("Kunde", "t"), f("KundenID", "t"), f("Netto", "c"), f("MwSt", "c"), f("Brutto", "c"),
        f("Waehrung", "s", WAEHRUNGEN), f("Steuerschluessel", "s", STEUERSCHLUESSEL),
        f("Status", "s", ["open", "paid", "overdue", "voided"]),
        f("Bezahlt_am", "d"), f("Quelle_Link", "u"), f("Notizen", "l"),
    ],
    # Bank_TradeRepublic / Bank_Sparkasse / Bank_C24 teilen sich dieses Schema.
    "_Bank": [
        f("ZeilenID", "t"), f("Buchungsdatum", "d"), f("Wertstellung", "d"),
        f("Von_An", "t"), f("Verwendungszweck", "t"), f("Betrag", "c"),
        f("Waehrung", "s", WAEHRUNGEN), f("Saldo", "c"),
        f("Geschaeftlich", "s", ["ja", "nein", "privat"]),
        # Beleg_Eingang / Beleg_Ausgang sind Link-Felder -> nach Anlage der Zieltabellen ergänzen.
        f("Kategorie", "s", ["Wareneinkauf", "Fremdleistung", "Buerobedarf",
                             "Reisekosten", "Sonstiges"]),
        f("Notizen", "l"),
    ],
    "Lohnjournal_2025": [
        f("Monat", "t"), f("Mitarbeiter", "t"), f("Bruttolohn", "c"), f("Lohnsteuer", "c"),
        f("Soli", "c"), f("Kirchensteuer", "c"), f("SV_AN_Anteil", "c"), f("SV_AG_Anteil", "c"),
        f("Nettolohn", "c"), f("AG_Gesamtkosten", "c"), f("Auszahlungsdatum", "d"),
        f("Bank_Ref", "t"), f("Notizen", "l"),
    ],
    "Vermietung_Verpachtung": [
        f("Objekt", "t"), f("Mieter", "t"), f("Monat", "t"), f("Kaltmiete", "c"),
        f("Nebenkosten", "c"), f("Gesamtmiete", "c"), f("Eingangsdatum", "d"),
        f("Bank_Ref", "t"), f("Werbungskosten", "c"), f("Notizen", "l"),
    ],
    "EUER_Uebersicht": [
        f("Position", "t"),
        f("Abschnitt", "s", ["Einnahmen", "Ausgaben", "Saldo", "nachrichtlich"]),
        f("Betrag", "c"), f("EUER_Zeile", "t"), f("Berechnung", "t"),
    ],
}

BANK_TABLES = ["Bank_TradeRepublic", "Bank_Sparkasse", "Bank_C24"]

# Mapping interner Kürzel -> Airtable Metadata-API Feldtypen
API_TYPE = {
    "t": lambda o: {"type": "singleLineText"},
    "l": lambda o: {"type": "multilineText"},
    "d": lambda o: {"type": "date", "options": {"dateFormat": {"name": "iso"}}},
    "c": lambda o: {"type": "currency", "options": EUR},
    "s": lambda o: {"type": "singleSelect",
                    "options": {"choices": [{"name": n} for n in o]}},
    "u": lambda o: {"type": "url"},
    "a": lambda o: {"type": "multipleAttachments"},
}


def expanded_schema() -> dict:
    """Ersetzt _Bank durch die drei konkreten Bank-Tabellen."""
    out = {}
    for name, fields in SCHEMA.items():
        if name == "_Bank":
            for bank in BANK_TABLES:
                out[bank] = fields
        else:
            out[name] = fields
    return out


def print_overview() -> None:
    for table, fields in expanded_schema().items():
        print(f"\n## {table}")
        for fld in fields:
            extra = f"  {fld['options']}" if fld["options"] else ""
            print(f"  - {fld['name']} [{fld['kind']}]{extra}")
    print("\nHinweis: Link-Felder Beleg_Eingang/Beleg_Ausgang auf den Bank-Tabellen "
          "nach Anlage von Eingangs-/Ausgangsrechnungen ergänzen.")


def create_via_api() -> int:
    import requests  # nur bei --create benötigt
    token = os.environ.get("AIRTABLE_TOKEN")
    base_id = os.environ.get("AIRTABLE_BASE_ID")
    if not token or not base_id:
        print("FEHLER: AIRTABLE_TOKEN und AIRTABLE_BASE_ID müssen gesetzt sein.", file=sys.stderr)
        return 2
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    for table, fields in expanded_schema().items():
        payload = {
            "name": table,
            "fields": [{"name": fld["name"], **API_TYPE[fld["kind"]](fld["options"])}
                       for fld in fields],
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.ok:
            print(f"angelegt: {table}")
        else:
            print(f"FEHLER bei {table}: {resp.status_code} {resp.text}", file=sys.stderr)
    print("Link-Felder (Beleg_Eingang/Beleg_Ausgang) ggf. manuell/via MCP nachziehen.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true", help="Schema als JSON ausgeben")
    parser.add_argument("--create", action="store_true", help="Base via Meta-API anlegen")
    args = parser.parse_args()

    if args.create:
        return create_via_api()
    if args.json:
        print(json.dumps(expanded_schema(), ensure_ascii=False, indent=2))
        return 0
    print_overview()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
