
import re

from engine.language.extract import extract_features
from engine.language.library import get_section
from engine.feature_registry import map_phrase_to_feature
from engine.registry import DIAGNOSES, FEATURES, SAFETY_DIAGNOSES, TEMPORAL_PATTERNS


_FEATURE_WEIGHT_VALUES = {
	"weak": 1,
	"strong": 2,
}


_MIN_EXPECTED_SCORE = 4


_QUESTION_PRIORITY_SCORES = {
	"haemodynamic_stability": 100,
	"headache_onset": 98,
	"headache_severity": 97,
	"headache_associated_features": 96,
	"pattern_bleeding_clarification": 99,
	"pregnancy_clarification": 95,
	"nausea_vomiting_clarification": 94,
	"fever_clarification": 93,
	"bleeding_clarification": 92,
	"pain_location": 90,
	"pain_migration": 85,
	"presence_of_pain": 80,
	"symptom_sequence": 75,
	"onset_pattern": 60,
	"generic_clarification": 50,
}


_GENERIC_FEATURE_FLOOR = 0.5
_STRONG_SIGNAL_VALUE = float(_FEATURE_WEIGHT_VALUES["strong"])


_APPENDICITIS_ORDER_SUPPORT_TEXT = "Pain preceded vomiting (supports appendicitis pattern)"
_APPENDICITIS_ORDER_AGAINST_TEXT = "Vomiting preceded pain (less typical for appendicitis)"


_BASE_RED_FLAG_RULES = [
	{
		"feature": "hypotension",
		"message": "hypotension is a red flag",
		"severity": "critical",
		"action": "hemodynamic_assessment",
		"safety_diagnoses": ["shock_state", "ruptured_abdominal_aortic_aneurysm"],
	},
	{
		"feature": "faint",
		"message": "possible haemodynamic instability",
		"severity": "high",
		"action": "prioritise",
		"safety_diagnoses": [],
	},
	{
		"feature": "dizzy",
		"message": "possible haemodynamic instability",
		"severity": "high",
		"action": "prioritise",
		"safety_diagnoses": [],
	}
]


_DIAGNOSIS_SCORE_CONFIG = {
	"appendicitis": {
		"feature_weights": {
			"abdominal_pain": "weak",
			"vomiting": "weak",
			"right_lower_quadrant_pain": "strong",
			"peritonism": "strong",
		},
		"contradiction_weights": {
			"diarrhoea": 1,
			"no_pain": 1,
			"diffuse_symptoms_without_localisation": 1,
		},
		"expected_features": ["right_lower_quadrant_pain"],
		"registry_priority": 1,
		"temporal_bonus_rules": [
			{
				"marker_feature": "pain_migration",
				"weight": 3,
				"explanation": "pain migration supports this diagnosis",
			},
			{
				"marker_feature": "pain_before_vomiting",
				"earlier_feature": "abdominal_pain",
				"later_feature": "vomiting",
				"weight": 2,
				"explanation": "pain before vomiting supports this diagnosis",
				"inverse_marker_feature": "vomiting_before_pain",
				"inverse_explanation": "vomiting before pain weakens this diagnosis",
			}
		],
	},
	"ectopic_pregnancy": {
		"base_weight": 1.0,
		"feature_weights": {
			"lower_abdominal_pain": "weak",
			"unilateral_pelvic_pain": "strong",
			"amenorrhea": "strong",
			"vaginal_bleeding": "strong",
			"syncope": "strong",
			"shoulder_tip_pain": "strong",
		},
		"contradiction_weights": {
			"male_sex": 2,
		},
		"expected_features": [],
		"registry_priority": 1,
		"temporal_bonus_rules": [],
	},
	"nonspecific_abdominal_process": {
		"feature_weights": {
			"abdominal_pain": "weak",
			"vomiting": "weak",
		},
		"contradiction_weights": {},
		"expected_features": ["abdominal_pain"],
		"registry_priority": 2,
		"temporal_bonus_rules": [],
	},
}

_VALIDATED_RULES = False


def _normalize_language_text(text: str) -> str:
	normalized_text = text.lower().strip()
	normalized_text = re.sub(r"\s*\([^)]*\)", "", normalized_text)
	normalized_text = normalized_text.replace("–", "-")
	normalized_text = re.sub(r"[^a-z0-9\s-]", "", normalized_text)
	return re.sub(r"\s+", " ", normalized_text).strip()


def _language_text_to_feature_id(text: str) -> str | None:
	normalized_text = _normalize_language_text(text)
	if normalized_text in FEATURES:
		return normalized_text
	feature_id = map_phrase_to_feature(normalized_text)
	if feature_id is None:
		feature_id = normalized_text.replace("-", "_").replace(" ", "_")
	if feature_id in FEATURES:
		return feature_id
	return None


def _extract_feature_ids(entries: list[str]) -> list[str]:
	feature_ids = []
	seen_feature_ids = set()

	for entry in entries:
		feature_id = _language_text_to_feature_id(entry)
		if feature_id is None or feature_id in seen_feature_ids:
			continue
		feature_ids.append(feature_id)
		seen_feature_ids.add(feature_id)

	return feature_ids


def _get_temporal_pattern(earlier_feature: str, later_feature: str) -> dict | None:
	for temporal_pattern in TEMPORAL_PATTERNS:
		if (
			temporal_pattern["earlier_feature"] == earlier_feature
			and temporal_pattern["later_feature"] == later_feature
		):
			return temporal_pattern
	return None


def _matches_temporal_description(entry: str, earlier_feature: str, later_feature: str) -> bool:
	temporal_pattern = _get_temporal_pattern(earlier_feature, later_feature)
	if temporal_pattern is None:
		return False

	normalized_entry = _normalize_language_text(entry)
	has_earlier_phrase = any(
		_normalize_language_text(phrase) in normalized_entry
		for phrase in temporal_pattern["earlier_phrases"]
	)
	has_later_phrase = any(
		_normalize_language_text(phrase) in normalized_entry
		for phrase in temporal_pattern["later_phrases"]
	)

	if not has_earlier_phrase or not has_later_phrase:
		return False

	if any(keyword in normalized_entry for keyword in ["before", "precedes", "precede", "preceded", "then", "later"]):
		return True

	return True


def _build_temporal_rules(temporal_entries: list[str], temporal_bonus_rules: list[dict]) -> list[dict]:
	return [
		temporal_rule
		for temporal_rule in temporal_bonus_rules
		if (
			"marker_feature" in temporal_rule and "earlier_feature" not in temporal_rule
		)
		or any(
			_matches_temporal_description(
				temporal_entry,
				temporal_rule["earlier_feature"],
				temporal_rule["later_feature"],
			)
			for temporal_entry in temporal_entries
		)
	]


def _build_diagnosis_rule(diagnosis_id: str) -> dict:
	data = extract_features(diagnosis_id)
	if data is None:
		raise ValueError(f"No language data registered for diagnosis '{diagnosis_id}'")

	scoring_config = _DIAGNOSIS_SCORE_CONFIG[diagnosis_id]
	supporting_feature_ids = _extract_feature_ids(data["symptoms"] + data["exam"])
	compatibility_features = [
		{
			"feature_id": feature_id,
			"feature_weight": scoring_config["feature_weights"][feature_id],
		}
		for feature_id in supporting_feature_ids
		if feature_id in scoring_config["feature_weights"]
	]

	return {
		"compatibility_features": compatibility_features,
		"expected_features": scoring_config["expected_features"],
		"contradiction_features": [
			{
				"feature_id": feature_id,
				"weight": scoring_config["contradiction_weights"][feature_id],
			}
			for feature_id in scoring_config["contradiction_weights"]
		],
		"red_flag_features": _extract_feature_ids(data["red_flags"]),
		"registry_priority": scoring_config["registry_priority"],
		"temporal_rules": _build_temporal_rules(data["temporal"], scoring_config["temporal_bonus_rules"]),
	}


def _get_diagnosis_rules() -> dict:
	return {
		diagnosis_id: _build_diagnosis_rule(diagnosis_id)
		for diagnosis_id in _DIAGNOSIS_SCORE_CONFIG
	}


def _default_red_flag_rule(feature_id: str) -> dict:
	return {
		"feature": feature_id,
		"message": f'{feature_id.replace("_", " ")} is a red flag',
		"severity": "warning",
		"action": "prioritise",
		"safety_diagnoses": [],
	}


def _get_red_flag_rules() -> list[dict]:
	red_flag_rules = {
		red_flag_rule["feature"]: dict(red_flag_rule)
		for red_flag_rule in _BASE_RED_FLAG_RULES
	}

	for diagnosis_rule in _get_diagnosis_rules().values():
		for feature_id in diagnosis_rule["red_flag_features"]:
			red_flag_rules.setdefault(feature_id, _default_red_flag_rule(feature_id))

	return list(red_flag_rules.values())


def _validate_diagnosis_rules() -> None:
	global _VALIDATED_RULES
	if _VALIDATED_RULES:
		return

	known_feature_ids = set(FEATURES)
	validation_errors = []
	diagnosis_rules = _get_diagnosis_rules()

	for diagnosis_id, rule in diagnosis_rules.items():
		if diagnosis_id not in DIAGNOSES:
			validation_errors.append(f"Unknown diagnosis rule: {diagnosis_id}")

		for compatibility_feature in rule["compatibility_features"]:
			feature_id = compatibility_feature["feature_id"]
			feature_weight = compatibility_feature["feature_weight"]
			if feature_id not in known_feature_ids:
				validation_errors.append(
					f"Unknown feature '{feature_id}' referenced in {diagnosis_id}.compatibility_features"
				)
			if feature_weight not in _FEATURE_WEIGHT_VALUES:
				validation_errors.append(
					f"Unknown feature weight '{feature_weight}' referenced in {diagnosis_id}.compatibility_features"
				)

		for field_name in ["expected_features", "red_flag_features"]:
			for feature_id in rule[field_name]:
				if feature_id not in known_feature_ids:
					validation_errors.append(
						f"Unknown feature '{feature_id}' referenced in {diagnosis_id}.{field_name}"
					)

		for contradiction_feature in rule["contradiction_features"]:
			feature_id = contradiction_feature["feature_id"]
			if feature_id not in known_feature_ids:
				validation_errors.append(
					f"Unknown feature '{feature_id}' referenced in {diagnosis_id}.contradiction_features"
				)

		for temporal_rule in rule["temporal_rules"]:
			for field_name in ["marker_feature", "inverse_marker_feature", "earlier_feature", "later_feature"]:
				feature_id = temporal_rule.get(field_name)
				if feature_id is None:
					continue
				if feature_id not in known_feature_ids:
					validation_errors.append(
						f"Unknown feature '{feature_id}' referenced in {diagnosis_id}.temporal_rules"
					)

	for red_flag_rule in _get_red_flag_rules():
		if red_flag_rule["feature"] not in known_feature_ids:
			validation_errors.append(
				f"Unknown feature '{red_flag_rule['feature']}' referenced in red flag rules"
			)
		if red_flag_rule["severity"] not in {"critical", "high", "warning"}:
			validation_errors.append(
				f"Unknown red flag severity '{red_flag_rule['severity']}' referenced in red flag rules"
			)
		for diagnosis_id in red_flag_rule["safety_diagnoses"]:
			if diagnosis_id not in SAFETY_DIAGNOSES:
				validation_errors.append(
					f"Unknown safety diagnosis '{diagnosis_id}' referenced in red flag rules"
				)

	if validation_errors:
		raise ValueError("; ".join(validation_errors))

	_VALIDATED_RULES = True


def _collect_supporting_features(rule: dict, present_feature_set: set) -> list:
	return [
		compatibility_feature["feature_id"]
		for feature_id in rule["compatibility_features"]
		for compatibility_feature in [feature_id]
		if compatibility_feature["feature_id"] in present_feature_set
	]


def _collect_signal_breakdown_supporting(rule: dict, present_feature_set: set) -> list:
	return [
		{
			"feature_id": compatibility_feature["feature_id"],
			"type": "supporting",
			"strength": compatibility_feature["feature_weight"],
		}
		for compatibility_feature in rule["compatibility_features"]
		if compatibility_feature["feature_id"] in present_feature_set
	]


def _collect_contradiction_signals(rule: dict, present_feature_set: set) -> list:
	return [
		{
			"feature": contradiction_feature["feature_id"],
			"strength": "contradiction",
			"kind": "contradiction",
		}
		for contradiction_feature in rule["contradiction_features"]
		if contradiction_feature["feature_id"] in present_feature_set
	]


def _collect_signal_breakdown_contradictions(rule: dict, present_feature_set: set) -> list:
	return [
		{
			"feature_id": contradiction_feature["feature_id"],
			"type": "contradiction",
			"strength": "strong",
		}
		for contradiction_feature in rule["contradiction_features"]
		if contradiction_feature["feature_id"] in present_feature_set
	]


def _get_feature_condition_frequency(feature_id: str) -> int:
	frequency = 0
	for diagnosis_rule in _get_diagnosis_rules().values():
		if any(
			compatibility_feature["feature_id"] == feature_id
			for compatibility_feature in diagnosis_rule["compatibility_features"]
		):
			frequency += 1
	return max(frequency, 1)


def _get_feature_signal_weight(compatibility_feature: dict) -> float:
	base_weight = _FEATURE_WEIGHT_VALUES[compatibility_feature["feature_weight"]]
	frequency = _get_feature_condition_frequency(compatibility_feature["feature_id"])
	if frequency <= 1:
		return float(base_weight)
	return max(base_weight / frequency, _GENERIC_FEATURE_FLOOR)


def _get_max_signal_score(rule: dict) -> int:
	return sum(
		_get_feature_signal_weight(compatibility_feature)
		for compatibility_feature in rule["compatibility_features"]
	)


def _weighted_support_score(rule: dict, present_feature_set: set) -> float:
	return sum(
		_get_feature_signal_weight(compatibility_feature)
		for compatibility_feature in rule["compatibility_features"]
		if compatibility_feature["feature_id"] in present_feature_set
	)


def _collect_missing_expected_features(rule: dict, present_feature_set: set) -> list:
	return [
		feature_id
		for feature_id in rule["expected_features"]
		if feature_id not in present_feature_set
	]


def _get_contradiction_penalty(rule: dict, present_feature_set: set) -> int:
	return sum(
		contradiction_feature["weight"]
		for contradiction_feature in rule["contradiction_features"]
		if contradiction_feature["feature_id"] in present_feature_set
	)


def _get_temporal_marker_features(earlier_feature: str, later_feature: str) -> tuple[str | None, str | None]:
	for temporal_pattern in TEMPORAL_PATTERNS:
		if (
			temporal_pattern["earlier_feature"] == earlier_feature
			and temporal_pattern["later_feature"] == later_feature
		):
			return (
				temporal_pattern["marker_feature"],
				temporal_pattern.get("inverse_marker_feature"),
			)

	return None, None


def _get_max_temporal_signal_bonus(rule: dict) -> int:
	return sum(max(0, temporal_rule["weight"]) for temporal_rule in rule["temporal_rules"])


def _apply_temporal_signal_rules(rule: dict, present_feature_set: set, diagnosis_signal_score: float) -> tuple[float, list[str], list[dict]]:
	updated_score = diagnosis_signal_score
	temporal_explanations = []
	temporal_signal_breakdown = []

	for temporal_rule in rule["temporal_rules"]:
		marker_feature = temporal_rule.get("marker_feature")
		inverse_marker_feature = temporal_rule.get("inverse_marker_feature")

		if marker_feature is None and "earlier_feature" in temporal_rule and "later_feature" in temporal_rule:
			marker_feature, inverse_marker_feature = _get_temporal_marker_features(
				temporal_rule["earlier_feature"], temporal_rule["later_feature"]
			)

		if marker_feature and marker_feature in present_feature_set:
			updated_score += temporal_rule["weight"]
			temporal_explanations.append(temporal_rule["explanation"])
			temporal_signal_breakdown.append(
				{
					"feature_id": marker_feature,
					"type": "temporal",
					"strength": "modifier",
				}
			)
		elif inverse_marker_feature and inverse_marker_feature in present_feature_set:
			updated_score = max(0, updated_score - temporal_rule["weight"])
			inverse_explanation = temporal_rule.get(
				"inverse_explanation",
				f'{temporal_rule["later_feature"].replace("_", " ")} before '
				f'{temporal_rule["earlier_feature"].replace("_", " ")} weakens this diagnosis'
			)
			temporal_explanations.append(inverse_explanation)
			temporal_signal_breakdown.append(
				{
					"feature_id": inverse_marker_feature,
					"type": "temporal",
					"strength": "modifier",
				}
			)

	return updated_score, temporal_explanations, temporal_signal_breakdown


def _get_pattern_strength(normalized_signal_score: float) -> str:
	if normalized_signal_score <= 0.25:
		return "weak"
	if normalized_signal_score <= 0.5:
		return "moderate"
	return "strong"


def _get_evidence_level(supporting_feature_count: int, normalized_signal_score: float) -> str:
	if supporting_feature_count < 2:
		return "insufficient"
	if normalized_signal_score <= 0.5:
		return "partial"
	return "strong"


def _get_context_adjusted_feature_set(diagnosis_id: str, present_feature_set: set, context: dict | None) -> set:
	effective_feature_set = set(present_feature_set)
	if diagnosis_id == "ectopic_pregnancy" and context and context.get("sex") == "male":
		effective_feature_set.add("male_sex")
	return effective_feature_set


def _get_context_signal_adjustments(diagnosis_id: str, context: dict | None) -> tuple[float, float, list[dict], float]:
	if diagnosis_id != "ectopic_pregnancy" or context is None:
		return 0.0, 0.0, [], 0.0

	support_bonus = 0.0
	contradiction_penalty = 0.0
	context_signal_breakdown = []
	max_signal_bonus = 0.0

	if context.get("pregnancy_possible") is True:
		support_bonus += _STRONG_SIGNAL_VALUE
		max_signal_bonus += _STRONG_SIGNAL_VALUE
		context_signal_breakdown.append(
			{
				"feature_id": "pregnancy_context",
				"type": "supporting",
				"strength": "strong",
			}
		)

	if context.get("sex") == "male":
		contradiction_penalty += float(_FEATURE_WEIGHT_VALUES["weak"])

	return support_bonus, contradiction_penalty, context_signal_breakdown, max_signal_bonus


def _is_pain_order_feature(feature_id: str) -> bool:
	return feature_id == "pain" or feature_id.endswith("_pain")


def _get_order_reasoning_signal_breakdown(diagnosis_id: str, context: dict | None) -> list[dict]:
	if diagnosis_id != "appendicitis" or context is None:
		return []

	relations = context.get("relations") or []
	order_signals = []
	seen_labels = set()

	for relation in relations:
		if relation.get("type") != "temporal_order":
			continue

		first = relation.get("first")
		second = relation.get("second")
		if not first or not second:
			continue

		if _is_pain_order_feature(first) and second == "vomiting":
			label = _APPENDICITIS_ORDER_SUPPORT_TEXT
			signal_type = "supporting"
		elif first == "vomiting" and _is_pain_order_feature(second):
			label = _APPENDICITIS_ORDER_AGAINST_TEXT
			signal_type = "contradiction"
		else:
			continue

		if label in seen_labels:
			continue

		order_signals.append(
			{
				"feature_id": "temporal_order",
				"type": signal_type,
				"strength": "modifier",
				"label": label,
			}
		)
		seen_labels.add(label)

	return order_signals


def _build_diagnosis_snapshot(diagnosis_id: str, rule: dict, present_feature_set: set, context: dict | None = None) -> dict:
	effective_feature_set = _get_context_adjusted_feature_set(diagnosis_id, present_feature_set, context)
	supporting_features = _collect_supporting_features(rule, effective_feature_set)
	supporting_feature_count = len(supporting_features)
	signal_breakdown = _collect_signal_breakdown_supporting(rule, effective_feature_set)
	signal_breakdown.extend(_collect_signal_breakdown_contradictions(rule, effective_feature_set))
	missing_expected_features = _collect_missing_expected_features(rule, effective_feature_set)
	base_signal_score = _weighted_support_score(rule, effective_feature_set)
	context_support_bonus, context_contradiction_penalty, context_signal_breakdown, context_max_signal_bonus = _get_context_signal_adjustments(
		diagnosis_id,
		context,
	)
	order_signal_breakdown = _get_order_reasoning_signal_breakdown(diagnosis_id, context)
	base_signal_score += context_support_bonus
	diagnosis_signal_score, temporal_explanations, temporal_signal_breakdown = _apply_temporal_signal_rules(
		rule, effective_feature_set, base_signal_score
	)
	diagnosis_signal_score = max(
		0,
		diagnosis_signal_score - _get_contradiction_penalty(rule, effective_feature_set) - context_contradiction_penalty,
	)
	max_signal_score = _get_max_signal_score(rule) + _get_max_temporal_signal_bonus(rule) + context_max_signal_bonus
	effective_max_score = max(max_signal_score, _MIN_EXPECTED_SCORE)
	diagnosis_signal_normalized = diagnosis_signal_score / effective_max_score if effective_max_score > 0 else 0.0
	raw_support_score = supporting_feature_count
	adjusted_score = max(0, diagnosis_signal_score - len(missing_expected_features))
	contradiction_score = sum(
		1 for contradiction_feature in rule["contradiction_features"] if contradiction_feature["feature_id"] in effective_feature_set
	)

	return {
		"id": diagnosis_id,
		"raw_support_score": raw_support_score,
		"adjusted_score": adjusted_score,
		"compatibility_score": adjusted_score,
		"contradiction_score": contradiction_score,
		"supporting_features": supporting_features,
		"supporting_feature_count": supporting_feature_count,
		"diagnosis_signal_score": diagnosis_signal_score,
		"diagnosis_signal_normalized": diagnosis_signal_normalized,
		"max_signal_score": max_signal_score,
		"signal_breakdown": signal_breakdown + context_signal_breakdown + temporal_signal_breakdown + order_signal_breakdown,
		"missing_expected_features": missing_expected_features,
		"temporal_explanations": temporal_explanations,
		"registry_priority": rule["registry_priority"],
	}


def _build_ranked_diagnoses(present_feature_set: set, context: dict | None = None) -> list:
	ranked_diagnoses = []
	for diagnosis_id, rule in _get_diagnosis_rules().items():
		if diagnosis_id not in DIAGNOSES:
			continue
		ranked_diagnoses.append(_build_diagnosis_snapshot(diagnosis_id, rule, present_feature_set, context))
	return ranked_diagnoses


def _score_summary(ranked_diagnoses: list) -> dict:
	highest_raw_support_score = max(
		(diagnosis["raw_support_score"] for diagnosis in ranked_diagnoses), default=0
	)
	highest_adjusted_score = max(
		(diagnosis["adjusted_score"] for diagnosis in ranked_diagnoses), default=0
	)
	raw_top_candidates = [
		diagnosis
		for diagnosis in ranked_diagnoses
		if diagnosis["raw_support_score"] == highest_raw_support_score
	]
	adjusted_top_candidates = [
		diagnosis
		for diagnosis in ranked_diagnoses
		if diagnosis["adjusted_score"] == highest_adjusted_score
	]
	low_evidence_tie = highest_adjusted_score == 1 and len(adjusted_top_candidates) > 1
	registry_priority_enabled = highest_adjusted_score > 1 and not low_evidence_tie

	return {
		"highest_raw_support_score": highest_raw_support_score,
		"highest_adjusted_score": highest_adjusted_score,
		"raw_top_candidates": raw_top_candidates,
		"adjusted_top_candidates": adjusted_top_candidates,
		"low_evidence_tie": low_evidence_tie,
		"registry_priority_enabled": registry_priority_enabled,
	}


def _rank_diagnoses(ranked_diagnoses: list, registry_priority_enabled: bool) -> list:
	if registry_priority_enabled:
		ranked_diagnoses.sort(
			key=lambda diagnosis: (
				-diagnosis["adjusted_score"],
				diagnosis["contradiction_score"],
				diagnosis["registry_priority"],
			)
		)
	else:
		ranked_diagnoses.sort(
			key=lambda diagnosis: (
				-diagnosis["adjusted_score"],
				diagnosis["contradiction_score"],
			)
		)

	return ranked_diagnoses


def _attach_explanations(ranked_diagnoses: list, present_feature_set: set) -> None:
	for diagnosis in ranked_diagnoses:
		explanations = [
			f'{feature_id.replace("_", " ")} supports this diagnosis'
			for feature_id in diagnosis["supporting_features"]
		]
		explanations.extend(diagnosis["temporal_explanations"])
		diagnosis["explanations"] = list(dict.fromkeys(explanations))


def _build_safety_outputs(present_feature_set: set) -> tuple[list, list]:
	red_flags = _detect_red_flags(present_feature_set)
	safety_diagnoses = []
	concerns = []
	seen_safety_ids = set()

	for red_flag in red_flags:
		concerns.append(red_flag["message"])
		for diagnosis_id in red_flag["safety_diagnoses"]:
			if diagnosis_id in SAFETY_DIAGNOSES and diagnosis_id not in seen_safety_ids:
				safety_diagnoses.append({"id": diagnosis_id})
				seen_safety_ids.add(diagnosis_id)

	return safety_diagnoses, concerns


def _build_safety_flags(present_feature_set: set) -> list[dict]:
	safety_flags = []
	seen_flag_ids = set()

	def add_flag(flag_id: str, severity: str, message: str) -> None:
		if flag_id in seen_flag_ids:
			return
		safety_flags.append(
			{
				"id": flag_id,
				"severity": severity,
				"message": message,
			}
		)
		seen_flag_ids.add(flag_id)

	if "syncope" in present_feature_set:
		add_flag("instability", "high", "Syncope - possible haemodynamic instability")

	if "shoulder_tip_pain" in present_feature_set:
		add_flag("intra_abdominal_bleed", "high", "Shoulder tip pain - possible intra-abdominal bleeding")

	if "hemodynamic_instability" in present_feature_set or "hypotension" in present_feature_set:
		add_flag("critical_state", "critical", "Possible haemodynamic instability")

	return safety_flags


def _detect_red_flags(present_feature_set: set) -> list:
	return [
		red_flag_rule
		for red_flag_rule in _get_red_flag_rules()
		if red_flag_rule["feature"] in present_feature_set
	]


def _has_critical_red_flag(red_flags: list) -> bool:
	return any(red_flag["severity"] == "critical" for red_flag in red_flags)


def _has_high_severity_red_flag(red_flags: list) -> bool:
	return any(red_flag["severity"] == "high" for red_flag in red_flags)


def _build_condition_rules(diagnosis: dict, context: dict | None) -> dict:
	rules = {
		"requirements": [],
		"exclusions": [],
	}

	if diagnosis["id"] == "ectopic_pregnancy":
		has_pregnancy_evidence = (
			"amenorrhea" in diagnosis.get("supporting_features", [])
			or (context and context.get("pregnancy_possible") is True)
		)
		rules["requirements"].append(
			{
				"id": "pregnancy_required",
				"status": "met" if has_pregnancy_evidence else "missing",
				"strength": "strong",
			}
		)

		if context and context.get("sex") == "male":
			rules["exclusions"].append(
				{
					"id": "male_context",
					"status": "triggered",
					"strength": "absolute",
				}
			)

	return rules


def _get_rule_signal_breakdown(rules: dict) -> list[dict]:
	signal_breakdown = []

	for requirement in rules["requirements"]:
		if requirement["status"] == "missing":
			signal_breakdown.append(
				{
					"feature_id": requirement["id"],
					"type": "requirement",
					"strength": "missing",
				}
			)

	for exclusion in rules["exclusions"]:
		if exclusion["status"] == "triggered":
			signal_breakdown.append(
				{
					"feature_id": exclusion["id"],
					"type": "rule_out",
					"strength": exclusion["strength"],
				}
			)

	return signal_breakdown


def _get_diagnostic_state_from_rules(rules: dict) -> str:
	if any(exclusion["status"] == "triggered" for exclusion in rules["exclusions"]):
		return "ruled_out"

	if any(requirement["status"] == "missing" for requirement in rules["requirements"]):
		return "insufficient"

	return "eligible"


def _build_condition_states(ranked_diagnoses: list, context: dict | None = None) -> list:
	condition_states = []

	for diagnosis in ranked_diagnoses:
		rules = _build_condition_rules(diagnosis, context)
		rule_signal_breakdown = _get_rule_signal_breakdown(rules)
		diagnostic_state = _get_diagnostic_state_from_rules(rules)
		is_ruled_out = diagnostic_state == "ruled_out"
		requirements_met = diagnostic_state != "insufficient"
		pattern_strength = _get_pattern_strength(diagnosis["diagnosis_signal_normalized"])
		if diagnostic_state == "ruled_out":
			pattern_strength = "ruled_out"
		elif diagnostic_state == "insufficient":
			pattern_strength = "weak"

		condition_state = {
			"id": diagnosis["id"],
			"normalized_signal_score": diagnosis["diagnosis_signal_normalized"],
			"supporting_feature_count": diagnosis["supporting_feature_count"],
			"signal_score": diagnosis["diagnosis_signal_score"],
			"max_signal_score": diagnosis["max_signal_score"],
			"signal_breakdown": diagnosis["signal_breakdown"] + rule_signal_breakdown,
			"pattern_strength": pattern_strength,
			"evidence_level": _get_evidence_level(
				diagnosis["supporting_feature_count"],
				diagnosis["diagnosis_signal_normalized"],
			),
			"rules": rules,
			"diagnostic_state": diagnostic_state,
			"is_ruled_out": is_ruled_out,
			"requirements_met": requirements_met,
		}

		if diagnostic_state != "eligible" or condition_state["pattern_strength"] == "weak":
			condition_state["should_display"] = False

		condition_states.append(condition_state)

	return condition_states


def _has_strong_supporting_signal(condition_state: dict) -> bool:
	return any(
		signal_entry.get("type") == "supporting" and signal_entry.get("strength") == "strong"
		for signal_entry in condition_state.get("signal_breakdown", [])
	)


def _get_non_rule_signal_count(condition_state: dict) -> int:
	return sum(
		1
		for signal_entry in condition_state.get("signal_breakdown", [])
		if signal_entry.get("type") in {"supporting", "temporal", "context"}
	)


def _meets_display_threshold(condition_state: dict) -> bool:
	if condition_state.get("supporting_feature_count", 0) >= 2:
		return True

	if _has_strong_supporting_signal(condition_state) and _get_non_rule_signal_count(condition_state) >= 2:
		return True

	return False


def _has_met_requirement(rules: dict, requirement_id: str) -> bool:
	return any(
		requirement.get("id") == requirement_id and requirement.get("status") == "met"
		for requirement in rules.get("requirements", [])
	)


def _has_ectopic_localising_feature(condition_state: dict) -> bool:
	ectopic_localising_features = {
		"vaginal_bleeding",
		"unilateral_pelvic_pain",
		"shoulder_tip_pain",
		"cervical_motion_tenderness",
	}

	return any(
		signal_entry.get("type") == "supporting"
		and signal_entry.get("feature_id") in ectopic_localising_features
		for signal_entry in condition_state.get("signal_breakdown", [])
	)


def _has_appendicitis_display_pattern(condition_state: dict) -> bool:
	feature_ids = {
		signal_entry.get("feature_id")
		for signal_entry in condition_state.get("signal_breakdown", [])
		if signal_entry.get("type") in {"supporting", "temporal"}
	}

	return (
		"right_lower_quadrant_pain" in feature_ids
		and bool(feature_ids & {"pain_migration", "nausea", "vomiting", "peritonism"})
	)


def _has_meaningful_signal(condition_state: dict) -> bool:
	supporting_count = condition_state.get("supporting_feature_count", 0)

	if supporting_count >= 2:
		return True

	if any(
		signal.get("label")
		and signal.get("type") in {"supporting", "contradiction"}
		for signal in condition_state.get("signal_breakdown", [])
	):
		return True

	for signal in condition_state.get("signal_breakdown", []):
		if signal.get("strength") == "strong":
			if signal.get("type") in ["supporting", "context"]:
				return True

	return False


def _apply_decision_guard(condition_states: list) -> list:
	if not condition_states:
		return condition_states

	for condition_state in condition_states:
		if (
			condition_state.get("id") == "appendicitis"
			and condition_state.get("diagnostic_state") == "eligible"
			and _has_appendicitis_display_pattern(condition_state)
		):
			condition_state["pattern_strength"] = "strong"
			condition_state["should_display"] = True

		if (
			condition_state.get("id") == "ectopic_pregnancy"
			and condition_state.get("diagnostic_state") == "eligible"
			and _has_met_requirement(condition_state.get("rules", {}), "pregnancy_required")
			and not _has_ectopic_localising_feature(condition_state)
		):
			condition_state["diagnostic_state"] = "insufficient"
			condition_state["requirements_met"] = False
			condition_state["should_display"] = False

		if (
			condition_state.get("diagnostic_state") == "eligible"
			and not (
				condition_state.get("id") == "appendicitis"
				and _has_appendicitis_display_pattern(condition_state)
			)
			and not _meets_display_threshold(condition_state)
		):
			condition_state["diagnostic_state"] = "insufficient"
			condition_state["requirements_met"] = False
			condition_state["should_display"] = False

	if not any(_has_meaningful_signal(condition_state) for condition_state in condition_states):
		return []

	top_condition_state = condition_states[0]
	if (
		top_condition_state.get("pattern_strength") == "weak"
		and top_condition_state.get("supporting_feature_count", 0) < 2
	):
		top_condition_state["diagnostic_state"] = "insufficient"
		top_condition_state["requirements_met"] = False
		top_condition_state["should_display"] = False

	return condition_states


def should_display_diagnosis(condition_state):
	return (
		condition_state.get("pattern_strength") == "strong"
		or condition_state.get("supporting_feature_count", 0) >= 3
	)


def _get_display_condition_states(condition_states: list) -> list:
	return [
		condition_state
		for condition_state in condition_states
		if not (
			condition_state.get("normalized_signal_score", 0.0) == 0
			and condition_state.get("supporting_feature_count", 0) == 0
		)
	]


def _get_top_condition_state(condition_states: list) -> dict | None:
	display_condition_states = _get_display_condition_states(condition_states)
	if not display_condition_states:
		return None

	return max(
		display_condition_states,
		key=lambda condition_state: condition_state.get("normalized_signal_score", 0.0),
	)


def _build_investigations(condition_states: list) -> list:
	top_condition_state = _get_top_condition_state(condition_states)
	if top_condition_state is None:
		return []

	investigations = get_section(top_condition_state["id"], "investigations")
	if investigations is None:
		return []

	return investigations


def _build_question_candidate(text: str, reason: str, dimension_type: str) -> dict:
	return {
		"text": text,
		"reason": reason,
		"dimension_type": dimension_type,
		"priority_score": _QUESTION_PRIORITY_SCORES[dimension_type],
	}


def is_question_valid(feature, known_features):
	return feature not in known_features


def _get_known_question_dimensions(present_feature_set: set) -> set:
	known_dimensions = set()

	headache_onset_features = {
		"sudden_onset_headache",
		"gradual_onset_headache",
		"thunderclap_headache",
		"worst_headache_of_life",
	}
	headache_severity_features = {
		"mild_headache",
		"severe_headache",
		"thunderclap_headache",
		"worst_headache_of_life",
	}

	if present_feature_set & {"abdominal_pain", "right_lower_quadrant_pain"}:
		known_dimensions.add("presence_of_pain")

	if present_feature_set & headache_onset_features:
		known_dimensions.add("headache_onset")

	if present_feature_set & headache_severity_features:
		known_dimensions.add("headache_severity")

	if {"neck_stiffness", "photophobia"}.issubset(present_feature_set):
		known_dimensions.add("headache_associated_features")

	if "right_lower_quadrant_pain" in present_feature_set:
		known_dimensions.add("pain_location")

	if "pain_migration" in present_feature_set:
		known_dimensions.add("pain_migration")

	if present_feature_set & {"pain_before_vomiting", "vomiting_before_pain"}:
		known_dimensions.add("symptom_sequence")

	if present_feature_set & {"vomiting", "nausea"}:
		known_dimensions.add("nausea_vomiting_clarification")

	if "fever" in present_feature_set:
		known_dimensions.add("fever_clarification")

	if "amenorrhea" in present_feature_set or "male_sex" in present_feature_set:
		known_dimensions.add("pregnancy_clarification")

	if "vaginal_bleeding" in present_feature_set:
		known_dimensions.add("bleeding_clarification")

	return known_dimensions


def _has_dominant_symptom(present_feature_set: set) -> bool:
	return bool(
		present_feature_set
		& {
			"headache",
			"abdominal_pain",
			"right_lower_quadrant_pain",
			"lower_abdominal_pain",
			"unilateral_pelvic_pain",
			"vomiting",
			"syncope",
		}
	)


def _build_question_candidates(
	present_feature_set: set,
	highest_raw_support_score: int,
	highest_adjusted_score: int,
	low_evidence_tie: bool,
	has_safety_priority: bool,
	has_high_severity_red_flag: bool,
	context: dict | None = None,
) -> list:
	candidates = []
	known_dimensions = _get_known_question_dimensions(present_feature_set)
	pregnancy_relevant_features = {
		"amenorrhea",
		"vaginal_bleeding",
		"syncope",
		"lower_abdominal_pain",
		"unilateral_pelvic_pain",
	}
	pregnancy_context_present = (
		"amenorrhea" in present_feature_set
		or (context is not None and context.get("pregnancy_possible") is True)
	)
	has_pregnancy_related_features = bool(present_feature_set & pregnancy_relevant_features)

	if has_safety_priority and is_question_valid("haemodynamic_stability", known_dimensions):
		candidates.append(
			_build_question_candidate(
				"Is the patient haemodynamically stable?",
				"Severity helps determine urgency and potential risk.",
				"haemodynamic_stability",
			)
		)

	if has_high_severity_red_flag and is_question_valid("haemodynamic_stability", known_dimensions):
		candidates.append(
			_build_question_candidate(
				"Is the patient feeling faint, dizzy, or lightheaded right now?",
				"Severity helps determine urgency and potential risk.",
				"haemodynamic_stability",
			)
		)

	if "headache" in present_feature_set:
		if is_question_valid("headache_onset", known_dimensions):
			candidates.append(
				_build_question_candidate(
					"Did the headache start suddenly or build gradually?",
					"Headache onset is a critical discriminator between benign and high-risk causes.",
					"headache_onset",
				)
			)

		if is_question_valid("headache_severity", known_dimensions):
			candidates.append(
				_build_question_candidate(
					"How severe is the headache right now?",
					"Severity helps stratify headache risk and urgency.",
					"headache_severity",
				)
			)

		if not {"neck_stiffness", "photophobia"}.issubset(present_feature_set):
			candidates.append(
				_build_question_candidate(
					"Do you have neck stiffness or sensitivity to light?",
					"Associated meningeal symptoms help identify high-risk headache presentations.",
					"headache_associated_features",
				)
			)

	if (
		pregnancy_context_present
		and "vaginal_bleeding" not in present_feature_set
		and is_question_valid("bleeding_clarification", known_dimensions)
	):
		candidates.append(
			_build_question_candidate(
				"Are you having any vaginal bleeding or spotting?",
				"Bleeding helps distinguish the likely source and urgency of pelvic or lower abdominal pain.",
				"pattern_bleeding_clarification",
			)
		)

	if "pain_migration" in present_feature_set:
		if (
			not (present_feature_set & {"vomiting", "nausea"})
			and is_question_valid("nausea_vomiting_clarification", known_dimensions)
		):
			candidates.append(
				_build_question_candidate(
					"Are you feeling nauseated or sick?",
					"Nausea or vomiting helps refine an appendicitis-like pattern once pain migration is present.",
					"nausea_vomiting_clarification",
				)
			)

		if "fever" not in present_feature_set and is_question_valid("fever_clarification", known_dimensions):
			candidates.append(
				_build_question_candidate(
					"Have you had a fever?",
					"Fever helps refine an appendicitis-like pattern once pain migration is present.",
					"fever_clarification",
				)
			)

	if (
		has_pregnancy_related_features
		and "male_sex" not in present_feature_set
		and context is not None
		and context.get("pregnancy_possible") is None
		and is_question_valid("pregnancy_clarification", known_dimensions)
	):
		candidates.append(
			_build_question_candidate(
				"Have you had a missed period or could you be pregnant?",
				"Pregnancy status helps narrow the clinical context for lower abdominal pain, bleeding, or collapse.",
				"pregnancy_clarification",
			)
		)
	elif (
		present_feature_set & {"amenorrhea", "syncope", "lower_abdominal_pain", "unilateral_pelvic_pain"}
		and "male_sex" not in present_feature_set
		and is_question_valid("bleeding_clarification", known_dimensions)
	):
		candidates.append(
			_build_question_candidate(
				"Are you having any vaginal bleeding or spotting?",
				"Bleeding helps distinguish the likely source and urgency of pelvic or lower abdominal pain.",
				"bleeding_clarification",
			)
		)

	if (
		"abdominal_pain" not in present_feature_set
		and "right_lower_quadrant_pain" not in present_feature_set
		and highest_raw_support_score >= 1
		and is_question_valid("presence_of_pain", known_dimensions)
	):
		candidates.append(
			_build_question_candidate(
				"Is there any abdominal pain?",
				"The presence of pain helps establish the main clinical domain before refining more specific features.",
				"presence_of_pain",
			)
		)

	if (
		"abdominal_pain" in present_feature_set
		and "right_lower_quadrant_pain" not in present_feature_set
		and "pain_migration" not in present_feature_set
	) or (
		low_evidence_tie
		and ("abdominal_pain" in present_feature_set or "right_lower_quadrant_pain" in present_feature_set)
		and "pain_migration" not in present_feature_set
	) and is_question_valid("pain_location", known_dimensions):
			candidates.append(
				_build_question_candidate(
					"Where is the abdominal pain located?",
					"Pain location helps determine whether the condition is localised or generalised.",
					"pain_location",
				)
			)

	if (
		"right_lower_quadrant_pain" in present_feature_set
		and "pain_migration" not in present_feature_set
		and is_question_valid("pain_migration", known_dimensions)
	):
		candidates.append(
			_build_question_candidate(
				"Did the pain migrate to the right lower quadrant?",
				"The sequence of symptoms helps identify the underlying cause.",
				"pain_migration",
			)
		)

	if (
		"abdominal_pain" in present_feature_set
		and "vomiting" in present_feature_set
		and "pain_before_vomiting" not in present_feature_set
		and "vomiting_before_pain" not in present_feature_set
		and is_question_valid("symptom_sequence", known_dimensions)
	):
		candidates.append(
			_build_question_candidate(
				"Did the pain start before the vomiting, or did vomiting come first?",
				"The sequence of symptoms helps identify the underlying cause.",
				"symptom_sequence",
			)
		)

	if "right_lower_quadrant_pain" in present_feature_set and is_question_valid("onset_pattern", known_dimensions):
		candidates.append(
			_build_question_candidate(
				"How did the pain start?",
				"The onset pattern helps clarify how the condition is evolving over time.",
				"onset_pattern",
			)
		)

	if (
		(highest_adjusted_score == 0 or not candidates)
		and not _has_dominant_symptom(present_feature_set)
		and is_question_valid("generic_clarification", known_dimensions)
	):
		candidates.append(
			_build_question_candidate(
				"Can you describe the main symptom?",
				"The main symptom defines the primary clinical dimension that needs to be clarified first.",
				"generic_clarification",
			)
		)

	return candidates


def _build_next_question(
	present_feature_set: set,
	highest_raw_support_score: int,
	highest_adjusted_score: int,
	low_evidence_tie: bool,
	has_safety_priority: bool,
	has_high_severity_red_flag: bool,
	context: dict | None = None,
) -> dict:
	questions = _build_question_candidates(
		present_feature_set,
		highest_raw_support_score,
		highest_adjusted_score,
		low_evidence_tie,
		has_safety_priority,
		has_high_severity_red_flag,
		context,
	)
	if not questions:
		if "headache" in present_feature_set:
			questions = [
				_build_question_candidate(
					"Did the headache start suddenly or build gradually?",
					"Headache onset is a critical discriminator between benign and high-risk causes.",
					"headache_onset",
				)
			]
		else:
			questions = [
				_build_question_candidate(
					"Can you describe the main symptom?",
					"The main symptom defines the primary clinical dimension that needs to be clarified first.",
					"generic_clarification",
				)
			]
	questions.sort(key=lambda question: question["priority_score"], reverse=True)
	assert questions == sorted(
		questions,
		key=lambda q: q["priority_score"],
		reverse=True,
	)
	return questions[0]


def _build_safety_override_question(safety_flags: list[dict]) -> dict:
	if any(safety_flag.get("severity") == "critical" for safety_flag in safety_flags):
		return {
			"text": "Is the patient stable?",
			"reason": "Safety concerns take priority over diagnosis refinement.",
			"dimension_type": "haemodynamic_stability",
			"priority_score": _QUESTION_PRIORITY_SCORES["haemodynamic_stability"],
		}

	return {
		"text": "Are you feeling faint, dizzy, or lightheaded right now?",
		"reason": "Safety concerns take priority over diagnosis refinement.",
		"dimension_type": "haemodynamic_stability",
		"priority_score": _QUESTION_PRIORITY_SCORES["haemodynamic_stability"],
	}

def select_diagnosis(present_feature_ids: list, clarification_question: str | None = None, context: dict | None = None) -> dict:
	_validate_diagnosis_rules()
	present_feature_set = set(present_feature_ids)
	red_flags = _detect_red_flags(present_feature_set)
	safety_diagnoses, concerns = _build_safety_outputs(present_feature_set)
	safety_flags = _build_safety_flags(present_feature_set)

	if clarification_question is not None:
		next_question = _build_safety_override_question(safety_flags) if safety_flags else {
			"text": clarification_question,
			"reason": "The main symptom defines the primary clinical dimension that needs to be clarified first.",
			"dimension_type": "generic_clarification",
			"priority_score": _QUESTION_PRIORITY_SCORES["generic_clarification"],
		}
		return {
			"condition_states": [],
			"investigations": [],
			"safety_flags": safety_flags,
			"next_question": next_question,
		}

	ranked_diagnoses = _build_ranked_diagnoses(present_feature_set, context)
	score_summary = _score_summary(ranked_diagnoses)
	ranked_diagnoses = _rank_diagnoses(ranked_diagnoses, score_summary["registry_priority_enabled"])
	_attach_explanations(ranked_diagnoses, present_feature_set)
	mode = "safety_priority" if _has_critical_red_flag(red_flags) else "diagnostic"
	next_question = (
		_build_safety_override_question(safety_flags)
		if safety_flags
		else _build_next_question(
			present_feature_set,
			score_summary["highest_raw_support_score"],
			score_summary["highest_adjusted_score"],
			score_summary["low_evidence_tie"],
			mode == "safety_priority",
			_has_high_severity_red_flag(red_flags),
			context,
		)
	)
	condition_states = _build_condition_states(ranked_diagnoses, context)
	condition_states = _apply_decision_guard(condition_states)
	top_condition_state = _get_top_condition_state(condition_states)
	if top_condition_state is not None:
		if not top_condition_state.get("is_ruled_out") and top_condition_state.get("requirements_met", True):
			top_condition_state["should_display"] = should_display_diagnosis(top_condition_state)
	investigations = _build_investigations(condition_states)
	return {
		"condition_states": condition_states,
		"investigations": investigations,
		"safety_flags": safety_flags,
		"next_question": next_question,
	}
