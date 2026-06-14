# Steuerschlüssel-Referenz (regelbesteuert)

Wertebereich für das Single-Select-Feld `Steuerschluessel` in den Tabellen
`Eingangsrechnungen` und `Ausgangsrechnungen`.

| Schlüssel | Bedeutung | USt-Satz | Wirkung in EÜR / USt-Voranmeldung |
|-----------|-----------|----------|-----------------------------------|
| `19` | Regelsteuersatz | 19 % | Eingang: Vorsteuer 19 %; Ausgang: USt 19 % |
| `7` | ermäßigter Steuersatz | 7 % | Eingang: Vorsteuer 7 %; Ausgang: USt 7 % |
| `0` | 0 % / nicht steuerbar | 0 % | keine USt |
| `RC-13b` | Reverse-Charge §13b UStG | 0 % (Übergang der Steuerschuld) | Leistungsempfänger schuldet die USt; gleichzeitig Vorsteuerabzug → i. d. R. neutral |
| `IG-Erwerb` | innergemeinschaftlicher Erwerb | 19 % / 7 % | Erwerbsteuer **und** Vorsteuer selbst zu erklären |
| `IG-Lieferung` | innergemeinschaftliche Lieferung (Ausgang) | 0 % | steuerfrei §4 Nr. 1b UStG (mit USt-IdNr.) |
| `stfrei` | echte Steuerbefreiung | 0 % | z. B. §4 UStG; kein Vorsteuerabzug auf Eingangsseite |

## Hinweise zur Anwendung

- **Auslandsrechnungen:** Originalwährung im Feld `Waehrung`, zusätzlich Hinweis im Feld
  `Auslandsvermerk` (z. B. „Reverse-Charge, Lieferant in IE" oder „§13b Leistungsempfänger").
- **Reverse-Charge & innergem. Erwerb** sind in der EÜR betragsmäßig meist neutral (USt = Vorsteuer),
  müssen aber in der USt-Voranmeldung gesondert gemeldet werden → im Feld `Notizen` festhalten.
- Bei `RC-13b`, `IG-Erwerb`, `IG-Lieferung` ist `MwSt_Betrag` in der Rechnung i. d. R. **0**;
  die rechnerische Steuer wird separat in der USt-Voranmeldung berücksichtigt.
- Default-Währung ist `EUR`.

> Keine Kleinunternehmerregelung (§19 UStG) angenommen. Falls sich der Status ändert, würde
> `KU-19` (keine USt ausgewiesen, kein Vorsteuerabzug) als zusätzlicher Schlüssel benötigt.
