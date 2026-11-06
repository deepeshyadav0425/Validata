/**
 * Validata — Authenticity Engine
 * Client Logic, Senior Accessibility & Responsive Visualizations
 */

let currentAnalysisReport = null;
let radarChartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initFontSize();
  initTabs();
  initCharCount();
  initClipboardPaste();
  initFileUpload();
  initHeroSampleChips();
  initViewModeToggles();
  fetchGlobalStats();
  fetchHistory();

  // Forms
  document.getElementById("textAnalysisForm").addEventListener("submit", handleTextSubmit);
  document.getElementById("urlAnalysisForm").addEventListener("submit", handleUrlSubmit);
  document.getElementById("btnClearText").addEventListener("click", clearTextForm);
  document.getElementById("themeToggleBtn").addEventListener("click", toggleTheme);
  document.getElementById("historyFilterSelect").addEventListener("change", () => fetchHistory());

  // Result actions
  document.getElementById("btnNewAnalysis").addEventListener("click", () => {
    document.getElementById("resultsSection").style.display = "none";
    document.getElementById("workspaceSection").scrollIntoView({ behavior: "smooth" });
  });
  document.getElementById("btnPrintReport").addEventListener("click", () => window.print());
  document.getElementById("btnExportJson").addEventListener("click", exportReportJson);

  // Modal
  document.getElementById("modalCloseBtn").addEventListener("click", closeModal);
  document.getElementById("modalDismissBtn").addEventListener("click", closeModal);
  document.getElementById("modalPrintBtn").addEventListener("click", () => window.print());
});

/* ========================================================= */
/* SENIOR-FRIENDLY FONT SIZE SCALING                         */
/* ========================================================= */
function initFontSize() {
  const savedScale = localStorage.getItem("validata_font_scale") || "medium";
  setFontScale(savedScale);

  document.getElementById("btnFontDec").addEventListener("click", () => setFontScale("small"));
  document.getElementById("btnFontReset").addEventListener("click", () => setFontScale("medium"));
  document.getElementById("btnFontInc").addEventListener("click", () => {
    const current = localStorage.getItem("validata_font_scale") || "medium";
    if (current === "medium") setFontScale("large");
    else setFontScale("xlarge");
  });
}

function setFontScale(scale) {
  document.body.classList.remove("font-small", "font-medium", "font-large", "font-xlarge");
  document.body.classList.add(`font-${scale}`);
  localStorage.setItem("validata_font_scale", scale);

  document.querySelectorAll(".btn-text-size").forEach(btn => btn.classList.remove("active"));
  if (scale === "small") document.getElementById("btnFontDec").classList.add("active");
  else if (scale === "medium") document.getElementById("btnFontReset").classList.add("active");
  else document.getElementById("btnFontInc").classList.add("active");

  if (radarChartInstance && currentAnalysisReport) {
    renderRadarChart(currentAnalysisReport.metrics);
  }
}

/* ========================================================= */
/* THEME MANAGEMENT                                          */
/* ========================================================= */
function initTheme() {
  const saved = localStorage.getItem("validata_theme") || "dark";
  if (saved === "light") {
    document.body.classList.remove("dark-theme");
    document.body.classList.add("light-theme");
  } else {
    document.body.classList.add("dark-theme");
    document.body.classList.remove("light-theme");
  }
}

function toggleTheme() {
  const isLight = document.body.classList.contains("light-theme");
  if (isLight) {
    document.body.classList.remove("light-theme");
    document.body.classList.add("dark-theme");
    localStorage.setItem("validata_theme", "dark");
  } else {
    document.body.classList.remove("dark-theme");
    document.body.classList.add("light-theme");
    localStorage.setItem("validata_theme", "light");
  }
  if (radarChartInstance && currentAnalysisReport) {
    renderRadarChart(currentAnalysisReport.metrics);
  }
}

/* ========================================================= */
/* TAB MANAGEMENT                                            */
/* ========================================================= */
function initTabs() {
  const tabs = document.querySelectorAll(".ws-tab");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));

      tab.classList.add("active");
      const targetId = tab.getAttribute("data-tab");
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) targetPanel.classList.add("active");

      if (targetId === "tab-history") {
        fetchHistory();
      }
    });
  });
}

function switchTab(tabId) {
  const tabBtn = document.querySelector(`.ws-tab[data-tab="${tabId}"]`);
  if (tabBtn) tabBtn.click();
}

/* ========================================================= */
/* CLIPBOARD PASTE (Senior & Mobile Friendly)                */
/* ========================================================= */
function initClipboardPaste() {
  const btnPaste = document.getElementById("btnPasteClipboard");
  btnPaste.addEventListener("click", async () => {
    try {
      if (navigator.clipboard && navigator.clipboard.readText) {
        const text = await navigator.clipboard.readText();
        if (text) {
          const bodyField = document.getElementById("inputBody");
          bodyField.value = text;
          updateWordCount();
          // Auto generate headline if empty
          const headField = document.getElementById("inputHeadline");
          if (!headField.value) {
            const lines = text.trim().split("\n");
            headField.value = lines[0].slice(0, 90);
          }
          alert("✓ Message pasted from clipboard!");
        } else {
          alert("Clipboard is empty. Please copy a message first!");
        }
      } else {
        alert("Please tap in the box and paste manually.");
      }
    } catch (e) {
      alert("Please paste the text directly into the box.");
    }
  });
}

function updateWordCount() {
  const text = document.getElementById("inputBody").value.trim();
  const words = text ? text.split(/\s+/).length : 0;
  document.getElementById("charCount").textContent = `${words} words`;
}

function initCharCount() {
  document.getElementById("inputBody").addEventListener("input", updateWordCount);
}

function clearTextForm() {
  document.getElementById("inputHeadline").value = "";
  document.getElementById("inputPublisher").value = "";
  document.getElementById("inputSourceUrl").value = "";
  document.getElementById("inputBody").value = "";
  updateWordCount();
}

/* ========================================================= */
/* 1-CLICK HERO SAMPLE CHIPS                                 */
/* ========================================================= */
const PRELOADED_SAMPLES = {
  "whatsapp_cancer_cure": {
    headline: "SHOCKING: Drinking boiled lemon peel and baking soda will destroy 100 percent of cancer cells in 3 days!",
    publisher: "WhatsApp Forward",
    sourceUrl: "",
    body: "Do not let the greedy doctors fool you! Modern hospitals don't want you to know that natural kitchen remedies are ten thousand times stronger than chemotherapy! Renowned secret researchers who cannot be named proved that mixing hot lemon water with baking soda immediately suffocates every tumor. Forward this to everyone before it gets deleted forever!"
  },
  "reuters_vaccine": {
    headline: "World Health Organization approves new pediatric malaria vaccine rollout",
    publisher: "Reuters",
    sourceUrl: "https://www.reuters.com/business/healthcare-pharmaceuticals/who-vaccine-approval",
    body: "The World Health Organization confirmed the prequalification of a new pediatric malaria vaccine, marking a major milestone in global public health. According to clinical trial data published in The Lancet medical journal, the vaccine demonstrated 77 percent efficacy in clinical trials conducted across four African nations. Dr. Tedros Adhanom Ghebreyesus, WHO Director-General, stated that distribution will begin next month in partnership with UNICEF."
  },
  "onion_belly_rubs": {
    headline: "The Onion: Nation's Dogs Announce Collective Strike Demanding Unlimited Belly Rubs",
    publisher: "The Onion",
    sourceUrl: "https://www.theonion.com/nations-dogs-strike",
    body: "WASHINGTON—In a coordinated nationwide walkout, over 70 million domestic canines sat down on front lawns Tuesday morning, refusing to fetch tennis balls or bark at mail carriers until human households guarantee 24-hour access to couch cushions and unearned bacon treats. Spokesdog Buster told reporters through an interpreter that negotiations are currently stalled over ear scritch quotas."
  },
  "isro_space_success": {
    headline: "Indian Space Research Organisation successfully tests semi-cryogenic engine stage",
    publisher: "The Hindu",
    sourceUrl: "https://www.thehindu.com/sci-tech/science/isro-tests-semi-cryogenic-engine",
    body: "The Indian Space Research Organisation (ISRO) successfully conducted a hot test of its 2000 kN semi-cryogenic engine at the propulsion complex in Mahendragiri. Scientists confirmed nominal engine parameters throughout the 150-second test duration, paving the way for heavy payload orbital launch vehicle development."
  }
};

function initHeroSampleChips() {
  document.querySelectorAll(".chip-action").forEach(btn => {
    btn.addEventListener("click", () => {
      const sampleKey = btn.getAttribute("data-sample");
      const sample = PRELOADED_SAMPLES[sampleKey];
      if (!sample) return;

      switchTab("tab-text");
      document.getElementById("inputHeadline").value = sample.headline;
      document.getElementById("inputPublisher").value = sample.publisher;
      document.getElementById("inputSourceUrl").value = sample.sourceUrl;
      document.getElementById("inputBody").value = sample.body;
      updateWordCount();

      document.getElementById("workspaceSection").scrollIntoView({ behavior: "smooth" });

      // Auto trigger analysis
      setTimeout(() => {
        document.getElementById("btnAnalyzeText").click();
      }, 350);
    });
  });
}

/* ========================================================= */
/* FILE UPLOAD ZONE (Drag & Drop or Tap)                     */
/* ========================================================= */
function initFileUpload() {
  const dropZone = document.getElementById("fileDropZone");
  const fileInput = document.getElementById("fileInputElement");
  const btnBrowse = document.getElementById("btnBrowseFile");
  const statusDiv = document.getElementById("fileUploadStatus");

  btnBrowse.addEventListener("click", () => fileInput.click());
  dropZone.addEventListener("click", (e) => {
    if (e.target !== btnBrowse) fileInput.click();
  });

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });

  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      processSelectedFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      processSelectedFile(e.target.files[0]);
    }
  });

  function processSelectedFile(file) {
    statusDiv.textContent = `Reading "${file.name}"...`;
    const reader = new FileReader();
    reader.onload = function(evt) {
      const content = evt.target.result;
      if (!content || !content.trim()) {
        alert("The selected file is empty.");
        statusDiv.textContent = "";
        return;
      }
      statusDiv.textContent = `✓ Loaded "${file.name}" successfully!`;

      // Fill in Text tab
      switchTab("tab-text");
      document.getElementById("inputHeadline").value = file.name.replace(/\.[^/.]+$/, "");
      document.getElementById("inputPublisher").value = "Uploaded Document";
      document.getElementById("inputBody").value = content.trim();
      updateWordCount();

      // Run analysis automatically
      setTimeout(() => {
        document.getElementById("btnAnalyzeText").click();
      }, 300);
    };
    reader.onerror = function() {
      alert("Failed to read file.");
      statusDiv.textContent = "";
    };
    reader.readAsText(file);
  }
}

/* ========================================================= */
/* VIEW MODE TOGGLE (Simple vs Forensic)                     */
/* ========================================================= */
function initViewModeToggles() {
  const btnSimple = document.getElementById("btnViewSimple");
  const btnForensic = document.getElementById("btnViewForensic");
  const simpleBox = document.getElementById("simpleViewContainer");
  const forensicBox = document.getElementById("forensicViewContainer");

  btnSimple.addEventListener("click", () => {
    btnSimple.classList.add("active");
    btnForensic.classList.remove("active");
    simpleBox.style.display = "block";
    forensicBox.style.display = "none";
  });

  btnForensic.addEventListener("click", () => {
    btnForensic.classList.add("active");
    btnSimple.classList.remove("active");
    simpleBox.style.display = "none";
    forensicBox.style.display = "block";
    if (currentAnalysisReport) {
      renderRadarChart(currentAnalysisReport.metrics);
    }
  });
}

/* ========================================================= */
/* API SUBMISSIONS                                           */
/* ========================================================= */
async function handleTextSubmit(e) {
  e.preventDefault();
  const headline = document.getElementById("inputHeadline").value.trim();
  const body = document.getElementById("inputBody").value.trim();
  const publisher = document.getElementById("inputPublisher").value.trim();
  const source_url = document.getElementById("inputSourceUrl").value.trim();

  if (!headline && !body) {
    alert("Please enter a headline or message text.");
    return;
  }

  const btn = document.getElementById("btnAnalyzeText");
  const spinner = btn.querySelector(".btn-spinner");
  btn.disabled = true;
  spinner.style.display = "inline-block";

  try {
    const res = await fetch("/api/analyze/text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ headline, body, publisher, source_url })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Analysis failed.");
    }

    const report = await res.json();
    currentAnalysisReport = report;
    displayResults(report);
    fetchGlobalStats();
  } catch (err) {
    alert("Error checking news: " + err.message);
  } finally {
    btn.disabled = false;
    spinner.style.display = "none";
  }
}

async function handleUrlSubmit(e) {
  e.preventDefault();
  const url = document.getElementById("inputUrl").value.trim();
  if (!url) {
    alert("Please enter a valid link.");
    return;
  }

  const btn = document.getElementById("btnAnalyzeUrl");
  const spinner = btn.querySelector(".btn-spinner");
  btn.disabled = true;
  spinner.style.display = "inline-block";

  const previewBox = document.getElementById("urlPreviewContainer");
  previewBox.style.display = "none";

  try {
    const res = await fetch("/api/analyze/url", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Could not read article from link.");
    }

    const report = await res.json();
    currentAnalysisReport = report;

    // Show preview card
    if (report.scraped_meta) {
      document.getElementById("previewTitle").textContent = report.scraped_meta.title || "Untitled";
      document.getElementById("previewPublisher").textContent = `Website: ${report.scraped_meta.publisher || "Unknown"}`;
      document.getElementById("previewAuthor").textContent = `Author: ${report.scraped_meta.author || "Not listed"}`;
      document.getElementById("previewDate").textContent = `Date: ${report.scraped_meta.publish_date || "Unknown"}`;
      document.getElementById("previewWords").textContent = `${report.scraped_meta.word_count || 0} words`;
      document.getElementById("previewSnippet").textContent = report.body_preview || "";
      previewBox.style.display = "block";
    }

    displayResults(report);
    fetchGlobalStats();
  } catch (err) {
    alert("Could not check link: " + err.message);
  } finally {
    btn.disabled = false;
    spinner.style.display = "none";
  }
}

/* ========================================================= */
/* RENDER RESULTS                                            */
/* ========================================================= */
function displayResults(report) {
  const section = document.getElementById("resultsSection");
  section.style.display = "block";

  const heroCard = document.getElementById("verdictHeroCard");
  const pill = document.getElementById("verdictPill");
  const verdictText = document.getElementById("verdictText");
  const adviceBox = document.getElementById("actionAdviceBox");
  const adviceIcon = document.getElementById("adviceIcon");
  const adviceText = document.getElementById("actionAdviceText");

  const v = (report.verdict || "questionable").toLowerCase();

  // Reset classes
  heroCard.className = "card verdict-card " + v;
  pill.className = "verdict-pill-badge " + v;
  adviceBox.className = "action-advice-banner " + v;

  // Plain-Language Status Texts
  verdictText.textContent = report.verdict_badge_text || report.verdict;
  document.getElementById("resultArticleTitle").textContent = report.title || "Checked Message";
  document.getElementById("verdictSummary").textContent = report.summary || "";

  // Plain Language Action Advice
  adviceText.textContent = report.action_advice || "Be careful before sharing this message.";
  if (v === "genuine") adviceIcon.textContent = "✅";
  else if (v === "fake") adviceIcon.textContent = "🚫";
  else if (v === "satire") adviceIcon.textContent = "😄";
  else adviceIcon.textContent = "⚠️";

  document.getElementById("resultPublisher").textContent = report.publisher || "Direct Message";
  document.getElementById("resultWordCount").textContent = report.word_count || 0;
  document.getElementById("resultDateTag").textContent = `Source Domain: ${report.source_domain || "Social Media / Text"}`;

  // Speedometer Gauge
  const score = Math.round(report.credibility_score);
  const circle = document.getElementById("gaugeProgressCircle");
  const scoreNum = document.getElementById("gaugeScoreNumber");

  scoreNum.textContent = score;
  const circumference = 2 * Math.PI * 42; // ~263.89
  const offset = circumference - (circumference * (score / 100));
  circle.style.strokeDashoffset = offset;

  if (v === "genuine") circle.style.stroke = "var(--emerald-green)";
  else if (v === "questionable") circle.style.stroke = "var(--amber-gold)";
  else if (v === "fake") circle.style.stroke = "var(--coral-red)";
  else if (v === "satire") circle.style.stroke = "var(--violet-purple)";

  // Sub-scores
  const m = report.metrics || {};
  updatePillar("Source", m.source_reputation || 0, report.layer_details?.source?.details || "");
  updatePillar("Style", m.linguistic_neutrality || 0, report.layer_details?.style?.details || "");
  updatePillar("Evidence", m.evidence_quality || 0, report.layer_details?.evidence?.details || "");
  updatePillar("ML", m.ml_authenticity || 0, `Pattern Confidence: ${report.layer_details?.ml?.confidence || 0}%`);

  // Warning signs list
  const listFlags = document.getElementById("listRedFlags");
  const countFlags = document.getElementById("countRedFlags");
  listFlags.innerHTML = "";
  const flags = report.red_flags || [];
  countFlags.textContent = flags.length;

  if (flags.length === 0) {
    listFlags.innerHTML = "<li>✓ No major rumor or fake news warning signs detected!</li>";
  } else {
    flags.forEach(f => {
      const li = document.createElement("li");
      li.textContent = `⚠️ ${f}`;
      listFlags.appendChild(li);
    });
  }

  // Credibility reasons list
  const listTrust = document.getElementById("listTrustIndicators");
  const countTrust = document.getElementById("countTrustIndicators");
  listTrust.innerHTML = "";
  const trusts = report.trust_indicators || [];
  countTrust.textContent = trusts.length;

  if (trusts.length === 0) {
    listTrust.innerHTML = "<li>No verified official citations found.</li>";
  } else {
    trusts.forEach(t => {
      const li = document.createElement("li");
      li.textContent = `✓ ${t}`;
      listTrust.appendChild(li);
    });
  }

  // Claims
  const claimsBox = document.getElementById("claimsListContainer");
  claimsBox.innerHTML = "";
  const claims = report.claims || [];

  if (claims.length === 0) {
    claimsBox.innerHTML = '<p class="text-muted">No testable factual assertions identified.</p>';
  } else {
    claims.forEach(c => {
      const div = document.createElement("div");
      div.className = "claim-item";
      div.innerHTML = `
        <div class="claim-type">${c.type}</div>
        <p class="claim-quote">"${escapeHtml(c.claim_text)}"</p>
        <p class="claim-tip">💡 <strong>Verification Tip:</strong> ${escapeHtml(c.verification_tip)}</p>
        <div class="claim-links">
          <a href="${c.google_factcheck_url}" target="_blank" rel="noopener noreferrer" class="fact-link">
            🔍 Check Google Fact Check Explorer ↗
          </a>
          <a href="${c.news_search_url}" target="_blank" rel="noopener noreferrer" class="fact-link">
            📰 Search Reuters & BBC News Wire ↗
          </a>
        </div>
      `;
      claimsBox.appendChild(div);
    });
  }

  // Chart
  renderRadarChart(m);

  // Scroll to results
  section.scrollIntoView({ behavior: "smooth", block: "start" });
}

function updatePillar(name, score, desc) {
  const scoreElem = document.getElementById(`score${name}`);
  const barElem = document.getElementById(`bar${name}`);
  const descElem = document.getElementById(`desc${name}`);

  scoreElem.textContent = `${Math.round(score)}/100`;
  barElem.style.width = `${Math.max(5, Math.min(100, score))}%`;
  if (descElem) descElem.textContent = desc;

  if (score >= 75) barElem.style.background = "linear-gradient(90deg, var(--cyan-neon), var(--emerald-green))";
  else if (score >= 45) barElem.style.background = "var(--amber-gold)";
  else barElem.style.background = "var(--coral-red)";
}

/* ========================================================= */
/* RADAR CHART (Luminous Emerald & Cyan Glow)                */
/* ========================================================= */
function renderRadarChart(metrics) {
  const ctx = document.getElementById("radarChart");
  if (!ctx) return;

  if (radarChartInstance) {
    radarChartInstance.destroy();
  }

  const isDark = document.body.classList.contains("dark-theme");
  const gridColor = isDark ? "rgba(0, 240, 255, 0.15)" : "rgba(11, 27, 61, 0.12)";
  const labelColor = isDark ? "#d1d5db" : "#1f2937";

  const dataValues = [
    metrics.source_reputation || 50,
    metrics.linguistic_neutrality || 50,
    metrics.evidence_quality || 50,
    metrics.ml_authenticity || 50,
    metrics.claim_coherence || 50
  ];

  radarChartInstance = new Chart(ctx, {
    type: "radar",
    data: {
      labels: [
        "Source Trust",
        "Language Objectivity",
        "Named Quotes",
        "AI Classifier",
        "Claim Coherence"
      ],
      datasets: [{
        label: "Authenticity Score",
        data: dataValues,
        fill: true,
        backgroundColor: "rgba(0, 230, 118, 0.22)",
        borderColor: "#00e676",
        pointBackgroundColor: "#00f0ff",
        pointBorderColor: "#ffffff",
        pointHoverBackgroundColor: "#ffffff",
        pointHoverBorderColor: "#00e676",
        borderWidth: 2.5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          min: 0,
          max: 100,
          ticks: {
            stepSize: 25,
            color: labelColor,
            backdropColor: "transparent",
            font: { size: 10, family: "'JetBrains Mono', monospace" }
          },
          grid: { color: gridColor },
          angleLines: { color: gridColor },
          pointLabels: {
            color: labelColor,
            font: { size: 12, weight: "800", family: "'Plus Jakarta Sans', sans-serif" }
          }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}

/* ========================================================= */
/* HISTORY & STATS                                           */
/* ========================================================= */
async function fetchGlobalStats() {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();
    document.getElementById("statTotal").textContent = data.total_analyzed || 0;
  } catch (e) {
    console.warn("Could not fetch stats:", e);
  }
}

async function fetchHistory() {
  const filter = document.getElementById("historyFilterSelect").value;
  const tbody = document.getElementById("historyTableBody");
  const badge = document.getElementById("historyBadgeCount");

  try {
    const url = filter && filter !== "ALL" ? `/api/history?verdict=${filter}` : "/api/history";
    const res = await fetch(url);
    const data = await res.json();
    const items = data.history || [];
    badge.textContent = items.length;

    if (items.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center empty-state">No previous checks recorded yet.</td></tr>';
      return;
    }

    tbody.innerHTML = "";
    items.forEach(item => {
      const tr = document.createElement("tr");
      const v = (item.verdict || "UNKNOWN").toLowerCase();
      tr.innerHTML = `
        <td style="white-space:nowrap;font-size:0.88rem;color:var(--text-muted);">${item.created_at}</td>
        <td><strong>${escapeHtml(item.title.slice(0, 50))}${item.title.length > 50 ? "..." : ""}</strong></td>
        <td>${escapeHtml(item.source_domain || item.publisher || "Direct Message")}</td>
        <td><span class="status-badge ${v}">${item.verdict}</span></td>
        <td><strong style="font-family:var(--font-mono);color:var(--cyan-neon);">${Math.round(item.credibility_score)}%</strong></td>
        <td>
          <button class="btn-table-action" onclick="viewHistoryItem(${item.id})">Read Report</button>
          <button class="btn-table-action delete" onclick="deleteHistoryEntry(${item.id})">Delete</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load history:", err);
  }
}

async function viewHistoryItem(id) {
  try {
    const res = await fetch(`/api/history/${id}`);
    const report = await res.json();

    document.getElementById("modalTitle").textContent = report.title || "Archived Report";
    const body = document.getElementById("modalBody");
    body.innerHTML = `
      <div style="margin-bottom:1rem;">
        <span class="status-badge ${report.verdict.toLowerCase()}">${report.verdict}</span>
        <strong style="margin-left:0.5rem;font-size:1.2rem;color:var(--cyan-neon);">Score: ${Math.round(report.credibility_score)}%</strong>
        <span style="margin-left:0.5rem;color:var(--text-muted);font-size:0.85rem;">(${report.created_at})</span>
      </div>
      <p style="margin-bottom:1rem;color:var(--text-secondary);font-size:1.05rem;">${escapeHtml(report.summary)}</p>
      
      <div style="background:var(--brand-navy-input);padding:1.15rem;border-radius:var(--radius-sm);margin-bottom:1.35rem;border:1px solid var(--border-color);">
        <p><strong>Source / Where it came from:</strong> ${escapeHtml(report.source_domain || report.publisher || "Direct Message")}</p>
        <p><strong>Word Count:</strong> ${report.word_count} words</p>
      </div>

      <h4 style="margin-bottom:0.5rem;color:var(--coral-red);">🚨 Warning Signs Found:</h4>
      <ul class="modal-flag-list red">
        ${(report.red_flags || []).map(f => `<li>${escapeHtml(f)}</li>`).join("") || "<li>None recorded.</li>"}
      </ul>

      <h4 style="margin-bottom:0.5rem;color:var(--emerald-green);">🛡️ Trustworthy Signs:</h4>
      <ul class="modal-flag-list green">
        ${(report.trust_indicators || []).map(t => `<li>${escapeHtml(t)}</li>`).join("") || "<li>None recorded.</li>"}
      </ul>
    `;

    document.getElementById("reportModal").style.display = "flex";
  } catch (e) {
    alert("Could not load report details.");
  }
}

async function deleteHistoryEntry(id) {
  if (!confirm("Are you sure you want to remove this report from history?")) return;
  try {
    await fetch(`/api/history/${id}`, { method: "DELETE" });
    fetchHistory();
    fetchGlobalStats();
  } catch (err) {
    alert("Failed to delete entry.");
  }
}

function closeModal() {
  document.getElementById("reportModal").style.display = "none";
}

function exportReportJson() {
  if (!currentAnalysisReport) return;
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentAnalysisReport, null, 2));
  const downloadAnchor = document.createElement("a");
  downloadAnchor.setAttribute("href", dataStr);
  downloadAnchor.setAttribute("download", `Validata_Report_${currentAnalysisReport.id || Date.now()}.json`);
  document.body.appendChild(downloadAnchor);
  downloadAnchor.click();
  downloadAnchor.remove();
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/[&<>"']/g, m => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[m]));
}
