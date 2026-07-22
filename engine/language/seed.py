from engine.language.library import register_condition


register_condition(
	"appendicitis",
	{
		"features": [
			"abdominal_pain",
			"periumbilical_pain",
			"right_lower_quadrant_pain",
			"vomiting",
			"anorexia",
			"fever",
			"pain_migration",
			"pain_before_vomiting",
			"peritonism",
			"hypotension",
		],
		"epidemiology": [
			"common age 10–20"
		],
		"pathophysiology": [
			"luminal obstruction (faecolith or lymphoid hyperplasia)",
			"bacterial invasion",
			"oedema leading to ischaemia and possible perforation"
		],
		"symptoms": [
			"abdominal pain",
			"peri-umbilical pain",
			"right lower quadrant pain",
			"vomiting (usually mild)",
			"anorexia",
			"fever 37.5–38"
		],
		"temporal": [
			"pain starts central then migrates to right lower quadrant",
			"pain precedes vomiting"
		],
		"exam": [
			"rebound tenderness",
			"guarding",
			"percussion tenderness",
			"rigidity (late)",
			"inability to hop (children)",
			"psoas sign (retrocaecal)"
		],
		"investigations": [
			"raised inflammatory markers",
			"neutrophil predominant leucocytosis",
			"ultrasound (children or females)",
			"CT if unclear"
		],
		"management": [
			"laparoscopic appendectomy",
			"antibiotics",
			"lavage if perforated"
		],
		"red_flags": [
			"hypotension",
			"rigid abdomen"
		],
		"notes": [
			"pain typically starts peri-umbilical then localises",
			"vomiting usually occurs after pain",
			"diarrhoea uncommon"
		]
	}
)


register_condition(
	"ectopic_pregnancy",
	{
		"features": [
			"lower_abdominal_pain",
			"unilateral_pelvic_pain",
			"amenorrhea",
			"vaginal_bleeding",
			"syncope",
			"shoulder_tip_pain",
			"pain_after_amenorrhea",
			"male_sex",
			"hemodynamic_instability",
		],
		"epidemiology": [],
		"pathophysiology": [],
		"symptoms": [
			"lower abdominal pain",
			"unilateral pelvic pain",
			"amenorrhea",
			"vaginal bleeding",
			"syncope",
			"shoulder tip pain",
		],
		"temporal": [],
		"exam": [],
		"investigations": [
			"pregnancy_test",
			"transvaginal_ultrasound",
		],
		"management": [],
		"red_flags": [
			"syncope",
			"hemodynamic instability",
		],
		"notes": [],
		"negatives": [
			"male",
		],
	}
)


register_condition(
	"subarachnoid_haemorrhage",
	{
		"features": [
			"headache",
			"severe_headache",
			"sudden_onset_headache",
			"thunderclap_headache",
			"vomiting",
			"neck_stiffness",
			"photophobia",
			"reduced_consciousness",
			"seizures",
			"sentinel_headache",
			"temporal_progression",
			"gradual_onset_headache",
			"mild_headache",
		],
		"epidemiology": [],
		"pathophysiology": [],
		"symptoms": [
			"thunderclap headache",
			"sudden onset headache",
			"worst headache of life",
			"severe headache",
			"vomiting",
			"neck stiffness",
			"photophobia",
			"reduced consciousness",
			"seizures",
			"sentinel headache",
		],
		"temporal": [
			"previous headache before sudden severe headache",
			"headache earlier then worst headache now",
		],
		"exam": [
			"neck stiffness",
			"reduced consciousness",
		],
		"investigations": [
			"urgent ct head",
			"lumbar puncture if ct negative and suspicion remains",
		],
		"management": [
			"urgent neurosurgical assessment",
			"blood pressure control",
		],
		"red_flags": [
			"thunderclap headache",
			"reduced consciousness",
			"seizures",
		],
		"notes": [
			"sudden severe headache is a medical emergency",
			"a prior warning headache may represent a sentinel bleed",
		],
		"negatives": [
			"gradual onset headache",
			"mild headache",
		],
	}
)


register_condition(
	"nonspecific_abdominal_process",
	{
		"features": [
			"abdominal_pain",
			"vomiting",
		],
		"epidemiology": [],
		"pathophysiology": [],
		"symptoms": [
			"abdominal pain",
			"vomiting"
		],
		"temporal": [],
		"exam": [],
		"investigations": [],
		"management": [],
		"red_flags": [],
		"notes": []
	}
)