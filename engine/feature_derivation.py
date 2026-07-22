import re


_SYMPTOM_SEVERITY_FEATURES = {
	"headache": {
		"mild": {"mild_headache"},
		"moderate": set(),
		"severe": {"severe_headache", "sudden_onset_headache", "thunderclap_headache"},
		"critical": {"worst_headache_of_life"},
	},
}

_SEVERITY_PRIORITY = ["mild", "moderate", "severe", "critical"]
_PAIN_WORD_PATTERN = re.compile(r"\b(pain|ache|aches|aching|hurt|hurts|hurting|tender|tenderness)\b")
_HEADACHE_WORD_PATTERN = re.compile(r"\bheadache\b")
_LOCATION_WINDOW_CHARS = 24


def _has_nearby_symptom_word(raw_text: str, assertion: dict, pattern: re.Pattern[str]) -> bool:
	start = max(0, assertion["start"] - _LOCATION_WINDOW_CHARS)
	end = min(len(raw_text), assertion["end"] + _LOCATION_WINDOW_CHARS)
	return pattern.search(raw_text[start:end]) is not None


def _get_present_assertions_by_meaning(assertions: list[dict]) -> dict[str, list[dict]]:
	present_assertions_by_meaning: dict[str, list[dict]] = {}

	for assertion in assertions:
		if assertion.get("polarity") != "present":
			continue
		present_assertions_by_meaning.setdefault(assertion["meaning_id"], []).append(assertion)

	return present_assertions_by_meaning


def _derive_location_features(state: dict, features: set[str], negated: set[str]) -> None:
	raw_text = state.get("raw_text", "").lower()
	present_assertions_by_meaning = _get_present_assertions_by_meaning(state.get("assertions", []))

	def location_has_pain(location_meaning: str) -> bool:
		return any(
			_has_nearby_symptom_word(raw_text, assertion, _PAIN_WORD_PATTERN)
			for assertion in present_assertions_by_meaning.get(location_meaning, [])
		)

	def location_has_headache(location_meaning: str) -> bool:
		return any(
			_has_nearby_symptom_word(raw_text, assertion, _HEADACHE_WORD_PATTERN)
			for assertion in present_assertions_by_meaning.get(location_meaning, [])
		)

	if location_has_pain("abdomen_location") and "abdominal_pain" not in negated:
		features.add("abdominal_pain")

	if location_has_pain("rlq_location") and "abdominal_pain" not in negated:
		features.add("abdominal_pain")
		features.add("right_lower_quadrant_pain")
		features.add("rlq_pain")

	if location_has_pain("llq_location") and "abdominal_pain" not in negated:
		features.add("abdominal_pain")
		features.add("left_lower_quadrant_pain")
		features.add("llq_pain")

	if location_has_pain("epigastric_location") and "abdominal_pain" not in negated:
		features.add("abdominal_pain")
		features.add("epigastric_pain")

	if location_has_pain("chest_location"):
		features.add("chest_pain")

	if location_has_pain("flank_location") and "abdominal_pain" not in negated:
		features.add("abdominal_pain")
		features.add("flank_pain")

	if location_has_headache("head_location") or location_has_pain("head_location"):
		features.add("headache")


def _prune_lower_severity_features(features: set[str]) -> set[str]:
	pruned_features = set(features)

	for severity_map in _SYMPTOM_SEVERITY_FEATURES.values():
		levels_present = [
			level
			for level in _SEVERITY_PRIORITY
			if pruned_features & severity_map[level]
		]
		if len(levels_present) <= 1:
			continue

		highest_level = levels_present[-1]
		for level in _SEVERITY_PRIORITY:
			if level == highest_level:
				continue
			pruned_features.difference_update(severity_map[level])

	return pruned_features


def _apply_clinical_concept_overrides(features: set[str]) -> set[str]:
	normalized_features = set(features)

	if "worst_headache_of_life" in normalized_features:
		normalized_features.discard("worst_headache_of_life")
		normalized_features.add("thunderclap_headache")
		normalized_features.add("headache")

	# Abrupt onset + severe intensity together are the clinical definition of
	# thunderclap headache, regardless of whether "sudden onset" came from a
	# direct phrase match or from an implied-onset contradiction pattern.
	if "sudden_onset_headache" in normalized_features and "severe_headache" in normalized_features:
		normalized_features.add("thunderclap_headache")

	if "thunderclap_headache" in normalized_features:
		normalized_features.discard("worst_headache_of_life")
		normalized_features.discard("severe_headache")
		normalized_features.discard("mild_headache")
		normalized_features.discard("sudden_onset_headache")

	return normalized_features


_IMPLIED_ONSET_SEVERITY_LEVELS = {"severe", "critical"}


def _derive_implied_onset_features(state: dict, features: set[str]) -> None:
	"""Promote an implied-abrupt-onset signal (set by assertions.py's negation-contrast
	resolution) to sudden_onset_headache, but only when the reasserted symptom is
	itself severe/critical -- a contradiction alone doesn't imply abruptness."""
	for assertion in state.get("assertions", []):
		if assertion.get("polarity") != "present":
			continue
		if not assertion.get("implied_abrupt_onset"):
			continue
		if assertion["meaning_id"] not in {"headache", "severe_headache"}:
			continue
		severity = assertion.get("severity") or {}
		if severity.get("level") in _IMPLIED_ONSET_SEVERITY_LEVELS:
			features.add("sudden_onset_headache")
			features.add("headache")


def derive_temporal_features(relations: list[dict], assertions: list[dict]) -> set[str]:
	features = set()
	id_to_assertion = {
		assertion["id"]: assertion
		for assertion in assertions
	}

	for relation in relations:
		if relation.get("type") == "temporal_progression":
			features.add("temporal_progression")
			if relation.get("symptom_family") == "headache":
				features.add("sentinel_headache")
			later_assertion = id_to_assertion.get(relation.get("later"))
			later_severity = (later_assertion or {}).get("severity") or {}
			if later_severity.get("level") == "critical":
				features.add("high_risk_progression")
			continue

		if relation.get("type") != "temporal_order":
			continue

		earlier_assertion = id_to_assertion.get(relation.get("earlier"))
		later_assertion = id_to_assertion.get(relation.get("later"))
		earlier_meaning = earlier_assertion["meaning_id"] if earlier_assertion else None
		later_meaning = later_assertion["meaning_id"] if later_assertion else None

		if earlier_meaning == "abdominal_pain" and later_meaning == "vomiting":
			features.add("pain_before_vomiting")

		if earlier_meaning == "vomiting" and later_meaning == "abdominal_pain":
			features.add("vomiting_before_pain")

	return features


def derive_features_from_state(state: dict) -> list[str]:
	present = set(state["present"])
	negated = set(state["negated"])
	relations = state.get("relations", [])
	assertions = state.get("assertions", [])
	features = set()

	if "abdominal_pain" in present:
		features.add("abdominal_pain")

	if "headache" in present:
		features.add("headache")

	if "severe_headache" in present:
		features.add("severe_headache")
		features.add("headache")

	if "mild_headache" in present:
		features.add("mild_headache")
		features.add("headache")

	if "sudden_onset_headache" in present:
		features.add("sudden_onset_headache")
		features.add("headache")

	if "gradual_onset_headache" in present:
		features.add("gradual_onset_headache")
		features.add("headache")

	if "worst_headache_of_life" in present:
		features.add("worst_headache_of_life")
		features.add("headache")

	if "thunderclap_headache" in present:
		features.add("thunderclap_headache")
		features.add("headache")

	if "sentinel_headache" in present:
		features.add("sentinel_headache")
		features.add("headache")

	if "nausea" in present:
		features.add("nausea")

	if "vomiting" in present:
		features.add("vomiting")

	if "sweating" in present:
		features.add("sweating")

	if "syncope" in present:
		features.add("syncope")

	if "amenorrhea" in present:
		features.add("amenorrhea")

	if "shoulder_tip_pain" in present:
		features.add("shoulder_tip_pain")

	if "peritonism" in present:
		features.add("peritonism")

	if "fever" in present:
		features.add("fever")

	if "neck_stiffness" in present:
		features.add("neck_stiffness")

	if "photophobia" in present:
		features.add("photophobia")

	if "reduced_consciousness" in present:
		features.add("reduced_consciousness")

	if "seizures" in present:
		features.add("seizures")

	if "lower_abdominal_pain" in present:
		features.add("lower_abdominal_pain")

	_derive_location_features(state, features, negated)
	_derive_implied_onset_features(state, features)

	for relation in relations:
		if relation["type"] == "migration":
			features.add("pain_migration")

	features.update(derive_temporal_features(relations, assertions))

	if "abdominal_pain" in negated:
		features.discard("abdominal_pain")
		features.discard("epigastric_pain")
		features.discard("flank_pain")
		features.discard("left_lower_quadrant_pain")
		features.discard("llq_pain")
		features.discard("rlq_pain")
		features.discard("right_lower_quadrant_pain")

	if "vomiting" in negated:
		features.discard("vomiting")

	if "syncope" in negated:
		features.discard("syncope")

	if "fever" in negated:
		features.discard("fever")

	if "headache" in negated:
		features.discard("headache")
		features.discard("severe_headache")
		features.discard("mild_headache")
		features.discard("sudden_onset_headache")
		features.discard("gradual_onset_headache")
		features.discard("worst_headache_of_life")
		features.discard("thunderclap_headache")
		features.discard("sentinel_headache")
		features.discard("temporal_progression")
		features.discard("high_risk_progression")

	if "seizures" in negated:
		features.discard("seizures")

	if "reduced_consciousness" in negated:
		features.discard("reduced_consciousness")

	features = _apply_clinical_concept_overrides(features)
	features = _prune_lower_severity_features(features)

	return sorted(features)


def derive_features(assertions: list[dict]) -> dict:
	"""Compatibility wrapper while callers move to clinical state."""
	from engine.clinical_state import build_clinical_state

	state = build_clinical_state("", assertions)
	return {"present_feature_ids": derive_features_from_state(state)}