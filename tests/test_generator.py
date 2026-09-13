import unittest
import gzip
import xml.etree.ElementTree as ET
from pathlib import Path
from engine.blueprint_loader import list_blueprints, get_blueprint, get_genres
from engine.als_generator import generate_als

class TestArrangementPilotEngine(unittest.TestCase):
    def test_blueprint_loader(self):
        blueprints = list_blueprints()
        self.assertGreaterEqual(len(blueprints), 4, "Should find at least 4 curated blueprints")
        genres = get_genres()
        self.assertIn("Techno", genres)
        self.assertIn("House", genres)

    def test_generate_als_with_clips(self):
        bp = get_blueprint("raw_hypnotic_chlar")
        self.assertIsNotNone(bp)
        als_bytes = generate_als(bp, bpm_override=139.5, include_clips=True)
        self.assertGreater(len(als_bytes), 1000)

        # Decompress and validate XML structure
        xml_text = gzip.decompress(als_bytes)
        root = ET.fromstring(xml_text)
        self.assertEqual(root.tag, "Ableton")

        # Verify Master BPM
        tempo = root.find(".//MainTrack/DeviceChain/Mixer/Tempo/Manual")
        self.assertIsNotNone(tempo)
        self.assertEqual(tempo.attrib.get("Value"), "139.5")

        # Verify Tracks
        tracks = root.findall(".//Tracks/MidiTrack")
        self.assertEqual(len(tracks), len(bp["tracks"]))

        # Verify Locators
        locators = root.findall(".//Locators/Locators/Locator")
        self.assertEqual(len(locators), len(bp["sections"]))

        # Verify Clips exist
        total_clips = sum(len(t.findall(".//ArrangerAutomation/Events/MidiClip")) for t in tracks)
        self.assertGreater(total_clips, 0)

    def test_generate_als_without_clips(self):
        bp = get_blueprint("hypnotic_mulero")
        self.assertIsNotNone(bp)
        als_bytes = generate_als(bp, include_clips=False)
        xml_text = gzip.decompress(als_bytes)
        root = ET.fromstring(xml_text)

        tracks = root.findall(".//Tracks/MidiTrack")
        self.assertEqual(len(tracks), len(bp["tracks"]))
        total_clips = sum(len(t.findall(".//ArrangerAutomation/Events/MidiClip")) for t in tracks)
        self.assertEqual(total_clips, 0)

    def test_all_curated_blueprints_generate_valid_als(self):
        from collections import Counter
        for bp_summary in list_blueprints():
            bp = get_blueprint(bp_summary["id"])
            als_bytes = generate_als(bp, include_clips=True)
            xml_text = gzip.decompress(als_bytes)
            root = ET.fromstring(xml_text)
            self.assertEqual(root.tag, "Ableton")
            tracks = root.findall(".//Tracks/MidiTrack")
            self.assertEqual(len(tracks), len(bp["tracks"]))

            # Verify strictly 0 duplicate Pointee IDs (prevent Ableton 'non-unique Pointee IDs' corruption error)
            id_counts = Counter()
            for el in root.iter():
                if "Id" in el.attrib:
                    id_counts[el.attrib["Id"]] += 1
            dups = {k: v for k, v in id_counts.items() if v > 1 and int(k) > 100}
            self.assertEqual(len(dups), 0, f"Blueprint {bp['id']} produced duplicate Pointee IDs: {dups}")

if __name__ == "__main__":
    unittest.main()
