# german-law-kit

Strukturierte, quellenklare Primärrechtsprüfung für deutsches Bundesrecht und amtliche BGH-Rechtsprechung.

## Highlights & Architektur

- **Python 3 Standard Library**: Zero pip dependencies. Keine Build-Schritte, kein Node.js, sofort lauffähig auf Windows, Linux und macOS.
- **Amtliche Primärquelle**: Direkter Zugriff auf konsolidierte Bundesgesetze über das XML-Repository von `gesetze-im-internet.de` (BMJ / BfJ).
- **Offizielle BGH-API**: Suche und Abruf von Bundesgerichtshofs-Entscheidungen über die neue NeuRIS REST API des Bundes (`testphase.rechtsinformationen.bund.de`).
- **Dual-Evidence Verification Receipts**: Jede Normprüfung liefert einen maschinenlesbaren Receipt mit amtlicher Dokumentnummer (`doknr`), amtlichem `builddate` und SHA-256 Hashes.
- **Structured CLI Envelope**: Vollständige Unterstützung von `--json` für LLM- und Agenten-Orchestrierung.

## Schnellstart

```bash
# Einzelnorm abfragen (z. B. § 535 BGB)
python scripts/german_law_cli.py fetch_norm --law bgb --paragraph "§ 535"

# Mit BGH-Judikatur und maschinenlesbarem JSON Envelope
python scripts/german_law_cli.py fetch_norm --law weg --paragraph "§ 20" --include-decisions --json

# BGH-Urteile suchen
python scripts/german_law_cli.py search_decisions --query "Mietpreisbremse" --court BGH --limit 3 --json

# Kanonischen Gesetzeskatalog auflisten
python scripts/german_law_cli.py list_canonical --json
```

## Testen

```bash
python tests/test_german_law_cli.py
```

## Lizenz

MIT License — Copyright (c) 2026 Martin Mayr
