from copy import deepcopy


LANGUAGE_SECTIONS = (
	"features",
	"epidemiology",
	"pathophysiology",
	"symptoms",
	"temporal",
	"exam",
	"investigations",
	"management",
	"red_flags",
	"notes",
)


LANGUAGE_LIBRARY = {}


def register_condition(name: str, data: dict):
	"""
	Stores a condition exactly as provided.
	No processing allowed.
	"""
	if name in LANGUAGE_LIBRARY:
		raise ValueError("Condition already exists")

	LANGUAGE_LIBRARY[name] = data


def get_condition(name: str):
	condition = LANGUAGE_LIBRARY.get(name)
	if condition is None:
		return None
	return deepcopy(condition)


def get_section(name: str, section: str):
	"""
	Returns a specific section (e.g. symptoms, red_flags)
	"""
	condition = LANGUAGE_LIBRARY.get(name)
	if not condition:
		return None
	section_data = condition.get(section)
	if section_data is None:
		return None
	return deepcopy(section_data)