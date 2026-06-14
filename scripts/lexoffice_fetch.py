#!/usr/bin/env python3
"""Lexoffice (Lexware Office) Public-API → kanonische CSV für die EÜR 2025.

Holt Ausgangsrechnungen, Eingangsbelege und Kontakte und schreibt sie in CSV-Dateien,
deren Spalten exakt dem Airtable-Schema (docs/SCHEMA.md) entsprechen. Das Schreiben nach
Airtable übernimmt anschließend Claude über den MCP-Connector (Upsert per Schlüssel).

Auth:   Umgebungsvariable LEXOFFICE_API_KEY (Public-API-Key, NICHT committen).
Limits: max. 2 Requests/Sekunde (global) -> Throttle 0.5s; Retry/Backoff bei HTTP 429/5xx.

Beispiele:
    python scripts/lexoffice_fetch.py --what contacts  --out data
    python scripts/lexoffice_fetch.py --what sales      --year 2025 --out data
    python scripts/lexoffice_fetch.py --what purchases  --year 2025 --out data
    python scripts/lexoffice_fetch.py --what all        --year 2025 --out data --limit 10
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from pathlib import Path

import requests

BASE_URL = "https://api.lexoffice.io/v1"
MIN_INTERVAL = 0.5  # Sekunden zwischen Requests (=> <= 2 req/s)
PAGE_SIZE = 250


class LexofficeClient:
    """Dünner REST-Client mit Throttling, Pagination und Retry."""

    def __init__(self, api_key: str, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
        )
        self._last_call = 0.0

    def _throttle(self) -> None:
        wait = MIN_INTERVAL - (time.monotonic() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.monotonic()

    def get(self, path: str, params: dict | None = None, max_retries: int = 5) -> dict:
        url = f"{self.base_url}/{path.lstrip('/')}"
        for attempt in range(max_retries):
            self._throttle()
            resp = self.session.get(url, params=params, timeout=30)
            if resp.status_code == 429 or resp.status_code >= 500:
                backoff = 2 ** attempt
                retry_after = resp.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    backoff = max(backoff, int(retry_after))
                print(f"  HTTP {resp.status_code} auf {path} – warte {backoff}s "
                      f"(Versuch {attempt + 1}/{max_retries})", file=sys.stderr)
                time.sleep(backoff)
                continue
            resp.raise_for_status()
            return resp.json()
        raise RuntimeError(f"Wiederholt fehlgeschlagen: GET {path}")

    def voucherlist(self, voucher_type: str, statuses: str,
                    date_from: str | None = None, date_to: str | None = None):
        """Iteriert paginiert über /voucherlist und liefert einzelne Einträge."""
        page = 0
        while True:
            params = {
                "voucherType": voucher_type,
                "voucherStatus": statuses,
                "size": PAGE_SIZE,
                "page": page,
            }
            if date_from:
                params["voucherDateFrom"] = date_from
            if date_to:
                params["voucherDateTo"] = date_to
            data = self.get("voucherlist", params)
            for entry in data.get("content", []):
                yield entry
            if page >= data.get("totalPages", 1) - 1 or not data.get("content"):
                break
            page += 1


def steuerschluessel_from_rate(rate) -> str:
    """Mappt einen USt-Satz auf einen Steuerschlüssel (siehe STEUERSCHLUESSEL.md)."""
    try:
        r = round(float(rate))
    except (TypeError, ValueError):
        return ""
    return {19: "19", 7: "7", 0: "0"}.get(r, str(r))


def year_filter(date_str: str | None, year: int | None) -> bool:
    if not year or not date_str:
        return True
    return str(date_str)[:4] == str(year)


# ---------------------------------------------------------------------------
# Fetch-Funktionen je Ressource
# ---------------------------------------------------------------------------

def fetch_contacts(client: LexofficeClient, limit: int | None) -> list[dict]:
    rows, page = [], 0
    while True:
        data = client.get("contacts", {"size": PAGE_SIZE, "page": page})
        for c in data.get("content", []):
            roles = c.get("roles", {}) or {}
            rows.append({
                "contactId": c.get("id", ""),
                "Name": c.get("company", {}).get("name")
                        or " ".join(filter(None, [
                            c.get("person", {}).get("firstName"),
                            c.get("person", {}).get("lastName")])),
                "Rolle": ",".join(roles.keys()),
                "Email": (c.get("emailAddresses", {}) or {}).get("business", [""])[0]
                         if c.get("emailAddresses") else "",
            })
            if limit and len(rows) >= limit:
                return rows
        if page >= data.get("totalPages", 1) - 1 or not data.get("content"):
            break
        page += 1
    return rows


def fetch_sales(client: LexofficeClient, year: int | None, limit: int | None) -> list[dict]:
    rows = []
    date_from = f"{year}-01-01T00:00:00.000+01:00" if year else None
    date_to = f"{year}-12-31T23:59:59.999+01:00" if year else None
    for e in client.voucherlist("salesinvoice", "open,paid,overdue,voided", date_from, date_to):
        if not year_filter(e.get("voucherDate"), year):
            continue
        detail = client.get(f"invoices/{e['id']}")
        rate = ""
        items = detail.get("lineItems") or []
        if items:
            rate = items[0].get("taxRatePercentage", "")
        rows.append({
            "LexofficeID": e.get("id", ""),
            "Rechnungsnummer": e.get("voucherNumber", ""),
            "Rechnungsdatum": str(e.get("voucherDate", ""))[:10],
            "Kunde": e.get("contactName", ""),
            "KundenID": detail.get("address", {}).get("contactId", ""),
            "Netto": detail.get("totalPrice", {}).get("totalNetAmount", ""),
            "MwSt": detail.get("totalPrice", {}).get("totalTaxAmount", ""),
            "Brutto": detail.get("totalPrice", {}).get("totalGrossAmount", ""),
            "Waehrung": detail.get("totalPrice", {}).get("currency", "EUR"),
            "Steuerschluessel": steuerschluessel_from_rate(rate),
            "Status": e.get("voucherStatus", ""),
            "Bezahlt_am": "",  # ggf. aus Zahlungsdaten ergänzen
            "Quelle_Link": "",
            "Notizen": "",
        })
        if limit and len(rows) >= limit:
            break
    return rows


def fetch_purchases(client: LexofficeClient, year: int | None, limit: int | None) -> list[dict]:
    rows = []
    date_from = f"{year}-01-01T00:00:00.000+01:00" if year else None
    date_to = f"{year}-12-31T23:59:59.999+01:00" if year else None
    for e in client.voucherlist("purchaseinvoice", "open,paid,overdue,voided", date_from, date_to):
        if not year_filter(e.get("voucherDate"), year):
            continue
        detail = client.get(f"vouchers/{e['id']}")
        items = detail.get("voucherItems") or []
        net = sum(float(i.get("netAmount", 0) or 0) for i in items)
        tax = sum(float(i.get("taxAmount", 0) or 0) for i in items)
        rate = items[0].get("taxRatePercent", "") if items else ""
        rows.append({
            "BelegID": f"lex:{e.get('id', '')}",
            "Belegnummer": e.get("voucherNumber", ""),
            "Rechnungsdatum": str(e.get("voucherDate", ""))[:10],
            "Zahlungsdatum": "",
            "Beschreibung": e.get("contactName", ""),
            "Lieferant": e.get("contactName", ""),
            "Nettobetrag": round(net, 2) if items else "",
            "MwSt_Betrag": round(tax, 2) if items else "",
            "Gesamtbetrag": e.get("totalAmount", ""),
            "Waehrung": detail.get("currency", "EUR"),
            "Auslandsvermerk": "",
            "Steuerschluessel": steuerschluessel_from_rate(rate),
            "Kategorie": "",
            "Quelle": "lexoffice",
            "Quelle_Link": "",
            "Beleg_PDF": "",
            "Notizen": "",
        })
        if limit and len(rows) >= limit:
            break
    return rows


def write_csv(rows: list[dict], path: Path, fieldnames: list[str], dry_run: bool) -> None:
    if dry_run:
        print(f"  [dry-run] {len(rows)} Zeilen -> {path} (nicht geschrieben)")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {len(rows)} Zeilen -> {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--what", choices=["contacts", "sales", "purchases", "all"],
                        default="all")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--out", default="data", help="Zielordner für die CSV-Dateien")
    parser.add_argument("--limit", type=int, default=None, help="max. Datensätze (Test)")
    parser.add_argument("--dry-run", action="store_true", help="nur abrufen, nichts schreiben")
    parser.add_argument("--base-url", default=BASE_URL)
    args = parser.parse_args()

    api_key = os.environ.get("LEXOFFICE_API_KEY")
    if not api_key:
        print("FEHLER: Umgebungsvariable LEXOFFICE_API_KEY ist nicht gesetzt.", file=sys.stderr)
        return 2

    client = LexofficeClient(api_key, args.base_url)
    out = Path(args.out)

    if args.what in ("contacts", "all"):
        print("Hole Kontakte …")
        rows = fetch_contacts(client, args.limit)
        write_csv(rows, out / "contacts.csv",
                  ["contactId", "Name", "Rolle", "Email"], args.dry_run)

    if args.what in ("sales", "all"):
        print(f"Hole Ausgangsrechnungen {args.year} …")
        rows = fetch_sales(client, args.year, args.limit)
        write_csv(rows, out / "ausgangsrechnungen.csv",
                  ["LexofficeID", "Rechnungsnummer", "Rechnungsdatum", "Kunde", "KundenID",
                   "Netto", "MwSt", "Brutto", "Waehrung", "Steuerschluessel", "Status",
                   "Bezahlt_am", "Quelle_Link", "Notizen"], args.dry_run)

    if args.what in ("purchases", "all"):
        print(f"Hole Eingangsbelege {args.year} …")
        rows = fetch_purchases(client, args.year, args.limit)
        write_csv(rows, out / "eingangsrechnungen_lexoffice.csv",
                  ["BelegID", "Belegnummer", "Rechnungsdatum", "Zahlungsdatum", "Beschreibung",
                   "Lieferant", "Nettobetrag", "MwSt_Betrag", "Gesamtbetrag", "Waehrung",
                   "Auslandsvermerk", "Steuerschluessel", "Kategorie", "Quelle", "Quelle_Link",
                   "Beleg_PDF", "Notizen"], args.dry_run)

    print("Fertig.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
