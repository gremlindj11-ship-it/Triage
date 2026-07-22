from generic_engine.diseases.appendicitis import APPENDICITIS
from generic_engine.diseases.subarachnoid_haemorrhage import SUBARACHNOID_HAEMORRHAGE


DISEASES = {
	"appendicitis": APPENDICITIS,
	"subarachnoid_haemorrhage": SUBARACHNOID_HAEMORRHAGE,
}


def _referenced_feature_ids(disease: dict) -> set:
	referenced = set()

	for section in ("supporting_features", "contradicting_features", "required_features", "red_flags"):
		for entry in disease[section]:
			referenced.add(entry["feature_id"])

	for bonus in disease["relational_bonuses"]:
		if bonus.get("marker_feature"):
			referenced.add(bonus["marker_feature"])
		for candidate in (bonus, bonus.get("inverse") or {}):
			for ref in (candidate.get("earlier"), candidate.get("later")):
				if ref and "feature_id" in ref:
					referenced.add(ref["feature_id"])

	return referenced


def validate_diseases(diseases: dict, fact_registry: dict) -> None:
	errors = []

	for disease_id, disease in diseases.items():
		if disease["id"] != disease_id:
			errors.append(f"Disease key '{disease_id}' does not match its id '{disease['id']}'")

		for feature_id in _referenced_feature_ids(disease):
			if feature_id not in fact_registry:
				errors.append(f"'{disease_id}' references unknown fact '{feature_id}'")

	if errors:
		raise ValueError("; ".join(errors))
