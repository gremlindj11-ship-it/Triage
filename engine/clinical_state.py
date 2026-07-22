from engine.severity import summarize_assertion_severity


def build_clinical_state(text: str, assertions: list[dict], relations: list[dict] | None = None) -> dict:
	"""Canonical truth object for the current input."""

	state = {
		"raw_text": text,
		"assertions": assertions,
		"relations": relations or [],
		"present": [],
		"negated": [],
		"uncertain": [],
		"severity": summarize_assertion_severity(assertions),
	}

	for assertion in assertions:
		polarity = assertion["polarity"]
		meaning_id = assertion["meaning_id"]

		if polarity == "present":
			state["present"].append(meaning_id)
		elif polarity == "negated":
			state["negated"].append(meaning_id)
		else:
			state["uncertain"].append(meaning_id)

	return state