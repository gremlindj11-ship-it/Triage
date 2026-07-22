from engine.diagnosis_definitions import DIAGNOSIS_DEFINITIONS


def score_diagnosis(features: list[str], context: dict) -> list[dict]:
	results = []
	feature_set = set(features)

	for diagnosis_id, config in DIAGNOSIS_DEFINITIONS.items():
		score = 0.0
		blocked = False

		for rule in config["blockers"]:
			if context.get(rule["context"]) == rule["value"]:
				blocked = True
				break

		if blocked:
			results.append(
				{
					"diagnosis": diagnosis_id,
					"score": 0,
					"state": "ruled_out",
				}
			)
			continue

		for feature_id in feature_set:
			score += config["evidence_weights"].get(feature_id, 0)

		for context_key, multiplier in config["context_modifiers"].items():
			if context.get(context_key):
				score *= multiplier

		max_possible = sum(config["evidence_weights"].values()) or 1
		confidence = min(score / max_possible, 1.0)

		if score >= 5:
			state = "likely"
		elif score >= 2:
			state = "possible"
		else:
			state = "unlikely"

		results.append(
			{
				"diagnosis": diagnosis_id,
				"score": score,
				"confidence": confidence,
				"state": state,
			}
		)

	return sorted(results, key=lambda item: item["score"], reverse=True)