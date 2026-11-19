# Triage

A rule-based clinical triage prototype. Free-text notes go in; extracted clinical signals, ranked differential diagnoses, red flags and a next discriminating question come out.

## Status: research prototype

**This is not a medical device and must not be used for real clinical decisions.**

- It has not been clinically validated, and it is not registered or approved for any clinical use.
- It covers a small number of conditions and relies on hand-written phrase matching, so it misses things.
- Do not enter real patient information. Use made-up cases only.
- If you are unwell, contact a clinician, NHS 111, or 999 in an emergency.

## What's here

- `main.py`: command-line loop.
- `web_app.py`: a Flask app with a simple web page and a `POST /triage` JSON endpoint.
- `engine/`: parsing, feature derivation, diagnosis scoring, red flags and reasoning.
- `generic_engine/`: a disease-agnostic version of the reasoning layer.
- `test_*.py`: standalone test scripts. They print `PASS`/`FAIL` lines and do not fail the exit code, so read the output.

## Running it

Needs Python 3 and Flask.

```bash
python main.py        # command line
python web_app.py     # web app
python debug_cli.py "pain near belly button then moved to right lower abdomen and feel sick"
```

## Licence

Copyright © 2026 Sofia Vidal. Released under the GNU Affero General Public License v3.0 (see [LICENSE](LICENSE)). You can use, change and share it, as long as anything you build from it stays open under the same licence, including when it runs as a web service.

## Contact

Sofia Vidal, via GitHub issues on this repository.
