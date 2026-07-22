from flask import Flask, jsonify, request

import engine.language.seed
from engine.case_pipeline import build_case_payload
from engine.validation import validate_language_alignment


app = Flask(__name__)


validate_language_alignment()


def _empty_case_payload() -> dict:
	return {
		"raw_input": "",
		"parsed": {
			"context": {},
			"meaning_matches": [],
			"matches": [],
			"assertions": [],
			"relations": [],
			"clinical_state": {
				"raw_text": "",
				"assertions": [],
				"relations": [],
				"present": [],
				"negated": [],
				"uncertain": [],
			},
			"present_feature_ids": [],
			"derived_feature_ids": [],
			"derived_features": [],
			"pattern_results": [],
			"diagnosis_results": [],
			"red_flags": [],
		},
		"condition_states": [],
		"investigations": [],
		"next_question": None,
		"safety_flags": [],
	}


@app.get("/")
def index() -> str:
	return r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Clinical Triage</title>
  <style>
    :root {
      --bg: #f4f6f8;
      --panel: #ffffff;
      --panel-soft: #fafbfc;
      --ink: #27313a;
      --muted: #687481;
      --line: #d9e0e7;
      --line-strong: #c8d1da;
      --green: #2c8b57;
      --green-soft: #e8f6ee;
      --amber: #b7791f;
      --amber-soft: #fff5df;
      --grey: #7a8793;
      --grey-soft: #f1f4f6;
      --red: #c53d3d;
      --red-soft: #fff0f0;
      --shadow: 0 8px 20px rgba(27, 39, 51, 0.08);
      --radius: 14px;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      padding: 24px 18px 40px;
      font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Palatino, Georgia, serif;
      color: var(--ink);
      background: var(--bg);
    }

    .shell {
      max-width: 1280px;
      margin: 0 auto;
    }

    .page-header {
      margin-bottom: 18px;
    }

    .eyebrow {
      margin: 0 0 6px;
      color: var(--muted);
      font-size: 0.76rem;
      letter-spacing: 0.16em;
      text-transform: uppercase;
    }

    h1 {
      margin: 0;
      font-size: clamp(1.8rem, 2.8vw, 2.7rem);
      line-height: 1;
      letter-spacing: 0.02em;
    }

    .header-copy {
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 0.98rem;
    }

    .workspace {
      display: grid;
      grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
      gap: 20px;
      align-items: start;
    }

    .column {
      display: grid;
      gap: 16px;
      min-width: 0;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow: hidden;
    }

    .panel.hidden {
      display: none;
    }

    .panel-header {
      padding: 14px 18px 10px;
      border-bottom: 1px solid var(--line);
      background: var(--panel-soft);
    }

    .panel-header h2,
    .panel-header h3 {
      margin: 0;
      font-size: 0.92rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
    }

    .panel-body {
      padding: 18px;
    }

    textarea {
      width: 100%;
      min-height: 180px;
      padding: 16px;
      border: 1px solid var(--line-strong);
      border-radius: 12px;
      background: #ffffff;
      color: var(--ink);
      font: inherit;
      line-height: 1.55;
      resize: vertical;
      outline: none;
    }

    textarea:focus {
      border-color: #9fb5ca;
      box-shadow: 0 0 0 3px rgba(94, 139, 196, 0.12);
    }

    .input-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-top: 14px;
      flex-wrap: wrap;
    }

    .helper-text {
      color: var(--muted);
      font-size: 0.94rem;
    }

    button {
      border: 1px solid #4b6278;
      border-radius: 10px;
      background: #546b80;
      color: #ffffff;
      padding: 10px 16px;
      font: inherit;
      letter-spacing: 0.04em;
      cursor: pointer;
    }

    button:hover {
      background: #455a6d;
    }

    .list-block + .list-block {
      margin-top: 14px;
    }

    .section-label {
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 0.82rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .list-block ul,
    .reasoning-section ul,
    .timeline-list,
    .state-list {
      margin: 0;
      padding-left: 18px;
    }

    li + li {
      margin-top: 6px;
    }

    .timeline-box {
      border: 1px solid var(--line);
      border-radius: 12px;
      background: var(--panel-soft);
      padding: 14px 16px;
    }

    .diagnosis-list {
      display: grid;
      gap: 12px;
    }

    .diagnosis-card {
      border: 1px solid var(--line);
      border-left-width: 6px;
      border-radius: 12px;
      background: #ffffff;
      padding: 14px 14px 14px 16px;
      box-shadow: 0 4px 12px rgba(27, 39, 51, 0.05);
    }

    .diagnosis-card.conf-high {
      border-left-color: var(--green);
    }

    .diagnosis-card.conf-mid {
      border-left-color: var(--amber);
    }

    .diagnosis-card.conf-low {
      border-left-color: var(--grey);
    }

    .diagnosis-card.ruled-out {
      border-left-color: #c9cfd6;
      background: #f7f9fb;
      color: var(--grey);
      opacity: 0.82;
    }

    .diagnosis-topline {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
    }

    .diagnosis-title {
      margin: 0;
      font-size: 1.06rem;
      font-weight: 700;
    }

    .diagnosis-subtitle {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 0.92rem;
    }

    .diagnosis-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: flex-end;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 0.82rem;
      font-weight: 700;
      letter-spacing: 0.03em;
    }

    .badge.conf-high {
      background: var(--green-soft);
      color: var(--green);
    }

    .badge.conf-mid {
      background: var(--amber-soft);
      color: var(--amber);
    }

    .badge.conf-low {
      background: var(--grey-soft);
      color: var(--grey);
    }

    .badge.state-badge {
      background: #eef2f6;
      color: var(--muted);
    }

    .reasoning-card {
      border: 1px solid var(--line);
      border-radius: 12px;
      background: #ffffff;
      box-shadow: 0 4px 12px rgba(27, 39, 51, 0.05);
      overflow: hidden;
    }

    .reasoning-card summary {
      list-style: none;
      cursor: pointer;
      padding: 16px;
    }

    .reasoning-card summary::-webkit-details-marker {
      display: none;
    }

    .reasoning-content {
      display: grid;
      gap: 12px;
      padding: 0 16px 16px;
    }

    .reasoning-section {
      border: 1px solid var(--line);
      border-radius: 10px;
      background: var(--panel-soft);
      padding: 12px 14px;
    }

    .reasoning-section h4 {
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 0.82rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .red-flag-panel {
      border-color: #efc1c1;
      background: var(--red-soft);
    }

    .red-flag-panel .panel-header {
      background: rgba(255, 255, 255, 0.45);
      border-bottom-color: #efc1c1;
    }

    .emergency-alert {
      border: 1px solid #e6aaaa;
      border-radius: var(--radius);
      background: #fdeaea;
      box-shadow: var(--shadow);
      padding: 16px 18px;
      margin-bottom: 18px;
    }

    .emergency-alert-title {
      margin: 0 0 10px;
      color: #9f1f1f;
      font-size: 1rem;
      font-weight: 700;
    }

    .emergency-alert ul {
      margin: 0;
      padding-left: 22px;
    }

    .emergency-alert li {
      color: #5a2323;
      font-weight: 700;
    }

    .muted,
    .empty-copy {
      color: var(--muted);
    }

    .empty-copy {
      margin: 0;
      font-size: 0.96rem;
      line-height: 1.5;
    }

    .note-preview {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font: inherit;
      line-height: 1.55;
      color: var(--ink);
    }

    @media (max-width: 960px) {
      .workspace {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <div class="page-header">
      <p class="eyebrow">Two-Stage Clinical Reasoning</p>
      <h1>Clinical Triage</h1>
      <p class="header-copy">Structured clinical note review with progressive reveal. Findings appear first, then the differential and reasoning.</p>
    </div>

    <div class="workspace">
      <div class="column">
        <section class="panel">
          <div class="panel-header">
            <h2>Clinical Note</h2>
          </div>
          <div class="panel-body">
            <textarea id="text" placeholder="Enter the patient note here"></textarea>
            <div class="input-meta">
              <p class="helper-text">Presentation only. Existing pipeline output is shown without changing reasoning, thresholds, or rule-outs.</p>
              <button id="submit" type="button">Run Triage</button>
            </div>
          </div>
        </section>
        <div id="top-output"></div>
        <div id="left-output"></div>
      </div>
      <div class="column" id="right-output"></div>
    </div>
  </div>

  <script>
    const submitButton = document.getElementById("submit");
    const textInput = document.getElementById("text");
    const topOutput = document.getElementById("top-output");
    const leftOutput = document.getElementById("left-output");
    const rightOutput = document.getElementById("right-output");

    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }

    function humanizeIdentifier(identifier) {
      const displayLabels = {
        rlq_pain: "RLQ Pain",
      };

      if (displayLabels[identifier]) {
        return displayLabels[identifier];
      }

      return String(identifier || "")
        .replaceAll("_", " ")
        .replace(/\b\w/g, (char) => char.toUpperCase());
    }

    function formatConfidence(value) {
      return typeof value === "number" ? value.toFixed(2) : "0.00";
    }

    function uniqueStrings(items) {
      return [...new Set((items || []).filter(Boolean))];
    }

    function hasItems(items) {
      return Array.isArray(items) && items.length > 0;
    }

    function getDiagnosisResults(parsed) {
      const diagnosisResults = Array.isArray(parsed.diagnosis_results) ? [...parsed.diagnosis_results] : [];
      diagnosisResults.sort((left, right) => (right.confidence || 0) - (left.confidence || 0));
      return diagnosisResults.slice(0, 3);
    }

    function getConfidenceClass(value) {
      if (value >= 0.7) {
        return "conf-high";
      }

      if (value >= 0.4) {
        return "conf-mid";
      }

      return "conf-low";
    }

    function renderBulletList(items) {
      if (!items || items.length === 0) {
        return "";
      }

      return `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
    }

    function getParsed(data) {
      return data && data.parsed ? data.parsed : {};
    }

    function getDisplayFeatureIds(featureIds) {
      const ids = Array.isArray(featureIds) ? [...featureIds] : [];
      const featureSet = new Set(ids);

      let filteredIds = ids;

      if (featureSet.has("thunderclap_headache")) {
        filteredIds = filteredIds.filter((featureId) => featureId !== "headache");
      }

      if (featureSet.has("rlq_pain")) {
        filteredIds = filteredIds.filter((featureId) => featureId !== "right_lower_quadrant_pain");
      }

      return filteredIds;
    }

    function getDisplayFeatureLabels(featureIds) {
      return uniqueStrings(getDisplayFeatureIds(featureIds).map((featureId) => humanizeIdentifier(featureId)));
    }

    function getSupportedDiagnoses(parsed) {
      return getDiagnosisResults(parsed).filter((diagnosis) => diagnosis.state !== "ruled_out");
    }

    function getRuledOutDiagnoses(parsed) {
      return getDiagnosisResults(parsed).filter((diagnosis) => diagnosis.state === "ruled_out");
    }

    function getAssertionsByPolarity(parsed, polarity) {
      const assertions = Array.isArray(parsed.assertions) ? parsed.assertions : [];
      return assertions.filter((assertion) => assertion.polarity === polarity).map((assertion) => assertion.meaning_id);
    }

    function getPatternForDiagnosis(parsed, diagnosisId) {
      return (parsed.pattern_results || []).find((patternResult) => patternResult.id === diagnosisId) || null;
    }

    function getAssertionById(parsed, assertionId) {
      return (parsed.assertions || []).find((assertion) => assertion.id === assertionId) || null;
    }

    function getConditionState(data, diagnosisId) {
      return (data.condition_states || []).find((conditionState) => conditionState.id === diagnosisId) || null;
    }

    function getReasoningLabels(data, diagnosisId, signalType) {
      const conditionState = getConditionState(data, diagnosisId);
      if (!conditionState) {
        return [];
      }

      return uniqueStrings(
        (conditionState.signal_breakdown || [])
          .filter((signalEntry) => signalEntry.type === signalType && signalEntry.label)
          .map((signalEntry) => signalEntry.label)
      );
    }

    function getSupportSignals(data, parsed, diagnosis) {
      const pattern = getPatternForDiagnosis(parsed, diagnosis.diagnosis);
      const patternSignals = pattern ? getDisplayFeatureLabels(pattern.matched) : [];
      const assertionSignals = getDisplayFeatureLabels(getAssertionsByPolarity(parsed, "present"));
      const derivedSignals = getDisplayFeatureLabels(parsed.derived_features || []);
      const reasoningSignals = getReasoningLabels(data, diagnosis.diagnosis, "supporting");
      return uniqueStrings([...reasoningSignals, ...patternSignals, ...assertionSignals, ...derivedSignals]).slice(0, 6);
    }

    function getRuledOutReason(parsed, diagnosis) {
      const context = parsed.context || {};
      if (diagnosis.diagnosis === "ectopic_pregnancy" && context.sex === "male") {
        return "Ruled out by male sex context";
      }
      return "Ruled out by current context";
    }

    function getCompetingDiagnosisNotes(data, parsed, currentDiagnosisId) {
      const supportedDiagnoses = getSupportedDiagnoses(parsed)
        .filter((diagnosis) => diagnosis.diagnosis !== currentDiagnosisId)
        .map((diagnosis) => `${humanizeIdentifier(diagnosis.diagnosis)} remains lower confidence at ${formatConfidence(diagnosis.confidence || 0)}`);
      const ruledOutDiagnoses = getRuledOutDiagnoses(parsed)
        .filter((diagnosis) => diagnosis.diagnosis !== currentDiagnosisId)
        .map((diagnosis) => `${humanizeIdentifier(diagnosis.diagnosis)}: ${getRuledOutReason(parsed, diagnosis)}`);
      const reasoningAgainst = getReasoningLabels(data, currentDiagnosisId, "contradiction");
      const negatedEvidence = getAssertionsByPolarity(parsed, "negated").map((featureId) => `${humanizeIdentifier(featureId)} is negated`);
      return uniqueStrings([...reasoningAgainst, ...ruledOutDiagnoses, ...supportedDiagnoses, ...negatedEvidence]).slice(0, 6);
    }

    function getDiscriminatingQuestions(data, parsed) {
      const questions = [];
      if (data && data.next_question && data.next_question.text) {
        questions.push(data.next_question.text);
      }
      questions.push(...getAssertionsByPolarity(parsed, "uncertain").map((featureId) => `Clarify whether ${humanizeIdentifier(featureId).toLowerCase()} is actually present`));
      if (parsed.clarification_question) {
        questions.push(parsed.clarification_question);
      }
      return uniqueStrings(questions).slice(0, 3);
    }

    function getRedFlagMessages(parsed) {
      return (parsed.red_flags || []).map((flag) => flag.message);
    }

    function getRedFlagTriggers(parsed) {
      const triggerFeatureIds = ["thunderclap_headache", "neck_stiffness", "photophobia"];
      const presentFeatures = new Set(parsed.present_feature_ids || []);
      const matchedTriggers = triggerFeatureIds
        .filter((featureId) => presentFeatures.has(featureId))
        .map((featureId) => humanizeIdentifier(featureId));

      return matchedTriggers.length > 0 ? matchedTriggers : getRedFlagMessages(parsed);
    }

    function getTimelineItems(parsed) {
      const relationItems = [];

      for (const relation of (parsed.relations || [])) {
        if (relation.type === "temporal_order") {
          const earlierAssertion = getAssertionById(parsed, relation.earlier);
          const laterAssertion = getAssertionById(parsed, relation.later);
          if (earlierAssertion && laterAssertion) {
            relationItems.push(`${humanizeIdentifier(earlierAssertion.meaning_id)} before ${humanizeIdentifier(laterAssertion.meaning_id)}`);
          }
          continue;
        }

        if (relation.type === "migration" && relation.source && relation.target) {
          relationItems.push(`${humanizeIdentifier(relation.source)} migrated to ${humanizeIdentifier(relation.target)}`);
        }
      }

      const derivedTemporalItems = [];
      if ((parsed.derived_features || []).includes("pain_before_vomiting")) {
        derivedTemporalItems.push("Pain before vomiting");
      }
      if ((parsed.derived_features || []).includes("vomiting_before_pain")) {
        derivedTemporalItems.push("Vomiting before pain");
      }
      if ((parsed.derived_features || []).includes("pain_migration")) {
        derivedTemporalItems.push("Pain migration present");
      }

      return uniqueStrings([...relationItems, ...derivedTemporalItems]);
    }

    function renderPanel(title, body, extraClass = "") {
      if (!body) {
        return "";
      }

      return `<section class="panel ${extraClass}"><div class="panel-header"><h2>${escapeHtml(title)}</h2></div><div class="panel-body">${body}</div></section>`;
    }

    function renderListBlock(title, items) {
      if (!hasItems(items)) {
        return "";
      }

      return `<div class="list-block"><p class="section-label">${escapeHtml(title)}</p>${renderBulletList(items)}</div>`;
    }

    function renderExtractedFindings(parsed) {
      const presentAssertions = getDisplayFeatureLabels(getAssertionsByPolarity(parsed, "present"));
      const negatedAssertions = getDisplayFeatureLabels(getAssertionsByPolarity(parsed, "negated"));
      const uncertainAssertions = getDisplayFeatureLabels(getAssertionsByPolarity(parsed, "uncertain"));
      const derivedFeatures = getDisplayFeatureLabels(parsed.derived_features || []);
      const meaningMatches = getDisplayFeatureLabels((parsed.meaning_matches || []).map((match) => match.meaning_id));
      const body = [
        renderListBlock("Present", presentAssertions),
        renderListBlock("Negated", negatedAssertions),
        renderListBlock("Uncertain", uncertainAssertions),
        renderListBlock("Derived", derivedFeatures),
        renderListBlock("Matched Terms", meaningMatches),
      ].filter(Boolean).join("");

      return renderPanel("Extracted Findings", body);
    }

    function renderSubmittedNote(data) {
      if (!data || !data.raw_input) {
        return "";
      }

      return renderPanel("Submitted Note", `<pre class="note-preview">${escapeHtml(data.raw_input)}</pre>`);
    }

    function renderClinicalState(parsed) {
      const state = parsed.clinical_state || {};
      const context = parsed.context || {};
      const contextEntries = [];
      if (context.sex) {
        contextEntries.push(`Sex: ${context.sex}`);
      }
      if (context.pregnancy_possible !== undefined) {
        contextEntries.push(`Pregnancy possible: ${context.pregnancy_possible === true ? "yes" : "no"}`);
      }

      const stateLines = [
        ...contextEntries,
        ...getDisplayFeatureIds(state.present || []).map((item) => `Present: ${humanizeIdentifier(item)}`),
        ...getDisplayFeatureIds(state.negated || []).map((item) => `Negated: ${humanizeIdentifier(item)}`),
        ...getDisplayFeatureIds(state.uncertain || []).map((item) => `Uncertain: ${humanizeIdentifier(item)}`),
      ];

      const body = renderBulletList(stateLines);
      return renderPanel("Clinical State", body);
    }

    function renderTimeline(parsed) {
      const timelineItems = getTimelineItems(parsed);
      if (!hasItems(timelineItems)) {
        return "";
      }

      const body = `<div class="timeline-box"><ul class="timeline-list">${timelineItems.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div>`;
      return renderPanel("Timeline", body);
    }

    function renderCandidateDiagnoses(parsed) {
      const diagnoses = getDiagnosisResults(parsed);
      if (!hasItems(diagnoses)) {
        return "";
      }

      const cards = diagnoses.map((diagnosis) => {
        const confidenceClass = getConfidenceClass(diagnosis.confidence || 0);
        const ruledOut = diagnosis.state === "ruled_out";
        const stateLabel = ruledOut ? "Less likely" : (diagnosis.state || "possible");

        return `
          <article class="diagnosis-card ${confidenceClass} ${ruledOut ? "ruled-out" : ""}">
            <div class="diagnosis-topline">
              <div>
                <p class="diagnosis-title">${escapeHtml(humanizeIdentifier(diagnosis.diagnosis))}</p>
                <p class="diagnosis-subtitle">${escapeHtml(stateLabel)}</p>
              </div>
              <div class="diagnosis-tags">
                <span class="badge ${confidenceClass}">${escapeHtml(formatConfidence(diagnosis.confidence || 0))}</span>
                <span class="badge state-badge">${escapeHtml(diagnosis.state || "possible")}</span>
              </div>
            </div>
          </article>
        `;
      }).join("");

      return renderPanel("Candidate Diagnoses", `<div class="diagnosis-list">${cards}</div>`);
    }

    function renderReasoningSection(title, items) {
      if (!hasItems(items)) {
        return "";
      }

      return `<section class="reasoning-section"><h4>${escapeHtml(title)}</h4>${renderBulletList(items)}</section>`;
    }

    function renderReasoningCard(data, diagnosis) {
      const parsed = getParsed(data);
      const supportSignals = getSupportSignals(data, parsed, diagnosis);
      const againstSignals = getCompetingDiagnosisNotes(data, parsed, diagnosis.diagnosis);
      const questions = getDiscriminatingQuestions(data, parsed);
      const redFlags = getRedFlagMessages(parsed);
      const confidenceClass = getConfidenceClass(diagnosis.confidence || 0);
      const sections = [
        renderReasoningSection("Why This Is Supported", supportSignals),
        renderReasoningSection("Why Less Likely", againstSignals),
        renderReasoningSection("Key Discriminating Question", questions.slice(0, 1)),
        renderReasoningSection("Do-Not-Miss Red Flags", redFlags),
      ].filter(Boolean).join("");

      if (!sections) {
        return "";
      }

      return `
        <details class="reasoning-card" ${diagnosis.state === "ruled_out" ? "" : "open"}>
          <summary>
            <div class="diagnosis-topline">
              <div>
                <p class="diagnosis-title">${escapeHtml(humanizeIdentifier(diagnosis.diagnosis))}</p>
                <p class="diagnosis-subtitle">${escapeHtml(diagnosis.state || "possible")}</p>
              </div>
              <div class="diagnosis-tags">
                <span class="badge ${confidenceClass}">${escapeHtml(formatConfidence(diagnosis.confidence || 0))}</span>
              </div>
            </div>
          </summary>
          <div class="reasoning-content">${sections}</div>
        </details>
      `;
    }

    function renderReasoningStage(data) {
      const parsed = getParsed(data);
      const diagnoses = getDiagnosisResults(parsed);
      const cards = diagnoses.map((diagnosis) => renderReasoningCard(data, diagnosis)).filter(Boolean).join("");
      if (!cards) {
        return "";
      }

      return renderPanel("Reasoning", cards);
    }

    function renderRedFlags(parsed) {
      const triggerItems = getRedFlagTriggers(parsed);
      if (!hasItems(triggerItems)) {
        return "";
      }

      return `
        <section class="emergency-alert">
          <p class="emergency-alert-title">⚠️ Possible emergency condition detected</p>
          <ul>
            ${triggerItems.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
          </ul>
        </section>
      `;
    }

    function renderOutput(data) {
      if (!data || !data.raw_input) {
        topOutput.innerHTML = "";
        leftOutput.innerHTML = "";
        rightOutput.innerHTML = "";
        return;
      }

      const parsed = getParsed(data);
      const topPanels = renderRedFlags(parsed);
      const leftPanels = [
        renderSubmittedNote(data),
        renderExtractedFindings(parsed),
        renderClinicalState(parsed),
        renderTimeline(parsed),
      ].filter(Boolean).join("");

      const rightPanels = [
        renderCandidateDiagnoses(parsed),
        renderReasoningStage(data),
      ].filter(Boolean).join("");

      topOutput.innerHTML = topPanels;
      leftOutput.innerHTML = leftPanels;
      rightOutput.innerHTML = rightPanels;
    }

    submitButton.addEventListener("click", async () => {
      const text = textInput.value.trim();
      if (!text) {
        renderOutput(null);
        return;
      }

      const response = await fetch("/triage", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({text}),
      });

      const data = await response.json();
      renderOutput(data);
    });
  </script>
</body>
</html>
	"""


@app.post("/triage")
def triage() -> tuple:
	request_data = request.get_json(silent=True) or {}
	user_input = (request_data.get("text") or "").strip()

	if not user_input:
		return jsonify(_empty_case_payload()), 200

	case_payload = build_case_payload(user_input)
	return jsonify(
		{
			"raw_input": case_payload["input"],
			"parsed": case_payload["parsed"],
			"condition_states": case_payload["condition_states"],
			"investigations": case_payload["investigations"],
			"safety_flags": case_payload["safety_flags"],
			"next_question": case_payload["next_question"],
		}
	), 200


if __name__ == "__main__":
	app.run(debug=True, host="0.0.0.0", port=5000)
