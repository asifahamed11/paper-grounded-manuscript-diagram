# Contributing

Thanks for helping improve this skill.

## Contribution principles

- Keep the core `SKILL.md` portable and tool-agnostic.
- Do not add platform-specific tool names as mandatory dependencies.
- Keep platform-specific setup instructions in `references/platform-compatibility.md`.
- Do not claim a script can do visual or scientific checks it cannot actually perform.
- Preserve research integrity, legal access, and figure originality requirements.
- Prefer small, documented helper scripts with clear error messages.
- Add or update tests when changing scripts.

## Before opening a pull request

Run:

```bash
python -m unittest discover -s tests -v
python scripts/validate_svg.py --help
python scripts/score_papers.py --help
python scripts/extract_pdf_figures.py --help
python scripts/build_contact_sheet.py --help
```

## Reporting a problem

Include:
- agent platform and version;
- operating system and Python version, if relevant;
- exact command or prompt;
- expected behavior;
- actual behavior;
- a minimal example that does not expose private research data.
