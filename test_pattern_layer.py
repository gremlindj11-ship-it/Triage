from main import run_ui_case


def test_cases() -> None:
	cases = [
		"severe right lower abdominal pain",
		"pain moved to right side and feel sick",
		"no abdominal pain but right lower quadrant pain",
		"feel sick",
		"vomiting",
	]

	for case in cases:
		result = run_ui_case(case)

		print("\n---")
		print("INPUT:", case)
		print("FEATURES:", result["parsed"]["present_feature_ids"])
		print("PATTERNS:", result["parsed"].get("pattern_results"))


if __name__ == "__main__":
	test_cases()