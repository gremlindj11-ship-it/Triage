# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

A rule-heavy clinical triage prototype. Free-text patient notes go in; extracted clinical signals, ranked
differential diagnoses, red flags, and a next discriminating question come out. Two user-facing entry points:

- `main.py` — CLI loop (`python main.py`), plus `run_ui_case()` used by most tests.
- `web_app.py` — Flask app with `/` (embedded HTML/JS UI) and `POST /triage` (JSON API).

This workspace is **not a git repository** — there is no commit history to inspect. Treat any claims about
"recent work" as inferred from code/test shape, not verified history.

## Commands

No `requirements.txt`/`pyproject.toml` exists; dependencies live only in `.venv` (Flask + friends). Use the repo's
venv interpreter.

```bash
# Run the CLI
python main.py

# Run the Flask web app (http://0.0.0.0:5000)
python web_app.py

# One-shot pipeline debug dump for a given input (defaults to a sample appendicitis case)
python debug_cli.py "pain near belly button then moved to right lower abdomen and feel sick"
```

There is no pytest/unittest wiring — every `test_*.py` is a standalone script with hand-rolled assertions
(`assert_true(condition, message)` that **prints PASS/FAIL rather than raising**). A "failed" run still exits 0,
so check stdout for `FAIL:` lines, not the exit code.

```bash
# Run one test file directly
python test_system_integrity.py

# Run all test files and grep for failures
for f in test_*.py; do python "$f"; done | grep FAIL
```

Test files and what they guard (see also inline comments in each):
- `test_input_safety.py`, `test_logical_safety.py`, `test_system_integrity.py` — negation, clause contradiction,
  severity conflicts, weird-input smoke coverage.
- `test_location.py` — location-to-feature mapping.
- `test_temporal.py`, `test_relations.py`, `test_order_reasoning.py` — symptom order/progression (e.g.
  pain-then-vomiting, headache progression, order-dependent appendicitis reasoning).
- `test_question_generation.py` — next-question prioritization.
- `test_red_flags.py`, `test_severity.py` — acute danger detection and headache severity handling.
- `test_diagnosis_engine.py` — score-based diagnosis expectations.
- `test_pattern_layer.py` — pattern matching layer.
- `test_web_app.py` — Flask route contract, and that malicious/raw input is preserved as plain text server-side
  and escaped client-side (never rendered as HTML).

## Architecture

### Data flow

`main.run_ui_case(text)` / the Flask `/triage` route both funnel through `engine.case_pipeline.build_case_payload(text)`:

1. `engine.parser.parse_text(text)` — extracts `present_feature_ids`, `clarification_question`, `context`
   (currently just sex / pregnancy-possible). Note: `parse_text` prints raw input and matched features to stdout;
   `build_case_payload` suppresses this with `redirect_stdout(StringIO())` — any new caller of `parse_text` must
   do the same or it will leak debug output.
2. `engine.case_pipeline.augment_parsed_output()` layers on: meaning matches (`engine.matcher`), assertions
   (`engine.assertions`), relations (`engine.relation_builder`), clinical state (`engine.clinical_state`), derived
   features (`engine.feature_derivation`), pattern results (`engine.pattern_engine`), score-based
   `diagnosis_results` (`engine.diagnosis_engine.score_diagnosis`), and parser-layer `red_flags`
   (`engine.red_flag_engine`).
3. `engine.reasoning.select_diagnosis(...)` — the rule/state-based engine — produces the actual user-facing
   `condition_states`, `investigations`, `next_question`, and reasoning-layer `safety_flags`. Relations are
   injected into its context here (base parser context + `relations`); this is the handoff point for any new
   relation-aware reasoning.
4. `ui.display_case()` (terminal) or the embedded JS in `web_app.py` (web) renders the result.

**Clarification short-circuit:** if parser output includes a `clarification_question`, `select_diagnosis()`
returns early with empty `condition_states`/`investigations` and just a `next_question`. Empty condition states do
not mean extraction failed.

**Language/feature registry alignment:** `engine.language.seed` registers per-condition feature/epidemiology data
into `engine.language.library.LANGUAGE_LIBRARY` at import time (imported first thing in both `main.py` and
`web_app.py`). `engine.validation.validate_language_alignment()` is then called at module load to assert every
feature referenced in `LANGUAGE_LIBRARY` exists in `engine.feature_registry.FEATURE_REGISTRY` — it raises
`ValueError` on mismatch, so a typo'd feature name in a seeded condition breaks app startup, not just a test.

### The central architectural fact: two parallel diagnosis systems

1. **Score-based parsed output** (`engine.diagnosis_engine.score_diagnosis`, attached as
   `parsed["diagnosis_results"]` in `case_pipeline.py`): weighted evidence + simple blockers/context modifiers,
   filtered by `case_pipeline.filter_diagnoses()` (keeps `ruled_out` entries for explainability, keeps others only
   above `confidence > 0.2`, truncates to 3). Still visible to tests and the web JSON response.
2. **Rule/state-based display reasoning** (`engine.reasoning.select_diagnosis`, ~1200 lines, the largest file in
   the repo): richer requirements/exclusions/decision-guard structure, drives `condition_states`,
   `investigations`, `next_question`, and the safety flags actually shown to the user.

These can drift — `parsed["diagnosis_results"]` and `condition_states` are produced by different modules with
different rules, and different tests independently validate each surface. **When adding a new diagnosis, feature,
or safety rule, update both layers** (score weights in `diagnosis_definitions.py`/`diagnosis_engine.py` *and* the
requirements/exclusions in `reasoning.py`) or the CLI/API/UI surfaces will silently disagree. Do not remove
`ruled_out` entries from filtered diagnosis output without checking UI/test expectations — they're kept
intentionally for explainability.

### Parser fragility

`engine/parser.py` and the `engine/language/` seed data rely on hand-maintained exact phrases, aliases, negation
windows, and temporal connector heuristics (see `engine/registry.py` for the `PHRASES`/`TEMPORAL_PATTERNS` tables
driving this). Extraction is deterministic but brittle to unseen phrasing — when adding a new alias or connector,
add a paired regression test (false-positive and negation case) rather than assuming coverage.

### Key engine modules (`engine/`)

- `parser.py` — phrase extraction, negation handling, clarification generation, context extraction.
- `matcher.py` / `meaning_dictionary.py` — raw text → meaning-id matches.
- `assertions.py` — meaning matches → present/negated/uncertain assertions.
- `relation_builder.py` — temporal/migration relations between assertions.
- `clinical_state.py` — aggregates assertions/relations into present/negated/uncertain feature sets + severity.
- `feature_derivation.py` — clinical state → derived feature ids (e.g. `pain_migration`, `pain_before_vomiting`).
- `pattern_engine.py` / `patterns.py` — feature-set pattern matching per diagnosis.
- `diagnosis_engine.py` / `diagnosis_definitions.py` — score-based diagnosis engine (system 1 above).
- `red_flag_engine.py` — acute danger detection from features/context.
- `reasoning.py` — rule/state-based diagnosis, question generation, safety flags (system 2 above; monolith).
- `case_pipeline.py` — top-level orchestration; best starting point for tracing a case end-to-end.
- `registry.py` / `feature_registry.py` — canonical feature/diagnosis/phrase/question/temporal-pattern tables.
- `validation.py` — startup-time consistency check between language library and feature registry.
- `language/` — `library.py` (registry + `register_condition`), `seed.py` (per-condition clinical data), `extract.py`.

### Suggested trace for orientation

A good end-to-end input to trace through `case_pipeline.py` is `"male with missed period and abdominal pain"` — it
exercises parsing, context extraction (male sex), blocker logic, both diagnosis outputs, and UI/API explainability
around a diagnosis that gets ruled out by context (ectopic pregnancy, blocked by male sex).

## Standing instruction: self-review before presenting work as done

For every implementation in this project, before presenting it as done: review it as a senior engineer would in a
critical pull request, specifically for hidden assumptions, edge cases, unnecessary complexity, duplicated logic,
future maintenance problems, performance issues, and safety risks. State these critiques explicitly rather than
defending the implementation. This applies especially to anything touching diagnosis logic or safety flags.

## Standing instruction: generality test for new reasoning-engine capabilities

Every new generic capability introduced into the reasoning engine must satisfy two criteria: (1) it solves a
problem observed in at least one real disease, and (2) it is disease-agnostic — usable by any disease that has the
relevant data, not just the one that motivated it. If a capability would only make sense for one specific disease
and cannot plausibly generalize, stop and flag it for discussion before implementing, rather than adding a
disease-specific exception.

## Known risks to keep in mind when editing

- `reasoning.py` controls ranking, display gating, question generation, safety flags, and rule validation all in
  one file — changes can have non-local side effects.
- Terminal UI (`ui.py`) is built around `condition_states`; the web JSON response returns both parsed internals and
  reasoning outputs. Changing either payload shape affects both consumers and their tests.
- `web_app.py` embeds the entire HTML/CSS/JS UI as a Python triple-quoted string — there is no separate
  templates/static setup.
