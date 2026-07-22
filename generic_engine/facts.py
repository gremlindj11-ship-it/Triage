from generic_engine.schema import PLACEHOLDER


def _fact(display_label: str, tags: list[str] | None = None, question_text: str | None = None) -> dict:
	return {
		"display_label": display_label,
		"tags": tags or [],
		"question_text": question_text,
		"question_status": PLACEHOLDER,
		"question_source": None,
	}


FACT_REGISTRY = {
	"headache": _fact("headache", question_text="Can you describe the main symptom?"),
	"abdominal_pain": _fact("abdominal pain", tags=["pain"], question_text="Is there any abdominal pain?"),
	"right_lower_quadrant_pain": _fact(
		"right lower quadrant pain", tags=["pain"],
		question_text="Did the pain migrate to the right lower quadrant?",
	),
	"peritonism": _fact("peritonism", question_text="Is the abdomen rigid or guarded on examination?"),
	"vomiting": _fact("vomiting", question_text="Are you feeling nauseated or vomiting?"),
	"diarrhoea": _fact("diarrhoea", question_text="Have you had any diarrhoea?"),
	"no_pain": _fact("no pain"),
	"diffuse_symptoms_without_localisation": _fact("diffuse, non-localised symptoms"),
	"pain_migration": _fact(
		"pain migration", tags=["temporal"],
		question_text="Did the pain start elsewhere and move to a different location?",
	),
	"thunderclap_headache": _fact(
		"thunderclap headache", tags=["headache"],
		question_text="Did the headache reach maximum intensity within seconds to minutes?",
	),
	"sudden_onset_headache": _fact(
		"sudden onset headache", tags=["headache"],
		question_text="Did the headache start suddenly or build gradually?",
	),
	"worst_headache_of_life": _fact(
		"worst headache of life", tags=["headache"],
		question_text="Is this the worst headache you have ever had?",
	),
	"severe_headache": _fact(
		"severe headache", tags=["headache"],
		question_text="How severe is the headache right now?",
	),
	"gradual_onset_headache": _fact("gradual onset headache", tags=["headache"]),
	"mild_headache": _fact("mild headache", tags=["headache"]),
	"neck_stiffness": _fact(
		"neck stiffness", tags=["headache"],
		question_text="Do you have neck stiffness or sensitivity to light?",
	),
	"photophobia": _fact(
		"photophobia", tags=["headache"],
		question_text="Do you have neck stiffness or sensitivity to light?",
	),
	"reduced_consciousness": _fact(
		"reduced consciousness", tags=["headache"],
		question_text="Is the patient fully alert and responsive right now?",
	),
	"seizures": _fact(
		"seizures", tags=["headache"],
		question_text="Has there been any seizure activity?",
	),
	"sentinel_headache": _fact(
		"sentinel headache", tags=["headache"],
		question_text="Was there an earlier, milder headache before this one?",
	),
	"hypotension": _fact("hypotension", question_text="Is the patient haemodynamically stable?"),
}
