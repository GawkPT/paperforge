# Changelog

All notable changes to PaperForge are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-10-23

### Added

- Blueprint format (JSON) describing a paper pattern: total marks, sections,
  per-section composition by question type and marks, spelling locale, and
  the word-limit rule; with a JSON Schema in `schema/blueprint.schema.json`.
- Paper specification format (JSON) carrying questions, options, passages,
  word limits, internal choices, and the marking scheme for every question.
- Typst templates rendering a print-ready question paper
  (`templates/paper.typ`) and its marking scheme (`templates/scheme.typ`)
  from the same specification.
- Auditor (`audit.py`, Python standard library only) checking marks
  totalling, section distribution, internal-choice consistency between
  paper and scheme, word-limit presence, scheme coverage, and spelling
  locale (en-GB default, en-US selectable), with a line-item report and a
  pass/fail exit status.
- Two complete worked samples with rendered PDFs: a secondary language
  paper and a secondary mathematics paper, each with its own blueprint,
  all questions original.
- Test suite (stdlib `unittest`) covering both clean samples, seven
  deliberately broken specifications, and the spelling-locale lint in both
  locales.
