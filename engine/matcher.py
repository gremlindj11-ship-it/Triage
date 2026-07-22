import re

from engine.meaning_dictionary import MEANING_DICTIONARY


def find_phrase_spans(text: str, phrase: str) -> list[tuple[int, int]]:
	pattern = r"\b" + re.escape(phrase) + r"\b"
	return [(match.start(), match.end()) for match in re.finditer(pattern, text)]


def match_meanings(text: str) -> list[dict]:
	text_lower = text.lower()
	raw_matches = []

	for entry in MEANING_DICTIONARY:
		for phrase in entry["surface_forms"]:
			for start, end in find_phrase_spans(text_lower, phrase):
				raw_matches.append(
					{
						"meaning_id": entry["meaning_id"],
						"phrase": phrase,
						"start": start,
						"end": end,
						"priority": entry["priority"],
					}
				)

	raw_matches.sort(key=lambda match: (-match["priority"], -(match["end"] - match["start"])))
	accepted_matches = []
	occupied_spans = []

	for match in raw_matches:
		overlaps_existing_span = any(
			not (match["end"] <= occupied_start or match["start"] >= occupied_end)
			for occupied_start, occupied_end in occupied_spans
		)
		if overlaps_existing_span:
			continue

		accepted_matches.append(match)
		occupied_spans.append((match["start"], match["end"]))

	accepted_matches.sort(key=lambda match: match["start"])
	return accepted_matches