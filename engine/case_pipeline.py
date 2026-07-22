from contextlib import redirect_stdout
from io import StringIO

from engine.assertions import build_assertions
from engine.clinical_state import build_clinical_state
from engine.diagnosis_engine import score_diagnosis
from engine.feature_derivation import derive_features_from_state
from engine.matcher import match_meanings
from engine.parser import parse_text
from engine.pattern_engine import evaluate_patterns
from engine.red_flag_engine import evaluate_red_flags
from engine.reasoning import select_diagnosis
from engine.relation_builder import build_relations


def filter_diagnoses(diagnoses: list[dict]) -> list[dict]:
	filtered = []

	for diagnosis in diagnoses:
		if diagnosis.get("state") == "ruled_out":
			filtered.append(diagnosis)
			continue
		if diagnosis.get("confidence", 0) > 0.2:
			filtered.append(diagnosis)

	return filtered[:3]


def build_assertion_pipeline(text: str) -> dict:
	matches = match_meanings(text)
	assertions = build_assertions(text, matches)
	relations = build_relations(assertions, text)
	clinical_state = build_clinical_state(text, assertions, relations)
	derived_features = derive_features_from_state(clinical_state)
	return {
		"matches": matches,
		"assertions": assertions,
		"relations": relations,
		"clinical_state": clinical_state,
		"derived_features": derived_features,
	}


def augment_parsed_output(text: str, parsed: dict) -> dict:
	assertion_pipeline = build_assertion_pipeline(text)
	parsed["matches"] = assertion_pipeline["matches"]
	parsed["meaning_matches"] = assertion_pipeline["matches"]
	parsed["assertions"] = assertion_pipeline["assertions"]
	parsed["relations"] = assertion_pipeline["relations"]
	parsed["clinical_state"] = assertion_pipeline["clinical_state"]
	parsed["severity"] = assertion_pipeline["clinical_state"].get("severity")
	parsed["present_feature_ids"] = assertion_pipeline["derived_features"]
	parsed["derived_feature_ids"] = assertion_pipeline["derived_features"]
	parsed["derived_features"] = assertion_pipeline["derived_features"]
	parsed["pattern_results"] = evaluate_patterns(parsed["present_feature_ids"])
	diagnosis_results = score_diagnosis(
		parsed["present_feature_ids"],
		parsed.get("context", {}),
	)
	parsed["diagnosis_results"] = filter_diagnoses(diagnosis_results)
	parsed["red_flags"] = evaluate_red_flags(
		parsed["present_feature_ids"],
		parsed.get("context", {}),
	)
	return parsed


def build_case_payload(text: str) -> dict:
	with redirect_stdout(StringIO()):
		parsed = parse_text(text)
	parsed = augment_parsed_output(text, parsed)

	result = select_diagnosis(
		parsed["present_feature_ids"],
		parsed["clarification_question"],
		{
			**(parsed.get("context") or {}),
			"relations": parsed.get("relations", []),
		},
	)

	return {
		"input": text,
		"parsed": parsed,
		"condition_states": result.get("condition_states", []),
		"investigations": result.get("investigations", []),
		"next_question": result.get("next_question"),
		"safety_flags": result.get("safety_flags", []),
	}