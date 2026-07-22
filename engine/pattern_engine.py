from engine.patterns import PATTERN_DEFINITIONS


def evaluate_patterns(feature_ids: list[str]) -> list[dict]:
	results = []
	feature_id_set = set(feature_ids)

	for pattern in PATTERN_DEFINITIONS:
		score = 0
		matched = []

		if any(required_feature not in feature_id_set for required_feature in pattern.get("requires", [])):
			results.append(
				{
					"id": pattern["id"],
					"score": 0,
					"status": "not_met",
					"matched": [],
				}
			)
			continue

		for feature_id in pattern.get("strong_support", []):
			if feature_id in feature_id_set:
				score += 3
				matched.append(feature_id)

		for feature_id in pattern.get("support", []):
			if feature_id in feature_id_set:
				score += 1
				matched.append(feature_id)

		for feature_id in pattern.get("red_flags", []):
			if feature_id in feature_id_set:
				score += 2
				matched.append(feature_id)

		for feature_id in pattern.get("against", []):
			if feature_id in feature_id_set:
				score -= 2

		results.append(
			{
				"id": pattern["id"],
				"score": score,
				"status": "candidate",
				"matched": matched,
			}
		)

	return sorted(results, key=lambda result: result["score"], reverse=True)