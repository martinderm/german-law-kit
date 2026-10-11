# Verification Receipt Schema & Vertrag

**Zweck:** Deterministischer, maschinenlesbarer Nachweis für deutsche Rechtsabfragen.
Jede erfolgreiche oder fehlgeschlagene Rechtsprüfung erzeugt einen maschinenlesbaren Receipt, um Stichtagsdisziplin und Halluzinationsfreiheit sicherzustellen.

---

## 1. Schema-Definition

```json
{
  "source_id": "BJNR001950896BJNE052902377",
  "law_slug": "bgb",
  "jurabk": "BGB",
  "enbez": "§ 535",
  "titel": "Inhalt und Hauptpflichten des Mietvertrags",
  "doknr": "BJNR001950896BJNE052902377",
  "builddate": "20260926215508",
  "retrieved_at": "2026-10-11T15:20:00Z",
  "effective_status": "in_force",
  "raw_content_sha256": "3a9f0...",
  "normalized_content_sha256": "8e71b...",
  "cached": true,
  "retrieval_method": "gesetze_im_internet_xml",
  "verification_status": "verified_current",
  "fallback_reason": null
}
```

---

## 2. Felddefinitionen

* **`source_id` / `doknr`**: Die amtliche Dokumentnummer der Einzelnorm auf `gesetze-im-internet.de`.
* **`builddate`**: Der amtliche Erstellungszeitstempel des Bundesamts für Justiz aus dem Norm-XML-Kopf.
* **`retrieved_at`**: UTC-Zeitstempel des Abrufs.
* **`raw_content_sha256`**: SHA-256 Hash des unveränderten XML-Snippets der Norm.
* **`normalized_content_sha256`**: SHA-256 Hash des bereinigten, mit Absatznummern versehenen Gesetzestextes.
* **`cached`**: `true`, wenn die Norm aus dem lokalen Disk-Cache bedient wurde; `false` bei Netzwerk-Fetch.
* **`retrieval_method`**:
  * `canonical_xml`: Direkt über `canonical-laws.json` und `xml.zip` aufgelöst.
  * `direct_slug`: Über direkten Slug von `gesetze-im-internet.de` geladen.
  * `web_search_fallback`: Über Volltextsuche ermittelt.
* **`verification_status`**:
  * `verified_current`: Erfolgreich aus tagesaktueller amtlicher XML-Fassung extrahiert.
  * `historical_version`: Ausdrücklich als historischer Stand angefordert und belegt.
  * `stichtag_mismatch`: Aufgerufener Stand weicht vom geforderten Stichtag ab.
  * `unverified_fallback`: Notfallsuche ohne amtliche Dokumentnummer.

---

## 3. Die 5-Schichten-Antwortstruktur

Jede Ausgabe für Agenten und Benutzer folgt dem 5-Schichten-Standard:

1. **A) Normwortlaut:** Unveränderter, authentischer Gesetzestext mit korrekter Absatzgliederung `(1)`, `(2)`.
2. **B) Metadaten & Verification Receipt:** Amtliche DokNr, Build-Datum, Content-Hash und Verifikationsstatus.
3. **C) Verständliche Zusammenfassung:** Prägnante Paraphrase des Norminhalts in juristischer Fachsprache.
4. **D) BGH-Judikatur & Leitsätze:** Relevante Entscheidungen des BGH mit Aktenzeichen, Datum und ECLI (via NeuRIS API).
5. **E) Schlussfolgerung & Rechtsunsicherheit:** Offene Auslegungsfragen, Tatbestandsmerkmale, Abgrenzung zur Rechtsberatung.
