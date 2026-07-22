from main import run_ui_case


def _features(text):
	r = run_ui_case(text)
	return set(r["parsed"]["present_feature_ids"])


def _assertions(text):
	r = run_ui_case(text)
	return r["parsed"]["assertions"]


# --------------------------------
# 1. CONTRADICTION
# --------------------------------
def test_contradiction_headache_not_absent():
	"""
	"no headache but worst headache of life"
	→ should NOT mark headache as absent
	→ should resolve to thunderclap_headache (present)
	"""
	feats = _features("no headache but worst headache of life")

	assert "thunderclap_headache" in feats, "Expected thunderclap_headache present"
	assert "headache" in feats, "Base headache should still exist internally"

	# ensure not negated
	assertions = _assertions("no headache but worst headache of life")
	negated = [a for a in assertions if a.get("polarity") == "negated"]
	assert not any(a.get("meaning_id") == "headache" for a in negated), \
		"Headache should not be negated when later positive evidence exists"


# --------------------------------
# 2. NEGATION PRIORITY
# --------------------------------
def test_negation_priority_separate_clauses():
	"""
	"no chest pain but vomiting"
	→ chest pain = false
	→ vomiting = true
	"""
	feats = _features("no chest pain but vomiting")

	assert "vomiting" in feats, "Vomiting should be present"
	assert "chest_pain" not in feats, "Chest pain should not be present"


# --------------------------------
# 3. LOCATION ALONE
# --------------------------------
def test_location_alone_no_symptom_creation():
	"""
	"rlq"
	→ should NOT create rlq_pain
	"""
	feats = _features("rlq")

	assert "rlq_pain" not in feats, "Location alone must not create symptom"
	assert "right_lower_quadrant_pain" not in feats, \
		"Canonical RLQ pain must not be created without symptom"


# --------------------------------
# 4. SEVERITY CONFLICT
# --------------------------------
def test_severity_conflict_headache():
	"""
	"mild headache now worst headache"
	→ only thunderclap_headache retained (plus base headache internally)
	"""
	feats = _features("mild headache now worst headache")

	assert "thunderclap_headache" in feats, "Expected thunderclap_headache"
	assert "mild_headache" not in feats, "Lower severity should be pruned"


def test_double_negation_weird_input():
	feats = _features("no no headache but now severe headache")
	assert "thunderclap_headache" in feats


# --------------------------------
# 5. THUNDERCLAP DETECTION: PHRASING VARIANTS
# --------------------------------
def test_thunderclap_alternate_negation_word_and_cue():
	"""
	"denies headache but suddenly severe headache"
	→ different negation word ("denies") + different onset cue ("suddenly")
	→ should still resolve to thunderclap_headache
	"""
	feats = _features("denies headache but suddenly severe headache")
	assert "thunderclap_headache" in feats, \
		"Expected thunderclap_headache with an alternate negation word and onset cue"


def test_thunderclap_then_cue_variant():
	"""
	"no headache but then severe headache"
	→ "then" as the onset-transition cue instead of "now"
	→ should still resolve to thunderclap_headache
	"""
	feats = _features("no headache but then severe headache")
	assert "thunderclap_headache" in feats, \
		"Expected thunderclap_headache when 'then' is used as the onset cue"


# --------------------------------
# 6. THUNDERCLAP DETECTION: NEGATION EDGE CASES (must NOT over-trigger)
# --------------------------------
def test_contrast_without_onset_cue_stays_severe():
	"""
	"no headache but severe headache" has a negation-contrast but no onset
	cue word (no "now"/"suddenly"/"then"/...).
	→ severity alone must not imply thunderclap; only severe_headache should remain.
	"""
	feats = _features("no headache but severe headache")
	assert "severe_headache" in feats
	assert "thunderclap_headache" not in feats, \
		"A bare contradiction without an onset cue must not be classified as thunderclap"


def test_onset_cue_with_mild_severity_does_not_escalate():
	"""
	"no headache but now mild headache" has the onset cue ("now") but the
	reasserted severity is mild, not severe/critical.
	→ must not escalate to sudden_onset_headache or thunderclap_headache.
	"""
	feats = _features("no headache but now mild headache")
	assert "mild_headache" in feats
	assert "sudden_onset_headache" not in feats
	assert "thunderclap_headache" not in feats, \
		"An onset cue must not manufacture thunderclap out of a mild headache"


# --------------------------------
# SMOKE RUNNER (for direct execution)
# --------------------------------
if __name__ == "__main__":
	test_contradiction_headache_not_absent()
	test_negation_priority_separate_clauses()
	test_location_alone_no_symptom_creation()
	test_severity_conflict_headache()
	test_double_negation_weird_input()
	test_thunderclap_alternate_negation_word_and_cue()
	test_thunderclap_then_cue_variant()
	test_contrast_without_onset_cue_stays_severe()
	test_onset_cue_with_mild_severity_does_not_escalate()
	print("PASS: logical safety tests")