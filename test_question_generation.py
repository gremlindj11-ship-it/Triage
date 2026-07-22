from main import run_ui_case


def test_headache_prefers_onset_question() -> None:
	r = run_ui_case("headache")
	next_question = r["next_question"]

	assert next_question is not None
	assert next_question["text"] == "Did the headache start suddenly or build gradually?"


def test_headache_avoids_generic_question() -> None:
	r = run_ui_case("headache")
	next_question = r["next_question"]

	assert next_question is not None
	assert next_question["text"] != "Can you describe the main symptom?"


def test_headache_prefers_associated_symptom_question_when_onset_known() -> None:
	r = run_ui_case("sudden onset headache")
	next_question = r["next_question"]

	assert next_question is not None
	assert next_question["text"] == "How severe is the headache right now?"


def test_generic_question_only_when_no_clear_symptom() -> None:
	r = run_ui_case("weird")
	next_question = r["next_question"]

	assert next_question is not None
	assert next_question["text"] == "Can you describe the symptom more clearly? Is it pain, nausea, or something else?"


if __name__ == "__main__":
	test_headache_prefers_onset_question()
	test_headache_avoids_generic_question()
	test_headache_prefers_associated_symptom_question_when_onset_known()
	test_generic_question_only_when_no_clear_symptom()
	print("PASS: question generation tests")