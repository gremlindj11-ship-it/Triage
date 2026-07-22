from generic_engine.schema import PLACEHOLDER


SUBARACHNOID_HAEMORRHAGE = {
	"id": "subarachnoid_haemorrhage",
	"display_name": "Subarachnoid Haemorrhage",
	"category": "neurological",

	"supporting_features": [
		{"feature_id": "thunderclap_headache", "weight": 3, "status": PLACEHOLDER, "source": None},
		{"feature_id": "sudden_onset_headache", "weight": 2, "status": PLACEHOLDER, "source": None},
		{"feature_id": "worst_headache_of_life", "weight": 2, "status": PLACEHOLDER, "source": None},
		{"feature_id": "severe_headache", "weight": 1, "status": PLACEHOLDER, "source": None},
		{"feature_id": "vomiting", "weight": 1, "status": PLACEHOLDER, "source": None},
		{"feature_id": "neck_stiffness", "weight": 2, "status": PLACEHOLDER, "source": None},
		{"feature_id": "photophobia", "weight": 1, "status": PLACEHOLDER, "source": None},
		{"feature_id": "reduced_consciousness", "weight": 3, "status": PLACEHOLDER, "source": None},
		{"feature_id": "seizures", "weight": 3, "status": PLACEHOLDER, "source": None},
		{"feature_id": "sentinel_headache", "weight": 2, "status": PLACEHOLDER, "source": None},
	],

	"contradicting_features": [
		{"feature_id": "gradual_onset_headache", "weight": 2, "status": PLACEHOLDER, "source": None},
		{"feature_id": "mild_headache", "weight": 1, "status": PLACEHOLDER, "source": None},
	],

	"required_features": [
		{"feature_id": "headache", "status": PLACEHOLDER, "source": None},
	],

	"exclusion_rules": [],

	"relational_bonuses": [
		{
			"relation_type": "temporal_order",
			"earlier": {"feature_id": "sentinel_headache"},
			"later": {"feature_id": "worst_headache_of_life"},
			"marker_feature": None,
			"weight": 2,
			"direction": "supports",
			"explanation": "An earlier warning headache followed by a worst headache supports this diagnosis",
			"inverse": None,
			"status": PLACEHOLDER, "source": None,
		},
	],

	"display_override_rules": [],

	"red_flags": [
		{
			"feature_id": "thunderclap_headache", "severity": "critical",
			"message": "Sudden severe headache - possible subarachnoid haemorrhage",
			"forces_min_state": "possible",
			"status": PLACEHOLDER, "source": None,
		},
		{
			"feature_id": "reduced_consciousness", "severity": "critical",
			"message": "Reduced consciousness - urgent neurological emergency",
			"forces_min_state": "likely",
			"status": PLACEHOLDER, "source": None,
		},
		{
			"feature_id": "seizures", "severity": "critical",
			"message": "Seizures - urgent intracranial pathology must be excluded",
			"forces_min_state": "likely",
			"status": PLACEHOLDER, "source": None,
		},
	],

	"investigations": [
		{"name": "urgent CT head", "tier": "first_line"},
		{"name": "lumbar puncture if CT negative and suspicion remains", "tier": "second_line"},
	],

	"management": [
		{"step": "urgent neurosurgical assessment", "condition": None},
		{"step": "blood pressure control", "condition": None},
	],

	"state_thresholds": {"likely": 6, "possible": 4, "status": PLACEHOLDER, "source": None},
}
