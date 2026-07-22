from engine.language.library import LANGUAGE_LIBRARY
from engine.feature_registry import FEATURE_REGISTRY


def validate_language_alignment():
	missing = []
	registry_values = set(FEATURE_REGISTRY.values())

	for condition_id, condition in LANGUAGE_LIBRARY.items():
		for feature in condition.get("features", []):
			if feature not in registry_values:
				missing.append((condition_id, feature))

	if missing:
		raise ValueError(f"Missing features in registry: {missing}")