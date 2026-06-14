# Anleitung für Kai – Steuer-Vorbereitung 2025 (ganz ohne Technik-Wissen)

Hallo Kai 👋 Diese Anleitung ist für dich, wenn du **kein Entwickler** bist und mit Technik-Begriffen
nichts anfangen kannst. Du musst hier **nichts programmieren**. Du klickst ein paar Dinge an und sagst
dem KI-Assistenten **Claude** in einfachen Sätzen, was er tun soll – den Rest erledigt Claude für dich.

Ziel: Am Ende liegt deine **Einnahmen-Überschuss-Rechnung 2025** (kurz „EÜR" – einfach gesagt:
*Einnahmen minus Ausgaben = Gewinn*) ordentlich aufbereitet in einer Online-Tabelle.

---

## Das Wichtigste in einem Satz
Du richtest einmal ein paar Konten/Verbindungen ein, und dann sagst du Claude der Reihe nach,
welchen Schritt er machen soll. Claude holt deine Rechnungen, durchsucht deine E-Mails nach Belegen
und trägt alles sauber in eine Tabelle ein.

---

## Schritt 1: Einmal vorbereiten (ca. 20–30 Minuten)

**a) Online-Tabelle „Airtable" anlegen**
- „Airtable" ist eine Tabelle im Internet – stell es dir wie eine etwas schlauere Excel-Tabelle im
  Browser vor.
- Gehe auf **airtable.com**, registriere dich (kostenlos).
- Lege dort eine **neue, leere Arbeitsmappe** an (Airtable nennt das eine „Base"). Nenne sie z. B.
  **„EÜR 2025 Kai"**.
- ❗ Du musst **keine** Spalten oder Tabellen selbst bauen. Das macht Claude später für dich.

**b) Claude mit deinen Konten verbinden**
- In Claude gibt es „Verbindungen" (Fachwort: *Connectoren*). Das sind Schalter, die Claude erlauben,
  z. B. deine Tabelle oder deine E-Mails zu benutzen.
- Verbinde: **Airtable** und dein **erstes Gmail-Postfach**. (Das zweite Postfach kommt später dran.)

**c) Lexoffice-Schlüssel besorgen**
- In Lexoffice/Lexware gibt es einen sogenannten „API-Schlüssel". Das ist einfach ein **geheimes
  Passwort**, mit dem Claude deine Rechnungen **lesen** darf (nur lesen, nichts ändern).
- Du findest ihn in Lexoffice unter **Einstellungen → Public API**. Dort einen Schlüssel erzeugen.
- Diesen Schlüssel gibst du ein, **wenn Claude dich danach fragt**. Behandle ihn wie ein Passwort –
  **nicht weitergeben, nicht in Chats posten, die andere sehen.**

---

## Schritt 2: Claude die Tabelle aufbauen lassen

Sag in deiner Claude-Sitzung einfach (kannst du kopieren):

> „Bitte lege in meiner Airtable-Arbeitsmappe ‚EÜR 2025 Kai' alle Tabellen und Spalten nach der
> Datei **docs/SCHEMA.md** an."

Claude baut dann ganz allein alle nötigen Tabellen (für Eingangsrechnungen, Ausgangsrechnungen,
die drei Bankkonten, Lohn, Vermietung und die Übersicht). Du musst dabei nur zuschauen.

---

## Schritt 3: Daten einsammeln (Claude macht die Arbeit)

Geh einfach diese Sätze der Reihe nach durch. Nach jedem Satz lässt du Claude fertig arbeiten.

1. **Rechnungen aus Lexoffice holen:**
   > „Bitte hole meine Rechnungen und Belege aus Lexoffice für 2025 und trage sie in die Tabelle ein."

2. **Erstes E-Mail-Postfach nach Belegen durchsuchen:**
   > „Bitte durchsuche mein E-Mail-Postfach nach Rechnungen/Belegen aus 2025, trage sie in die Tabelle
   > ein und markiere jede erledigte E-Mail mit dem Schild ‚EÜR-2025-erfasst'."

   👉 Das „Schild" (Fachwort: *Label*) sorgt dafür, dass die gleiche E-Mail später **nicht doppelt**
   erfasst wird.

3. **Kurze Pause – zweites Postfach verbinden.** Danach denselben Satz wie oben noch einmal für dein
   **zweites** Gmail-Postfach.

4. **Bankauszüge & Lohnliste:** Lade dir die Umsätze deiner drei Banken
   (Trade Republic, Sparkasse, C24) als Datei herunter und gib sie Claude. Genauso die Lohnliste,
   falls du Mitarbeiter hast. Sag dann:
   > „Bitte trage diese Bankumsätze (bzw. die Lohnliste) in die passende Tabelle ein."

5. **Alles zusammenrechnen:**
   > „Bitte verknüpfe die Bankzahlungen mit den Rechnungen und erstelle die EÜR-Übersicht."

Fertig – die Übersicht zeigt dir dann Einnahmen, Ausgaben und den Gewinn.

---

## Wer macht was?

| Aufgabe | Das machst **du** | Das macht **Claude** |
|---|:---:|:---:|
| Airtable-Konto + leere Arbeitsmappe anlegen | ✅ | |
| Verbindungen in Claude einschalten | ✅ | |
| Lexoffice-Schlüssel eingeben (wenn gefragt) | ✅ | |
| Bankauszüge & Lohnliste herunterladen | ✅ | |
| Tabellen/Spalten bauen | | ✅ |
| Rechnungen aus Lexoffice holen | | ✅ |
| E-Mails nach Belegen durchsuchen + markieren | | ✅ |
| Alles eintragen und die EÜR zusammenrechnen | | ✅ |

---

## Kleine Wörterliste (falls dir ein Begriff begegnet)

- **EÜR** – Einnahmen-Überschuss-Rechnung. Einfache Gewinnermittlung: Einnahmen minus Ausgaben.
- **Airtable / „Base"** – Online-Tabelle im Browser bzw. eine Arbeitsmappe darin.
- **Verbindung / „Connector"** – ein Schalter, der Claude erlaubt, z. B. deine Mails oder Tabelle zu nutzen.
- **API-Schlüssel** – ein geheimes Passwort, mit dem Programme auf deine Daten zugreifen dürfen.
- **Label / „Schild"** – eine farbige Markierung an einer E-Mail (hier: „schon erledigt").
- **Skript** – ein kleines Hilfsprogramm. Das startet **Claude** für dich; du musst es nicht verstehen.
- **Repository / „Repo"** – einfach der Ordner, in dem diese Anleitung und die Hilfsprogramme liegen.
- **Anlage V** – das Steuerformular für **Miet-Einnahmen** (wird getrennt von der EÜR geführt).

---

## Sicherheit (kurz)
- Den Lexoffice-Schlüssel und Zugangsdaten **niemals** an Unbefugte weitergeben.
- Deine Belege und Kontodaten bleiben in **deinen** Konten – sie werden nicht öffentlich gespeichert.

## Zum Schluss
Diese Vorbereitung ersetzt **keine Steuerberatung**. Lass das fertige Ergebnis am Ende bitte von
deinem Steuerberater prüfen, bevor du es beim Finanzamt einreichst.

> Wenn du irgendwo nicht weiterkommst: Sag es Claude in deinen eigenen Worten – z. B.
> „Ich verstehe Schritt 3 nicht, kannst du mir das einfacher erklären?"
