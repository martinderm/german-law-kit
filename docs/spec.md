# Spezifikation: german-law-kit

**Status:** Confirmed Spec (SEK to-spec)  
**Datum:** 2026-10-11  
**Autor:** Antigravity / Agent Architecture  
**Ziel:** Deterministische, quellenklare Primärrechtsprüfung für deutsches Bundesrecht mit maschinenlesbaren Verification Receipts und BGH-Judikatur.

---

## 1. Problemstellung & Zielbild

Für deutsche Immobilien- und Zivilrechts-Workflows (z. B. `immo-mietrecht-de`, `immo-germany-precheck`, `immo-hausverwaltung-de`) fehlt ein autonomes, quellenklares Normenwerkzeug analog zu `austrian-law-kit`.
Rechtliche Feststellungen dürfen von LLMs nicht „aus dem Gedächtnis“ generiert werden (Halluzinationsgefahr, veraltete Fassungen, fehlerhafte Absätze).

`german-law-kit` löst dieses Problem durch:
1. **Norm-Primärquelle:** Abruf tagesaktueller, konsolidierter Bundesgesetze und Verordnungen aus dem amtlichen XML-Bestand des BMJ (`gesetze-im-internet.de`).
2. **Rechtsprechungs-Sekundärquelle:** Abruf von Entscheidungen und Leitsätzen des Bundesgerichtshofs (BGH) über die offizielle NeuRIS REST API (`testphase.rechtsinformationen.bund.de`).
3. **Dual-Evidence Verification:** Erzeugung kryptografisch belegter Verification Receipts (Dokumentnummer, Build-Datum, Content SHA-256 Hash).
4. **Python-First & Zero-Dependencies:** 100 % Python 3 Standardbibliothek (keine Node.js-, esbuild- oder pip-Abhängigkeiten).

---

## 2. Bestätigte Seams & Schnittstellen

### Seam 1: Canonical Laws Resolver (`canonical-laws.json`)
- Mappt kanonische Akronyme und Freitextbegriffe (z. B. `bgb`, `weg`, `baugb`, `betrkv`, `woflv`, `grestg`) auf den amtlichen Upstream-Slug von `gesetze-im-internet.de` (z. B. `bbaug` für BauGB, `woeigg` für WEG, `wovermrg` für WoVermittG).
- Ermöglicht $O(1)$-Auflösung ohne vorherige Volltextsuche.

### Seam 2: Gesetze-im-Internet XML Client (`gii_client.py`)
- Lädt das amtliche `xml.zip` eines Gesetzes herunter und entpackt es atomar im Cache.
- Parst das XML und isoliert die gewünschte Einzelnorm anhand `<enbez>` (z. B. `§ 535`).
- Liefert:
  - `doknr`: Amtliche Dokumentnummer (z. B. `BJNR001950896BJNE052902377`)
  - `builddate`: Amtlicher Build-Zeitstempel (z. B. `20260926215508`)
  - `jurabk`: Juristische Abkürzung (z. B. `BGB`)
  - `enbez`: Einzelnormbezeichnung (z. B. `§ 535`)
  - `titel`: Amtlicher Paragrafentitel
  - `text`: Normalisierter Text mit Absatznummern
  - `fussnoten`: Stand/Änderungsangaben.

### Seam 3: NeuRIS Judikatur Client (`neuris_client.py`)
- Fragt `https://testphase.rechtsinformationen.bund.de/v1/document/lucene-search/case-law` ab.
- Filtert nach Gerichtstyp (Standard: `BGH`) und Suchbegriffen.
- Liefert strukturierte Urteile mit ECLI, Aktenzeichen, Datum und Leitsatz.

### Seam 4: Receipt & Formatting Engine (`receipt.py`)
- Berechnet SHA-256 Hashes des Rohinhalts und des bereinigten Normtexts.
- Erstellt das maschinenlesbare `VerificationReceipt`.
- Formatiert die standardisierte 5-Schichten-Ausgabe (A: Wortlaut, B: Receipt, C: Paraphrase, D: BGH-Judikatur, E: Unsicherheit/Grenzen).

### Seam 5: CLI Envelope (`german_law_cli.py`)
- Unterstützt Subcommands:
  - `fetch_norm`: `--law <slug|alias> --paragraph <enbez> [--include-decisions]`
  - `fetch_whole_law`: `--law <slug|alias>`
  - `search_decisions`: `--query <text> [--court BGH] [--limit 5]`
  - `list_canonical`: Auflistung aller vorindizierten Gesetze
- Standardmäßiger JSON-Envelope bei Flag `--json`:
  ```json
  {
    "action": "fetch_norm",
    "success": true,
    "state": "verified_current",
    "message": "Norm § 535 BGB erfolgreich verifiziert",
    "data": { ... },
    "error": null
  }
  ```

---

## 3. Testing Decisions (TDD)

1. **Test Unit 1 (Canonical Mapping):** Jeder Alias in `canonical-laws.json` löst auf einen validen GII-Slug auf.
2. **Test Unit 2 (XML Parsing & Normalization):** Ein synthetisches/gespeichertes XML-Fixture wird fehlerfrei in DokNr, Titel, Absätze und Fußnoten zerlegt.
3. **Test Unit 3 (Receipt Generation):** Der Content-Hash ist deterministisch und reproduzierbar.
4. **Test Unit 4 (NeuRIS Client):** Korrektes Parsen der JSON-Antwort von NeuRIS.
5. **Test Unit 5 (CLI Envelope & Live Smoke):** Ausführung von `fetch_norm --law bgb --paragraph "§ 535" --json` liefert `success: true`.

---

## 4. Out of Scope

- Keine automatische Rechtsberatung oder automatische Vertragserstellung.
- Keine Landesbauordnungen im Bundessystem (Landesrecht liegt nicht auf gesetze-im-internet.de; wird in einem separaten Schritt für Landesrecht behandelt).
- Keine Schreiboperationen auf Upstream-Behördenseiten.
