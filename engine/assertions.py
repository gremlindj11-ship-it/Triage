from engine.qualifier import qualify_match
from engine.severity import detect_assertion_severity


_SYMPTOM_FAMILY_BY_MEANING = {
	"headache": "headache",
	"mild_headache": "headache",
	"severe_headache": "headache",
	"sudden_onset_headache": "headache",
	"gradual_onset_headache": "headache",
	"thunderclap_headache": "headache",
	"sentinel_headache": "headache",
}

# Words that mark an abrupt transition when they sit between a negated mention
# of a symptom and a later contrasting present mention of the same symptom
# family (e.g. "no headache but now severe headache"). Presence of one of
# these is treated as an implied sudden/abrupt onset signal, independent of
# which symptom family it applies to.
_ABRUPT_ONSET_CUES = ("now", "suddenly", "then", "abruptly", "immediately", "all of a sudden")


def _resolve_contrasted_negations(text: str, assertions: list[dict]) -> list[dict]:
	resolved_assertions = []
	lowered_text = text.lower()

	for assertion in assertions:
		if assertion["polarity"] != "negated":
			resolved_assertions.append(assertion)
			continue

		symptom_family = _SYMPTOM_FAMILY_BY_MEANING.get(assertion["meaning_id"])
		if symptom_family is None:
			resolved_assertions.append(assertion)
			continue

		contrasting_assertions = [
			other_assertion
			for other_assertion in assertions
			if other_assertion["polarity"] == "present"
			and _SYMPTOM_FAMILY_BY_MEANING.get(other_assertion["meaning_id"]) == symptom_family
			and other_assertion["start"] > assertion["end"]
			and "but" in lowered_text[assertion["end"]:other_assertion["start"]]
		]

		if not contrasting_assertions:
			resolved_assertions.append(assertion)
			continue

		for other_assertion in contrasting_assertions:
			connector_text = lowered_text[assertion["end"]:other_assertion["start"]]
			if any(cue in connector_text for cue in _ABRUPT_ONSET_CUES):
				other_assertion["implied_abrupt_onset"] = True

	return resolved_assertions


def build_assertions(text: str, matches: list[dict]) -> list[dict]:
	assertions = []

	for index, match in enumerate(matches):
		polarity, qualification_rule = qualify_match(text, match)
		severity = detect_assertion_severity(text, match["start"], match["end"]) if polarity == "present" else None
		assertions.append(
			{
				"id": f"a{index}",
				"meaning_id": match["meaning_id"],
				"polarity": polarity,
				"certainty": "explicit",
				"source_span": text[match["start"]:match["end"]],
				"start": match["start"],
				"end": match["end"],
				"derived_from": {
					"rule_id": qualification_rule or "direct_match",
					"source_assertion_ids": [],
				},
				"severity": severity,
			}
		)

	return _resolve_contrasted_negations(text, assertions)