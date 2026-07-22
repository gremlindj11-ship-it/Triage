from main import run_ui_case


def _temporal_order_relations(text: str) -> list[dict]:
	r = run_ui_case(text)
	return [
		relation
		for relation in r["parsed"].get("relations", [])
		if relation.get("type") == "temporal_order"
	]


def _has_relation(text: str, first: str, second: str) -> bool:
	return any(
		relation.get("first") == first and relation.get("second") == second
		for relation in _temporal_order_relations(text)
	)


def test_pain_then_vomiting_relation() -> None:
	assert _has_relation("pain then vomiting", "pain", "vomiting")


def test_vomiting_then_pain_relation() -> None:
	assert _has_relation("vomiting then pain", "vomiting", "pain")


def test_pain_and_vomiting_has_no_temporal_relation() -> None:
	assert _temporal_order_relations("pain and vomiting") == []


def test_pain_before_vomiting_relation() -> None:
	assert _has_relation("pain before vomiting", "pain", "vomiting")


def test_vomiting_after_pain_relation() -> None:
	assert _has_relation("vomiting after pain", "pain", "vomiting")


if __name__ == "__main__":
	test_pain_then_vomiting_relation()
	test_vomiting_then_pain_relation()
	test_pain_and_vomiting_has_no_temporal_relation()
	test_pain_before_vomiting_relation()
	test_vomiting_after_pain_relation()
	print("PASS: relation tests")