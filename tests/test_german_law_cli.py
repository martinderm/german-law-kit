#!/usr/bin/env python3
"""
Unit- und Integrationstests für german-law-kit.
"""

import sys
import unittest
from pathlib import Path

# Add scripts directory to path
SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from lib.gii_client import parse_norm_from_xml_string, resolve_canonical_law
from lib.receipt import create_verification_receipt, format_5_layer_output, NormResult, DecisionResult
from lib.cache import AtomicDiskCache


class TestCanonicalLaws(unittest.TestCase):
    def test_canonical_lookups(self):
        canonical_file = SKILL_DIR / "references" / "canonical-laws.json"
        self.assertTrue(canonical_file.exists(), "canonical-laws.json must exist")

        # Test resolution of key real-estate laws
        cases = [
            ("bgb", "bgb", "BGB"),
            ("BGB", "bgb", "BGB"),
            ("weg", "woeigg", "WEG"),
            ("wohnungseigentumsgesetz", "woeigg", "WEG"),
            ("baugb", "bbaug", "BauGB"),
            ("betrkv", "betrkv", "BetrKV"),
            ("heizkostenv", "heizkostenv", "HeizkostenV"),
            ("wovermittg", "wovermrg", "WoVermittG"),
            ("mabv", "gewo_34cdv", "MaBV"),
            ("grestg", "grestg_1983", "GrEStG"),
            ("gnotkg", "gnotkg", "GNotKG"),
        ]
        for query, expected_slug, expected_short in cases:
            law = resolve_canonical_law(query, canonical_file)
            self.assertIsNotNone(law, f"Failed to resolve {query}")
            self.assertEqual(law["slug"], expected_slug, f"Slug mismatch for {query}")
            self.assertEqual(law["short_title"], expected_short, f"Short title mismatch for {query}")


class TestNormParsing(unittest.TestCase):
    def setUp(self):
        self.fixture_path = SKILL_DIR / "tests" / "fixtures" / "bgb_sample.xml"

    def test_parse_norm(self):
        xml_content = self.fixture_path.read_text(encoding="utf-8")
        norm = parse_norm_from_xml_string(xml_content, "§ 535")
        self.assertIsNotNone(norm, "Norm § 535 should be found")
        self.assertEqual(norm.doknr, "BJNR001950896BJNE052902377")
        self.assertEqual(norm.jurabk, "BGB")
        self.assertEqual(norm.enbez, "§ 535")
        self.assertEqual(norm.titel, "Inhalt und Hauptpflichten des Mietvertrags")
        self.assertEqual(norm.builddate, "20260926215508")
        self.assertIn("(1) Durch den Mietvertrag wird der Vermieter verpflichtet", norm.text)
        self.assertIn("(2) Der Mieter ist verpflichtet", norm.text)
        self.assertIn("Zur Nichtanwendung vgl. § 549", norm.fussnoten)

    def test_parse_norm_not_found(self):
        xml_content = self.fixture_path.read_text(encoding="utf-8")
        norm = parse_norm_from_xml_string(xml_content, "§ 9999")
        self.assertIsNone(norm, "Unknown paragraph should return None")


class TestReceiptAndFormatting(unittest.TestCase):
    def test_receipt_generation(self):
        norm = NormResult(
            law_slug="bgb",
            jurabk="BGB",
            enbez="§ 535",
            titel="Inhalt und Hauptpflichten des Mietvertrags",
            doknr="BJNR001950896BJNE052902377",
            builddate="20260926215508",
            text="(1) Test text\n(2) Test text 2",
            raw_xml="<norm>test</norm>",
            fussnoten="Test fussnote",
        )
        receipt = create_verification_receipt(norm, cached=True)
        self.assertEqual(receipt["doknr"], "BJNR001950896BJNE052902377")
        self.assertEqual(receipt["verification_status"], "verified_current")
        self.assertEqual(len(receipt["raw_content_sha256"]), 64)
        self.assertEqual(len(receipt["normalized_content_sha256"]), 64)
        self.assertTrue(receipt["cached"])

    def test_5_layer_formatting(self):
        norm = NormResult(
            law_slug="bgb",
            jurabk="BGB",
            enbez="§ 535",
            titel="Inhalt und Hauptpflichten des Mietvertrags",
            doknr="BJNR001950896BJNE052902377",
            builddate="20260926215508",
            text="(1) Test text",
            raw_xml="<norm>test</norm>",
            fussnoten="Test fussnote",
        )
        receipt = create_verification_receipt(norm, cached=False)
        decisions = [
            DecisionResult(
                document_number="KARE123",
                ecli="ECLI:DE:BGH:2025:U.123",
                file_number="VIII ZR 1/25",
                court_type="BGH",
                decision_date="2025-05-15",
                headline="BGH, Urteil vom 15. Mai 2025 - VIII ZR 1/25",
                title_line="Schönheitsreparaturen im Mietrecht",
                summary="Leitsatz zum Mietrecht",
            )
        ]
        output = format_5_layer_output(norm, receipt, decisions)
        self.assertIn("## A) Normwortlaut", output)
        self.assertIn("## B) Metadaten & Verification Receipt", output)
        self.assertIn("## C) Verständliche Zusammenfassung", output)
        self.assertIn("## D) BGH-Judikatur & Leitsätze", output)
        self.assertIn("## E) Schlussfolgerung & Rechtsunsicherheit", output)
        self.assertIn("VIII ZR 1/25", output)


class TestAtomicCache(unittest.TestCase):
    def test_cache_write_and_read(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = AtomicDiskCache(Path(tmpdir))
            cache.put_text("test_key.txt", "Hello World")
            content = cache.get_text("test_key.txt")
            self.assertEqual(content, "Hello World")
            self.assertTrue(cache.has("test_key.txt"))


if __name__ == "__main__":
    unittest.main()
