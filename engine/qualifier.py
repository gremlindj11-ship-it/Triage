import re

from engine.clause_splitter import find_clause_for_span


NEGATION_WORDS = [
	"no",
	"not",
	"never",
	"denies",
	"did not",
	"didn't",
]

META_PHRASES = [
	"the word",
	"means",
	"said",
	"she said",
	"he said",
	"they said",
]

RIGHT_NEGATION_PATTERNS = [
	r"\?\s*no\b",
]

WINDOW_CHARS = 20


def _contains_window_phrase(window: str, phrase: str) -> bool:
	return re.search(rf"\b{re.escape(phrase)}\b", window) is not None


def _get_left_window(text: str, start: int) -> str:
	return text[max(0, start - WINDOW_CHARS):start].lower()


def _get_right_window(text: str, end: int) -> str:
	return text[end:end + WINDOW_CHARS].lower()


def _is_meta(text: str, start: int) -> bool:
	window = _get_left_window(text, start)
	return any(_contains_window_phrase(window, phrase) for phrase in META_PHRASES)


def _is_left_negated(text: str, start: int) -> bool:
	window = _get_left_window(text, start)
	return any(_contains_window_phrase(window, word) for word in NEGATION_WORDS)


def _is_right_negated(text: str, end: int) -> bool:
	window = _get_right_window(text, end)
	return any(re.search(pattern, window) for pattern in RIGHT_NEGATION_PATTERNS)


def qualify_match(text: str, match: dict) -> tuple[str, str | None]:
	clause_text, clause_start = find_clause_for_span(text, match["start"], match["end"])
	local_start = match["start"] - clause_start
	local_end = match["end"] - clause_start

	if _is_meta(clause_text, local_start):
		return "uncertain", "meta_language"

	if _is_right_negated(clause_text, local_end):
		return "negated", "right_negation"

	if _is_left_negated(clause_text, local_start):
		return "negated", "left_negation"

	return "present", None