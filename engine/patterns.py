PATTERN_DEFINITIONS = [
	{
		"id": "appendicitis",
		"requires": ["right_lower_quadrant_pain"],
		"strong_support": ["pain_migration"],
		"support": ["nausea", "fever", "peritonism"],
		"against": ["vomiting_before_pain"],
	},
	{
		"id": "ectopic_pregnancy",
		"requires": [],
		"strong_support": ["amenorrhea", "vaginal_bleeding"],
		"support": ["lower_abdominal_pain"],
		"red_flags": ["shoulder_tip_pain", "syncope"],
	},
	{
		"id": "subarachnoid_haemorrhage",
		"requires": ["headache"],
		"strong_support": [
			"thunderclap_headache",
			"sudden_onset_headache",
			"worst_headache_of_life",
			"sentinel_headache",
		],
		"support": ["severe_headache", "vomiting", "neck_stiffness", "photophobia"],
		"red_flags": ["reduced_consciousness", "seizures"],
		"against": ["gradual_onset_headache", "mild_headache"],
	},
]