"use strict";

const statement = document.querySelector("#statement");
const checkButton = document.querySelector("#check-button");
const badge = document.querySelector("#result-badge");
const title = document.querySelector("#result-title");
const description = document.querySelector("#result-description");
const icon = document.querySelector("#result-icon");
const locationLabel = document.querySelector("#result-location");
const tokenPanel = document.querySelector("#token-panel");
let controller;
let requestId = 0;
let hasResult = false;

function updateEditor() {
  document.querySelector("#char-count").textContent = `${statement.value.length} / 4096`;
  document.querySelector("#line-numbers").textContent = statement.value.split("\n").map((_, index) => index + 1).join("\n");
}

function resetChecks() {
  document.querySelectorAll("[data-check]").forEach(item => {
    item.className = "";
    item.querySelector(".check-symbol").textContent = "·";
  });
  document.querySelector("#check-count").textContent = "0 / 5";
}

function invalidatePending() {
  requestId++;
  if (controller) controller.abort();
  checkButton.disabled = false;
  checkButton.replaceChildren(document.createTextNode("Check statement "));
  const arrow = document.createElement("span");
  arrow.textContent = "↗";
  arrow.setAttribute("aria-hidden", "true");
  checkButton.append(arrow);
  document.querySelector("#result-content").removeAttribute("aria-busy");
}

function setState(state, heading, detail, symbol, label) {
  badge.className = `result-badge ${state}`;
  badge.textContent = label;
  icon.className = `result-icon ${state}`;
  icon.textContent = symbol;
  title.textContent = heading;
  description.textContent = detail;
  locationLabel.hidden = true;
}

function onEdit() {
  invalidatePending();
  updateEditor();
  statement.removeAttribute("aria-invalid");
  if (hasResult) {
    hasResult = false;
    setState("stale", "Statement updated.", "Check your statement again to see the latest analysis.", "↻", "EDITED");
    resetChecks();
    tokenPanel.hidden = true;
  }
}

async function validate() {
  invalidatePending();
  const id = requestId;
  const source = statement.value;
  controller = new AbortController();
  checkButton.disabled = true;
  checkButton.textContent = "Checking…";
  document.querySelector("#result-content").setAttribute("aria-busy", "true");
  try {
    const response = await fetch("/api/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ statement: source }),
      signal: controller.signal,
    });
    const result = await response.json();
    if (id !== requestId) return;
    if (!response.ok) throw new Error(result.error || "The statement could not be checked.");
    hasResult = true;
    setState(result.valid ? "valid" : "invalid", result.message, result.detail, result.valid ? "✓" : "×", result.valid ? "VALID" : "INVALID");
    statement.setAttribute("aria-invalid", String(!result.valid));
    if (!result.valid) {
      locationLabel.textContent = `Line ${result.line}, column ${result.column}`;
      locationLabel.hidden = false;
    }
    let passed = 0;
    for (const check of result.checks) {
      const item = document.querySelector(`[data-check="${check.id}"]`);
      item.className = check.status;
      item.querySelector(".check-symbol").textContent = check.status === "pass" ? "✓" : check.status === "fail" ? "×" : "·";
      if (check.status === "pass") passed++;
    }
    document.querySelector("#check-count").textContent = `${passed} / 5`;
    const tokens = document.querySelector("#tokens");
    tokens.replaceChildren();
    for (const token of result.tokens) {
      const chip = document.createElement("div");
      chip.className = `token ${token.kind}`;
      const value = document.createElement("code");
      value.textContent = token.value;
      const kind = document.createElement("span");
      kind.textContent = token.kind.toUpperCase();
      chip.append(value, kind);
      tokens.append(chip);
    }
    document.querySelector("#token-count").textContent = `${result.tokens.length} TOKENS`;
    tokenPanel.hidden = result.tokens.length === 0;
  } catch (error) {
    if (error.name === "AbortError" || id !== requestId) return;
    hasResult = true;
    resetChecks();
    tokenPanel.hidden = true;
    setState("error", "Couldn’t connect.", `${error.message} Make sure the Python server is running, then try again.`, "!", "ERROR");
  } finally {
    if (id === requestId) invalidatePending();
  }
}

statement.addEventListener("input", onEdit);
statement.addEventListener("scroll", () => {
  document.querySelector("#line-numbers").scrollTop = statement.scrollTop;
});
statement.addEventListener("keydown", event => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    validate();
  }
});
checkButton.addEventListener("click", validate);
document.querySelector("#clear-button").addEventListener("click", () => {
  invalidatePending();
  statement.value = "";
  statement.removeAttribute("aria-invalid");
  hasResult = false;
  resetChecks();
  updateEditor();
  tokenPanel.hidden = true;
  setState("idle", "Ready when you are.", "Enter an assignment and check it. We’ll take it one token at a time.", "⌁", "READY");
  statement.focus();
});
document.querySelectorAll(".example").forEach(button => {
  button.addEventListener("click", () => {
    statement.value = button.dataset.source;
    onEdit();
    statement.focus();
    validate();
  });
});
updateEditor();
