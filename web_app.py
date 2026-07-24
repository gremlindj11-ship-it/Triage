import json
import os
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request

import engine.language.seed
from engine.case_pipeline import build_case_payload
from engine.validation import validate_language_alignment


app = Flask(__name__)


validate_language_alignment()


NOTES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_notes.json")


def _load_notes() -> list:
	if not os.path.exists(NOTES_FILE):
		return []
	with open(NOTES_FILE, "r", encoding="utf-8") as notes_file:
		return json.load(notes_file)


def _save_notes(notes: list) -> None:
	with open(NOTES_FILE, "w", encoding="utf-8") as notes_file:
		json.dump(notes, notes_file, indent=2)


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

    input[type="text"] {
      width: 100%;
      padding: 12px 14px;
      border: 1px solid var(--line-strong);
      border-radius: 10px;
      background: #ffffff;
      color: var(--ink);
      font: inherit;
      outline: none;
    }

    input[type="text"]:focus {
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

    button.secondary {
      background: #ffffff;
      color: #455a6d;
    }

    button.secondary:hover {
      background: #eef2f6;
    }

    .button-row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
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
    .state-list,
    .signal-list {
      margin: 0;
      padding-left: 18px;
    }

    li + li {
      margin-top: 6px;
    }

    .signal-list li.signal-supporting {
      color: var(--green);
    }

    .signal-list li.signal-contradiction,
    .signal-list li.signal-rule_out {
      color: var(--red);
    }

    .signal-list li.signal-temporal {
      color: var(--amber);
    }

    .timeline-box {
      border: 1px solid var(--line);
      border-radius: 12px;
      background: var(--panel-soft);
      padding: 14px 16px;
    }

    .hypothesis-block {
      border: 1px solid var(--line);
      border-radius: 12px;
      background: var(--panel-soft);
      padding: 16px;
      margin-bottom: 14px;
    }

    .hypothesis-title {
      margin: 0;
      font-size: 1.3rem;
      font-weight: 700;
    }

    .hypothesis-subtitle {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 0.94rem;
    }

    .other-possibility-list {
      display: grid;
      gap: 8px;
    }

    .other-possibility-row {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 12px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: #ffffff;
      padding: 10px 12px;
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

    .badge.state-eligible {
      background: var(--green-soft);
      color: var(--green);
    }

    .badge.state-insufficient {
      background: var(--amber-soft);
      color: var(--amber);
    }

    .badge.state-ruled_out {
      background: var(--grey-soft);
      color: var(--grey);
    }

    .reasoning-section {
      border: 1px solid var(--line);
      border-radius: 10px;
      background: var(--panel-soft);
      padding: 12px 14px;
    }

    .reasoning-section + .reasoning-section {
      margin-top: 12px;
    }

    .reasoning-section h4 {
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 0.82rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .tech-details summary {
      cursor: pointer;
      padding: 14px 18px;
      font-size: 0.92rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
      background: var(--panel-soft);
      border-bottom: 1px solid var(--line);
      list-style: none;
    }

    .tech-details summary::-webkit-details-marker {
      display: none;
    }

    .tech-details[open] summary {
      border-bottom: 1px solid var(--line);
    }

    .tech-details .panel-body {
      display: grid;
      gap: 14px;
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

    .question-card {
      border: 1px solid #cfdae3;
      border-radius: 12px;
      background: #eef4f9;
      padding: 14px 16px;
    }

    .question-text {
      margin: 0 0 4px;
      font-weight: 700;
      font-size: 1.02rem;
    }

    .question-reason {
      margin: 0 0 12px;
      color: var(--muted);
      font-size: 0.9rem;
    }

    .answer-row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }

    .answer-row input[type="text"] {
      flex: 1 1 220px;
    }

    .status-note {
      margin: 0;
      color: var(--muted);
      font-size: 0.92rem;
      font-style: italic;
    }

    .notes-list {
      display: grid;
      gap: 8px;
      margin: 0 0 12px;
      padding: 0;
      list-style: none;
      max-height: 260px;
      overflow-y: auto;
    }

    .note-item {
      border: 1px solid var(--line);
      border-radius: 10px;
      background: var(--panel-soft);
      padding: 10px 12px;
      cursor: pointer;
    }

    .note-item:hover {
      border-color: var(--line-strong);
      background: #eef2f6;
    }

    .note-item-timestamp {
      margin: 0 0 4px;
      color: var(--muted);
      font-size: 0.78rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }

    .note-item-preview {
      margin: 0;
      font-size: 0.92rem;
      line-height: 1.4;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
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
      <p class="eyebrow">Clinical Reasoning Engine</p>
      <h1>Clinical Triage</h1>
      <p class="header-copy">Differential diagnosis, investigations, and safety flags, in plain language. Answer the next question to keep refining, or expand Technical Details to inspect raw pipeline internals.</p>
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
              <div class="button-row">
                <button id="reset" type="button" class="secondary">Start Over</button>
                <button id="submit" type="button">Run Triage</button>
              </div>
            </div>
          </div>
        </section>
        <div id="conversation-output"></div>
        <section class="panel">
          <div class="panel-header">
            <h2>Saved Notes</h2>
          </div>
          <div class="panel-body">
            <ul class="notes-list" id="notes-list"></ul>
            <button id="save-note" type="button" class="secondary">Save Current Note</button>
          </div>
        </section>
      </div>
      <div class="column">
        <div id="top-output"></div>
        <div id="primary-output"></div>
        <div id="tech-output"></div>
      </div>
    </div>
  </div>

  <script>
    const submitButton = document.getElementById("submit");
    const resetButton = document.getElementById("reset");
    const saveNoteButton = document.getElementById("save-note");
    const textInput = document.getElementById("text");
    const conversationOutput = document.getElementById("conversation-output");
    const notesListEl = document.getElementById("notes-list");
    const topOutput = document.getElementById("top-output");
    const primaryOutput = document.getElementById("primary-output");
    const techOutput = document.getElementById("tech-output");

    const MAX_TURNS = 3;
    const RULE_LABELS = {
      pregnancy_required: "No evidence of pregnancy",
      male_context: "Male patient",
    };

    let conversation = null; // { currentText, previousFeatureIds, turnCount, done, lastData }

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

    function getAssertionsByPolarity(parsed, polarity) {
      const assertions = Array.isArray(parsed.assertions) ? parsed.assertions : [];
      return assertions.filter((assertion) => assertion.polarity === polarity).map((assertion) => assertion.meaning_id);
    }

    function getAssertionById(parsed, assertionId) {
      return (parsed.assertions || []).find((assertion) => assertion.id === assertionId) || null;
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

    // --------------------------------------------------------------
    // Primary result: sourced from condition_states / investigations /
    // safety_flags / next_question (the reasoning engine's actual
    // user-facing output), ported from ui.py's terminal renderer so the
    // web UI and CLI agree on what "the diagnosis" means.
    // --------------------------------------------------------------

    function getTopConditionState(conditionStates) {
      return hasItems(conditionStates) ? conditionStates[0] : null;
    }

    function getSecondaryConditionStates(conditionStates) {
      return hasItems(conditionStates) ? conditionStates.slice(1) : [];
    }

    function getMainHypothesisText(conditionState) {
      if (!conditionState) {
        return "No clear diagnosis yet";
      }
      const diagnosticState = conditionState.diagnostic_state;
      if (diagnosticState === "ruled_out") {
        return "Not possible";
      }
      if (diagnosticState === "insufficient") {
        return "More information needed";
      }
      if (diagnosticState === "eligible") {
        return humanizeIdentifier(conditionState.id || "");
      }
      return "No clear diagnosis yet";
    }

    function getRuleLabel(ruleId) {
      return RULE_LABELS[ruleId] || humanizeIdentifier(ruleId);
    }

    function getSupportingSignalEntries(conditionState) {
      if (!conditionState) {
        return [];
      }
      return (conditionState.signal_breakdown || []).filter((entry) =>
        ["supporting", "temporal"].includes(entry.type || "supporting")
      );
    }

    function getMissingRequirements(conditionState) {
      if (!conditionState) {
        return [];
      }
      const requirements = (conditionState.rules || {}).requirements || [];
      return requirements
        .filter((requirement) => requirement.status === "missing")
        .map((requirement) => getRuleLabel(requirement.id || ""));
    }

    function getExclusions(conditionState) {
      if (!conditionState) {
        return [];
      }
      const exclusions = (conditionState.rules || {}).exclusions || [];
      return exclusions.map((exclusion) => getRuleLabel(exclusion.id || ""));
    }

    function getDisplayMode(conditionState) {
      if (!conditionState) {
        return "insufficient";
      }
      if (conditionState.diagnostic_state === "ruled_out") {
        return "exclusion";
      }
      if (hasItems(getMissingRequirements(conditionState))) {
        return "requirement";
      }
      if (conditionState.should_display) {
        return "hypothesis";
      }
      return "insufficient";
    }

    function getSectionSpecs(conditionState) {
      const supportingSignals = getSupportingSignalEntries(conditionState);
      const missingRequirements = getMissingRequirements(conditionState);
      const exclusions = getExclusions(conditionState);
      const displayMode = getDisplayMode(conditionState);

      if (displayMode === "exclusion") {
        return [
          {title: "Excluded Because", items: exclusions, itemType: "text"},
          {title: "Conflicting Evidence", items: supportingSignals, itemType: "signal"},
        ];
      }
      if (displayMode === "requirement") {
        return [
          {title: "Still Needed To Confirm", items: missingRequirements, itemType: "text"},
          {title: "Supporting Evidence", items: supportingSignals, itemType: "signal"},
        ];
      }
      if (displayMode === "hypothesis") {
        return [
          {title: "Supporting Evidence", items: supportingSignals, itemType: "signal"},
          {title: "Still Needed To Confirm", items: missingRequirements, itemType: "text"},
        ];
      }
      return [{title: "Supporting Evidence", items: supportingSignals, itemType: "signal"}];
    }

    function formatSignalEntry(entry) {
      const type = entry.type || "supporting";
      const label = entry.label ? entry.label : humanizeIdentifier(entry.feature_id || "");
      if (type === "contradiction") {
        return `${label} (contradicts this diagnosis)`;
      }
      if (type === "temporal") {
        return `${label} (timing modifier)`;
      }
      if (entry.strength) {
        return `${label} (${entry.strength})`;
      }
      return label;
    }

    function renderSignalList(entries) {
      if (!hasItems(entries)) {
        return "";
      }
      const items = entries
        .map((entry) => `<li class="signal-${entry.type || "supporting"}">${escapeHtml(formatSignalEntry(entry))}</li>`)
        .join("");
      return `<ul class="signal-list">${items}</ul>`;
    }

    function renderSectionSpec(spec) {
      if (!hasItems(spec.items)) {
        return "";
      }
      const body = spec.itemType === "signal" ? renderSignalList(spec.items) : renderBulletList(spec.items);
      return `<section class="reasoning-section"><h4>${escapeHtml(spec.title)}</h4>${body}</section>`;
    }

    function renderOtherPossibilities(conditionStates) {
      const secondary = getSecondaryConditionStates(conditionStates);
      if (!hasItems(secondary)) {
        return "";
      }
      const rows = secondary
        .map((conditionState) => {
          const stateClass = `state-${conditionState.diagnostic_state || "insufficient"}`;
          const stateLabel = conditionState.diagnostic_state === "ruled_out" ? "Not possible" : (conditionState.diagnostic_state || "possible").replace("_", " ");
          return `
            <div class="other-possibility-row">
              <span>${escapeHtml(humanizeIdentifier(conditionState.id || ""))}</span>
              <span class="badge ${stateClass}">${escapeHtml(stateLabel)}</span>
            </div>
          `;
        })
        .join("");
      return `<div class="list-block"><p class="section-label">Other Possibilities</p><div class="other-possibility-list">${rows}</div></div>`;
    }

    function renderInvestigations(data) {
      const investigations = data.investigations || [];
      if (!hasItems(investigations)) {
        return "";
      }
      return `<div class="list-block"><p class="section-label">Recommended Investigations</p>${renderBulletList(investigations)}</div>`;
    }

    function renderPrimaryResult(data) {
      const conditionStates = data.condition_states || [];
      const topConditionState = getTopConditionState(conditionStates);
      const hypothesisText = getMainHypothesisText(topConditionState);
      const sectionSpecs = getSectionSpecs(topConditionState);

      const stateClass = topConditionState ? `state-${topConditionState.diagnostic_state || "insufficient"}` : "";
      const badge = topConditionState
        ? `<span class="badge ${stateClass}">${escapeHtml((topConditionState.diagnostic_state || "").replace("_", " ") || "assessing")}</span>`
        : "";

      const sections = sectionSpecs.map(renderSectionSpec).filter(Boolean).join("");

      const body = `
        <div class="hypothesis-block">
          <p class="hypothesis-title">${escapeHtml(hypothesisText)} ${badge}</p>
          <p class="hypothesis-subtitle">Primary hypothesis from the clinical reasoning engine.</p>
        </div>
        ${sections}
        ${renderOtherPossibilities(conditionStates)}
        ${renderInvestigations(data)}
      `;

      return renderPanel("Clinical Assessment", body);
    }

    function getSafetyMessages(data) {
      const parsed = getParsed(data);
      const reasoningMessages = (data.safety_flags || []).map((flag) => flag.message).filter(Boolean);
      const parserMessages = (parsed.red_flags || []).map((flag) => flag.message).filter(Boolean);
      // Union of both red-flag sources: reasoning.py's safety_flags only covers a
      // narrow set (syncope, shoulder tip pain, haemodynamic instability) and does
      // not include thunderclap headache / neck stiffness / photophobia / reduced
      // consciousness / seizures, which only the parser-layer red_flags cover.
      // Showing only one would silently drop real red-flag coverage.
      return uniqueStrings([...reasoningMessages, ...parserMessages]);
    }

    function renderSafetyBanner(data) {
      const messages = getSafetyMessages(data);
      if (!hasItems(messages)) {
        return "";
      }
      return `
        <section class="emergency-alert">
          <p class="emergency-alert-title">⚠️ Possible emergency condition detected</p>
          <ul>
            ${messages.map((message) => `<li>${escapeHtml(message)}</li>`).join("")}
          </ul>
        </section>
      `;
    }

    // --------------------------------------------------------------
    // Technical details (debug only, collapsed by default)
    // --------------------------------------------------------------

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

      return body ? `<section class="reasoning-section"><h4>Extracted Findings</h4>${body}</section>` : "";
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

      if (!hasItems(stateLines)) {
        return "";
      }
      return `<section class="reasoning-section"><h4>Clinical State (raw)</h4>${renderBulletList(stateLines)}</section>`;
    }

    function renderTimeline(parsed) {
      const timelineItems = getTimelineItems(parsed);
      if (!hasItems(timelineItems)) {
        return "";
      }
      return `<section class="reasoning-section"><h4>Timeline</h4><div class="timeline-box"><ul class="timeline-list">${timelineItems.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul></div></section>`;
    }

    function renderScoreBasedDiagnoses(parsed) {
      const diagnoses = getDiagnosisResults(parsed);
      if (!hasItems(diagnoses)) {
        return "";
      }
      const rows = diagnoses
        .map((diagnosis) => {
          const confidenceClass = getConfidenceClass(diagnosis.confidence || 0);
          return `<li>${escapeHtml(humanizeIdentifier(diagnosis.diagnosis))} — ${escapeHtml(diagnosis.state || "possible")} (confidence ${escapeHtml(formatConfidence(diagnosis.confidence || 0))}, ${confidenceClass.replace("conf-", "")})</li>`;
        })
        .join("");
      return `<section class="reasoning-section"><h4>Score-Based Diagnoses (system 1, debug)</h4><ul>${rows}</ul></section>`;
    }

    function renderPatternResults(parsed) {
      const patterns = parsed.pattern_results || [];
      if (!hasItems(patterns)) {
        return "";
      }
      const rows = patterns
        .map((pattern) => `<li>${escapeHtml(humanizeIdentifier(pattern.id))} — ${escapeHtml(pattern.status)} (score ${pattern.score})</li>`)
        .join("");
      return `<section class="reasoning-section"><h4>Pattern Results</h4><ul>${rows}</ul></section>`;
    }

    function renderTechnicalDetails(data) {
      const parsed = getParsed(data);
      const sections = [
        renderExtractedFindings(parsed),
        renderClinicalState(parsed),
        renderTimeline(parsed),
        renderPatternResults(parsed),
        renderScoreBasedDiagnoses(parsed),
      ].filter(Boolean).join("");

      if (!sections) {
        return "";
      }

      return `
        <details class="panel tech-details">
          <summary>Technical Details (debug)</summary>
          <div class="panel-body">${sections}</div>
        </details>
      `;
    }

    // --------------------------------------------------------------
    // Conversational loop: mirrors main.py's CLI loop exactly (append
    // the answer to the accumulated note text and re-run the full
    // pipeline each turn -- no new backend state, /triage stays
    // stateless). Stops when the feature set stops changing between
    // turns, a turn cap is hit, or there is no next_question.
    // --------------------------------------------------------------

    function featureSetsEqual(a, b) {
      if (!a || !b) {
        return false;
      }
      if (a.size !== b.size) {
        return false;
      }
      for (const value of a) {
        if (!b.has(value)) {
          return false;
        }
      }
      return true;
    }

    function renderConversation() {
      if (!conversation) {
        conversationOutput.innerHTML = "";
        return;
      }

      const data = conversation.lastData;
      const notePreview = renderPanel("Submitted Note", `<pre class="note-preview">${escapeHtml(data.raw_input)}</pre>`);

      let questionBlock = "";
      if (!conversation.done && data.next_question && data.next_question.text) {
        questionBlock = `
          <div class="question-card">
            <p class="question-text">${escapeHtml(data.next_question.text)}</p>
            <p class="question-reason">${escapeHtml(data.next_question.reason || "")}</p>
            <div class="answer-row">
              <input type="text" id="answer-input" placeholder="Type the answer...">
              <button id="answer-submit" type="button">Submit Answer</button>
              <button id="answer-stop" type="button" class="secondary">Stop Asking</button>
            </div>
          </div>
        `;
      } else if (conversation.done) {
        questionBlock = `<p class="status-note">No further information changes the assessment. Final assessment shown on the right.</p>`;
      }

      conversationOutput.innerHTML = renderPanel("Conversation", `${notePreview}${questionBlock}`);

      const answerSubmit = document.getElementById("answer-submit");
      const answerInput = document.getElementById("answer-input");
      const answerStop = document.getElementById("answer-stop");

      if (answerSubmit && answerInput) {
        const submitAnswer = () => {
          const answer = answerInput.value.trim();
          if (!answer) {
            return;
          }
          conversation.currentText = `${conversation.currentText} ${answer}`.trim();
          runConversationTurn();
        };
        answerSubmit.addEventListener("click", submitAnswer);
        answerInput.addEventListener("keydown", (event) => {
          if (event.key === "Enter") {
            submitAnswer();
          }
        });
      }

      if (answerStop) {
        answerStop.addEventListener("click", () => {
          conversation.done = true;
          renderConversation();
        });
      }
    }

    function renderAll() {
      if (!conversation) {
        topOutput.innerHTML = "";
        primaryOutput.innerHTML = "";
        techOutput.innerHTML = "";
        conversationOutput.innerHTML = "";
        return;
      }

      const data = conversation.lastData;
      topOutput.innerHTML = renderSafetyBanner(data);
      primaryOutput.innerHTML = renderPrimaryResult(data);
      techOutput.innerHTML = renderTechnicalDetails(data);
      renderConversation();
    }

    async function runConversationTurn() {
      const response = await fetch("/triage", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({text: conversation.currentText}),
      });
      const data = await response.json();

      const currentFeatureIds = new Set(getParsed(data).present_feature_ids || []);
      conversation.turnCount += 1;

      const noNewInformation = conversation.previousFeatureIds !== null
        && featureSetsEqual(conversation.previousFeatureIds, currentFeatureIds);
      const turnCapReached = conversation.turnCount >= MAX_TURNS;
      const noMoreQuestions = !data.next_question || !data.next_question.text;

      conversation.lastData = data;
      conversation.done = noNewInformation || turnCapReached || noMoreQuestions;
      conversation.previousFeatureIds = currentFeatureIds;

      renderAll();
    }

    submitButton.addEventListener("click", () => {
      const text = textInput.value.trim();
      if (!text) {
        return;
      }
      conversation = {
        currentText: text,
        previousFeatureIds: null,
        turnCount: 0,
        done: false,
        lastData: null,
      };
      runConversationTurn();
    });

    resetButton.addEventListener("click", () => {
      conversation = null;
      textInput.value = "";
      renderAll();
    });

    // --------------------------------------------------------------
    // Saved notes
    // --------------------------------------------------------------

    function formatTimestamp(isoString) {
      const parsed = new Date(isoString);
      if (Number.isNaN(parsed.getTime())) {
        return isoString || "";
      }
      return parsed.toLocaleString();
    }

    function renderSavedNotes(notes) {
      if (!hasItems(notes)) {
        notesListEl.innerHTML = '<p class="empty-copy">No saved notes yet.</p>';
        return;
      }

      notesListEl.innerHTML = notes
        .map((note) => `
          <li class="note-item" data-note-id="${escapeHtml(note.id)}">
            <p class="note-item-timestamp">${escapeHtml(formatTimestamp(note.timestamp))}</p>
            <p class="note-item-preview">${escapeHtml(note.text)}</p>
          </li>
        `)
        .join("");

      notesListEl.querySelectorAll(".note-item").forEach((item, index) => {
        item.addEventListener("click", () => {
          textInput.value = notes[index].text;
          conversation = null;
          renderAll();
        });
      });
    }

    async function loadSavedNotes() {
      const response = await fetch("/notes");
      const notes = await response.json();
      renderSavedNotes(notes);
    }

    saveNoteButton.addEventListener("click", async () => {
      const text = (conversation ? conversation.currentText : textInput.value.trim());
      if (!text) {
        return;
      }
      await fetch("/notes", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({text}),
      });
      await loadSavedNotes();
    });

    loadSavedNotes();
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


@app.get("/notes")
def list_notes() -> tuple:
	notes = _load_notes()
	notes.sort(key=lambda note: note.get("timestamp", ""), reverse=True)
	return jsonify(notes), 200


@app.post("/notes")
def create_note() -> tuple:
	request_data = request.get_json(silent=True) or {}
	text = (request_data.get("text") or "").strip()

	if not text:
		return jsonify({"error": "text is required"}), 400

	note = {
		"id": uuid.uuid4().hex,
		"timestamp": datetime.now(timezone.utc).isoformat(),
		"text": text,
	}
	notes = _load_notes()
	notes.append(note)
	_save_notes(notes)
	return jsonify(note), 201


if __name__ == "__main__":
	app.run(debug=True, host="0.0.0.0", port=5000)
