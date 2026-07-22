from typing import Optional


_FEATURE_REGISTRY_ITEMS = [
	("headache", "headache"),
	("severe headache", "severe_headache"),
	("mild headache", "mild_headache"),
	("sudden onset headache", "sudden_onset_headache"),
	("gradual onset headache", "gradual_onset_headache"),
	("worst headache", "thunderclap_headache"),
	("worst headache of life", "thunderclap_headache"),
	("worst headache of my life", "thunderclap_headache"),
	("thunderclap headache", "thunderclap_headache"),
	("sudden severe headache", "thunderclap_headache"),
	("explosive headache", "thunderclap_headache"),
	("hit like a baseball bat headache", "thunderclap_headache"),
	("sentinel headache", "sentinel_headache"),
	("temporal progression", "temporal_progression"),
	("neck stiffness", "neck_stiffness"),
	("stiff neck", "neck_stiffness"),
	("photophobia", "photophobia"),
	("reduced consciousness", "reduced_consciousness"),
	("reduced conscious level", "reduced_consciousness"),
	("seizure", "seizures"),
	("seizures", "seizures"),
	("abdominal pain", "abdominal_pain"),
	("abdomen pain", "abdominal_pain"),
	("chest pain", "chest_pain"),
	("epigastric pain", "epigastric_pain"),
	("flank pain", "flank_pain"),
	("lower abdominal pain", "lower_abdominal_pain"),
	("unilateral pelvic pain", "unilateral_pelvic_pain"),
	("left lower quadrant pain", "left_lower_quadrant_pain"),
	("llq pain", "left_lower_quadrant_pain"),
	("right lower quadrant pain", "right_lower_quadrant_pain"),
	("rlq pain", "right_lower_quadrant_pain"),
	("vomiting", "vomiting"),
	("nausea", "nausea"),
	("sweating", "sweating"),
	("sweaty", "sweating"),
	("diaphoresis", "sweating"),
	("amenorrhea", "amenorrhea"),
	("amenorrhoea", "amenorrhea"),
	("missed period", "amenorrhea"),
	("missed my period", "amenorrhea"),
	("late period", "amenorrhea"),
	("period is late", "amenorrhea"),
	("pain after amenorrhea", "pain_after_amenorrhea"),
	("pain after missed period", "pain_after_amenorrhea"),
	("vaginal bleeding", "vaginal_bleeding"),
	("bleeding", "vaginal_bleeding"),
	("spotting", "vaginal_bleeding"),
	("diarrhoea", "diarrhoea"),
	("no pain", "no_pain"),
	("diffuse symptoms without localisation", "diffuse_symptoms_without_localisation"),
	("feels faint", "faint"),
	("syncope", "syncope"),
	("fainted", "syncope"),
	("passed out", "syncope"),
	("collapse", "hemodynamic_instability"),
	("shock", "hemodynamic_instability"),
	("hemodynamic instability", "hemodynamic_instability"),
	("lightheaded", "faint"),
	("dizzy", "dizzy"),
	("dizziness", "dizzy"),
	("shoulder tip pain", "shoulder_tip_pain"),
	("male", "male_sex"),
	("low blood pressure", "hypotension"),
	("bp 80/50", "hypotension"),
	("blood pressure 80/50", "hypotension"),
	("periumbilical pain", "periumbilical_pain"),
	("central abdominal pain", "periumbilical_pain"),
	("pain migration", "pain_migration"),
	("pain moved", "pain_migration"),
	("pain moved to", "pain_migration"),
	("moved to right side", "pain_migration"),
	("started near belly button then moved", "pain_migration"),
	("pain started near belly button then moved", "pain_migration"),
	("feel sick", "vomiting"),
	("feeling sick", "vomiting"),
	("right side pain", "right_lower_quadrant_pain"),
	("pain in right side", "right_lower_quadrant_pain"),
	("pain on right side", "right_lower_quadrant_pain"),
	("right side", "right_lower_quadrant_pain"),
	("pain before vomiting", "pain_before_vomiting"),
	("vomiting before pain", "vomiting_before_pain"),
	("pain worse on coughing", "peritonism"),
	("guarding", "peritonism"),
	("rigidity", "peritonism"),
	("rebound tenderness", "peritonism"),
	("loss of appetite", "anorexia"),
	("fever", "fever"),
	("temperature", "fever"),
	("anorexia", "anorexia"),
]


def _validate_registry():
	keys = [key for key, _ in _FEATURE_REGISTRY_ITEMS]
	if len(keys) != len(set(keys)):
		duplicate_keys = sorted({key for key in keys if keys.count(key) > 1})
		raise ValueError(f"Duplicate keys detected in FEATURE_REGISTRY: {duplicate_keys}")


_validate_registry()


FEATURE_REGISTRY = dict(_FEATURE_REGISTRY_ITEMS)
FEATURE_VOCAB = FEATURE_REGISTRY


def map_phrase_to_feature(phrase: str) -> Optional[str]:
	return FEATURE_REGISTRY.get(phrase.strip().lower())