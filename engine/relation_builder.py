import re


TEMPORAL_CUES = ["then", "after", "before", "followed by"]
PAST_REFERENCES = ["before", "earlier", "previously", "last week", "days ago", "recently"]
CURRENT_REFERENCES = ["now", "today", "currently"]
CHANGE_MARKERS = ["worse", "worsening", "severe", "worst", "sudden", "suddenly"]
_PROGRESSION_QUALIFIER_TOKENS = {"severe", "sudden", "worst", "worsening", "thunderclap"}
_PROGRESSION_MODIFIER_TOKENS = {
	"severe",
	"sudden",
	"worst",
	"worsening",
	"thunderclap",
	"mild",
	"reduced",
	"onset",
	"of",
	"life",
}
_CONTEXT_WINDOW_CHARS = 20
_FORWARD_TEMPORAL_CUES = {"then", "before", "followed by"}
_REVERSE_TEMPORAL_CUES = {"after"}


def _contains_phrase(text: str, phrase: str) -> bool:
	return re.search(rf"\b{re.escape(phrase)}\b", text) is not None


def _contains_any_phrase(text: str, phrases: list[str]) -> bool:
	return any(_contains_phrase(text, phrase) for phrase in phrases)


def _get_context_window(text: str, start: int, end: int) -> str:
	window_start = max(0, start - _CONTEXT_WINDOW_CHARS)
	window_end = min(len(text), end + _CONTEXT_WINDOW_CHARS)
	return text[window_start:window_end]


def _has_past_reference_before(text: str, start: int) -> bool:
	return _contains_any_phrase(text[:start], PAST_REFERENCES)


def _has_past_reference_near(text: str, assertion: dict) -> bool:
	window_text = _get_context_window(text, assertion["start"], assertion["end"])
	return _contains_any_phrase(window_text, PAST_REFERENCES)


def _has_current_reference_near(text: str, assertion: dict) -> bool:
	window_text = _get_context_window(text, assertion["start"], assertion["end"])
	return _contains_any_phrase(window_text, CURRENT_REFERENCES)


def _has_change_marker_near(text: str, assertion: dict) -> bool:
	window_text = _get_context_window(text, assertion["start"], assertion["end"])
	meaning_tokens = set(assertion["meaning_id"].split("_"))
	return any(token in meaning_tokens for token in _PROGRESSION_QUALIFIER_TOKENS) or _contains_any_phrase(
		window_text,
		CHANGE_MARKERS,
	)


def _has_current_progression_context(text: str, assertion: dict) -> bool:
	return _has_current_reference_near(text, assertion) and _has_change_marker_near(text, assertion)


def _get_symptom_family(meaning_id: str) -> str | None:
	filtered_tokens = [token for token in meaning_id.split("_") if token not in _PROGRESSION_MODIFIER_TOKENS]
	if not filtered_tokens:
		return None
	if "headache" in filtered_tokens:
		return "headache"
	return filtered_tokens[-1]


def _build_progression_relation(earlier_assertion: dict, later_assertion: dict, symptom_family: str) -> dict:
	return {
		"id": f"progression_{earlier_assertion['id']}_{later_assertion['id']}",
		"type": "temporal_progression",
		"relation_type": "temporal_progression",
		"earlier": earlier_assertion["id"],
		"later": later_assertion["id"],
		"symptom_family": symptom_family,
		"certainty": "inferred",
	}


def detect_temporal_progression(assertions: list[dict], text: str) -> list[dict]:
	progression_relations = []
	present_assertions = [assertion for assertion in assertions if assertion["polarity"] == "present"]
	family_to_assertions = {}

	for assertion in present_assertions:
		symptom_family = _get_symptom_family(assertion["meaning_id"])
		if symptom_family is None:
			continue
		family_to_assertions.setdefault(symptom_family, []).append(assertion)

	for symptom_family, family_assertions in family_to_assertions.items():
		ordered_assertions = sorted(family_assertions, key=lambda assertion: assertion["start"])

		for earlier_assertion, later_assertion in zip(ordered_assertions, ordered_assertions[1:]):
			if not _has_past_reference_before(text, later_assertion["start"]):
				continue
			if not _has_current_progression_context(text, later_assertion):
				continue

			progression_relations.append(_build_progression_relation(earlier_assertion, later_assertion, symptom_family))
			break
		else:
			if len(ordered_assertions) != 1:
				continue

			assertion = ordered_assertions[0]
			if not _has_past_reference_near(text, assertion):
				continue
			if not _has_current_progression_context(text, assertion):
				continue

			progression_relations.append(_build_progression_relation(assertion, assertion, symptom_family))

	return progression_relations


def detect_temporal_order(assertions: list[dict], text: str) -> list[dict]:
	relations = []
	present_assertions = [assertion for assertion in assertions if assertion["polarity"] == "present"]
	text_lower = text.lower()

	for cue in TEMPORAL_CUES:
		pattern = re.escape(cue)
		for match in re.finditer(pattern, text_lower):
			cue_start = match.start()
			cue_end = match.end()

			left_assertions = [
				assertion
				for assertion in present_assertions
				if assertion["end"] <= cue_start
			]
			right_assertions = [
				assertion
				for assertion in present_assertions
				if assertion["start"] >= cue_end
			]

			if not left_assertions or not right_assertions:
				continue

			left_assertion = max(left_assertions, key=lambda assertion: assertion["end"])
			right_assertion = min(right_assertions, key=lambda assertion: assertion["start"])

			if cue in _FORWARD_TEMPORAL_CUES:
				first_assertion = left_assertion
				second_assertion = right_assertion
			elif cue in _REVERSE_TEMPORAL_CUES:
				first_assertion = right_assertion
				second_assertion = left_assertion
			else:
				continue

			relations.append(
				{
					"id": f"r_{first_assertion['id']}_{second_assertion['id']}_{cue_start}",
					"type": "temporal_order",
					"relation_type": "temporal_order",
					"first": first_assertion["meaning_id"],
					"second": second_assertion["meaning_id"],
					"earlier": first_assertion["id"],
					"later": second_assertion["id"],
					"certainty": "inferred",
					"source_span": text[cue_start:cue_end],
				}
			)

	return relations


def build_relations(assertions: list[dict], text: str = "") -> list[dict]:
	relations = []
	present_assertions = [assertion for assertion in assertions if assertion["polarity"] == "present"]
	meaning_to_assertion = {
		assertion["meaning_id"]: assertion
		for assertion in present_assertions
	}
	meaning_ids = [assertion["meaning_id"] for assertion in present_assertions]

	if "periumbilical_pain" in meaning_ids and "rlq_location" in meaning_ids:
		relations.append(
			{
				"id": "r0",
				"type": "migration",
				"source": "periumbilical_pain",
				"target": "rlq_location",
				"source_assertion_ids": [meaning_to_assertion["periumbilical_pain"]["id"]],
				"target_assertion_ids": [meaning_to_assertion["rlq_location"]["id"]],
			}
		)

	if text:
		relations.extend(detect_temporal_order(assertions, text))
		relations.extend(detect_temporal_progression(assertions, text.lower()))

	return relations