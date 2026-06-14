#!/usr/bin/env python3
"""Aggregiert die kanonischen CSV-Tabellen zur EÜR-Übersicht 2025.

Liest aus dem Datenordner:
  eingangsrechnungen*.csv  (Quelle lexoffice und/oder aus Airtable exportierte Gmail-Belege)
  ausgangsrechnungen*.csv
  lohnjournal*.csv
  vermietung*.csv          (nur nachrichtlich – NICHT im EÜR-Saldo)
und schreibt euer_uebersicht.csv im Schema der Tabelle EUER_Uebersicht (docs/SCHEMA.md).

Hinweis: Gmail-Belege und Bankzeilen liegen im Live-Betrieb in Airtable. Für eine vollständige
EÜR entweder (a) die Airtable-Tabellen vorher als CSV nach `data/` exportieren, oder (b) Claude
dieselbe Logik direkt auf den Airtable-Tabellen rechnen lassen.

EÜR-Prinzip: Ist-Versteuerung (Zufluss/Abfluss). Einnahmen werden bei Status `paid` gezählt.
USt-Behandlung folgt der amtlichen Anlage EÜR (vereinnahmte USt = Einnahme, Vorsteuer = Ausgabe).

Beispiele:
    python scripts/build_euer.py --data data --out data/euer_uebersicht.csv
    python scripts/build_euer.py --hash-bank data/bank_traderepublic.csv   # ZeilenID erzeugen
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import sys
from pathlib import Path

WARENEINKAUF_KATEGORIEN = {"Wareneinkauf", "Fremdleistung", "Fremdleistungen"}


def to_float(value) -> float:
    if value is None:
        return 0.0
    s = str(value).strip().replace("€", "").replace(" ", "")
    if not s:
        return 0.0
    # deutsches Format 1.234,56 -> 1234.56
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def read_rows(data_dir: Path, pattern: str) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(glob.glob(str(data_dir / pattern))):
        with open(path, newline="", encoding="utf-8") as fh:
            rows.extend(csv.DictReader(fh))
    return rows


def build_overview(data_dir: Path) -> list[dict]:
    sales = read_rows(data_dir, "ausgangsrechnungen*.csv")
    purchases = read_rows(data_dir, "eingangsrechnungen*.csv")
    payroll = read_rows(data_dir, "lohnjournal*.csv")
    rent = read_rows(data_dir, "vermietung*.csv")

    paid_sales = [r for r in sales if str(r.get("Status", "")).lower() == "paid"] or sales
    umsatz_netto = sum(to_float(r.get("Netto")) for r in paid_sales)
    vereinnahmte_ust = sum(to_float(r.get("MwSt")) for r in paid_sales)
    summe_einnahmen = umsatz_netto + vereinnahmte_ust

    wareneinkauf = sum(to_float(r.get("Nettobetrag")) for r in purchases
                       if r.get("Kategorie") in WARENEINKAUF_KATEGORIEN)
    uebrige = sum(to_float(r.get("Nettobetrag")) for r in purchases
                  if r.get("Kategorie") not in WARENEINKAUF_KATEGORIEN)
    vorsteuer = sum(to_float(r.get("MwSt_Betrag")) for r in purchases)
    personalkosten = sum(to_float(r.get("AG_Gesamtkosten")) for r in payroll)
    summe_ausgaben = wareneinkauf + uebrige + vorsteuer + personalkosten

    saldo = summe_einnahmen - summe_ausgaben
    vv_einnahmen = sum(to_float(r.get("Gesamtmiete")) for r in rent)

    def pos(position, abschnitt, betrag, zeile, berechnung):
        return {"Position": position, "Abschnitt": abschnitt,
                "Betrag": round(betrag, 2), "EUER_Zeile": zeile, "Berechnung": berechnung}

    return [
        pos("Umsatzerlöse (netto)", "Einnahmen", umsatz_netto, "Z. 14",
            "Σ Ausgangsrechnungen.Netto (Status=paid)"),
        pos("Vereinnahmte Umsatzsteuer", "Einnahmen", vereinnahmte_ust, "Z. 16",
            "Σ Ausgangsrechnungen.MwSt (Status=paid)"),
        pos("Sonstige Einnahmen", "Einnahmen", 0.0, "Z. 15/18", "manuell zu ergänzen"),
        pos("Summe Betriebseinnahmen", "Saldo", summe_einnahmen, "Z. 22", "Σ Einnahmen"),
        pos("Wareneinkauf / Fremdleistungen", "Ausgaben", wareneinkauf, "Z. 26/27",
            "Σ Eingangsrechnungen.Nettobetrag (Kategorie Wareneinkauf/Fremdleistung)"),
        pos("Personalkosten", "Ausgaben", personalkosten, "Z. 31",
            "Σ Lohnjournal.AG_Gesamtkosten"),
        pos("Gezahlte Vorsteuer", "Ausgaben", vorsteuer, "Z. 59",
            "Σ Eingangsrechnungen.MwSt_Betrag"),
        pos("Übrige Betriebsausgaben", "Ausgaben", uebrige, "Z. 60",
            "Σ Eingangsrechnungen.Nettobetrag (übrige Kategorien)"),
        pos("Summe Betriebsausgaben", "Saldo", summe_ausgaben, "Z. 73", "Σ Ausgaben"),
        pos("Gewinn / Verlust (Saldo)", "Saldo", saldo, "Z. 91",
            "Summe Einnahmen − Summe Ausgaben"),
        pos("Einkünfte Vermietung & Verpachtung (Anlage V)", "nachrichtlich", vv_einnahmen, "—",
            "Σ Vermietung.Gesamtmiete — NICHT im EÜR-Saldo"),
    ]


def write_overview(rows: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["Position", "Abschnitt", "Betrag", "EUER_Zeile", "Berechnung"]
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"EÜR-Übersicht geschrieben: {out}")
    for r in rows:
        print(f"  {r['Abschnitt']:13} {r['Position']:48} {r['Betrag']:>12,.2f} €")


def hash_bank(paths: list[str]) -> None:
    """Ergänzt jede Bank-CSV um eine stabile ZeilenID (Hash aus Datum+Betrag+Zweck)."""
    for p in paths:
        path = Path(p)
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
            fields = reader.fieldnames or []
        if "ZeilenID" not in fields:
            fields = ["ZeilenID", *fields]
        for r in rows:
            key = "|".join([str(r.get("Buchungsdatum", "")), str(r.get("Betrag", "")),
                            str(r.get("Verwendungszweck", ""))])
            r["ZeilenID"] = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        print(f"ZeilenID ergänzt: {path} ({len(rows)} Zeilen)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", default="data", help="Ordner mit den CSV-Tabellen")
    parser.add_argument("--out", default="data/euer_uebersicht.csv")
    parser.add_argument("--hash-bank", nargs="+", metavar="CSV",
                        help="Bank-CSV(s): stabile ZeilenID ergänzen statt EÜR zu bauen")
    args = parser.parse_args()

    if args.hash_bank:
        hash_bank(args.hash_bank)
        return 0

    data_dir = Path(args.data)
    if not data_dir.exists():
        print(f"FEHLER: Datenordner {data_dir} existiert nicht.", file=sys.stderr)
        return 2
    rows = build_overview(data_dir)
    write_overview(rows, Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
