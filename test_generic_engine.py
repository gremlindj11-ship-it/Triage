from generic_engine.diseases import DISEASES, validate_diseases
from generic_engine.facts import FACT_REGISTRY
from generic_engine.reasoning import build_next_question, evaluate_all, rank_next_questions


def test_diseases_validate_against_fact_registry() -> None:
	validate_diseases(DISEASES, FACT_REGISTRY)


def test_appendicitis_scores_likely_with_classic_presentation() -> None:
	facts = {"abdominal_pain", "right_lower_quadrant_pain", "vomiting"}
	relations = [{"type": "temporal_order", "first": "abdominal_pain", "second": "vomiting"}]
	results = evaluate_all(DISEASES, facts, relations=relations, fact_registry=FACT_REGISTRY)
	appendicitis = next(result for result in results if result["id"] == "appendicitis")
	assert appendicitis["state"] == "likely", appendicitis
	assert "abdominal pain supports this diagnosis" in appendicitis["supporting_explanations"]


def test_sah_present_in_differential_for_original_bug_input() -> None:
	# Reproduces the exact input that started this investigation: under the OLD reasoning.py,
	# this diagnosis never appeared in condition_states at all, because subarachnoid_haemorrhage
	# was absent from _DIAGNOSIS_SCORE_CONFIG. It must now appear, ranked, with real evidence.
	facts = {"headache", "thunderclap_headache", "neck_stiffness", "vomiting"}
	results = evaluate_all(DISEASES, facts, fact_registry=FACT_REGISTRY)
	sah = next(result for result in results if result["id"] == "subarachnoid_haemorrhage")
	assert sah["state"] in ("possible", "likely"), sah
	assert sah["score"] > 0


def test_sah_sparse_evidence_still_reaches_display_via_forces_min_state() -> None:
	facts = {"headache", "thunderclap_headache"}
	results = evaluate_all(DISEASES, facts, fact_registry=FACT_REGISTRY)
	sah = next(result for result in results if result["id"] == "subarachnoid_haemorrhage")

	sah_definition = DISEASES["subarachnoid_haemorrhage"]
	raw_score = sum(f["weight"] for f in sah_definition["supporting_features"] if f["feature_id"] in facts)
	assert raw_score < sah_definition["state_thresholds"]["possible"], raw_score

	assert sah["state"] not in ("insufficient", "ruled_out"), sah


def test_critical_red_flag_short_circuits_question_selection() -> None:
	facts = {"headache", "thunderclap_headache"}
	results = evaluate_all(DISEASES, facts, fact_registry=FACT_REGISTRY)
	question = build_next_question(results, DISEASES, facts, FACT_REGISTRY)
	assert question["short_circuited"] is True, question
	assert "subarachnoid haemorrhage" in question["text"].lower()


def test_rank_next_questions_prefers_discriminating_facts() -> None:
	facts = {"abdominal_pain", "vomiting"}
	results = evaluate_all(DISEASES, facts, fact_registry=FACT_REGISTRY)
	ranked = rank_next_questions(results, DISEASES, facts, FACT_REGISTRY)
	ranked_ids = [entry["id"] for entry in ranked]

	assert "right_lower_quadrant_pain" in ranked_ids

	# right_lower_quadrant_pain (appendicitis-only signal) must outrank a fact that means
	# nothing extra for either currently-live disease.
	assert ranked_ids.index("right_lower_quadrant_pain") < ranked_ids.index("diarrhoea")


if __name__ == "__main__":
	test_diseases_validate_against_fact_registry()
	test_appendicitis_scores_likely_with_classic_presentation()
	test_sah_present_in_differential_for_original_bug_input()
	test_sah_sparse_evidence_still_reaches_display_via_forces_min_state()
	test_critical_red_flag_short_circuits_question_selection()
	test_rank_next_questions_prefers_discriminating_facts()
	print("PASS: generic engine end-to-end")
