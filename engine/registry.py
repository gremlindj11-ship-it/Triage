FEATURES = {
	"headache": {},
	"severe_headache": {},
	"mild_headache": {},
	"sudden_onset_headache": {},
	"gradual_onset_headache": {},
	"worst_headache_of_life": {},
	"thunderclap_headache": {},
	"sentinel_headache": {},
	"temporal_progression": {},
	"high_risk_progression": {},
	"neck_stiffness": {},
	"photophobia": {},
	"reduced_consciousness": {},
	"seizures": {},
	"vomiting": {},
	"sweating": {},
	"diarrhoea": {},
	"faint": {},
	"dizzy": {},
	"syncope": {},
	"no_pain": {},
	"diffuse_symptoms_without_localisation": {},
	"periumbilical_pain": {},
	"chest_pain": {},
	"epigastric_pain": {},
	"flank_pain": {},
	"rlq_pain": {},
	"right_lower_quadrant_pain": {},
	"llq_pain": {},
	"left_lower_quadrant_pain": {},
	"lower_abdominal_pain": {},
	"unilateral_pelvic_pain": {},
	"amenorrhea": {},
	"vaginal_bleeding": {},
	"shoulder_tip_pain": {},
	"male_sex": {},
	"pain_after_amenorrhea": {},
	"hemodynamic_instability": {},
	"pain_migration": {},
	"peritonism": {},
	"pain_before_vomiting": {},
	"vomiting_before_pain": {},
	"abdominal_pain": {},
	"hypotension": {},
}

PHRASES = {
	"rlq pain": "right_lower_quadrant_pain",
	"llq pain": "left_lower_quadrant_pain",
	"dizziness": "dizzy",
}

DIAGNOSES = {
	"appendicitis": {},
	"ectopic_pregnancy": {},
	"subarachnoid_haemorrhage": {},
	"nonspecific_abdominal_process": {},
}

SAFETY_DIAGNOSES = {
	"shock_state": {},
	"ruptured_abdominal_aortic_aneurysm": {},
}

QUESTIONS = {
	"pain_migration": "Did the pain migrate to the right lower quadrant?",
	"sudden_headache_peak": "Did the headache reach maximum intensity within seconds to minutes?",
}

TEMPORAL_PATTERNS = [
	{
		"marker_feature": "pain_migration",
		"earlier_feature": "periumbilical_pain",
		"later_feature": "right_lower_quadrant_pain",
		"earlier_phrases": ["periumbilical pain", "central abdominal pain"],
		"later_phrases": ["right lower quadrant pain", "rlq pain"],
		"connectors": ["then", "later", "before", "after", "moved", "migrated", "to"],
	},
	{
		"marker_feature": "pain_before_vomiting",
		"inverse_marker_feature": "vomiting_before_pain",
		"earlier_feature": "abdominal_pain",
		"later_feature": "vomiting",
		"earlier_phrases": ["stomach pain", "abdominal pain", "pain"],
		"later_phrases": ["vomiting"],
		"connectors": ["then", "later", "before", "after"],
	},
]
