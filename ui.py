def _print_section(title: str) -> None:
	print("========================")
	print(title)
	print("========================")
	print()


def _humanize_identifier(identifier: str) -> str:
	return identifier.replace("_", " ").capitalize()


def _get_main_hypothesis_display_text(condition_state: dict | None) -> str:
	if not condition_state:
		return "No clear diagnosis yet"

	diagnostic_state = condition_state.get("diagnostic_state")
	if diagnostic_state == "ruled_out":
		return "Not possible"
	if diagnostic_state == "insufficient":
		return "More information needed"
	if diagnostic_state == "eligible":
		return _humanize_identifier(condition_state.get("id", ""))
	return "No clear diagnosis yet"


def _get_top_condition_state(condition_states: list) -> dict | None:
	if not condition_states:
		return None

	return condition_states[0]


def _get_secondary_condition_states(condition_states: list) -> list:
	if not condition_states:
		return []

	return condition_states[1:]


def _format_signal_breakdown_entry(signal_entry: dict) -> str:
	signal_type = signal_entry.get("type", "supporting")
	feature = _humanize_identifier(signal_entry["feature_id"])
	if signal_type == "contradiction":
		return f'- {feature} (contradiction)'
	if signal_type == "temporal":
		return f'~ {feature} (modifier)'
	strength = signal_entry.get("strength")
	if strength:
		return f'+ {feature} ({strength})'
	return f'+ {feature}'


def _get_top_diagnosis_title() -> str:
	return "MAIN HYPOTHESIS"


def _print_safety_flags(safety_flags: list) -> None:
	if not safety_flags:
		return

	_print_section("CLINICAL CONCERN")
	for safety_flag in safety_flags:
		print(f'- {safety_flag["message"]}')
	print()


def _get_supporting_signal_entries(condition_state: dict | None) -> list:
	if not condition_state:
		return []

	return [
		signal_entry
		for signal_entry in condition_state.get("signal_breakdown", [])
		if signal_entry.get("type", "supporting") in {"supporting", "temporal"}
	]


def _get_rule_label(rule_id: str) -> str:
	rule_labels = {
		"pregnancy_required": "No evidence of pregnancy",
		"male_context": "Male patient",
	}
	return rule_labels.get(rule_id, _humanize_identifier(rule_id))


def _get_missing_requirements(condition_state: dict | None) -> list[str]:
	if not condition_state:
		return []

	requirements = condition_state.get("rules", {}).get("requirements", [])
	return [
		_get_rule_label(requirement.get("id", ""))
		for requirement in requirements
		if requirement.get("status") == "missing"
	]


def _get_exclusions(condition_state: dict | None) -> list[str]:
	if not condition_state:
		return []

	exclusions = condition_state.get("rules", {}).get("exclusions", [])
	return [
		_get_rule_label(exclusion.get("id", ""))
		for exclusion in exclusions
	]


def _get_display_mode(condition_state: dict | None) -> str:
	if not condition_state:
		return "insufficient"

	if condition_state.get("diagnostic_state") == "ruled_out":
		return "exclusion"

	if _get_missing_requirements(condition_state):
		return "requirement"

	if condition_state.get("should_display"):
		return "hypothesis"

	return "insufficient"


def _get_section_specs(condition_state: dict | None) -> list[tuple[str, list[str] | list[dict], str]]:
	supporting_signals = _get_supporting_signal_entries(condition_state)
	missing_requirements = _get_missing_requirements(condition_state)
	exclusions = _get_exclusions(condition_state)
	display_mode = _get_display_mode(condition_state)

	if display_mode == "exclusion":
		return [
			("EXCLUSIONS", exclusions, "text"),
			("CONFLICTING EVIDENCE", supporting_signals, "signal"),
		]

	if display_mode == "requirement":
		return [
			("MISSING REQUIREMENTS", missing_requirements, "text"),
			("SUPPORTING EVIDENCE", supporting_signals, "signal"),
		]

	if display_mode == "hypothesis":
		return [
			("SUPPORTING EVIDENCE", supporting_signals, "signal"),
			("MISSING REQUIREMENTS", missing_requirements, "text"),
		]

	return [
		("SUPPORTING EVIDENCE", supporting_signals, "signal"),
	]


def _print_section_content(title: str, items: list, item_type: str) -> None:
	if not items:
		return

	_print_section(title)
	if item_type == "signal":
		for signal_entry in items:
			print(_format_signal_breakdown_entry(signal_entry))
	else:
		for item_text in items:
			print(f'- {item_text}')
	print()



def _print_other_possibility(condition_state: dict) -> None:
	print(f'- {_humanize_identifier(condition_state["id"])}')


def display_case(result: dict, features: list) -> None:
	condition_states = _get_secondary_condition_states(result.get("condition_states", []))
	top_condition_state = _get_top_condition_state(result.get("condition_states", []))
	display_text = _get_main_hypothesis_display_text(top_condition_state)
	section_specs = _get_section_specs(top_condition_state)
	safety_flags = result.get("safety_flags", [])

	_print_safety_flags(safety_flags)

	_print_section("NEXT QUESTION")
	print(f'- {result["next_question"]["text"]}')
	print(f'- reason: {result["next_question"]["reason"]}')
	print()

	_print_section(_get_top_diagnosis_title())
	print(f'- {display_text}')
	print()

	for title, items, item_type in section_specs:
		_print_section_content(title, items, item_type)

	if condition_states:
		_print_section("OTHER POSSIBILITIES")
		for condition_state in condition_states:
			_print_other_possibility(condition_state)
		print()