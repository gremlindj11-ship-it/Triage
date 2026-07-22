from main import run_ui_case


def assert_true(condition: bool, message: str) -> None:
	if not condition:
		print("FAIL:", message)
	else:
		print("PASS:", message)


def meta_tests() -> None:
	r = run_ui_case("no abdominal pain but right lower quadrant pain")
	features = r["parsed"]["present_feature_ids"]
	assert_true(
		"right_lower_quadrant_pain" not in features,
		"Negation blocks derived RLQ pain",
	)

	r = run_ui_case("feel sick")
	features = r["parsed"]["present_feature_ids"]
	assert_true(
		"vomiting" not in features,
		"Nausea does NOT become vomiting",
	)

	r = run_ui_case("right lower abdominal pain")
	features = r["parsed"]["present_feature_ids"]
	assert_true(
		"pain_migration" not in features,
		"Migration not inferred incorrectly",
	)

	r = run_ui_case("pain near belly button then moved to right lower abdomen")
	features = r["parsed"]["present_feature_ids"]
	assert_true(
		"pain_migration" in features,
		"Migration detected correctly",
	)

	r1 = run_ui_case("feel sick")
	r2 = run_ui_case("feel sick")
	assert_true(
		r1["parsed"]["present_feature_ids"] == r2["parsed"]["present_feature_ids"],
		"Deterministic output",
	)

	r = run_ui_case("fainted and feel sick")
	flags = r["parsed"]["red_flags"]
	assert_true(
		len(flags) > 0,
		"Red flag overrides relevance",
	)

	r = run_ui_case("abdominal pain vomiting")
	features = r["parsed"]["present_feature_ids"]
	assert_true(
		"pain_before_vomiting" not in features,
		"Temporal relation requires cue",
	)


if __name__ == "__main__":
	meta_tests()