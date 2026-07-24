import os

from web_app import NOTES_FILE, app


def _clear_saved_notes() -> None:
	if os.path.exists(NOTES_FILE):
		os.remove(NOTES_FILE)


def test_triage_route_uses_expanded_pipeline() -> None:
	client = app.test_client()
	response = client.post("/triage", json={"text": "male with missed period and abdominal pain"})

	assert response.status_code == 200
	payload = response.get_json()
	assert payload is not None

	parsed = payload["parsed"]
	for key in [
		"assertions",
		"clinical_state",
		"derived_features",
		"pattern_results",
		"diagnosis_results",
		"red_flags",
	]:
		assert key in parsed

	ectopic = [
		diagnosis
		for diagnosis in parsed["diagnosis_results"]
		if diagnosis["diagnosis"] == "ectopic_pregnancy"
	][0]
	assert ectopic["state"] == "ruled_out"


def test_malicious_input_is_treated_as_plain_text() -> None:
	client = app.test_client()
	malicious_input = "<script>alert('hack')</script> headache"
	response = client.post("/triage", json={"text": malicious_input})

	assert response.status_code == 200
	payload = response.get_json()
	assert payload is not None
	assert payload["raw_input"] == malicious_input
	assert "headache" in payload["parsed"]["present_feature_ids"]


def test_index_escapes_submitted_note_rendering() -> None:
	client = app.test_client()
	response = client.get("/")
	html = response.get_data(as_text=True)

	assert response.status_code == 200
	assert "escapeHtml(data.raw_input)" in html
	assert '${data.raw_input}' not in html


def test_notes_list_is_empty_with_no_saved_notes() -> None:
	_clear_saved_notes()
	client = app.test_client()

	response = client.get("/notes")

	assert response.status_code == 200
	assert response.get_json() == []


def test_notes_save_then_appears_in_list() -> None:
	_clear_saved_notes()
	client = app.test_client()

	create_response = client.post("/notes", json={"text": "male with missed period and abdominal pain"})
	assert create_response.status_code == 201
	created_note = create_response.get_json()
	assert created_note["text"] == "male with missed period and abdominal pain"
	assert created_note["id"]
	assert created_note["timestamp"]

	list_response = client.get("/notes")
	assert list_response.status_code == 200
	notes = list_response.get_json()
	assert len(notes) == 1
	assert notes[0]["id"] == created_note["id"]

	_clear_saved_notes()


def test_notes_save_rejects_empty_text() -> None:
	_clear_saved_notes()
	client = app.test_client()

	response = client.post("/notes", json={"text": "   "})

	assert response.status_code == 400
	_clear_saved_notes()


if __name__ == "__main__":
	test_triage_route_uses_expanded_pipeline()
	test_malicious_input_is_treated_as_plain_text()
	test_index_escapes_submitted_note_rendering()
	test_notes_list_is_empty_with_no_saved_notes()
	test_notes_save_then_appears_in_list()
	test_notes_save_rejects_empty_text()
	print("PASS: web app tests")