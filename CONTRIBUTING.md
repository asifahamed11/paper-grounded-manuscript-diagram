# Contributing

Help make research diagrams clearer, more faithful and easier to reproduce.

## Useful contributions

- A minimal example that exposes a spacing, typography, icon-placement or connector problem.
- A new diagram convention supported by an actual paper/figure locator.
- A focused renderer fix, meaningful regression test or clearer workflow guidance.

## Make a change

1. Start from a small public or synthetic example. Keep unpublished research and personal data out of issues, fixtures and previews.
2. Keep the change focused. Preserve scientific labels and relationships, skill portability and the local-first workflow. New generators, models or hosted services must remain optional.
3. For rendering changes, run the tests with Matplotlib and Pillow available. Open both full and print-size exports; inspect cutouts on light/dark backgrounds when relevant.

```sh
python -m unittest discover -s tests -v
python scripts/render_diagram.py templates/parallel-study.json --output-dir diagram-output --stem method
python scripts/validate_svg.py diagram-output/method.svg
```

A run that skips optional rendering tests is not a rendering pass. Use the existing project environment or follow [setup guidance](references/platform-compatibility.md).

4. Include the problem, resulting behaviour, tests actually run and any remaining limits in your pull request. Add before/after images for a visual change. If an example changes, refresh its README preview from the same source specification.

## Report a bug

Open an issue with the agent/client, OS and Python versions, exact command or prompt, expected behaviour, actual output and a minimal shareable specification. Attach a preview and QA report where possible.

Do not treat a successful script or a high fill metric as proof of scientific correctness or visual quality. Report only checks you actually performed.
