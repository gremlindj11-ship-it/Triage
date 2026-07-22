
import re

from engine.feature_registry import FEATURE_VOCAB, map_phrase_to_feature
from engine.registry import TEMPORAL_PATTERNS


_ABDOMINAL_PAIN_ALIASES = [
	"stomach pain",
	"abdominal pain",
]

_RIGHT_LOWER_QUADRANT_PAIN_ALIASES = [
	"rlq pain",
	"rlq",
	"rlq tenderness",
	"rif pain",
	"right side",
	"right side pain",
	"pain in right side",
	"pain on right side",
	"right iliac fossa pain",
	"right iliac fossa tenderness",
	"right lower pain",
	"right lowr abdominal pain",
	"right lower abdo pain",
	"right lower abd pain",
	"right lower quadrant pain",
	"right lower abdominal pain",
	"pain in the right lower abdomen",
]

_NEGATION_WORDS = {"no", "not", "without", "denies"}
_NEGATION_WINDOW_WORDS = 8
_NEGATION_BOUNDARY_WORDS = {"but", "however"}
_TEMPORAL_CONNECTOR_DIRECTIONS = {
	"then": "forward",
	"later": "forward",
	"before": "forward",
	"after": "reverse",
}
_NORMALIZATION_REPLACEMENTS = {
	"dizzn": "dizzy",
	"vomitin": "vomiting",
	"vomitng": "vomiting",
}
_CONCATENATION_REPLACEMENTS = {
	"vomitingi": "vomiting i",
}
_RLQ_COMPONENT_PREFIX_WORD = "right"
_RLQ_COMPONENT_MIDDLE_WORDS = ["lower", "lowr"]
_RLQ_COMPONENT_SUFFIX_WORDS = ["pain", "tenderness"]
_AMBIGUOUS_WORDS = {"weird", "strange", "off", "odd"}
_CLARIFICATION_SYMPTOM_WORDS = {
	"pain",
	"dizzy",
	"weird",
	"sick",
	"discomfort",
	"strange",
	"stomach",
	"nausea",
	"nauseous",
}
_CLARIFICATION_QUESTION = "Can you describe the symptom more clearly? Is it pain, nausea, or something else?"
_AMBIGUITY_CLARIFICATION_QUESTION = "Can you describe the symptom more clearly?"
_RAW_MATCH_FEATURE_IDS = {"no_pain", "diffuse_symptoms_without_localisation"}
_MALE_CONTEXT_PHRASES = ["male"]
_FEMALE_CONTEXT_PHRASES = ["female"]
_PREGNANCY_CONTEXT_PHRASES = [
	"pregnant",
	"missed period",
	"missed my period",
	"late period",
	"period is late",
	"amenorrhea",
	"amenorrhoea",
]


def _normalize_text(raw_text: str) -> str:
	normalized_text = raw_text.lower()

	for source_text, target_text in _CONCATENATION_REPLACEMENTS.items():
		normalized_text = re.sub(rf"(?<!\w){re.escape(source_text)}(?!\w)", target_text, normalized_text)

	for source_text, target_text in _NORMALIZATION_REPLACEMENTS.items():
		normalized_text = re.sub(rf"(?<!\w){re.escape(source_text)}(?!\w)", target_text, normalized_text)

	return re.sub(r"\s+", " ", normalized_text).strip()


def _contains_exact_phrase(text: str, phrase: str) -> bool:
	pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"
	return re.search(pattern, text) is not None


def _find_exact_phrase_matches(text: str, phrase: str) -> list[re.Match[str]]:
	pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"
	return list(re.finditer(pattern, text))


def _remove_exact_phrase(text: str, phrase: str) -> str:
	pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"
	updated_text = re.sub(pattern, " ", text)
	return re.sub(r"\s+", " ", updated_text).strip()


def _add_feature(feature_id: str, present_feature_ids: list, seen_feature_ids: set) -> None:
	if feature_id is None:
		return
	if feature_id not in set(FEATURE_VOCAB.values()):
		return
	if feature_id not in seen_feature_ids:
		present_feature_ids.append(feature_id)
		seen_feature_ids.add(feature_id)


def _add_feature_from_phrase(phrase: str, present_feature_ids: list, seen_feature_ids: set) -> None:
	_add_feature(map_phrase_to_feature(phrase), present_feature_ids, seen_feature_ids)


def _contains_any_exact_phrase(text: str, phrases: list[str]) -> bool:
	return any(_contains_exact_phrase(text, phrase) for phrase in phrases)


def _get_negation_spans(text: str) -> list[tuple[int, int]]:
	word_matches = list(re.finditer(r"\b\w+\b", text))
	negation_spans = []

	for index, match in enumerate(word_matches):
		if match.group(0) not in _NEGATION_WORDS:
			continue

		window_end_index = min(index + _NEGATION_WINDOW_WORDS, len(word_matches) - 1)
		for candidate_index in range(index + 1, min(index + _NEGATION_WINDOW_WORDS + 1, len(word_matches))):
			if word_matches[candidate_index].group(0) in _NEGATION_BOUNDARY_WORDS:
				window_end_index = candidate_index - 1
				break

		if window_end_index >= index + 1:
			negation_spans.append((match.end(), word_matches[window_end_index].end()))

	return negation_spans



def _is_negated(text: str, phrase_start: int, phrase_end: int) -> bool:
	preceding_words = re.findall(r"\b\w+\b", text[:phrase_start])[-3:]
	if any(word in _NEGATION_WORDS for word in preceding_words):
		return True

	for negation_start, negation_end in _get_negation_spans(text):
		if phrase_start >= negation_start and phrase_end <= negation_end:
			return True

	return False


def _contains_non_negated_exact_phrase(text: str, phrase: str) -> bool:
	for match in _find_exact_phrase_matches(text, phrase):
		if not _is_negated(text, match.start(), match.end()):
			return True
	return False


def _contains_any_non_negated_phrase(text: str, phrases: list[str]) -> bool:
	return any(_contains_non_negated_exact_phrase(text, phrase) for phrase in phrases)


def _contains_ambiguous_word(text: str) -> bool:
	return any(_contains_non_negated_exact_phrase(text, word) for word in _AMBIGUOUS_WORDS)


def _get_matching_non_negated_phrases(text: str, phrases: list[str]) -> list[str]:
	return [phrase for phrase in phrases if _contains_non_negated_exact_phrase(text, phrase)]


def _find_non_negated_word_positions(text: str, words: list[str]) -> list[tuple[int, int]]:
	positions = []
	for word in words:
		for match in _find_exact_phrase_matches(text, word):
			if not _is_negated(text, match.start(), match.end()):
				positions.append((match.start(), match.end()))
	return sorted(positions)


def _matches_rlq_components(text: str) -> bool:
	right_positions = _find_non_negated_word_positions(text, [_RLQ_COMPONENT_PREFIX_WORD])
	lower_positions = _find_non_negated_word_positions(text, _RLQ_COMPONENT_MIDDLE_WORDS)
	pain_positions = _find_non_negated_word_positions(text, _RLQ_COMPONENT_SUFFIX_WORDS)

	for right_start, _right_end in right_positions:
		for lower_start, _lower_end in lower_positions:
			if lower_start <= right_start:
				continue
			for pain_start, pain_end in pain_positions:
				if pain_start <= lower_start:
					continue
				if not _is_negated(text, right_start, pain_end):
					return True

	return False


def _find_non_negated_phrase_positions(text: str, phrases: list[str]) -> list[tuple[int, int]]:
	positions = []
	for phrase in phrases:
		for match in _find_exact_phrase_matches(text, phrase):
			if not _is_negated(text, match.start(), match.end()):
				positions.append((match.start(), match.end()))
	return sorted(positions)


def _segment_contains_connector(segment: str, connectors: list[str], direction: str) -> bool:
	for connector in connectors:
		if _TEMPORAL_CONNECTOR_DIRECTIONS.get(connector) != direction:
			continue
		if re.search(rf"\b{re.escape(connector)}\b", segment):
			return True
	return False


def _has_temporal_sequence(text: str, earlier_phrases: list[str], later_phrases: list[str], connectors: list[str]) -> bool:
	earlier_positions = _find_non_negated_phrase_positions(text, earlier_phrases)
	later_positions = _find_non_negated_phrase_positions(text, later_phrases)

	for earlier_start, earlier_end in earlier_positions:
		for later_start, _later_end in later_positions:
			if earlier_start < later_start:
				segment = text[earlier_end:later_start]
				if _segment_contains_connector(segment, connectors, "forward"):
					return True
			elif later_start < earlier_start:
				segment = text[_later_end:earlier_start]
				if _segment_contains_connector(segment, connectors, "reverse"):
					return True

	return False


def _extract_temporal_features(text: str) -> list[str]:
	temporal_feature_ids = []

	for temporal_pattern in TEMPORAL_PATTERNS:
		if _has_temporal_sequence(
			text,
			temporal_pattern["earlier_phrases"],
			temporal_pattern["later_phrases"],
			temporal_pattern["connectors"],
		):
			temporal_feature_ids.append(temporal_pattern["marker_feature"])
			continue

		inverse_marker_feature = temporal_pattern.get("inverse_marker_feature")
		if inverse_marker_feature and _has_temporal_sequence(
			text,
			temporal_pattern["later_phrases"],
			temporal_pattern["earlier_phrases"],
			temporal_pattern["connectors"],
		):
			temporal_feature_ids.append(inverse_marker_feature)

	return temporal_feature_ids


def _collect_consumed_word_indexes(text: str, consumed_phrases: list[str]) -> set[int]:
	word_matches = list(re.finditer(r"\b\w+\b", text))
	consumed_indexes = set()

	for phrase in consumed_phrases:
		for match in _find_exact_phrase_matches(text, phrase):
			if _is_negated(text, match.start(), match.end()):
				continue
			for index, word_match in enumerate(word_matches):
				if word_match.start() >= match.start() and word_match.end() <= match.end():
					consumed_indexes.add(index)

	return consumed_indexes


def _build_clarification_question(text: str, consumed_phrases: list[str]) -> str | None:
	word_matches = list(re.finditer(r"\b\w+\b", text))
	consumed_indexes = _collect_consumed_word_indexes(text, consumed_phrases)

	for index, word_match in enumerate(word_matches):
		if index in consumed_indexes:
			continue
		if word_match.group(0) in _CLARIFICATION_SYMPTOM_WORDS:
			return _CLARIFICATION_QUESTION

	return None


def _extract_context(text: str) -> dict:
	sex = None
	if _contains_any_non_negated_phrase(text, _MALE_CONTEXT_PHRASES):
		sex = "male"
	elif _contains_any_non_negated_phrase(text, _FEMALE_CONTEXT_PHRASES):
		sex = "female"

	pregnancy_possible = None
	if _contains_any_non_negated_phrase(text, _PREGNANCY_CONTEXT_PHRASES):
		pregnancy_possible = True

	return {
		"sex": sex,
		"pregnancy_possible": pregnancy_possible,
	}


def parse(text: str, debug: bool = False) -> dict:
	normalized_text = _normalize_text(text)
	original_normalized_text = normalized_text
	present_feature_ids = []
	seen_feature_ids = set()
	consumed_phrases = []

	for phrase, feature_id in FEATURE_VOCAB.items():
		if feature_id in {"abdominal_pain", "right_lower_quadrant_pain"}:
			continue
		phrase_found = (
			_contains_exact_phrase(normalized_text, phrase)
			if feature_id in _RAW_MATCH_FEATURE_IDS
			else _contains_non_negated_exact_phrase(normalized_text, phrase)
		)
		if phrase_found:
			_add_feature(feature_id, present_feature_ids, seen_feature_ids)
			consumed_phrases.append(phrase)
			normalized_text = _remove_exact_phrase(normalized_text, phrase)

	specific_pain_phrases = _RIGHT_LOWER_QUADRANT_PAIN_ALIASES + _ABDOMINAL_PAIN_ALIASES

	right_lower_quadrant_matches = _get_matching_non_negated_phrases(
		original_normalized_text,
		_RIGHT_LOWER_QUADRANT_PAIN_ALIASES,
	)
	abdominal_pain_matches = _get_matching_non_negated_phrases(
		original_normalized_text,
		_ABDOMINAL_PAIN_ALIASES,
	)

	if right_lower_quadrant_matches:
		_add_feature_from_phrase("right lower quadrant pain", present_feature_ids, seen_feature_ids)
		consumed_phrases.extend(right_lower_quadrant_matches)
	elif _matches_rlq_components(original_normalized_text):
		_add_feature_from_phrase("right lower quadrant pain", present_feature_ids, seen_feature_ids)
	elif abdominal_pain_matches or (
		not _contains_any_exact_phrase(normalized_text, specific_pain_phrases)
		and _contains_non_negated_exact_phrase(normalized_text, "pain")
	):
		_add_feature_from_phrase("abdominal pain", present_feature_ids, seen_feature_ids)
		if abdominal_pain_matches:
			consumed_phrases.extend(abdominal_pain_matches)
		else:
			consumed_phrases.append("pain")

	for temporal_feature_id in _extract_temporal_features(original_normalized_text):
		_add_feature(temporal_feature_id, present_feature_ids, seen_feature_ids)
		if temporal_feature_id in {"pain_before_vomiting", "vomiting_before_pain"}:
			_add_feature_from_phrase("abdominal pain", present_feature_ids, seen_feature_ids)

	clarification_question = None
	if present_feature_ids and _contains_ambiguous_word(original_normalized_text):
		clarification_question = _AMBIGUITY_CLARIFICATION_QUESTION
	elif len(present_feature_ids) == 0:
		clarification_question = _build_clarification_question(original_normalized_text, consumed_phrases)

	extracted = {
		"present_feature_ids": present_feature_ids,
		"clarification_question": clarification_question,
		"context": _extract_context(original_normalized_text),
	}

	if debug:
		print("Parsed features:", extracted)

	return extracted


def parse_text(raw_text: str) -> dict:
	parsed = parse(raw_text)
	print("RAW INPUT:", raw_text)
	print("MATCHED FEATURES:", parsed["present_feature_ids"])
	return parsed
