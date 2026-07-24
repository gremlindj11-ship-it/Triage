# Handover For Next AI

## What This Project Is

This repo is a rule-heavy clinical triage prototype with two user-facing entry points:

- `main.py`: CLI loop plus helpers like `run_ui_case()` used by most tests.
- `web_app.py`: Flask app with `/` and `/triage` routes.

The system takes free text, extracts clinical signals, derives features, scores/ranks diagnoses, raises red flags, and generates a next question.

Important: this workspace copy is **not a git repository**, so there is no local commit history to inspect. Anything in the "recently done" section below is inferred from code shape and test coverage.

## Fast Start For A New Maintainer

If you need to continue development quickly, open these files first:

- `engine/case_pipeline.py`: best top-level orchestration view.
- `engine/parser.py`: phrase extraction, negation handling, clarification generation, limited context extraction.
- `engine/reasoning.py`: main rule engine for displayed diagnoses, questions, investigations, and safety flags.
- `engine/diagnosis_engine.py`: separate score-based diagnosis engine still used in parsed output.
- `ui.py`: terminal rendering of condition states.
- `web_app.py`: embedded HTML UI plus Flask JSON endpoint.

## Current Data Flow

The most accurate path through the system today is:

1. `main.run_ui_case(text)` or `web_app` receives text.
2. `engine.case_pipeline.build_case_payload(text)` is called.
3. `engine.parser.parse_text(text)` extracts:
   - `present_feature_ids`
   - `clarification_question`
   - `context`
4. `engine.case_pipeline.augment_parsed_output()` adds:
   - meaning matches
   - assertions
   - relations
   - clinical state
   - derived features
   - pattern results
   - score-based `diagnosis_results`
   - parser-layer `red_flags`
5. `engine.reasoning.select_diagnosis(...)` produces the user-facing reasoning output:
   - `condition_states`
   - `investigations`
   - `next_question`
   - reasoning-layer `safety_flags`
6. `ui.display_case()` or the web client renders the result.

## The Most Important Architectural Fact

There are **two diagnosis systems** in active use:

### 1. Score-Based Parsed Output

Built in `engine/diagnosis_engine.py` and attached in `engine/case_pipeline.py` as `parsed["diagnosis_results"]`.

Characteristics:

- uses `DIAGNOSIS_DEFINITIONS`
- weighted evidence + simple blockers/context modifiers
- filtered by `filter_diagnoses()`
- still visible to tests and web responses

### 2. Rule/State-Based Display Reasoning

Built in `engine/reasoning.py` and returned as `condition_states`, `investigations`, `next_question`, and `safety_flags`.

Characteristics:

- richer explanation structure
- requirements/exclusions/decision guards
- display gating and question selection
- appears to drive the actual user-facing hypothesis output

### Why This Matters

This split is the biggest source of maintenance risk. A new change can make:

- `parsed["diagnosis_results"]` say one thing
- `condition_states` say another

That divergence may already be tolerated by tests because different tests inspect different layers.

If you continue development, decide early whether to:

- keep both layers intentionally and document their responsibilities, or
- converge on one diagnosis source of truth and downgrade the other to a compatibility layer.

## What Seems To Have Been Done Recently

This is inferred mainly from the test suite because git history is missing.

### Extraction Safety Hardening

There is strong recent coverage around not over-triggering features:

- negation handling
- contradiction handling across clauses
- location alone not creating pain features
- nausea not becoming vomiting
- severity conflicts pruning weaker headache features

See:

- `test_input_safety.py`
- `test_logical_safety.py`
- `test_system_integrity.py`
- `test_location.py`

### Temporal And Order Reasoning

There is explicit support for symptom order and progression:

- `pain then vomiting`
- `vomiting then pain`
- headache progression over time
- sentinel/high-risk headache progression

See:

- `test_temporal.py`
- `test_relations.py`
- `test_order_reasoning.py`

### Headache / SAH Enrichment

Coverage suggests active recent work on dangerous headache recognition:

- thunderclap mapping
- sudden severe headache normalization
- worst headache severity handling
- reduced consciousness / seizures red flags
- question prioritization for headache onset and severity

See:

- `test_diagnosis_engine.py`
- `test_red_flags.py`
- `test_question_generation.py`
- `test_severity.py`

### Explainability / Blocker Preservation

`engine/case_pipeline.filter_diagnoses()` explicitly preserves `ruled_out` diagnoses instead of hiding them. This is important for explainability and was likely done intentionally.

Do not casually remove ruled-out entries from filtered diagnosis output unless you also update tests and UI expectations.

### Web Safety Work

`test_web_app.py` checks:

- malicious input is treated as plain text
- raw input is preserved in payload
- the HTML page escapes rendered user content on the client side

## Clear Problems, Risks, And Likely Solutions

### Problem 1: Dual Diagnosis Engines Can Drift

Symptoms:

- score-based `parsed["diagnosis_results"]` and rule-based `condition_states` are produced by different modules with different rules
- tests validate both surfaces independently

Why it matters:

- the API may expose one ranking while the UI highlights another
- debugging becomes confusing because "correct" depends on which layer the caller inspects

Potential solutions:

- short-term: document one surface as authoritative for each consumer
- medium-term: generate `parsed["diagnosis_results"]` from reasoning outputs, or vice versa
- long-term: separate "feature extraction", "evidence model", and "display model" explicitly if both are truly needed

### Problem 2: `engine/reasoning.py` Is A Monolith

Symptoms:

- one very large file controls ranking, display gating, question generation, safety flags, investigations, and rule validation

Why it matters:

- hard to safely change one behavior without side effects
- difficult for a new model/engineer to localize bugs

Potential solutions:

- split into modules such as:
  - `reasoning_rank.py`
  - `reasoning_rules.py`
  - `question_generation.py`
  - `safety_reasoning.py`
  - `investigation_selection.py`
- preserve current public entry point `select_diagnosis()` while extracting internals behind it

### Problem 3: Parser Logic Is Powerful But Fragile

Symptoms:

- `engine/parser.py` relies on many exact phrases, hand-maintained aliases, custom negation windows, and temporal connector heuristics
- extraction is deterministic but brittle to unseen phrasing

Why it matters:

- feature quality controls the rest of the system
- small phrase additions can create regressions in negation, ambiguity, or false positives

Potential solutions:

- move more phrase/alias logic into registries or data files instead of code constants
- add table-driven tests when adding any new alias or connector
- consider representing extraction rules as structured patterns instead of ad hoc condition blocks

### Problem 4: Parser Has Stdout Side Effects

Symptoms:

- `engine.parser.parse_text()` prints raw input and matched features
- `build_case_payload()` suppresses this with `redirect_stdout(StringIO())`

Why it matters:

- surprising behavior for direct callers
- brittle if another code path forgets to suppress output
- harder to reuse in APIs or batch jobs

Potential solutions:

- remove printing from `parse_text()` entirely
- replace with optional debug logging flag
- if preserving behavior, route logs through a logger rather than stdout

### Problem 5: Context Extraction Is Minimal

Symptoms:

- parser context currently extracts only a small set of fields such as sex and pregnancy possibility
- more advanced reasoning rules depend heavily on having the right context

Why it matters:

- many diagnoses need richer demographic and clinical context
- safety logic can be limited by sparse context

Potential solutions:

- expand context extraction in a controlled, test-backed way
- define a formal context schema first so rules do not grow around ad hoc keys

### Problem 6: Web UI Is Embedded Inline In `web_app.py`

Symptoms:

- HTML, CSS, and JS are inside a Python triple-quoted string

Why it matters:

- harder to iterate on front-end behavior
- risk of accidental breakage during backend edits

Potential solutions:

- move UI to templates/static assets
- keep the endpoint contract stable while separating presentation from Python logic

### Problem 7: Test Harness Is Functional But Basic

Symptoms:

- many tests are standalone Python scripts with `if __name__ == "__main__":`
- no git metadata here and no visible CI wiring in this workspace snapshot

Why it matters:

- easy to run locally, but quality gates are informal
- future maintainers may miss which tests guard which behaviors

Potential solutions:

- keep direct execution support, but standardize on `pytest` collection too
- add a short test map document grouped by behavior area
- add CI once repo history/integration exists again

## Practical Code Notes That Will Save Time

### Clarification Questions Short-Circuit Diagnosis Display

If parser output includes `clarification_question`, `select_diagnosis()` returns early with:

- empty `condition_states`
- empty `investigations`
- a `next_question`

This is intentional. Do not assume empty condition states always mean extraction failure.

### Relations Are Injected Into Reasoning Context

`build_case_payload()` passes `relations` into the reasoning context:

- base parser context
- plus `relations`

If you add relation-aware reasoning, this is the current handoff point.

### Filtered Diagnosis Output Is Not The Full Raw Score List

`filter_diagnoses()` currently:

- keeps ruled-out entries
- keeps non-ruled-out entries only when confidence is above `0.2`
- truncates to 3 entries

That means parsed diagnosis output is already a presentation-friendly subset, not a raw evidence dump.

### Terminal UI And Web UI Consume Different Shapes

- terminal display in `ui.py` is built around `condition_states`
- web JSON returns both parsed internals and reasoning outputs

Be careful when changing payload contracts. Tests inspect both.

## Suggested Development Priorities

If the next AI should continue improving the system, this is the order I would use:

1. Decide whether the diagnosis source of truth is `engine/diagnosis_engine.py`, `engine/reasoning.py`, or both.
2. Refactor `engine/reasoning.py` into smaller modules without changing behavior.
3. Remove stdout side effects from parsing and replace them with structured debug logging.
4. Expand extraction/context coverage only with paired regression tests.
5. Separate the web UI assets from `web_app.py` if front-end iteration is expected.

## Safe Way To Add New Clinical Logic

When adding new symptoms, diagnoses, or safety rules:

1. Add or update phrase mapping / feature extraction.
2. Add regression tests for false positives and negation cases.
3. Update both diagnosis layers if both are still active.
4. Check question generation still asks the most discriminating next question.
5. Check red flags and display gating still behave sensibly.

If you skip step 3, the two diagnosis surfaces may silently diverge.

## Useful Tests By Behavior

- `test_input_safety.py`: clause contradiction, negation priority, severity conflict.
- `test_logical_safety.py`: similar safety invariants plus weird-input smoke coverage.
- `test_location.py`: location-to-feature mapping.
- `test_temporal.py`: temporal progression and ordering.
- `test_relations.py`: explicit temporal relation objects.
- `test_order_reasoning.py`: order-dependent appendicitis reasoning explanations.
- `test_question_generation.py`: next-question prioritization.
- `test_red_flags.py`: acute danger detection.
- `test_diagnosis_engine.py`: score-based diagnosis expectations.
- `test_web_app.py`: route contract and input escaping.
- `test_system_integrity.py`: cross-cutting regressions.

## Current Validation Snapshot (2026-07-24)

Ran every `test_*.py` file in the repo (still 17 files — `test_web_app.py` gained 3 new test
functions for the `/notes` routes, no new files) via the repo's `.venv` interpreter under WSL.
All pass (`test_pattern_layer.py` has no assertions — it's a smoke dump script, not a PASS/FAIL test).
Also manually smoke-tested `/triage` and `/` via Flask's test client after the web UI change (see
"Web UI Overhaul" section below) to confirm the primary panel actually renders from `condition_states`
and not just that the test suite happens to still pass.

### What changed and why

Two tests were failing coming into this session: `test_logical_safety.py` (its last case,
`test_double_negation_weird_input`) and `test_question_generation.py` (its last case,
`test_generic_question_only_when_no_clear_symptom`). Both were root-caused before touching code;
neither was a flaky test.

**`thunderclap_headache` detection gap (real gap, not a regression).** Before this change,
`thunderclap_headache` could only be produced two ways: (a) a direct phrase alias match in
`engine/meaning_dictionary.py` ("thunderclap headache", "worst headache of life", "sudden severe
headache", etc.), or (b) a `worst_headache_of_life` → `thunderclap_headache` override in
`engine/feature_derivation.py`. Path (b) was already dead code — nothing in the meaning
dictionary ever emits meaning_id `worst_headache_of_life` (the phrase is aliased straight to
`thunderclap_headache`), and `test_severity.py` explicitly asserts that id is never in features.
There was no path from a contradiction pattern like "no headache but now severe headache" to
thunderclap, even though the sentence's own structure (absent → severe, with a "now"/"then"/
"suddenly" transition marker) is itself an abrupt-onset signal — the clinical hallmark of
thunderclap headache (severe + abrupt onset).

Fix, implemented as disease-agnostic infrastructure plus one headache-specific rule:
- `engine/assertions.py`: the existing negation-contrast resolver (the one that already un-negates
  "no X but Y" patterns) now also scans the connector text between the negated and contrasting
  present assertion for an onset-transition cue (`now`, `suddenly`, `then`, `abruptly`,
  `immediately`, `all of a sudden`) and tags the present assertion with `implied_abrupt_onset`.
  This is keyed by `symptom_family`, not hardcoded to headache, so any future symptom family
  registered in `_SYMPTOM_FAMILY_BY_MEANING` can reuse it.
- `engine/feature_derivation.py`: a new `_derive_implied_onset_features` promotes that flag to
  `sudden_onset_headache`, but only when the reasserted assertion's own severity is severe/critical
  (a bare contradiction without severity escalation is not sufficient — this was checked explicitly
  with negative test cases, see below). `_apply_clinical_concept_overrides` now also promotes
  `severe_headache + sudden_onset_headache → thunderclap_headache`, mirroring the existing
  `worst_headache_of_life` promotion, and discards `sudden_onset_headache` once `thunderclap_headache`
  is set (parity with the existing `severe_headache`/`mild_headache` discards).
- `test_logical_safety.py`: added 4 new cases — two phrasing variants that should hit thunderclap
  (alternate negation word "denies" + cue "suddenly"; cue "then" instead of "now"), and two negation
  edge cases that must **not** over-trigger (a contrast with no onset cue stays `severe_headache`;
  an onset cue with only mild severity does not escalate). The negative cases matter clinically —
  the goal was to avoid manufacturing false-positive thunderclap flags out of ordinary contradictions.
- Known dead code was **not** removed in this pass (the `worst_headache_of_life` pruning-tier entry
  in `_SYMPTOM_SEVERITY_FEATURES["headache"]["critical"]` is unreachable) — flagged here for a future
  cleanup pass, out of scope for this fix.

**Clarification question wording (stale test, not a code bug).** `engine/parser.py` deliberately
maintains two different clarification strings for two different scenarios: `_CLARIFICATION_QUESTION`
(long, with examples) when zero features were extracted at all, and
`_AMBIGUITY_CLARIFICATION_QUESTION` (short) when some features were extracted but the text also
has an ambiguity marker. A third, still different string exists as `reasoning.py`'s internal
fallback ("Can you describe the main symptom?"), and another test in the same file already
distinguishes that one correctly. The failing test's literal expected string for the "weird" input
(zero features → long constant is correct by design) just hadn't been updated to match. Fixed by
updating the test string in `test_question_generation.py`, not the engine.

### Residual uncertainty

This workspace has no git history, so "was this ever intentional" can only be inferred from code
shape, not confirmed from commits. Both conclusions above are well-supported by cross-referencing
other passing tests and dead-code evidence, but treat them as strong inference, not certainty.

## Web UI Overhaul (2026-07-24)

The web UI (`web_app.py`) previously surfaced raw pipeline internals as the primary view, and — this
was the important part — its "Candidate Diagnoses" panel was reading `parsed.diagnosis_results`
(the score-based engine, system 1), not `condition_states` (the rule-based reasoning engine, system
2, the one CLAUDE.md and `ui.py`'s terminal renderer treat as the actual user-facing result). That
was the core defect fixed here. This was a front-end/presentation-only change; nothing in `engine/*`,
reasoning thresholds, or the `/triage` response shape changed.

### What changed

- **Primary result panel now reads `condition_states` / `investigations` / `safety_flags` /
  `next_question`, never `parsed.diagnosis_results`.** `renderPrimaryResult(data)` in `web_app.py`
  reads `data.condition_states` exclusively. The logic (main hypothesis text, supporting-evidence
  vs. missing-requirements vs. exclusion section ordering, rule-label mapping) is a direct port of
  `ui.py`'s terminal renderer (`_get_main_hypothesis_display_text`, `_get_section_specs`,
  `_get_rule_label`, etc.) so the web UI and CLI now agree on what "the diagnosis" means. The
  score-based `diagnosis_results` (system 1) is still shown, but only inside Technical Details,
  explicitly labeled `"Score-Based Diagnoses (system 1, debug)"`.
- **Technical Details collapsible** (`<details class="tech-details">`, closed by default) now holds
  everything that used to be front-and-center: present/negated/uncertain assertions, derived/matched
  terms, raw `clinical_state` (severity, context incl. `pregnancy_possible`/`sex`), `pattern_results`,
  and the system-1 diagnosis list.
- **Conversational `next_question` loop.** Client-side only, no new backend state — `/triage` stayed
  stateless. Mirrors `main.py`'s existing CLI loop exactly: accumulate a `currentText` string, append
  the user's typed answer (`"{current} {answer}"`, same join as `main.py`), re-POST the full text each
  turn. Stops when `next_question` is null, the `present_feature_ids` set is unchanged from the
  previous turn, or a 3-turn cap is hit (`MAX_TURNS`, same cap as `main.py`'s `max_turns`) — a manual
  "Stop Asking" button was also added as an escape hatch (not explicitly requested, low-risk addition).
  This stopping logic is **duplicated** in JS rather than shared with `main.py`'s loop; there was no
  clean way to share it without a larger refactor of `main.py`, which was out of scope. If the CLI
  loop's heuristics ever change, the web one will not follow automatically — check both.
- **Saved notes.** Two new additive Flask routes, `GET /notes` and `POST /notes`, backed by a flat
  `saved_notes.json` file at the repo root (gitignored — it will hold free-text note content).
  `_load_notes()`/`_save_notes()` in `web_app.py` do plain `json.load`/`json.dump`, no locking. Tests
  added in `test_web_app.py`: empty-list case, save-then-appears-in-list, and empty-text rejection
  (400). This is a prototype-grade store — see risks below.

### A real safety gap found and worked around, not just a design choice

`reasoning.py`'s `safety_flags` (the reasoning-layer output the user asked to surface) only covers
**syncope, shoulder tip pain, and haemodynamic instability/hypotension** (`_build_safety_flags` in
`engine/reasoning.py`). It does **not** include thunderclap headache, neck stiffness, photophobia,
reduced consciousness, or seizures — those only exist in the parser-layer `parsed.red_flags`
(`engine/red_flag_engine.py`). Showing only `safety_flags` in the new emergency banner would have
silently dropped visible coverage for those headache/neuro red flags versus the old UI. Fixed by
having `getSafetyMessages(data)` in `web_app.py` union both sources (deduplicated) for display. This
is a real, pre-existing split between the two red-flag systems (same shape as the two-diagnosis-engine
split CLAUDE.md already warns about) — worth deciding, at some point, whether `_build_safety_flags`
should be the canonical safety-flag source and get expanded to match `red_flag_engine.py`'s coverage,
or whether the two are meant to stay separate. Not fixed here since it would touch reasoning logic.

### New risks introduced by this UI change

- **Two red-flag systems, now both visibly relied on in one UI surface.** See above — the web UI's
  emergency banner now depends on both `safety_flags` and `parsed.red_flags` staying in sync in
  coverage terms. If someone adds a new red-flag feature to only one of the two systems, the banner
  will still show it (since it's a union), but the underlying inconsistency between the two systems
  keeps growing untracked.
- **`saved_notes.json` has no locking.** Fine for the single-process Flask dev server this app already
  runs as (`app.run(debug=True, ...)`); would race under multiple workers/processes. Not an issue
  today, worth remembering if this is ever containerized/scaled.
- **Saved notes are plaintext on disk.** Acceptable for a local prototype; would need real storage
  and access control before this app is anything other than a local tool.
- **`renderPrimaryResult`'s top-condition selection is a direct port of `ui.py`'s `condition_states[0]`
  approach**, not `reasoning.py`'s own internal `_get_top_condition_state` (which filters out
  zero-score entries and picks by max `normalized_signal_score`, not list order). These two selection
  algorithms are not provably identical in every case — `ui.py` has used the naive `[0]` approach for
  the CLI all along, so this isn't a new risk introduced by the web UI, just an existing characteristic
  now also relied on in a second place. Worth a closer look if the two engines are ever consolidated
  (see the "Dual Diagnosis Engines Can Drift" problem below).

## Recommended First Move For The Next AI

Start in `engine/case_pipeline.py` and trace one case end to end.

A good first trace input is:

- `male with missed period and abdominal pain`

It exercises:

- parsing
- context extraction
- blocker logic
- dual diagnosis outputs
- UI/API explainability around a ruled-out diagnosis