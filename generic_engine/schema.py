PLACEHOLDER = "placeholder"
GUIDELINE_DERIVED = "guideline_derived"
VALIDATED_SCORE = "validated_score"

STATUS_VALUES = {PLACEHOLDER, GUIDELINE_DERIVED, VALIDATED_SCORE}

SEVERITY_VALUES = {"critical", "high", "warning"}
SEVERITY_RANK = {"critical": 3, "high": 2, "warning": 1}

STATE_RANK = {"ruled_out": 0, "insufficient": 1, "possible": 2, "likely": 3}
