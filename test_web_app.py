from web_app import app


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


if __name__ == "__main__":
	test_triage_route_uses_expanded_pipeline()
	test_malicious_input_is_treated_as_plain_text()
	test_index_escapes_submitted_note_rendering()
	print("PASS: web app tests")