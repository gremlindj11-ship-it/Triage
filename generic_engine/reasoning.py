from generic_engine.schema import SEVERITY_RANK, STATE_RANK


def _matches_ref(feature_id: str, ref: dict | None, fact_registry: dict) -> bool:
	if ref is None or feature_id is None:
		return False
	if "feature_id" in ref:
		return feature_id == ref["feature_id"]
	if "tag" in ref:
		return ref["tag"] in fact_registry.get(feature_id, {}).get("tags", [])
	return False


def _match_relational_bonus(bonus: dict, facts: set, relations: list, fact_registry: dict) -> tuple:
	if bonus["relation_type"] == "marker":
		if bonus["marker_feature"] in facts:
			return True, bonus["direction"], bonus["explanation"]
		return False, None, None

	if bonus["relation_type"] == "temporal_order":
		for relation in relations:
			if relation.get("type") != "temporal_order":
				continue
			first, second = relation.get("first"), relation.get("second")
			if _matches_ref(first, bonus["earlier"], fact_registry) and _matches_ref(second, bonus["later"], fact_registry):
				return True, bonus["direction"], bonus["explanation"]

		inverse = bonus.get("inverse")
		if inverse:
			for relation in relations:
				if relation.get("type") != "temporal_order":
					continue
				first, second = relation.get("first"), relation.get("second")
				if _matches_ref(first, inverse["earlier"], fact_registry) and _matches_ref(second, inverse["later"], fact_registry):
					return True, inverse["direction"], inverse["explanation"]

	return False, None, None


def _evaluate_predicate(predicate: dict, facts: set, context: dict) -> bool:
	if "all_of" in predicate:
		return all(ref["feature_id"] in facts for ref in predicate["all_of"])
	if "any_of" in predicate:
		return any(ref["feature_id"] in facts for ref in predicate["any_of"])
	if "and" in predicate:
		return all(_evaluate_predicate(p, facts, context) for p in predicate["and"])
	if "or" in predicate:
		return any(_evaluate_predicate(p, facts, context) for p in predicate["or"])
	if "not" in predicate:
		return not _evaluate_predicate(predicate["not"], facts, context)
	if "context_key" in predicate:
		value = context.get(predicate["context_key"]) if context else None
		operator = predicate["operator"]
		if operator == "==":
			return value == predicate["value"]
		if operator == "!=":
			return value != predicate["value"]
		if operator == "in":
			return value in predicate["value"]
		if operator == "is_true":
			return value is True
		if operator == "is_false":
			return value is False
	return False


def _classify_state(score: float, thresholds: dict) -> str:
	if score >= thresholds["likely"]:
		return "likely"
	if score >= thresholds["possible"]:
		return "possible"
	return "insufficient"


def _promote_state(state: str, min_state: str | None) -> str:
	if min_state is None:
		return state
	if STATE_RANK[min_state] > STATE_RANK[state]:
		return min_state
	return state


def evaluate(disease: dict, facts: set, context: dict, relations: list, fact_registry: dict) -> dict:
	if any(_evaluate_predicate(rule["predicate"], facts, context) for rule in disease["exclusion_rules"]):
		return {
			"id": disease["id"], "score": 0, "state": "ruled_out",
			"missing_required": [], "supporting_explanations": [], "contradicting_explanations": [],
			"triggered_red_flags": [],
		}

	score = sum(f["weight"] for f in disease["supporting_features"] if f["feature_id"] in facts)
	score -= sum(f["weight"] for f in disease["contradicting_features"] if f["feature_id"] in facts)

	supporting_explanations, contradicting_explanations = [], []
	for bonus in disease["relational_bonuses"]:
		matched, direction, explanation = _match_relational_bonus(bonus, facts, relations, fact_registry)
		if not matched:
			continue
		score += bonus["weight"] if direction == "supports" else -bonus["weight"]
		(supporting_explanations if direction == "supports" else contradicting_explanations).append(explanation)

	for feature in disease["supporting_features"]:
		if feature["feature_id"] in facts:
			label = fact_registry.get(feature["feature_id"], {}).get("display_label", feature["feature_id"])
			supporting_explanations.append(f"{label} supports this diagnosis")

	for feature in disease["contradicting_features"]:
		if feature["feature_id"] in facts:
			label = fact_registry.get(feature["feature_id"], {}).get("display_label", feature["feature_id"])
			contradicting_explanations.append(f"{label} weakens this diagnosis")

	missing_required = [f["feature_id"] for f in disease["required_features"] if f["feature_id"] not in facts]

	state = _classify_state(score, disease["state_thresholds"])

	triggered_red_flags = [rf for rf in disease["red_flags"] if rf["feature_id"] in facts]
	for red_flag in triggered_red_flags:
		state = _promote_state(state, red_flag["forces_min_state"])

	for rule in disease["display_override_rules"]:
		if rule["effect"] == "force_display" and _evaluate_predicate(rule["predicate"], facts, context):
			state = _promote_state(state, rule["value"])

	return {
		"id": disease["id"], "score": score, "state": state,
		"missing_required": missing_required,
		"supporting_explanations": supporting_explanations,
		"contradicting_explanations": contradicting_explanations,
		"triggered_red_flags": triggered_red_flags,
	}


def evaluate_all(diseases: dict, facts: set, context: dict | None = None, relations: list | None = None,
				  fact_registry: dict | None = None) -> list:
	context = context or {}
	relations = relations or []
	fact_registry = fact_registry or {}
	results = [evaluate(disease, facts, context, relations, fact_registry) for disease in diseases.values()]
	return sorted(results, key=lambda result: result["score"], reverse=True)


def _signed_relevance(disease: dict, feature_id: str) -> float:
	for feature in disease["supporting_features"]:
		if feature["feature_id"] == feature_id:
			return feature["weight"]
	for feature in disease["contradicting_features"]:
		if feature["feature_id"] == feature_id:
			return -feature["weight"]
	for red_flag in disease["red_flags"]:
		if red_flag["feature_id"] == feature_id:
			return SEVERITY_RANK[red_flag["severity"]]
	return 0.0


def _candidate_fact_ids(diseases: dict, disease_ids: list, known_facts: set) -> list:
	candidates = set()
	for disease_id in disease_ids:
		disease = diseases[disease_id]
		for section in ("supporting_features", "contradicting_features", "required_features", "red_flags"):
			for entry in disease[section]:
				candidates.add(entry["feature_id"])
	return sorted(candidates - known_facts)


def _variance(values: list) -> float:
	mean = sum(values) / len(values)
	return sum((value - mean) ** 2 for value in values) / len(values)


def rank_next_questions(active_results: list, diseases: dict, known_facts: set, fact_registry: dict) -> list:
	live_disease_ids = [result["id"] for result in active_results
						 if result["state"] != "ruled_out" and result["score"] > 0]

	if len(live_disease_ids) < 2:
		disease_ids = [result["id"] for result in active_results if result["state"] != "ruled_out"]
		candidate_ids = _candidate_fact_ids(diseases, disease_ids, known_facts)
		return [dict(fact_registry[fid], id=fid) for fid in candidate_ids if fact_registry.get(fid, {}).get("question_text")]

	candidate_ids = _candidate_fact_ids(diseases, live_disease_ids, known_facts)
	scored = []
	for feature_id in candidate_ids:
		if not fact_registry.get(feature_id, {}).get("question_text"):
			continue
		relevances = [_signed_relevance(diseases[disease_id], feature_id) for disease_id in live_disease_ids]
		scored.append((_variance(relevances), feature_id))

	scored.sort(key=lambda pair: (-pair[0], pair[1]))
	return [dict(fact_registry[fid], id=fid) for _, fid in scored]


def build_next_question(active_results: list, diseases: dict, known_facts: set, fact_registry: dict) -> dict | None:
	for result in active_results:
		if result["state"] == "ruled_out":
			continue
		urgent_flags = [rf for rf in result["triggered_red_flags"] if rf["severity"] in ("critical", "high")]
		if urgent_flags:
			flag = max(urgent_flags, key=lambda rf: SEVERITY_RANK[rf["severity"]])
			return {
				"text": f'Is the patient stable? ({flag["message"]})',
				"reason": "Safety concerns take priority over further differential-narrowing questions.",
				"short_circuited": True,
				"source_disease": result["id"],
			}

	ranked = rank_next_questions(active_results, diseases, known_facts, fact_registry)
	if not ranked:
		return None

	top = ranked[0]
	return {
		"text": top["question_text"],
		"reason": "Ranked by discriminative value across the active differential.",
		"short_circuited": False,
		"source_fact": top["id"],
	}
