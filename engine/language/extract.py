from engine.language.library import get_condition


def extract_features(condition_name: str):
	"""
	Returns structured features for reasoning from language library.
	No scoring logic here, just selection.
	"""
	condition = get_condition(condition_name)
	if condition is None:
		return None

	symptoms = condition.get("symptoms", [])
	exam = condition.get("exam", [])
	temporal = condition.get("temporal", [])
	negatives = condition.get("negatives", [])
	red_flags = condition.get("red_flags", [])

	return {
		"symptoms": symptoms,
		"exam": exam,
		"temporal": temporal,
		"negatives": negatives,
		"red_flags": red_flags,
	}