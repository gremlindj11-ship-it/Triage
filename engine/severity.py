import re


SEVERITY_LEVELS = {
	"mild": 0,
	"moderate": 1,
	"severe": 2,
	"critical": 3,
}

SEVERITY_PHRASES = {
	"mild": ["mild", "slight"],
	"moderate": ["moderate"],
	"severe": ["severe", "very painful"],
	"critical": ["worst", "worst ever", "unbearable", "excruciating"],
}

WINDOW_TOKENS = 4


def _word_matches(text: str) -> list[re.Match[str]]:
	return list(re.finditer(r"\b[\w']+\b", text.lower()))


def _token_window_text(text: str, start: int, end: int) -> str:
	word_matches = _word_matches(text)
	if not word_matches:
		return text.lower()

	overlapping_indexes = [
		index
		for index, match in enumerate(word_matches)
		if not (match.end() <= start or match.start() >= end)
	]

	if not overlapping_indexes:
		return text.lower()

	window_start_index = max(0, overlapping_indexes[0] - WINDOW_TOKENS)
	window_end_index = min(len(word_matches) - 1, overlapping_indexes[-1] + WINDOW_TOKENS)
	window_start = word_matches[window_start_index].start()
	window_end = word_matches[window_end_index].end()
	return text[window_start:window_end].lower()


def _contains_phrase(text: str, phrase: str) -> bool:
	return re.search(rf"\b{re.escape(phrase)}\b", text) is not None


def _get_highest_level(levels: list[str]) -> str | None:
	if not levels:
		return None
	return max(levels, key=lambda level: SEVERITY_LEVELS[level])


def detect_assertion_severity(text: str, start: int, end: int) -> dict | None:
	window_text = _token_window_text(text, start, end)
	matched_levels = []

	for level, phrases in SEVERITY_PHRASES.items():
		if any(_contains_phrase(window_text, phrase) for phrase in phrases):
			matched_levels.append(level)

	highest_level = _get_highest_level(matched_levels)
	if highest_level is None:
		return None

	return {"level": highest_level}


def summarize_assertion_severity(assertions: list[dict]) -> dict | None:
	levels = [
		assertion["severity"]["level"]
		for assertion in assertions
		if assertion.get("polarity") == "present" and assertion.get("severity")
	]

	highest_level = _get_highest_level(levels)
	if highest_level is None:
		return None

	return {"level": highest_level}