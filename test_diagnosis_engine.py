from main import run_ui_case


def test_appendicitis() -> None:
	r = run_ui_case("pain near belly button then moved to right lower abdomen and feel sick")
	results = r["parsed"]["diagnosis_results"]
	top = results[0]

	assert top["diagnosis"] == "appendicitis"
	assert top["score"] >= 4


def test_ectopic_blocked_in_male() -> None:
	r = run_ui_case("male with missed period and abdominal pain")
	results = r["parsed"]["diagnosis_results"]
	ectopic = [d for d in results if d["diagnosis"] == "ectopic_pregnancy"][0]

	assert ectopic["state"] == "ruled_out"


def test_ectopic_red_flag() -> None:
	r = run_ui_case("missed period, shoulder tip pain, fainted")
	results = r["parsed"]["diagnosis_results"]
	ectopic = [d for d in results if d["diagnosis"] == "ectopic_pregnancy"][0]

	assert ectopic["score"] >= 5


def test_no_false_vomiting() -> None:
	r = run_ui_case("feel sick")
	features = r["parsed"]["present_feature_ids"]

	assert "vomiting" not in features


def test_engine_determinism() -> None:
	r1 = run_ui_case("pain moved to right lower abdomen")
	r2 = run_ui_case("pain moved to right lower abdomen")

	assert r1["parsed"]["diagnosis_results"] == r2["parsed"]["diagnosis_results"]


def test_top_diagnosis_only() -> None:
	r = run_ui_case("pain moved to right lower abdomen and feel sick")
	results = r["parsed"]["diagnosis_results"]

	assert len(results) <= 3


def test_subarachnoid_haemorrhage() -> None:
	r = run_ui_case("thunderclap headache with vomiting and neck stiffness")
	results = r["parsed"]["diagnosis_results"]
	top = results[0]

	assert top["diagnosis"] == "subarachnoid_haemorrhage"
	assert top["score"] >= 5


def test_sah_alias_maps_to_thunderclap() -> None:
	r = run_ui_case("hit like a baseball bat headache")
	features = r["parsed"]["present_feature_ids"]

	assert "thunderclap_headache" in features


if __name__ == "__main__":
	test_appendicitis()
	test_ectopic_blocked_in_male()
	test_ectopic_red_flag()
	test_no_false_vomiting()
	test_engine_determinism()
	test_top_diagnosis_only()
	test_subarachnoid_haemorrhage()
	test_sah_alias_maps_to_thunderclap()
	print("PASS: diagnosis engine tests")