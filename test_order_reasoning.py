from main import run_ui_case


def _appendicitis_condition_state(text: str) -> dict:
	r = run_ui_case(text)
	return next(
		(condition_state for condition_state in r["condition_states"] if condition_state["id"] == "appendicitis"),
		None,
	)


def _signal_labels(text: str, signal_type: str) -> list[str]:
	condition_state = _appendicitis_condition_state(text)
	if condition_state is None:
		return []
	return [
		signal_entry.get("label")
		for signal_entry in condition_state.get("signal_breakdown", [])
		if signal_entry.get("type") == signal_type and signal_entry.get("label")
	]


def test_pain_then_vomiting_adds_appendicitis_support_reasoning() -> None:
	labels = _signal_labels("pain then vomiting", "supporting")
	assert "Pain preceded vomiting (supports appendicitis pattern)" in labels


def test_vomiting_then_pain_adds_appendicitis_less_likely_reasoning() -> None:
	labels = _signal_labels("vomiting then pain", "contradiction")
	assert "Vomiting preceded pain (less typical for appendicitis)" in labels


def test_pain_and_vomiting_adds_no_order_reasoning() -> None:
	support_labels = _signal_labels("pain and vomiting", "supporting")
	against_labels = _signal_labels("pain and vomiting", "contradiction")

	assert "Pain preceded vomiting (supports appendicitis pattern)" not in support_labels
	assert "Vomiting preceded pain (less typical for appendicitis)" not in against_labels


if __name__ == "__main__":
	test_pain_then_vomiting_adds_appendicitis_support_reasoning()
	test_vomiting_then_pain_adds_appendicitis_less_likely_reasoning()
	test_pain_and_vomiting_adds_no_order_reasoning()
	print("PASS: order reasoning tests")