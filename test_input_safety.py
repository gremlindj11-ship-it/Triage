from main import run_ui_case


def test_contradiction_preserves_positive_headache_signal() -> None:
	r = run_ui_case("no headache but worst headache of life")
	features = r["parsed"]["present_feature_ids"]
	clinical_state = r["parsed"]["clinical_state"]

	assert "thunderclap_headache" in features
	assert "headache" not in clinical_state.get("negated", [])


def test_negation_priority_separates_chest_pain_from_vomiting() -> None:
	r = run_ui_case("no chest pain but vomiting")
	features = r["parsed"]["present_feature_ids"]

	assert "chest_pain" not in features
	assert "vomiting" in features


def test_location_alone_does_not_create_rlq_pain() -> None:
	r = run_ui_case("rlq")
	features = r["parsed"]["present_feature_ids"]

	assert "rlq_pain" not in features
	assert "right_lower_quadrant_pain" not in features


def test_severity_conflict_keeps_only_thunderclap_headache() -> None:
	r = run_ui_case("mild headache now worst headache")
	features = r["parsed"]["present_feature_ids"]

	assert "thunderclap_headache" in features
	assert "mild_headache" not in features


if __name__ == "__main__":
	test_contradiction_preserves_positive_headache_signal()
	test_negation_priority_separates_chest_pain_from_vomiting()
	test_location_alone_does_not_create_rlq_pain()
	test_severity_conflict_keeps_only_thunderclap_headache()
	print("PASS: input safety tests")