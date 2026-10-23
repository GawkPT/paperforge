# Contributing to PaperForge

Thank you for considering a contribution. PaperForge aims to stay small,
dependency-free, and useful to any teacher who sets an examination paper.

## Principles

- **The engine stays generic.** Nothing subject-specific or board-specific
  belongs in `audit.py` or the templates. Specifics live in blueprints and
  paper specifications.
- **The auditor uses the Python standard library only.** If a change needs
  a third-party package, it is probably the wrong change.
- **Paper and scheme come from one specification.** Never introduce a
  feature that lets the two drift apart.
- **Sample content is original.** Never add questions copied from a real
  examination paper, a textbook, or a commercial question bank.

## Getting started

```sh
git clone <your fork>
cd paperforge
python3 -m unittest discover -s tests -v
python3 audit.py samples/english/spec.json \
    --blueprint blueprints/secondary-language-80.json
```

You will need Python 3.10+ and, for rendering, Typst.

## Making a change

1. Open an issue first for anything larger than a typo fix, so the design
   can be discussed before code is written.
2. Keep the change focused; one pull request per concern.
3. Add or update tests. Every new audit check needs at least one test in
   which a deliberately broken specification fails with the new finding
   code, and the clean samples must keep passing.
4. Run the full suite, audit both samples, and re-render both sample
   papers and schemes before submitting:

   ```sh
   python3 -m unittest discover -s tests -v
   typst compile --root . samples/english/paper.typ
   typst compile --root . samples/english/scheme.typ
   typst compile --root . samples/maths/paper.typ
   typst compile --root . samples/maths/scheme.typ
   ```

5. Update `CHANGELOG.md` under the Unreleased heading.

## Style

- Python: follow PEP 8; keep functions short and findings worded as a
  teacher would phrase them.
- Documentation uses British English spelling.
- Typst templates: prefer plain, readable markup over clever code; the
  printed face of a paper should stay conservative.

## Reporting problems

Please include the blueprint and paper specification (with any real
questions replaced by dummy text) that reproduce the problem, the auditor
output, and your Python and Typst versions.
