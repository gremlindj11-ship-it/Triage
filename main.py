from contextlib import redirect_stdout

import engine.language.seed

from io import StringIO

from engine.case_pipeline import augment_parsed_output, build_assertion_pipeline, build_case_payload
from engine.parser import parse_text
from engine.reasoning import select_diagnosis
from engine.validation import validate_language_alignment
from ui import display_case


validate_language_alignment()


max_turns = 3


def run_ui_case(text: str) -> dict:
	case_payload = build_case_payload(text)
	parsed = case_payload["parsed"]
	top_condition_state = case_payload["condition_states"][0] if case_payload.get("condition_states") else None
	next_question = case_payload.get("next_question")
	safety_flags = case_payload.get("safety_flags", [])

	buffer = StringIO()
	with redirect_stdout(buffer):
		display_case(
			{
				"condition_states": case_payload["condition_states"],
				"investigations": case_payload["investigations"],
				"next_question": case_payload["next_question"],
				"safety_flags": case_payload["safety_flags"],
			},
			parsed["present_feature_ids"],
		)

	return {
		"input": text,
		"display": buffer.getvalue(),
		"parsed": parsed,
		"condition_states": case_payload.get("condition_states", []),
		"investigations": case_payload.get("investigations", []),
		"top_condition": top_condition_state,
		"next_question": next_question,
		"safety_flags": safety_flags,
	}


def run_cases(cases: list[str]) -> list[dict]:
	return [run_ui_case(text) for text in cases]


def debug_assertion_pipeline(cases: list[str]) -> list[dict]:
	return [
		{
			"input": text,
			**build_assertion_pipeline(text),
		}
		for text in cases
	]


def debug_full_pipeline(text: str) -> dict:
	return run_ui_case(text)


def main() -> None:
	while True:
		input_text = input("Enter patient info (or 'exit'): ").strip()
		if input_text == "exit":
			break

		current_input = input_text
		turn_count = 0
		previous_feature_set = None

		while True:
			parsed = augment_parsed_output(current_input, parse_text(current_input))
			current_feature_set = set(parsed["present_feature_ids"])
			result = select_diagnosis(
				parsed["present_feature_ids"],
				parsed["clarification_question"],
				parsed.get("context"),
			)
			display_case(result, parsed["present_feature_ids"])
			turn_count += 1

			if previous_feature_set == current_feature_set or turn_count >= max_turns:
				print("No further information gained. Final assessment above.")
				break

			previous_feature_set = current_feature_set
			print("NEXT QUESTION:")
			print(f'- {result["next_question"]["text"]}')
			print(f'- reason: {result["next_question"]["reason"]}')
			user_answer = input(f'{result["next_question"]["text"]} ').strip()
			current_input = f"{current_input} {user_answer}".strip()


if __name__ == "__main__":
	main()