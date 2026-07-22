from main import run_ui_case


def test_pain_before_vomiting() -> None:
	r = run_ui_case("abdominal pain then vomiting")
	features = r["parsed"]["present_feature_ids"]
	assert "pain_before_vomiting" in features


def test_vomiting_before_pain() -> None:
	r = run_ui_case("vomiting then abdominal pain")
	features = r["parsed"]["present_feature_ids"]
	assert "vomiting_before_pain" in features


def test_no_false_temporal() -> None:
	r = run_ui_case("abdominal pain and vomiting")
	features = r["parsed"]["present_feature_ids"]
	assert "pain_before_vomiting" not in features
	assert "vomiting_before_pain" not in features


def test_headache_progression_maps_to_sentinel() -> None:
	r = run_ui_case("had headache last week and now sudden severe headache")
	features = r["parsed"]["present_feature_ids"]

	assert "temporal_progression" in features
	assert "sentinel_headache" in features


def test_headache_progression_with_single_mention_and_change() -> None:
	r = run_ui_case("headache last week now worse")
	features = r["parsed"]["present_feature_ids"]

	assert "headache" in features
	assert "temporal_progression" in features


def test_no_false_progression_for_intermittent_headache() -> None:
	r = run_ui_case("intermittent headache")
	features = r["parsed"]["present_feature_ids"]

	assert "temporal_progression" not in features
	assert "sentinel_headache" not in features


def test_no_false_progression_for_repeated_symptom_without_markers() -> None:
	r = run_ui_case("headache headache")
	features = r["parsed"]["present_feature_ids"]

	assert "headache" in features
	assert "temporal_progression" not in features
	assert "sentinel_headache" not in features


def test_no_false_progression_for_negated_headache_now() -> None:
	r = run_ui_case("no headache now")
	features = r["parsed"]["present_feature_ids"]

	assert "headache" not in features
	assert "temporal_progression" not in features
	assert "sentinel_headache" not in features


if __name__ == "__main__":
	test_pain_before_vomiting()
	test_vomiting_before_pain()
	test_no_false_temporal()
	test_headache_progression_maps_to_sentinel()
	test_headache_progression_with_single_mention_and_change()
	test_no_false_progression_for_intermittent_headache()
	test_no_false_progression_for_repeated_symptom_without_markers()
	test_no_false_progression_for_negated_headache_now()
	print("PASS: temporal tests")