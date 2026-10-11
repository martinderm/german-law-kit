#!/usr/bin/env python3
"""
german_law_cli.py — Zentraler CLI-Router für german-law-kit.

Befehle:
  fetch_norm        Holt eine Einzelnorm (z. B. § 535 BGB), validiert sie und erzeugt Receipt
  fetch_whole_law   Lädt die amtliche Gesamtfassung eines Gesetzes in den Cache
  search_decisions  Sucht BGH-Entscheidungen über NeuRIS
  list_canonical    Listet alle vorindizierten Bundesgesetze auf

Unterstützt --json für den standardisierten Structured CLI Envelope.
"""

import argparse
import json
import sys
from pathlib import Path

# Setup import path
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.cache import AtomicDiskCache
from lib.gii_client import fetch_norm, resolve_canonical_law, fetch_law_xml_bytes, extract_xml_from_zip
from lib.neuris_client import search_case_law
from lib.receipt import create_verification_receipt, format_5_layer_output, asdict


def get_default_cache_dir() -> Path:
    return SKILL_DIR / "data" / "cache"


def output_envelope(action: str, success: bool, state: str, message: str, data=None, error=None, as_json: bool = False):
    envelope = {
        "action": action,
        "success": success,
        "state": state,
        "message": message,
        "data": data,
        "error": error,
    }
    if as_json:
        print(json.dumps(envelope, indent=2, ensure_ascii=False))
    else:
        if not success:
            print(f"FEHLER [{state}]: {message}", file=sys.stderr)
            if error:
                print(f"Details: {error}", file=sys.stderr)
        else:
            if isinstance(data, dict) and "formatted_output" in data:
                print(data["formatted_output"])
            elif isinstance(data, str):
                print(data)
            else:
                print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_fetch_norm(args):
    cache_dir = Path(args.cache_dir) if args.cache_dir else get_default_cache_dir()
    cache = AtomicDiskCache(cache_dir)
    canonical_file = SKILL_DIR / "references" / "canonical-laws.json"

    try:
        norm, was_cached = fetch_norm(
            law_query=args.law,
            paragraph_query=args.paragraph,
            cache=cache,
            canonical_path=canonical_file,
            force_refresh=args.force_refresh,
        )
    except Exception as e:
        output_envelope(
            action="fetch_norm",
            success=False,
            state="fetch_error",
            message=f"Fehler beim Laden des Gesetzes '{args.law}': {e}",
            error=str(e),
            as_json=args.json,
        )
        return 1

    if not norm:
        output_envelope(
            action="fetch_norm",
            success=False,
            state="norm_not_found",
            message=f"Norm '{args.paragraph}' in Gesetz '{args.law}' nicht gefunden.",
            error="Norm not found in XML",
            as_json=args.json,
        )
        return 2

    # Receipt generieren
    receipt = create_verification_receipt(norm, cached=was_cached)

    # Optional BGH-Judikatur laden
    decisions = []
    if args.include_decisions:
        query_term = f"{norm.jurabk} {norm.enbez}"
        decisions = search_case_law(query_term, court="BGH", limit=args.decisions_limit)

    formatted_md = format_5_layer_output(norm, receipt, decisions)

    data_payload = {
        "receipt": receipt,
        "norm": asdict(norm),
        "decisions": [asdict(d) for d in decisions],
        "formatted_output": formatted_md,
    }

    output_envelope(
        action="fetch_norm",
        success=True,
        state="verified_current",
        message=f"{norm.jurabk} {norm.enbez} erfolgreich verifiziert",
        data=data_payload,
        as_json=args.json,
    )
    return 0


def cmd_fetch_whole_law(args):
    cache_dir = Path(args.cache_dir) if args.cache_dir else get_default_cache_dir()
    cache = AtomicDiskCache(cache_dir)
    canonical_file = SKILL_DIR / "references" / "canonical-laws.json"

    law = resolve_canonical_law(args.law, canonical_file)
    slug = law["slug"] if law else args.law.strip().lower()
    cache_key = f"{slug}_full.xml"

    if not args.force_refresh and cache.has(cache_key):
        output_envelope(
            action="fetch_whole_law",
            success=True,
            state="cached",
            message=f"Gesetz '{slug}' ist bereits im lokalen Cache vorhanden.",
            data={"slug": slug, "cache_path": str(cache.get_path(cache_key)), "cached": True},
            as_json=args.json,
        )
        return 0

    try:
        zip_bytes = fetch_law_xml_bytes(slug)
        xml_content = extract_xml_from_zip(zip_bytes)
        target_path = cache.put_text(cache_key, xml_content)
        output_envelope(
            action="fetch_whole_law",
            success=True,
            state="downloaded",
            message=f"Gesetz '{slug}' erfolgreich geladen ({len(xml_content)} Zeichen).",
            data={"slug": slug, "cache_path": str(target_path), "cached": False, "size_chars": len(xml_content)},
            as_json=args.json,
        )
        return 0
    except Exception as e:
        output_envelope(
            action="fetch_whole_law",
            success=False,
            state="download_failed",
            message=f"Fehler beim Download von '{slug}': {e}",
            error=str(e),
            as_json=args.json,
        )
        return 1


def cmd_search_decisions(args):
    try:
        decisions = search_case_law(query=args.query, court=args.court, limit=args.limit)
        data = [asdict(d) for d in decisions]
        output_envelope(
            action="search_decisions",
            success=True,
            state="success",
            message=f"{len(decisions)} Entscheidungen gefunden für '{args.query}'",
            data=data,
            as_json=args.json,
        )
        return 0
    except Exception as e:
        output_envelope(
            action="search_decisions",
            success=False,
            state="search_error",
            message=f"Fehler bei Rechtsprechungs-Suche: {e}",
            error=str(e),
            as_json=args.json,
        )
        return 1


def cmd_list_canonical(args):
    canonical_file = SKILL_DIR / "references" / "canonical-laws.json"
    if not canonical_file.exists():
        output_envelope(
            action="list_canonical",
            success=False,
            state="not_found",
            message="canonical-laws.json nicht gefunden",
            as_json=args.json,
        )
        return 1

    try:
        data = json.loads(canonical_file.read_text(encoding="utf-8"))
        laws = data.get("laws", [])
        if args.json:
            output_envelope(
                action="list_canonical",
                success=True,
                state="success",
                message=f"{len(laws)} kanonische Gesetze indiziert",
                data=laws,
                as_json=True,
            )
        else:
            lines = [f"{'ID':<12} {'Kürzel':<10} {'Upstream Slug':<16} {'Titel'}"]
            lines.append("-" * 75)
            for l in laws:
                lines.append(f"{l.get('id',''):<12} {l.get('short_title',''):<10} {l.get('slug',''):<16} {l.get('title','')}")
            print("\n".join(lines))
        return 0
    except Exception as e:
        output_envelope(
            action="list_canonical",
            success=False,
            state="error",
            message=str(e),
            error=str(e),
            as_json=args.json,
        )
        return 1


def main():
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--json", action="store_true", help="Gibt Ausgabe im standardisierten JSON-Envelope aus")
    common_parser.add_argument("--cache-dir", type=str, default=None, help="Pfad zum Cache-Verzeichnis")

    parser = argparse.ArgumentParser(
        description="german-law-kit CLI — Recherchen in deutschem Bundesrecht und BGH-Judikatur",
        parents=[common_parser],
    )

    subparsers = parser.add_subparsers(dest="subcommand", help="Verfügbare Befehle")

    # fetch_norm
    p_norm = subparsers.add_parser("fetch_norm", help="Holt und validiert eine Einzelnorm", parents=[common_parser])
    p_norm.add_argument("--law", "-l", required=True, help="Gesetzeskürzel oder Name (z. B. bgb, weg, baugb)")
    p_norm.add_argument("--paragraph", "-p", required=True, help="Paragraf (z. B. '§ 535', '556d', '20')")
    p_norm.add_argument("--include-decisions", action="store_true", help="Lädt ergänzend BGH-Entscheidungen")
    p_norm.add_argument("--decisions-limit", type=int, default=3, help="Max. Anzahl BGH-Entscheidungen")
    p_norm.add_argument("--force-refresh", action="store_true", help="Erzwingt Neu-Download des Gesetzes")

    # fetch_whole_law
    p_law = subparsers.add_parser("fetch_whole_law", help="Lädt ein gesamtes Gesetz in den lokalen Cache", parents=[common_parser])
    p_law.add_argument("--law", "-l", required=True, help="Gesetzeskürzel oder Name")
    p_law.add_argument("--force-refresh", action="store_true", help="Erzwingt Neu-Download")

    # search_decisions
    p_dec = subparsers.add_parser("search_decisions", help="Sucht BGH-Entscheidungen über NeuRIS", parents=[common_parser])
    p_dec.add_argument("--query", "-q", required=True, help="Suchbegriff (z. B. 'Mietpreisbremse Rüge')")
    p_dec.add_argument("--court", "-c", default="BGH", help="Gerichtstyp (Standard: BGH)")
    p_dec.add_argument("--limit", type=int, default=3, help="Maximale Trefferanzahl")

    # list_canonical
    subparsers.add_parser("list_canonical", help="Listet alle vorkonfigurierten kanonischen Gesetze auf", parents=[common_parser])

    args = parser.parse_args()

    if not args.subcommand:
        parser.print_help()
        sys.exit(1)

    if args.subcommand == "fetch_norm":
        sys.exit(cmd_fetch_norm(args))
    elif args.subcommand == "fetch_whole_law":
        sys.exit(cmd_fetch_whole_law(args))
    elif args.subcommand == "search_decisions":
        sys.exit(cmd_search_decisions(args))
    elif args.subcommand == "list_canonical":
        sys.exit(cmd_list_canonical(args))


if __name__ == "__main__":
    main()
