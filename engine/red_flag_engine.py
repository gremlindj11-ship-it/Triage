def evaluate_red_flags(features: list[str], context: dict) -> list[dict]:
	flags = []
	feature_set = set(features)

	if "syncope" in feature_set:
		flags.append(
			{
				"type": "instability",
				"message": "Loss of consciousness - possible haemodynamic instability",
			}
		)

	if "shoulder_tip_pain" in feature_set:
		flags.append(
			{
				"type": "internal_bleeding",
				"message": "Shoulder tip pain - possible intra-abdominal bleeding",
			}
		)

	if "thunderclap_headache" in feature_set or "sudden_onset_headache" in feature_set:
		flags.append(
			{
				"type": "intracranial_emergency",
				"message": "Sudden severe headache - possible subarachnoid haemorrhage",
			}
		)

	if "reduced_consciousness" in feature_set:
		flags.append(
			{
				"type": "neurological_deterioration",
				"message": "Reduced consciousness - urgent neurological emergency",
			}
		)

	if "seizures" in feature_set:
		flags.append(
			{
				"type": "neurological_event",
				"message": "Seizures - urgent intracranial pathology must be excluded",
			}
		)

	if context.get("not_speaking_full_sentences"):
		flags.append(
			{
				"type": "respiratory_distress",
				"message": "Unable to speak full sentences - severe respiratory distress",
			}
		)

	return flags