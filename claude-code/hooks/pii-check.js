#!/usr/bin/env node
/*
 * pii-check.js - a Claude Code UserPromptSubmit hook.
 *
 * It reads the prompt the user just submitted, looks for things that identify
 * real people, and if it finds any it injects a non-blocking warning so the
 * model (and the user) are reminded to de-identify before processing. It does
 * NOT send anything anywhere and it does NOT block by default.
 *
 * Wire it up in .claude/settings.json (see settings.example.json in this folder):
 *
 *   "hooks": {
 *     "UserPromptSubmit": [
 *       { "hooks": [ { "type": "command",
 *                      "command": "node /path/to/pii-check.js" } ] }
 *     ]
 *   }
 *
 * Optional: set REDACT_NAMES to a names-list file and it will also flag those.
 * Set REDACT_BLOCK=1 to make it block submission instead of just warning.
 */
"use strict";

const fs = require("fs");

function luhnOk(number) {
  const digits = number.split("").map(Number);
  let sum = 0;
  for (let i = 0; i < digits.length; i++) {
    let d = digits[digits.length - 1 - i];
    if (i % 2 === 1) {
      d *= 2;
      if (d > 9) d -= 9;
    }
    sum += d;
  }
  return sum % 10 === 0;
}

function loadNames() {
  const path = process.env.REDACT_NAMES;
  if (!path) return [];
  try {
    return fs
      .readFileSync(path, "utf8")
      .split(/\r?\n/)
      .map((s) => s.trim())
      .filter((s) => s && !s.startsWith("#"));
  } catch {
    return [];
  }
}

function detect(text) {
  const counts = {};
  const bump = (k, n) => (counts[k] = (counts[k] || 0) + n);

  const emails = text.match(/\b[\w.+-]+@[\w-]+\.[\w.-]+\b/g) || [];
  if (emails.length) bump("email", emails.length);

  const phones = text.match(/(?<![\w+])(?:\+27|0)(?:[\s-]?\d){9}(?!\d)/g) || [];
  if (phones.length) bump("phone", phones.length);

  const idCandidates = text.match(/(?<!\d)\d{13}(?!\d)/g) || [];
  const ids = idCandidates.filter(luhnOk);
  if (ids.length) bump("ID number", ids.length);

  const names = loadNames();
  if (names.length) {
    const re = new RegExp(
      "\\b(" + names.map((n) => n.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|") + ")\\b",
      "gi"
    );
    const hits = text.match(re) || [];
    if (hits.length) bump("name", hits.length);
  }
  return counts;
}

function main() {
  let raw = "";
  try {
    raw = fs.readFileSync(0, "utf8");
  } catch {
    process.exit(0);
  }

  let prompt = "";
  try {
    const data = JSON.parse(raw);
    prompt = data.prompt || data.user_prompt || "";
  } catch {
    prompt = raw;
  }
  if (!prompt) process.exit(0);

  const counts = detect(prompt);
  const kinds = Object.keys(counts);
  if (!kinds.length) process.exit(0);

  const summary = kinds
    .map((k) => `${counts[k]} ${k}${counts[k] > 1 ? "s" : ""}`)
    .join(", ");

  const message =
    `Heads up: this prompt appears to contain personal data (${summary}). ` +
    `Consider de-identifying it first (redact.py encode) so real values are not ` +
    `sent to the model. This is a reminder, not legal advice.`;

  if (process.env.REDACT_BLOCK === "1") {
    // Block submission and tell the user why.
    console.log(JSON.stringify({ decision: "block", reason: message }));
    process.exit(0);
  }

  // Non-blocking: surface as additional context / a warning.
  console.log(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "UserPromptSubmit",
        additionalContext: message,
      },
    })
  );
  process.exit(0);
}

main();
