from generic_engine.schema import PLACEHOLDER


APPENDICITIS = {
	"id": "appendicitis",
	"display_name": "Appendicitis",
	"category": "abdominal",

	"supporting_features": [
		{"feature_id": "abdominal_pain", "weight": 1, "status": PLACEHOLDER, "source": None},
		{"feature_id": "vomiting", "weight": 1, "status": PLACEHOLDER, "source": None},
		{"feature_id": "right_lower_quadrant_pain", "weight": 2, "status": PLACEHOLDER, "source": None},
		{"feature_id": "peritonism", "weight": 2, "status": PLACEHOLDER, "source": None},
	],

	"contradicting_features": [
		{"feature_id": "diarrhoea", "weight": 1, "status": PLACEHOLDER, "source": None},
		{"feature_id": "no_pain", "weight": 1, "status": PLACEHOLDER, "source": None},
		{"feature_id": "diffuse_symptoms_without_localisation", "weight": 1, "status": PLACEHOLDER, "source": None},
	],

	"required_features": [
		{"feature_id": "right_lower_quadrant_pain", "status": PLACEHOLDER, "source": None},
	],

	"exclusion_rules": [],

	"relational_bonuses": [
		{
			"relation_type": "marker",
			"marker_feature": "pain_migration",
			"earlier": None, "later": None,
			"weight": 3,
			"direction": "supports",
			"explanation": "Pain migration supports this diagnosis",
			"inverse": None,
			"status": PLACEHOLDER, "source": None,
		},
		{
			"relation_type": "temporal_order",
			"earlier": {"tag": "pain"},
			"later": {"feature_id": "vomiting"},
			"marker_feature": None,
			"weight": 2,
			"direction": "supports",
			"explanation": "Pain preceded vomiting supports this diagnosis",
			"inverse": {
				"earlier": {"feature_id": "vomiting"},
				"later": {"tag": "pain"},
				"weight": 2,
				"direction": "weakens",
				"explanation": "Vomiting preceded pain weakens this diagnosis",
			},
			"status": PLACEHOLDER, "source": None,
		},
	],

	"display_override_rules": [
		{
			"predicate": {
				"and": [
					{"all_of": [{"feature_id": "right_lower_quadrant_pain"}]},
					{"any_of": [
						{"feature_id": "pain_migration"},
						{"feature_id": "vomiting"},
						{"feature_id": "peritonism"},
					]},
				]
			},
			"effect": "force_display",
			"value": "possible",
			"status": PLACEHOLDER, "source": None,
		},
	],

	"red_flags": [
		{
			"feature_id": "hypotension", "severity": "critical",
			"message": "hypotension is a red flag", "forces_min_state": None,
			"status": PLACEHOLDER, "source": None,
		},
		{
			"feature_id": "peritonism", "severity": "high",
			"message": "rigid or guarded abdomen is a red flag", "forces_min_state": None,
			"status": PLACEHOLDER, "source": None,
		},
	],

	"investigations": [
		{"name": "raised inflammatory markers", "tier": "first_line"},
		{"name": "neutrophil predominant leucocytosis", "tier": "first_line"},
		{"name": "ultrasound (children or females)", "tier": "first_line"},
		{"name": "CT if unclear", "tier": "second_line"},
	],

	"management": [
		{"step": "laparoscopic appendectomy", "condition": None},
		{"step": "antibiotics", "condition": None},
		{"step": "lavage", "condition": "if perforated"},
	],

	"state_thresholds": {"likely": 5, "possible": 2, "status": PLACEHOLDER, "source": None},
}
