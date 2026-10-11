#!/usr/bin/env python3
"""
gesetze-im-internet.de XML Client für german-law-kit.
Lädt amtliche Norm-XMLs herunter, extrahiert Einzelnormen und normalisiert Paragrafentexte.
"""

import io
import json
import re
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from .cache import AtomicDiskCache
from .receipt import NormResult


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) german-law-kit/1.0"


def normalize_paragraph_string(s: str) -> str:
    """Normalisiert Paragrafenangaben wie '535', '§535', '§ 535 ' auf '§ 535'."""
    s = s.strip().replace("\xa0", " ")
    # Handle pure digits or alphanumeric e.g. '535' or '556d'
    if not s.startswith("§") and not s.lower().startswith("art"):
        s = f"§ {s}"
    # Ensure space after §
    if s.startswith("§") and not s.startswith("§ "):
        s = f"§ {s[1:].strip()}"
    return s


def resolve_canonical_law(query: str, canonical_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Löst ein Gesetzeskürzel oder einen Namen über canonical-laws.json auf."""
    if canonical_path is None:
        canonical_path = Path(__file__).resolve().parent.parent.parent / "references" / "canonical-laws.json"

    if not canonical_path.exists():
        return None

    try:
        data = json.loads(canonical_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    q_clean = query.strip().lower()

    for law in data.get("laws", []):
        if law.get("id", "").lower() == q_clean:
            return law
        if law.get("slug", "").lower() == q_clean:
            return law
        if law.get("short_title", "").lower() == q_clean:
            return law
        for alias in law.get("aliases", []):
            if alias.lower() == q_clean:
                return law

    return None


def fetch_law_xml_bytes(slug: str) -> bytes:
    """Lädt das offizielle XML-ZIP von gesetze-im-internet.de herunter."""
    url = f"https://www.gesetze-im-internet.de/{slug}/xml.zip"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} fetching {url}")
        return resp.read()


def extract_xml_from_zip(zip_bytes: bytes) -> str:
    """Entpackt die XML-Datei aus dem ZIP-Archiv."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        for name in z.namelist():
            if name.endswith(".xml"):
                raw_bytes = z.read(name)
                # Decode with fallback
                for enc in ["utf-8", "iso-8859-1", "latin-1"]:
                    try:
                        return raw_bytes.decode(enc)
                    except UnicodeDecodeError:
                        continue
                return raw_bytes.decode("utf-8", errors="replace")
    raise ValueError("Keine XML-Datei im ZIP-Archiv gefunden")


def parse_norm_from_xml_string(xml_content: str, paragraph_query: str) -> Optional[NormResult]:
    """Sucht eine Einzelnorm im XML-Text und extrahiert Metadaten und Text."""
    target_enbez = normalize_paragraph_string(paragraph_query)

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise ValueError(f"Ungültiges XML: {e}")

    # Find all norm elements
    for norm_elem in root.findall(".//norm"):
        doknr = norm_elem.get("doknr", "")
        builddate = norm_elem.get("builddate", "")

        meta_elem = norm_elem.find("metadaten")
        if meta_elem is None:
            continue

        jurabk_elem = meta_elem.find("jurabk")
        jurabk = jurabk_elem.text.strip() if jurabk_elem is not None and jurabk_elem.text else ""

        enbez_elem = meta_elem.find("enbez")
        enbez_raw = enbez_elem.text.strip() if enbez_elem is not None and enbez_elem.text else ""
        enbez_norm = normalize_paragraph_string(enbez_raw)

        if enbez_norm != target_enbez and enbez_raw != paragraph_query.strip():
            continue

        titel_elem = meta_elem.find("titel")
        titel = titel_elem.text.strip() if titel_elem is not None and titel_elem.text else ""

        # Extract text paragraphs
        paragraphs = []
        text_elem = norm_elem.find(".//textdaten/text")
        if text_elem is not None:
            for p in text_elem.findall(".//P"):
                p_text = "".join(p.itertext()).strip()
                if p_text:
                    paragraphs.append(p_text)

        full_text = "\n\n".join(paragraphs) if paragraphs else ""

        # Extract footnotes / stand
        fussnoten = []
        fuss_elem = norm_elem.find(".//textdaten/fussnoten")
        if fuss_elem is not None:
            for p in fuss_elem.findall(".//P"):
                f_text = "".join(p.itertext()).strip()
                if f_text:
                    fussnoten.append(f_text)
        fussnoten_text = "\n".join(fussnoten)

        # Raw XML of the norm element
        raw_xml = ET.tostring(norm_elem, encoding="utf-8").decode("utf-8")

        return NormResult(
            law_slug="",
            jurabk=jurabk,
            enbez=enbez_raw or target_enbez,
            titel=titel,
            doknr=doknr,
            builddate=builddate,
            text=full_text,
            raw_xml=raw_xml,
            fussnoten=fussnoten_text,
        )

    return None


def fetch_norm(
    law_query: str,
    paragraph_query: str,
    cache: AtomicDiskCache,
    canonical_path: Optional[Path] = None,
    force_refresh: bool = False,
) -> Tuple[Optional[NormResult], bool]:
    """
    Holt eine Einzelnorm: Löst Canonical Law auf, nutzt Disk-Cache oder lädt XML herunter.
    Rückgabe: (NormResult oder None, was_cached)
    """
    law = resolve_canonical_law(law_query, canonical_path)
    if law:
        slug = law["slug"]
    else:
        # Fallback to query as slug
        slug = law_query.strip().lower()

    cache_key = f"{slug}_full.xml"
    xml_content = None
    was_cached = False

    if not force_refresh and cache.has(cache_key):
        xml_content = cache.get_text(cache_key)
        was_cached = True

    if not xml_content:
        zip_bytes = fetch_law_xml_bytes(slug)
        xml_content = extract_xml_from_zip(zip_bytes)
        cache.put_text(cache_key, xml_content)
        was_cached = False

    norm = parse_norm_from_xml_string(xml_content, paragraph_query)
    if norm:
        norm.law_slug = slug
        if law and not norm.jurabk:
            norm.jurabk = law["short_title"]

    return norm, was_cached
