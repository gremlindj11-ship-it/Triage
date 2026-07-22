def _humanize_identifier(identifier: str) -> str:
	return identifier.replace("_", " ")


def _get_top_diagnosis_display(top_diagnoses: list[dict]) -> str:
	if len(top_diagnoses) == 0:
		return "none"

	if all(
		diagnosis["raw_support_score"] >= 1 and diagnosis["adjusted_score"] == 0
		for diagnosis in top_diagnoses
	):
		return "uncertain"

	return _humanize_identifier(top_diagnoses[0]["id"])


def _get_main_problem(result: dict, top_diagnosis_display: str) -> str:
	if result["mode"] == "safety_priority" and result["safety_diagnoses"]:
		return _humanize_identifier(result["safety_diagnoses"][0]["id"])

	if top_diagnosis_display not in {"none", "uncertain"}:
		return top_diagnosis_display

	if result["concerns"]:
		return "clinical concern requiring clarification"

	return "undifferentiated presentation"


def _get_missing_or_next_step(result: dict) -> str:
	if result["top_diagnoses"]:
		missing_features = result["top_diagnoses"][0]["missing_expected_features"]
		if missing_features:
			missing_text = ", ".join(_humanize_identifier(feature) for feature in missing_features)
			return (
				f"Key features are missing, including {missing_text}. "
				f"Next step: {result['next_question']['text']}"
			)

	return f"Next step: {result['next_question']['text']}"


def build_summary(result: dict) -> str:
	top_diagnosis_display = _get_top_diagnosis_display(result["top_diagnoses"])
	main_problem = _get_main_problem(result, top_diagnosis_display)
	key_concern = result["concerns"][0] if result["concerns"] else "none"
	missing_or_next_step = _get_missing_or_next_step(result)

	return (
		f"Main problem: {main_problem}. "
		f"Key concern: {key_concern}. "
		f"Top diagnosis: {top_diagnosis_display}. "
		f"{missing_or_next_step}."
	)