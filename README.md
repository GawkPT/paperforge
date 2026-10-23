# PaperForge

**A blueprint-driven exam-paper engine.** Describe the pattern of an
examination once — sections, question types, marks, word limits, internal
choices — and PaperForge renders a print-ready question paper *and* its
marking scheme from a single specification, then audits the paper against
the pattern before anyone prints it.

PaperForge is subject-agnostic and board-agnostic. The engine knows nothing
about any particular examination system; everything specific lives in two
JSON files:

- a **blueprint** — the pattern a paper must follow (total marks, sections,
  the composition of each section by question type and marks);
- a **paper specification** — one actual paper: its questions, options,
  passages, word limits, internal choices, and the marking scheme for every
  question.

Because the paper and the scheme are rendered from the *same* specification,
they cannot drift apart — the classic failure in which the scheme marks a
choice the paper never offered, or the paper totals 78 of a declared 80.

## Who it is for

- Teachers who set class tests and terminal examinations in any subject.
- Departments and schools that want every paper checked against the pattern
  before it reaches the print room.
- Examination cells tired of hand-totalling marks in a spreadsheet.

## What the auditor checks

`audit.py` (Python, standard library only) verifies a paper specification
against its blueprint and reports line-item findings:

1. **Marks totalling** — the grand total and every section subtotal.
2. **Section distribution** — each section holds exactly the composition of
   question types and marks-per-question the blueprint prescribes.
3. **Choice consistency** — where a question offers an internal choice, the
   marking scheme must mirror it, with value points for the alternative;
   a scheme that mirrors a choice the question does not offer is flagged.
4. **Word limits** — where the blueprint requires them, every long-answer
   question declares one. (Blueprints for subjects such as mathematics,
   whose long answers are worked solutions, can switch this off.)
5. **Scheme coverage** — every question carries a scheme entry: an answer
   for objective questions, value points for written ones.
6. **Spelling locale** — the paper's text is linted for spellings from the
   wrong locale (`en-GB` by default, `en-US` selectable).

## Quickstart

Requirements: [Typst](https://typst.app) for rendering, Python 3.10+ for the
auditor. Nothing else — no packages to install.

```sh
# 1. Audit a sample paper against its blueprint
python3 audit.py samples/english/spec.json \
    --blueprint blueprints/secondary-language-80.json

# 2. Render the paper and its marking scheme (run from the repo root;
#    --root is needed because the samples import the shared templates)
typst compile --root . samples/english/paper.typ
typst compile --root . samples/english/scheme.typ

# 3. Run the test suite
python3 -m unittest discover -s tests -v
```

A second sample, in mathematics, lives in `samples/maths/` with its own
blueprint (`blueprints/secondary-maths-80.json`) — same engine, different
subject, different paper shape.

### Example auditor output

A passing paper:

```text
PaperForge audit: samples/english/spec.json
Blueprint: Secondary Language Paper - 80 marks | Locale: en-GB
------------------------------------------------------------
All checks passed: totals, distribution, choice
consistency, word limits, scheme coverage, spelling.
------------------------------------------------------------
RESULT: PASS
```

A paper with a mistyped mark, an unmirrored choice, and a missing word
limit:

```text
FAIL [SECTION_SUBTOTAL] Section A: questions total 24 marks, but the blueprint subtotal is 20.
FAIL [COMPOSITION_MISMATCH] Section A: blueprint expects 5 x mcq at 1 mark(s) each; the paper has 4.
FAIL [CHOICE_NOT_MIRRORED] Q11: the question offers an internal choice but the marking scheme does not mirror it.
FAIL [WORD_LIMIT_MISSING] Q13: long-answer question declares no word limit.
FAIL [TOTAL_MISMATCH] The paper's questions total 84 marks, but the blueprint total is 80.
------------------------------------------------------------
RESULT: FAIL - 7 finding(s)
```

The auditor exits with status 1 on any finding, so it drops straight into a
script or a pre-print checklist.

## Writing your own paper

1. **Copy a blueprint** from `blueprints/` and adjust it: total marks,
   sections, compositions. The JSON Schema in `schema/blueprint.schema.json`
   documents every field.
2. **Copy a sample specification** from `samples/` and replace the
   questions with your own, keeping the structure: each question carries
   `id`, `type`, `marks`, `prompt`, and a `scheme`; long answers add
   `word_limit`; an internal choice adds a `choice` object to the question
   and `mirrors_choice` plus `alternative_value_points` to its scheme.
3. **Audit, then render** with the commands above, using a small driver
   file like the ones in the samples:

   ```typst
   #import "templates/paper.typ": render-paper
   #render-paper(json("spec.json"))
   ```

Question types understood by the templates and the auditor: `mcq`,
`very-short-answer`, `short-answer`, `long-answer`, `case-based`.

## Repository layout

```text
audit.py                  the auditor (stdlib only)
blueprints/               example paper patterns (JSON)
schema/                   JSON Schema for blueprints
templates/
  paper.typ               question-paper template (Typst)
  scheme.typ              marking-scheme template (Typst)
samples/
  english/                a complete worked language paper + scheme (PDF)
  maths/                  a complete worked mathematics paper + scheme (PDF)
tests/                    unittest suite for the auditor
```

All sample questions are original, written for this repository as worked
examples. They are illustrations of the format, not reproductions of any
examination.

## Licence

MIT — see [LICENSE](LICENSE). Contributions are welcome; see
[CONTRIBUTING.md](CONTRIBUTING.md).
