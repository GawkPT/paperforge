#!/usr/bin/env python3
"""PaperForge auditor.

Checks a paper specification (JSON) against its blueprint (JSON) and reports
line-item findings. A paper passes only when every check passes.

Checks performed
----------------
1. Marks totalling - the paper's grand total and every section subtotal
   match the blueprint.
2. Section distribution - each section contains exactly the composition of
   question types and marks-per-question the blueprint prescribes.
3. Choice consistency - wherever a question offers an internal choice, the
   marking scheme must mirror that choice (an alternative answer with its
   own value points). A scheme that mirrors a choice the question does not
   offer is flagged too.
4. Word limits - where the blueprint requires them, every long-answer
   question declares a word limit.
5. Marking scheme presence - every question carries a scheme entry (an
   answer for objective questions, value points for written answers).
6. Spelling locale - the paper's text is linted for spellings from the
   wrong locale (en-GB by default; en-US selectable).

Usage:
    python3 audit.py PAPER_SPEC --blueprint BLUEPRINT [--locale en-GB|en-US]

Exit status is 0 when the paper passes and 1 when any finding is raised.
Only the Python standard library is used.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Spellings that betray the wrong locale. Keys are the offending spelling,
# values the expected spelling in the target locale. The lists are kept
# deliberately conservative: only words whose spelling differs unambiguously
# between the two locales are included.
US_SPELLINGS = {
    "organize": "organise",
    "organized": "organised",
    "organizing": "organising",
    "organization": "organisation",
    "behavior": "behaviour",
    "color": "colour",
    "colors": "colours",
    "center": "centre",
    "centers": "centres",
    "realize": "realise",
    "realized": "realised",
    "recognize": "recognise",
    "traveling": "travelling",
    "traveled": "travelled",
    "favorite": "favourite",
    "labor": "labour",
    "neighbor": "neighbour",
    "neighbors": "neighbours",
    "defense": "defence",
    "liter": "litre",
    "meter": "metre",
    "program": "programme",
    "analyze": "analyse",
    "characterize": "characterise",
    "summarize": "summarise",
    "minimize": "minimise",
    "maximize": "maximise",
    "utilize": "utilise",
    "practice": None,  # noun/verb distinction differs; never flagged
}
US_SPELLINGS.pop("practice")

GB_SPELLINGS = {
    "organise": "organize",
    "organised": "organized",
    "organising": "organizing",
    "organisation": "organization",
    "behaviour": "behavior",
    "colour": "color",
    "colours": "colors",
    "centre": "center",
    "centres": "centers",
    "realise": "realize",
    "realised": "realized",
    "recognise": "recognize",
    "travelling": "traveling",
    "travelled": "traveled",
    "favourite": "favorite",
    "labour": "labor",
    "neighbour": "neighbor",
    "neighbours": "neighbors",
    "defence": "defense",
    "litre": "liter",
    "metre": "meter",
    "programme": "program",
    "analyse": "analyze",
    "characterise": "characterize",
    "summarise": "summarize",
    "minimise": "minimize",
    "maximise": "maximize",
    "utilise": "utilize",
}


class Finding:
    """One audit finding: a stable code plus a human-readable message."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Finding({self.code!r}, {self.message!r})"


def _iter_strings(obj, path="paper"):
    """Yield (path, text) for every string anywhere inside *obj*."""
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for key, value in obj.items():
            yield from _iter_strings(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from _iter_strings(value, f"{path}[{index}]")


def _question_label(section_id: str, question: dict, index: int) -> str:
    return question.get("id") or f"Section {section_id} question {index + 1}"


def audit(spec: dict, blueprint: dict, locale: str | None = None) -> list[Finding]:
    """Audit *spec* against *blueprint*. Returns a list of findings.

    An empty list means the paper passes. *locale* overrides the spelling
    locale; when omitted, the blueprint's locale (default en-GB) is used.
    """
    findings: list[Finding] = []
    locale = locale or blueprint.get("locale", "en-GB")

    spec_sections = {s.get("id"): s for s in spec.get("sections", [])}
    bp_sections = {s.get("id"): s for s in blueprint.get("sections", [])}

    # -- Section presence -------------------------------------------------
    for section_id in bp_sections:
        if section_id not in spec_sections:
            findings.append(
                Finding(
                    "SECTION_MISSING",
                    f"Blueprint section {section_id} is missing from the paper.",
                )
            )
    for section_id in spec_sections:
        if section_id not in bp_sections:
            findings.append(
                Finding(
                    "SECTION_UNEXPECTED",
                    f"Paper section {section_id} has no counterpart in the blueprint.",
                )
            )

    # -- Per-section checks ------------------------------------------------
    require_word_limits = blueprint.get("long_answer_requires_word_limit", True)
    for section_id, bp_section in bp_sections.items():
        spec_section = spec_sections.get(section_id)
        if spec_section is None:
            continue
        questions = spec_section.get("questions", [])

        # Marks totalling within the section.
        section_total = sum(q.get("marks", 0) for q in questions)
        if section_total != bp_section.get("subtotal"):
            findings.append(
                Finding(
                    "SECTION_SUBTOTAL",
                    f"Section {section_id}: questions total {section_total} marks, "
                    f"but the blueprint subtotal is {bp_section.get('subtotal')}.",
                )
            )

        # Composition: counts per (type, marks-per-question).
        expected = Counter()
        for entry in bp_section.get("composition", []):
            expected[(entry["type"], entry["marks_each"])] += entry["count"]
        actual = Counter((q.get("type"), q.get("marks")) for q in questions)
        for key in sorted(set(expected) | set(actual), key=str):
            if expected[key] != actual[key]:
                qtype, marks_each = key
                findings.append(
                    Finding(
                        "COMPOSITION_MISMATCH",
                        f"Section {section_id}: blueprint expects {expected[key]} "
                        f"x {qtype} at {marks_each} mark(s) each; "
                        f"the paper has {actual[key]}.",
                    )
                )

        # Per-question checks.
        for index, question in enumerate(questions):
            label = _question_label(section_id, question, index)
            scheme = question.get("scheme")

            # Marking scheme presence.
            if not scheme:
                findings.append(
                    Finding(
                        "SCHEME_MISSING",
                        f"{label}: no marking scheme entry.",
                    )
                )
            elif question.get("type") == "mcq":
                if not scheme.get("answer"):
                    findings.append(
                        Finding(
                            "SCHEME_MISSING",
                            f"{label}: objective question has no scheme answer.",
                        )
                    )
            elif not scheme.get("value_points"):
                findings.append(
                    Finding(
                        "SCHEME_MISSING",
                        f"{label}: written question has no scheme value points.",
                    )
                )

            # Choice consistency, in both directions.
            has_choice = bool(question.get("choice"))
            if has_choice:
                if not scheme or not scheme.get("mirrors_choice"):
                    findings.append(
                        Finding(
                            "CHOICE_NOT_MIRRORED",
                            f"{label}: the question offers an internal choice "
                            "but the marking scheme does not mirror it.",
                        )
                    )
                elif not scheme.get("alternative_value_points"):
                    findings.append(
                        Finding(
                            "CHOICE_SCHEME_MISSING",
                            f"{label}: the scheme mirrors the internal choice "
                            "but gives no value points for the alternative.",
                        )
                    )
            elif scheme and scheme.get("mirrors_choice"):
                findings.append(
                    Finding(
                        "CHOICE_MIRROR_WITHOUT_CHOICE",
                        f"{label}: the scheme mirrors an internal choice "
                        "that the question does not offer.",
                    )
                )

            # Word limits on long answers.
            if (
                require_word_limits
                and question.get("type") == "long-answer"
                and not question.get("word_limit")
            ):
                findings.append(
                    Finding(
                        "WORD_LIMIT_MISSING",
                        f"{label}: long-answer question declares no word limit.",
                    )
                )

    # -- Grand total --------------------------------------------------------
    paper_total = sum(
        q.get("marks", 0)
        for section in spec.get("sections", [])
        for q in section.get("questions", [])
    )
    declared = spec.get("paper", {}).get("max_marks")
    if declared is not None and declared != paper_total:
        findings.append(
            Finding(
                "TOTAL_MISMATCH",
                f"The paper declares {declared} maximum marks but its "
                f"questions total {paper_total}.",
            )
        )
    if paper_total != blueprint.get("total_marks"):
        findings.append(
            Finding(
                "TOTAL_MISMATCH",
                f"The paper's questions total {paper_total} marks, but the "
                f"blueprint total is {blueprint.get('total_marks')}.",
            )
        )

    # -- Spelling locale ------------------------------------------------------
    offenders = US_SPELLINGS if locale == "en-GB" else GB_SPELLINGS
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(word) for word in offenders) + r")\b",
        re.IGNORECASE,
    )
    for path, text in _iter_strings(spec):
        for match in pattern.finditer(text):
            word = match.group(0).lower()
            findings.append(
                Finding(
                    "SPELLING_LOCALE",
                    f"{path}: '{match.group(0)}' is not {locale} spelling; "
                    f"use '{offenders[word]}'.",
                )
            )

    return findings


def format_report(
    spec_path: str, blueprint_name: str, locale: str, findings: list[Finding]
) -> str:
    lines = [
        f"PaperForge audit: {spec_path}",
        f"Blueprint: {blueprint_name} | Locale: {locale}",
        "-" * 60,
    ]
    if findings:
        for finding in findings:
            lines.append(f"FAIL [{finding.code}] {finding.message}")
        lines.append("-" * 60)
        lines.append(f"RESULT: FAIL - {len(findings)} finding(s)")
    else:
        lines.append("All checks passed: totals, distribution, choice")
        lines.append("consistency, word limits, scheme coverage, spelling.")
        lines.append("-" * 60)
        lines.append("RESULT: PASS")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit a PaperForge paper specification against its blueprint."
    )
    parser.add_argument("spec", help="Path to the paper specification JSON.")
    parser.add_argument(
        "--blueprint", required=True, help="Path to the blueprint JSON."
    )
    parser.add_argument(
        "--locale",
        choices=["en-GB", "en-US"],
        default=None,
        help="Spelling locale to lint against (default: the blueprint's locale).",
    )
    args = parser.parse_args(argv)

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    blueprint = json.loads(Path(args.blueprint).read_text(encoding="utf-8"))
    locale = args.locale or blueprint.get("locale", "en-GB")

    findings = audit(spec, blueprint, locale=args.locale)
    print(format_report(args.spec, blueprint.get("name", "?"), locale, findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
