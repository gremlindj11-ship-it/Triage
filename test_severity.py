from main import run_ui_case


def test_mild_headache_severity() -> None:
	r = run_ui_case("mild headache")
	severity = r["parsed"].get("severity")

	assert severity is not None
	assert severity["level"] == "mild"


def test_severe_abdominal_pain_severity() -> None:
	r = run_ui_case("severe abdominal pain")
	severity = r["parsed"].get("severity")

	assert severity is not None
	assert severity["level"] == "severe"


def test_worst_headache_is_critical() -> None:
	r = run_ui_case("worst headache of my life")
	severity = r["parsed"].get("severity")
	features = r["parsed"]["present_feature_ids"]

	assert severity is not None
	assert severity["level"] == "critical"
	assert "thunderclap_headache" in features
	assert "worst_headache_of_life" not in features


def test_high_risk_progression_from_critical_temporal_change() -> None:
	r = run_ui_case("headache last week now worst ever")
	severity = r["parsed"].get("severity")
	features = r["parsed"]["present_feature_ids"]

	assert severity is not None
	assert severity["level"] == "critical"
	assert "temporal_progression" in features
	assert "high_risk_progression" in features


def test_keep_only_highest_headache_severity_feature() -> None:
	r = run_ui_case("mild headache now worst headache of life")
	features = r["parsed"]["present_feature_ids"]

	assert "thunderclap_headache" in features
	assert "worst_headache_of_life" not in features
	assert "mild_headache" not in features


def test_sudden_severe_headache_maps_to_thunderclap() -> None:
	r = run_ui_case("sudden severe headache")
	features = r["parsed"]["present_feature_ids"]

	assert "thunderclap_headache" in features


def test_mild_headache_remains_mild_headache() -> None:
	r = run_ui_case("mild headache")
	features = r["parsed"]["present_feature_ids"]

	assert "mild_headache" in features
	assert "thunderclap_headache" not in features


def test_do_not_remove_unrelated_findings() -> None:
	r = run_ui_case("mild headache with vomiting")
	features = r["parsed"]["present_feature_ids"]

	assert "headache" in features
	assert "vomiting" in features


def test_single_severity_abdominal_pain_remains() -> None:
	r = run_ui_case("mild abdominal pain worsening")
	features = r["parsed"]["present_feature_ids"]

	assert "abdominal_pain" in features


if __name__ == "__main__":
	test_mild_headache_severity()
	test_severe_abdominal_pain_severity()
	test_worst_headache_is_critical()
	test_high_risk_progression_from_critical_temporal_change()
	test_keep_only_highest_headache_severity_feature()
	test_sudden_severe_headache_maps_to_thunderclap()
	test_mild_headache_remains_mild_headache()
	test_do_not_remove_unrelated_findings()
	test_single_severity_abdominal_pain_remains()
	print("PASS: severity tests")