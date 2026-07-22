import re


CLAUSE_SPLIT_PATTERNS = [
	r"\bbut\b",
	r"\band\b",
	r",",
]


def split_clauses(text: str) -> list[tuple[str, int]]:
	"""Return stripped clause text and its start index in the original input."""

	splits = []
	last_index = 0
	pattern = "|".join(CLAUSE_SPLIT_PATTERNS)

	for match in re.finditer(pattern, text.lower()):
		clause_text = text[last_index:match.start()]
		leading_ws = len(clause_text) - len(clause_text.lstrip())
		stripped_clause = clause_text.strip()
		if stripped_clause:
			splits.append((stripped_clause, last_index + leading_ws))
		last_index = match.end()

	final_clause = text[last_index:]
	leading_ws = len(final_clause) - len(final_clause.lstrip())
	stripped_clause = final_clause.strip()
	if stripped_clause:
		splits.append((stripped_clause, last_index + leading_ws))

	return splits


def find_clause_for_span(text: str, start: int, end: int) -> tuple[str, int]:
	for clause_text, clause_start in split_clauses(text):
		clause_end = clause_start + len(clause_text)
		if clause_start <= start and end <= clause_end:
			return clause_text, clause_start

	return text, 0