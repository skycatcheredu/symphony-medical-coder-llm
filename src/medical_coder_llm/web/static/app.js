(async function () {
  const $ = (id) => document.getElementById(id);

  const noteEl = $("note");
  const ontologyEl = $("ontology");
  const runBtn = $("run");
  const loadingEl = $("loading");
  const errorEl = $("error");
  const resultsEl = $("results");
  const summaryEl = $("summary");
  const dxBody = $("dx-table").querySelector("tbody");
  const pxBody = $("px-table").querySelector("tbody");
  const traceEl = $("trace");
  const thoughtEl = $("thought-process");
  const copyBtn = $("copy-json");
  const downloadEl = $("download-json");

  const ledeDefault = $("lede-default");
  const ledeSetup = $("lede-setup");
  const setupPanel = $("setup-panel");
  const setupLedeNew = $("setup-lede-new");
  const setupLedeOverride = $("setup-lede-override");
  const setupProvider = $("setup-provider");
  const setupModel = $("setup-model");
  const setupOpenaiUrlRow = $("setup-openai-url-row");
  const setupOpenaiUrl = $("setup-openai-url");
  const setupApiKeyLabel = $("setup-api-key-label");
  const setupApiKey = $("setup-api-key");
  const setupApiKeyHint = $("setup-api-key-hint");
  const setupSave = $("setup-save");
  const setupCancel = $("setup-cancel");
  const setupTools = $("setup-tools");
  const btnChangeLlm = $("btn-change-llm");
  const btnClearDotenv = $("btn-clear-dotenv");

  let lastPayload = null;
  /** True until `/api/setup-status` reports no mandatory setup (pessimistic until then). */
  let mustConfigure = true;
  /** True while “Change LLM settings” panel is open (optional cancel). */
  let setupOpenForOverride = false;

  function runShouldBeEnabled() {
    return !mustConfigure && !setupOpenForOverride;
  }

  function syncRunButton() {
    const loading = !loadingEl.classList.contains("hidden");
    runBtn.disabled = loading || !runShouldBeEnabled();
  }

  function formatErrorDetail(data) {
    const d = data.detail;
    if (d == null) return null;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) {
      return d
        .map((item) => {
          if (item && typeof item === "object" && "msg" in item) return String(item.msg);
          try {
            return JSON.stringify(item);
          } catch {
            return String(item);
          }
        })
        .join(" ");
    }
    if (typeof d === "object" && d.msg) return String(d.msg);
    try {
      return JSON.stringify(d);
    } catch {
      return String(d);
    }
  }

  function setError(msg) {
    if (!msg) {
      errorEl.textContent = "";
      errorEl.classList.add("hidden");
      return;
    }
    errorEl.textContent = msg;
    errorEl.classList.remove("hidden");
  }

  function setLoading(on) {
    loadingEl.classList.toggle("hidden", !on);
    syncRunButton();
  }

  function setSetupLedeOverrideMode(on) {
    setupLedeNew.classList.toggle("hidden", on);
    setupLedeOverride.classList.toggle("hidden", !on);
  }

  function showMandatorySetupUi() {
    mustConfigure = true;
    setupOpenForOverride = false;
    setSetupLedeOverrideMode(false);
    setupPanel.classList.remove("hidden");
    setupCancel.classList.add("hidden");
    ledeDefault.classList.add("hidden");
    ledeSetup.classList.remove("hidden");
    setupTools.classList.add("hidden");
    syncRunButton();
  }

  function hideSetupUi() {
    setupPanel.classList.add("hidden");
    setupCancel.classList.add("hidden");
    setSetupLedeOverrideMode(false);
    ledeDefault.classList.remove("hidden");
    ledeSetup.classList.add("hidden");
  }

  function openOverrideSetup() {
    setError("");
    mustConfigure = false;
    setupOpenForOverride = true;
    setSetupLedeOverrideMode(true);
    setupPanel.classList.remove("hidden");
    setupCancel.classList.remove("hidden");
    ledeDefault.classList.remove("hidden");
    ledeSetup.classList.add("hidden");
    syncRunButton();
  }

  function cancelOverrideSetup() {
    setupOpenForOverride = false;
    hideSetupUi();
    syncRunButton();
  }

  function syncProviderUi() {
    const isOpenai = setupProvider.value === "openai";
    setupOpenaiUrlRow.classList.toggle("hidden", !isOpenai);
    setupApiKeyLabel.textContent = isOpenai ? "OpenAI API key" : "Gemini API key";
    setupApiKeyHint.textContent = isOpenai
      ? "Required for OpenAI cloud. Optional for many local servers (any value is often accepted)."
      : "Required. Create a key in Google AI Studio.";
  }

  async function initSetup() {
    try {
      const res = await fetch("/api/setup-status");
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        mustConfigure = false;
        return;
      }
      if (data.needsSetup) {
        mustConfigure = true;
        showMandatorySetupUi();
        syncProviderUi();
        return;
      }
      mustConfigure = false;
      setupTools.classList.toggle("hidden", !data.dotenvPresent);
    } catch {
      mustConfigure = false;
    }
    syncRunButton();
  }

  setupProvider.addEventListener("change", syncProviderUi);

  btnChangeLlm.addEventListener("click", () => {
    openOverrideSetup();
    syncProviderUi();
  });

  btnClearDotenv.addEventListener("click", async () => {
    if (
      !confirm(
        "Remove the .env file from the server’s working directory and clear LLM settings from this process? You will need to configure again before generating codes.",
      )
    ) {
      return;
    }
    setError("");
    btnClearDotenv.disabled = true;
    try {
      const res = await fetch("/api/setup", { method: "DELETE" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(formatErrorDetail(data) || res.statusText || "Could not remove configuration");
        return;
      }
      mustConfigure = true;
      setupOpenForOverride = false;
      setupTools.classList.add("hidden");
      showMandatorySetupUi();
      syncProviderUi();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Network error");
    } finally {
      btnClearDotenv.disabled = false;
    }
  });

  setupCancel.addEventListener("click", () => {
    cancelOverrideSetup();
  });

  setupSave.addEventListener("click", async () => {
    setError("");
    const provider = setupProvider.value;
    const model_name = setupModel.value.trim();
    if (!model_name) {
      setError("Model name is required.");
      return;
    }

    const open_ai_url = setupOpenaiUrl.value.trim();
    const key = setupApiKey.value;

    const body = {
      model_provider: provider,
      model_name,
      open_ai_url: provider === "openai" ? open_ai_url : "",
      openai_api_key: provider === "openai" ? key : "",
      gemini_api_key: provider === "gemini" ? key : "",
      overwrite: setupOpenForOverride,
    };

    setupSave.disabled = true;
    try {
      const res = await fetch("/api/setup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = formatErrorDetail(data) || res.statusText || "Setup failed";
        setError(detail);
        return;
      }
      mustConfigure = false;
      setupOpenForOverride = false;
      hideSetupUi();
      setupTools.classList.remove("hidden");
      syncRunButton();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Network error");
    } finally {
      setupSave.disabled = false;
    }
  });

  function rowForCode(c) {
    const tr = document.createElement("tr");
    tr.innerHTML = [
      escapeHtml(c.code ?? ""),
      escapeHtml(c.description ?? ""),
      escapeHtml(c.codingSystem ?? ""),
      c.confidence != null ? escapeHtml(String(c.confidence)) : "",
    ]
      .map((cell) => `<td>${cell}</td>`)
      .join("");
    return tr;
  }

  function escapeHtml(s) {
    return s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  const STAGE_TITLES = {
    evidence_extraction: "Evidence extraction",
    index_navigation: "Index navigation",
    tabular_validation: "Tabular validation",
    code_reconciliation: "Code reconciliation",
  };

  function stageTitle(stage) {
    return STAGE_TITLES[stage] || stage;
  }

  function fillThoughtProcess(container, trace) {
    container.textContent = "";
    if (!trace || trace.length === 0) {
      const p = document.createElement("p");
      p.className = "thought-lede";
      p.textContent = "No pipeline trace returned.";
      container.appendChild(p);
      return;
    }
    for (const entry of trace) {
      const details = document.createElement("details");
      details.className = "thought-stage";
      const summary = document.createElement("summary");
      const title = escapeHtml(stageTitle(entry.stage));
      const sumLine = escapeHtml(entry.summary != null ? String(entry.summary) : "");
      summary.innerHTML = `<strong>${title}</strong> — ${sumLine}`;
      const pre = document.createElement("pre");
      pre.className = "thought-pre";
      pre.textContent = JSON.stringify(entry.stageOutput != null ? entry.stageOutput : {}, null, 2);
      details.appendChild(summary);
      details.appendChild(pre);
      container.appendChild(details);
    }
  }

  function fillTable(tbody, rows) {
    tbody.textContent = "";
    if (!rows || rows.length === 0) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 4;
      td.textContent = "None";
      tr.appendChild(td);
      tbody.appendChild(tr);
      return;
    }
    for (const c of rows) {
      tbody.appendChild(rowForCode(c));
    }
  }

  async function run() {
    setError("");
    resultsEl.classList.add("hidden");
    lastPayload = null;

    const body = {
      note: noteEl.value,
      ontology: ontologyEl.value.trim() || "data/ontology/codes.csv",
    };

    setLoading(true);
    try {
      const res = await fetch("/api/code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = formatErrorDetail(data) || res.statusText || "Request failed";
        setError(detail);
        return;
      }
      lastPayload = data;
      summaryEl.textContent = data.patientSummary ?? "";
      fillTable(dxBody, data.diagnosisCodes);
      fillTable(pxBody, data.procedureCodes);
      fillThoughtProcess(thoughtEl, data.stageTrace);
      traceEl.textContent = JSON.stringify(data.stageTrace ?? [], null, 2);
      resultsEl.classList.remove("hidden");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Network error");
    } finally {
      setLoading(false);
    }
  }

  runBtn.addEventListener("click", run);

  copyBtn.addEventListener("click", async () => {
    if (!lastPayload) return;
    try {
      await navigator.clipboard.writeText(JSON.stringify(lastPayload, null, 2));
      copyBtn.textContent = "Copied!";
      setTimeout(() => {
        copyBtn.textContent = "Copy JSON";
      }, 1500);
    } catch {
      setError("Could not copy to clipboard.");
    }
  });

  downloadEl.addEventListener("click", (ev) => {
    if (!lastPayload) {
      ev.preventDefault();
      return;
    }
    const blob = new Blob([JSON.stringify(lastPayload, null, 2)], { type: "application/json" });
    downloadEl.href = URL.createObjectURL(blob);
    setTimeout(() => URL.revokeObjectURL(downloadEl.href), 30_000);
  });

  syncRunButton();
  await initSetup();
})();
