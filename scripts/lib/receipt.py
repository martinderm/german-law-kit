#!/usr/bin/env python3
"""
Verification Receipt und 5-Schichten-Ausgabe für german-law-kit.
"""

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any


@dataclass
class NormResult:
    law_slug: str
    jurabk: str
    enbez: str
    titel: str
    doknr: str
    builddate: str
    text: str
    raw_xml: str
    fussnoten: str = ""


@dataclass
class DecisionResult:
    document_number: str
    ecli: str
    file_number: str
    court_type: str
    decision_date: str
    headline: str
    title_line: str
    summary: str


def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()


def create_verification_receipt(
    norm: NormResult,
    cached: bool = False,
    retrieval_method: str = "canonical_xml",
    verification_status: str = "verified_current",
    fallback_reason: Optional[str] = None,
) -> Dict[str, Any]:
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "source_id": norm.doknr,
        "law_slug": norm.law_slug,
        "jurabk": norm.jurabk,
        "enbez": norm.enbez,
        "titel": norm.titel,
        "doknr": norm.doknr,
        "builddate": norm.builddate,
        "retrieved_at": now_utc,
        "effective_status": "in_force",
        "raw_content_sha256": compute_sha256(norm.raw_xml),
        "normalized_content_sha256": compute_sha256(norm.text),
        "cached": cached,
        "retrieval_method": retrieval_method,
        "verification_status": verification_status,
        "fallback_reason": fallback_reason,
    }


def format_5_layer_output(
    norm: NormResult,
    receipt: Dict[str, Any],
    decisions: Optional[List[DecisionResult]] = None,
    paraphrase: Optional[str] = None,
    assessment: Optional[str] = None,
) -> str:
    parts = []

    # Layer A: Normwortlaut
    parts.append(f"# {norm.jurabk} {norm.enbez} — {norm.titel}")
    parts.append("\n## A) Normwortlaut")
    parts.append(norm.text.strip())
    if norm.fussnoten:
        parts.append(f"\n*Amtlicher Nachweis / Fußnoten:*\n{norm.fussnoten.strip()}")

    # Layer B: Metadaten & Verification Receipt
    parts.append("\n## B) Metadaten & Verification Receipt")
    parts.append("```json")
    parts.append(json.dumps(receipt, indent=2, ensure_ascii=False))
    parts.append("```")

    # Layer C: Verständliche Zusammenfassung
    parts.append("\n## C) Verständliche Zusammenfassung")
    if paraphrase:
        parts.append(paraphrase.strip())
    else:
        parts.append(
            f"{norm.enbez} {norm.jurabk} regelt den Gegenstand '{norm.titel}'. "
            f"Der Normtext gliedert sich in die vorstehenden Absätze und ist in der konsolidierten "
            f"amtlichen Fassung (Build-Stand: {norm.builddate}) in Kraft."
        )

    # Layer D: BGH-Judikatur & Leitsätze
    parts.append("\n## D) BGH-Judikatur & Leitsätze")
    if decisions and len(decisions) > 0:
        for idx, dec in enumerate(decisions, start=1):
            parts.append(
                f"### {idx}. {dec.court_type} — {dec.file_number} ({dec.decision_date})\n"
                f"- **Titel:** {dec.title_line or dec.headline}\n"
                f"- **ECLI:** `{dec.ecli}` (DokNr: `{dec.document_number}`)\n"
                f"- **Leitsatz/Auszug:** {dec.summary[:500]}..."
            )
    else:
        parts.append("*Keine einschlägigen BGH-Entscheidungen im Sofort-Abruf.*")

    # Layer E: Schlussfolgerung & Rechtsunsicherheit
    parts.append("\n## E) Schlussfolgerung & Rechtsunsicherheit")
    if assessment:
        parts.append(assessment.strip())
    else:
        parts.append(
            "Dieser Auszug stellt authentischen Normtext und amtliche Rechtsprechung dar. "
            "Er ersetzt keine einzelfallbezogene Rechtsberatung durch eine Rechtsanwältin oder einen Rechtsanwalt."
        )

    return "\n".join(parts)
