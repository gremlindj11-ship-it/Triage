from main import run_ui_case


def test_syncope_flag() -> None:
	r = run_ui_case("fainted")
	assert len(r["parsed"]["red_flags"]) > 0


def test_shoulder_tip_flag() -> None:
	r = run_ui_case("shoulder tip pain")
	flags = r["parsed"]["red_flags"]
	assert any("bleeding" in flag["message"] for flag in flags)


def test_no_false_flags() -> None:
	r = run_ui_case("feel sick")
	assert len(r["parsed"]["red_flags"]) == 0


def test_thunderclap_headache_flag() -> None:
	r = run_ui_case("thunderclap headache")
	flags = r["parsed"]["red_flags"]
	assert any("subarachnoid haemorrhage" in flag["message"].lower() for flag in flags)


def test_reduced_consciousness_flag() -> None:
	r = run_ui_case("reduced consciousness")
	flags = r["parsed"]["red_flags"]
	assert len(flags) > 0


if __name__ == "__main__":
	test_syncope_flag()
	test_shoulder_tip_flag()
	test_no_false_flags()
	test_thunderclap_headache_flag()
	test_reduced_consciousness_flag()
	print("PASS: red flag tests")