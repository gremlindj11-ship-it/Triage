from main import run_ui_case


def test_rlq_location_with_pain_and_vomiting() -> None:
	r = run_ui_case("rlq pain vomiting")
	features = r["parsed"]["present_feature_ids"]

	assert "rlq_pain" in features
	assert "right_lower_quadrant_pain" in features
	assert "vomiting" in features


def test_chest_location_with_pain_and_sweating() -> None:
	r = run_ui_case("chest pain sweating")
	features = r["parsed"]["present_feature_ids"]

	assert "chest_pain" in features
	assert "sweating" in features


def test_epigastric_alias_maps_from_upper_abdomen() -> None:
	r = run_ui_case("upper abdomen pain")
	features = r["parsed"]["present_feature_ids"]

	assert "epigastric_pain" in features


def test_abdominal_pain_remains_supported() -> None:
	r = run_ui_case("abdominal pain")
	features = r["parsed"]["present_feature_ids"]

	assert "abdominal_pain" in features


def test_head_location_with_pain_maps_to_headache() -> None:
	r = run_ui_case("head pain")
	features = r["parsed"]["present_feature_ids"]

	assert "headache" in features


def test_location_alone_does_not_emit_pain_feature() -> None:
	r = run_ui_case("rlq")
	features = r["parsed"]["present_feature_ids"]

	assert "rlq_pain" not in features
	assert "right_lower_quadrant_pain" not in features


if __name__ == "__main__":
	test_rlq_location_with_pain_and_vomiting()
	test_chest_location_with_pain_and_sweating()
	test_epigastric_alias_maps_from_upper_abdomen()
	test_abdominal_pain_remains_supported()
	test_head_location_with_pain_maps_to_headache()
	test_location_alone_does_not_emit_pain_feature()
	print("PASS: location tests")