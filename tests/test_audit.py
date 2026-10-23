"""Tests for the PaperForge auditor (audit.py).

Run from the repository root:

    python3 -m unittest discover -s tests -v

The clean sample papers must pass; deliberately broken specifications must
fail with the expected finding codes.
"""

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import audit  # noqa: E402


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def codes(findings):
    return [f.code for f in findings]


class CleanSamplesPass(unittest.TestCase):
    def test_english_sample_passes(self):
        spec = load("samples/english/spec.json")
        blueprint = load("blueprints/secondary-language-80.json")
        self.assertEqual(audit.audit(spec, blueprint), [])

    def test_maths_sample_passes(self):
        spec = load("samples/maths/spec.json")
        blueprint = load("blueprints/secondary-maths-80.json")
        self.assertEqual(audit.audit(spec, blueprint), [])


class BrokenSpecsFail(unittest.TestCase):
    def setUp(self):
        self.spec = load("samples/english/spec.json")
        self.blueprint = load("blueprints/secondary-language-80.json")

    def test_wrong_total_is_caught(self):
        broken = copy.deepcopy(self.spec)
        # Inflate one question's marks: section subtotal, composition and
        # grand total all break.
        broken["sections"][0]["questions"][0]["marks"] = 5
        findings = audit.audit(broken, self.blueprint)
        self.assertIn("TOTAL_MISMATCH", codes(findings))
        self.assertIn("SECTION_SUBTOTAL", codes(findings))
        self.assertIn("COMPOSITION_MISMATCH", codes(findings))

    def test_missing_question_is_caught(self):
        broken = copy.deepcopy(self.spec)
        del broken["sections"][2]["questions"][0]
        findings = audit.audit(broken, self.blueprint)
        self.assertIn("COMPOSITION_MISMATCH", codes(findings))
        self.assertIn("TOTAL_MISMATCH", codes(findings))

    def test_unmirrored_choice_is_caught(self):
        broken = copy.deepcopy(self.spec)
        # Q11 offers an internal choice; strip the scheme's mirror flag.
        question = broken["sections"][1]["questions"][0]
        self.assertIn("choice", question)
        question["scheme"]["mirrors_choice"] = False
        findings = audit.audit(broken, self.blueprint)
        self.assertIn("CHOICE_NOT_MIRRORED", codes(findings))

    def test_choice_without_alternative_points_is_caught(self):
        broken = copy.deepcopy(self.spec)
        question = broken["sections"][1]["questions"][0]
        del question["scheme"]["alternative_value_points"]
        findings = audit.audit(broken, self.blueprint)
        self.assertIn("CHOICE_SCHEME_MISSING", codes(findings))

    def test_mirror_without_choice_is_caught(self):
        broken = copy.deepcopy(self.spec)
        # Q13 has no internal choice; pretend its scheme mirrors one.
        question = broken["sections"][1]["questions"][2]
        self.assertNotIn("choice", question)
        question["scheme"]["mirrors_choice"] = True
        question["scheme"]["alternative_value_points"] = ["Anything."]
        findings = audit.audit(broken, self.blueprint)
        self.assertIn("CHOICE_MIRROR_WITHOUT_CHOICE", codes(findings))

    def test_missing_word_limit_is_caught(self):
        broken = copy.deepcopy(self.spec)
        question = broken["sections"][1]["questions"][2]
        del question["word_limit"]
        findings = audit.audit(broken, self.blueprint)
        self.assertIn("WORD_LIMIT_MISSING", codes(findings))

    def test_missing_scheme_is_caught(self):
        broken = copy.deepcopy(self.spec)
        question = broken["sections"][0]["questions"][5]
        del question["scheme"]
        findings = audit.audit(broken, self.blueprint)
        self.assertIn("SCHEME_MISSING", codes(findings))


class SpellingLocale(unittest.TestCase):
    def setUp(self):
        self.blueprint = load("blueprints/secondary-language-80.json")

    def _minimal_spec(self, prompt_text):
        return {
            "paper": {"max_marks": 1},
            "sections": [
                {
                    "id": "A",
                    "title": "Reading",
                    "questions": [
                        {
                            "id": "Q1",
                            "type": "mcq",
                            "marks": 1,
                            "prompt": prompt_text,
                            "options": ["x", "y"],
                            "scheme": {"answer": "a) x"},
                        }
                    ],
                }
            ],
        }

    def _minimal_blueprint(self):
        return {
            "name": "Minimal",
            "total_marks": 1,
            "locale": "en-GB",
            "sections": [
                {
                    "id": "A",
                    "title": "Reading",
                    "subtotal": 1,
                    "composition": [{"type": "mcq", "count": 1, "marks_each": 1}],
                }
            ],
        }

    def test_us_spelling_flagged_under_en_gb(self):
        spec = self._minimal_spec("How does the center organize the data?")
        findings = audit.audit(spec, self._minimal_blueprint())
        self.assertIn("SPELLING_LOCALE", codes(findings))
        messages = " ".join(f.message for f in findings)
        self.assertIn("centre", messages)
        self.assertIn("organise", messages)

    def test_gb_spelling_flagged_under_en_us(self):
        spec = self._minimal_spec("How does the centre organise the data?")
        findings = audit.audit(spec, self._minimal_blueprint(), locale="en-US")
        self.assertIn("SPELLING_LOCALE", codes(findings))

    def test_gb_spelling_passes_under_en_gb(self):
        spec = self._minimal_spec("How does the centre organise the data?")
        findings = audit.audit(spec, self._minimal_blueprint())
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
