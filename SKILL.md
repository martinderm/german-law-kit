---
name: german-law-kit
description: Workspace-Skill für die strukturierte, quellenklare Arbeit mit deutschen Rechtstexten (Bundesgesetze und Verordnungen via gesetze-im-internet.de) und amtlicher Rechtsprechung (insb. BGH via NeuRIS API). Liefert unveränderten Normwortlaut mit maschinenlesbaren Verification Receipts, Stichtagsvalidierung und 5-Schichten-Ausgabe.
triggers: [german law, deutsches recht, bundesrecht, BGB, WEG, BauGB, BauNVO, BetrKV, HeizkostenV, GrEStG, GNotKG, WoVermittG, BGH, Rechtsprechung, Paragraf]
category: legal
blast_radius: workspace_scoped
language: python
---

# Skill: german-law-kit

## Zweck

Dieser Skill steuert die fachliche Orchestrierung für deutsche Bundesrechtstexte und amtliche Rechtsprechung mit robuster, reproduzierbarer Primärrechtsprüfung, maschinenlesbarem Verification Receipt und klarer 5-Schichten-Ausgabe.

## Verbindliche Quellenpolitik

1. **Ausschließlich gesetze-im-internet.de (BMJ / BfJ) ist Primärquelle** für konsolidierten Normtext, Struktur, amtliche Dokumentnummer (`doknr`) und Fassungsstand (`builddate`).
2. **NeuRIS API (DigitalService des Bundes / BMJ) ist Sekundärquelle** für amtliche Rechtsprechung (BGH-Entscheidungen, ECLI, Leitsätze) und Discovery.
3. **Kein Belegersatz**: Sekundärquellen oder Web-Suchtreffer dürfen einen fehlenden amtlichen Primärbeleg unter keinen Umständen ersetzen.
4. Jede Normabfrage erzeugt ein kryptografisch gehashtes **Verification Receipt** (SHA-256 für Roh- und Bereinigten Text).
5. Keine ungeprüften Handrechnungen von Fristen oder Quoten im LLM; volatile Schwellenwerte müssen aus der Primärquelle stammen.

## Verfügbare CLI-Werkzeuge (`scripts/german_law_cli.py`)

Alle Werkzeuge sind in **Python 3 Standardbibliothek (zero pip dependencies)** implementiert und unterstützen `--json` für den standardisierten Structured CLI Envelope:

### 1. Einzelnorm abrufen und verifizieren (`fetch_norm`)
Holt den authentischen Text einer Einzelnorm, generiert das Verification Receipt und formatiert die 5 Schichten:
```bash
python scripts/german_law_cli.py fetch_norm --law bgb --paragraph "§ 535" --json
```
Mit optionaler BGH-Rechtsprechungsabfrage:
```bash
python scripts/german_law_cli.py fetch_norm --law bgb --paragraph "§ 556d" --include-decisions --json
```

### 2. Gesamtes Gesetz im Cache vorhalten (`fetch_whole_law`)
Lädt das vollständige amtliche XML-Paket eines Gesetzes in den lokalen Cache:
```bash
python scripts/german_law_cli.py fetch_whole_law --law weg --json
```

### 3. BGH-Rechtsprechung & Leitsätze recherchieren (`search_decisions`)
Fragt amtliche Entscheidungen über die NeuRIS REST API ab:
```bash
python scripts/german_law_cli.py search_decisions --query "Mietpreisbremse Auskunft" --court BGH --limit 3 --json
```

### 4. Kanonischen Gesetzeskatalog einsehen (`list_canonical`)
Listet alle vorkonfigurierten Bundesgesetze auf:
```bash
python scripts/german_law_cli.py list_canonical --json
```

## Kanonische Gesetzeskataloge (`references/canonical-laws.json`)

Der Skill enthält vorkonfigurierte $O(1)$-Auflösungen für über 20 Kern-Normen der Immobilien- und Zivilpraxis:
- **Miet- und Zivilrecht:** `bgb` (Bürgerliches Gesetzbuch), `bgbeg` (EGBGB), `wistrg` (Wirtschaftsstrafgesetz / Mietwucher).
- **Wohnungseigentum & Verwaltung:** `weg` (Wohnungseigentumsgesetz n.F. / WEMoG), `betrkv` (Betriebskostenverordnung), `heizkostenv` (Heizkostenverordnung), `woflv` (Wohnflächenverordnung), `trinkwv` (Trinkwasserverordnung).
- **Planung & Baurecht:** `baugb` (Baugesetzbuch / bbaug), `baunvo` (Baunutzungsverordnung), `geg` (Gebäudeenergiegesetz / Heizungsgesetz).
- **Transaktion, Steuern & Gebühren:** `grestg` (Grunderwerbsteuergesetz 1983), `gnotkg` (Gerichts- und Notarkostengesetz), `estg` (Einkommensteuergesetz), `ustg` (Umsatzsteuergesetz), `gbo` (Grundbuchordnung), `beurkg` (Beurkundungsgesetz), `erbbaurg` (Erbbaurechtsgesetz).
- **Maklerrecht:** `wovermittg` (Wohnungsvermittlungsgesetz / Bestellerprinzip), `mabv` (Makler- und Bauträgerverordnung), `gewo` (Gewerbeordnung).

## Antwortstruktur (5 Schichten)

A) **Normwortlaut**
- Konkrete Fundstelle und unveränderter, authentischer Gesetzestext mit Absatznummern `(1)`, `(2)`.

B) **Metadaten & Verification Receipt**
- Maschinenlesbarer Nachweis: Dokumentnummer (`doknr`), Build-Datum, Content SHA-256, Abrufmethode und Verifikationsstatus.

C) **Verständliche Zusammenfassung (Paraphrase)**
- Erläuterung des Inhalts in präziser juristischer Fachsprache.

D) **BGH-Judikatur & Leitsätze (Sekundärkontext)**
- Relevante Leitentscheidungen des BGH mit Aktenzeichen, Datum und ECLI sauber getrennt vom Normtext.

E) **Schlussfolgerung & Rechtsunsicherheit**
- Tatbestandsmerkmale, offene Fragen und transparente Unsicherheitskommunikation; keine Rechtsberatung.
