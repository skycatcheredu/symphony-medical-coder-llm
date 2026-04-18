(function () {
  const $ = (id) => document.getElementById(id);

  const noteEl = $("note");
  const ontologyEl = $("ontology");
  const providerEl = $("provider");
  const modelEl = $("model");
  const runBtn = $("run");
  const loadingEl = $("loading");
  const errorEl = $("error");
  const resultsEl = $("results");
  const summaryEl = $("summary");
  const dxBody = $("dx-table").querySelector("tbody");
  const pxBody = $("px-table").querySelector("tbody");
  const traceEl = $("trace");
  const copyBtn = $("copy-json");
  const downloadEl = $("download-json");

  let lastPayload = null;

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
    runBtn.disabled = on;
  }

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
      provider: providerEl.value || null,
      model: modelEl.value.trim() || null,
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
        const detail = data.detail != null ? String(data.detail) : res.statusText || "Request failed";
        setError(detail);
        return;
      }
      lastPayload = data;
      summaryEl.textContent = data.patientSummary ?? "";
      fillTable(dxBody, data.diagnosisCodes);
      fillTable(pxBody, data.procedureCodes);
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
})();
