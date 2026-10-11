#!/usr/bin/env python3
"""
NeuRIS REST Client für german-law-kit.
Fragt amtliche Gerichtsentscheidungen (insb. BGH) über testphase.rechtsinformationen.bund.de ab.
"""

import json
import urllib.parse
import urllib.request
from typing import List, Optional

from .receipt import DecisionResult


NEURIS_CASE_LAW_URL = "https://testphase.rechtsinformationen.bund.de/v1/document/lucene-search/case-law"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) german-law-kit/1.0"


def search_case_law(query: str, court: str = "BGH", limit: int = 3, timeout: int = 15) -> List[DecisionResult]:
    """
    Sucht Rechtsprechung über die NeuRIS-API des Bundes.
    Standardmäßig wird nach BGH-Entscheidungen gefiltert.
    """
    full_query = f"{query} {court}".strip() if court else query.strip()
    encoded_query = urllib.parse.quote(full_query)
    url = f"{NEURIS_CASE_LAW_URL}?q={encoded_query}&size={limit}"

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return []
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        # Graceful degradation if NeuRIS testphase is temporarily unreachable
        return []

    results: List[DecisionResult] = []
    members = data.get("member", [])

    for entry in members:
        item = entry.get("item", {})
        if not item:
            continue

        file_numbers = item.get("fileNumbers", [])
        file_num_str = ", ".join(file_numbers) if isinstance(file_numbers, list) else str(file_numbers)

        summary_text = (
            item.get("otherLongText")
            or item.get("titleLine")
            or item.get("headline")
            or ""
        )

        results.append(
            DecisionResult(
                document_number=item.get("documentNumber", ""),
                ecli=item.get("ecli", ""),
                file_number=file_num_str,
                court_type=item.get("courtType", court),
                decision_date=item.get("decisionDate", ""),
                headline=item.get("headline", ""),
                title_line=item.get("titleLine", ""),
                summary=summary_text,
            )
        )

    return results
