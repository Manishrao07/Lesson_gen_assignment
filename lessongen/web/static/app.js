// LessonGen Studio Interactive Dashboard Client

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initEventListeners();
  loadInitialData();
});

// Tab Navigation
function initTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));

      tab.classList.add("active");
      const targetId = tab.getAttribute("data-tab");
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) {
        targetPanel.classList.add("active");
      }
    });
  });
}

// Event Listeners
function initEventListeners() {
  document.getElementById("sidebarRunBtn").addEventListener("click", handleRunPipeline);
  document.getElementById("headerRunBtn").addEventListener("click", handleRunPipeline);
  document.getElementById("copyMarkdownBtn").addEventListener("click", handleCopyMarkdown);
  document.getElementById("submitFeedbackBtn").addEventListener("click", handleSubmitFeedback);
  document.getElementById("evolveDryRunBtn").addEventListener("click", () => handleEvolve(false));
  document.getElementById("evolveApproveBtn").addEventListener("click", () => handleEvolve(true));
}

// Fetch Initial Data
async function loadInitialData() {
  try {
    await Promise.all([
      fetchOutputs(),
      fetchMemory(),
      fetchKnowledge()
    ]);
  } catch (err) {
    console.error("Error loading initial data:", err);
  }
}

// Simple Client Markdown Renderer
function renderMarkdown(mdText) {
  if (!mdText) return "<p>No content available.</p>";
  
  let html = mdText
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/^---$/gim, '<hr>')
    .replace(/^\- (.*$)/gim, '<li>$1</li>')
    .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
    .replace(/\n\n+/g, '</p><p>');

  return `<p>${html}</p>`;
}

// Load and Render Outputs
async function fetchOutputs() {
  try {
    const res = await fetch("/api/outputs");
    if (!res.ok) return;
    const data = await res.json();

    if (data.final_lesson_md) {
      document.getElementById("lessonContent").innerHTML = renderMarkdown(data.final_lesson_md);
    }

    if (data.rejection_log_json) {
      try {
        const logs = JSON.parse(data.rejection_log_json);
        renderRejectionLog(logs);
      } catch (e) {
        console.error("Failed to parse rejection_log.json", e);
      }
    }
  } catch (e) {
    console.error("Fetch outputs error", e);
  }
}

function renderRejectionLog(logs) {
  const container = document.getElementById("rejectionLogContainer");
  const countBadge = document.getElementById("tabRejectionCount");
  
  if (!logs || logs.length === 0) {
    container.innerHTML = "<p class='subtitle'>No rejection logs recorded yet.</p>";
    countBadge.textContent = "0";
    return;
  }

  let totalFails = 0;
  container.innerHTML = logs.map(log => {
    const isPass = log.passed;
    if (!isPass) totalFails += log.failed_checkpoints.length;

    let failuresHtml = "";
    if (!isPass && log.failed_checkpoints && log.failed_checkpoints.length > 0) {
      failuresHtml = log.failed_checkpoints.map(cpId => {
        const reason = (log.reasons && log.reasons[cpId]) || "Pass condition not met.";
        const evidence = (log.evidence && log.evidence[cpId]) || "None cited.";
        return `
          <div class="fail-item">
            <h5>Checkpoint ${cpId} FAILED</h5>
            <p>${reason}</p>
            <div class="fail-evidence">"${evidence}"</div>
          </div>
        `;
      }).join("");
    }

    let reflectorHtml = "";
    if (log.fix_instruction) {
      reflectorHtml = `
        <div class="reflector-box">
          <h5>Reflector Healing Plan:</h5>
          <pre class="code-preview">${log.fix_instruction}</pre>
          ${log.diff_summary ? `<small><strong>Diff Summary:</strong> ${log.diff_summary}</small>` : ''}
        </div>
      `;
    }

    return `
      <div class="attempt-card ${isPass ? 'passed' : 'failed'}">
        <div class="attempt-meta">
          <h4>Attempt ${log.attempt}</h4>
          <span class="tag ${isPass ? 'tag-success' : 'tag-danger'}">
            ${isPass ? 'PASSED (Ready to Ship)' : 'REJECTED (Errors Caught)'}
          </span>
        </div>
        ${failuresHtml}
        ${reflectorHtml}
      </div>
    `;
  }).join("");

  countBadge.textContent = totalFails.toString();
}

// Fetch Memory & Learned Rules
async function fetchMemory() {
  try {
    const res = await fetch("/api/memory");
    if (!res.ok) return;
    const data = await res.json();

    const rulesList = document.getElementById("activeRulesList");
    const countBadge = document.getElementById("rulesCountBadge");

    if (data.learned_rules && data.learned_rules.length > 0) {
      countBadge.textContent = `${data.learned_rules.length} active rules`;
      rulesList.innerHTML = data.learned_rules.map(r => `<li>${r}</li>`).join("");
    } else {
      countBadge.textContent = "0 rules (Cold Start)";
      rulesList.innerHTML = "<li>No learned rules yet. Failures will automatically distill rules here.</li>";
    }
  } catch (e) {
    console.error("Fetch memory error", e);
  }
}

// Fetch Knowledge & Rubric
async function fetchKnowledge() {
  try {
    const res = await fetch("/api/knowledge");
    if (!res.ok) return;
    const data = await res.json();

    if (data.rag_facts) {
      document.getElementById("ragFactsPreview").textContent = data.rag_facts;
    }
    if (data.rubric_yaml) {
      document.getElementById("rubricYamlPreview").textContent = data.rubric_yaml;
      renderCheckpointsFromYaml(data.rubric_yaml);
    }
  } catch (e) {
    console.error("Fetch knowledge error", e);
  }
}

// Render Checkpoint Grid
function renderCheckpointsFromYaml(yamlText) {
  const grid = document.getElementById("checkpointsGrid");
  // Hardcoded metadata fallback for rich card rendering
  const checkpoints = [
    { id: "ACC-1", dim: "ACC", layer: "judge", title: "Grounding Pack Consistency", cond: "All claims consistent with rag_facts.md (Lewis et al. 2020)." },
    { id: "ACC-2", dim: "ACC", layer: "judge", title: "No Invented Statistics", cond: "Zero synthetic benchmark numbers or hallucinated citations." },
    { id: "ACC-3", dim: "ACC", layer: "judge", title: "RAG as Retrieve-then-Generate", cond: "Explains RAG keeps model weights frozen and does not retrain weights." },
    { id: "BEG-1", dim: "BEG", layer: "code", title: "Average Sentence Length", cond: "Average sentence length <= 15.0 words across lesson body." },
    { id: "BEG-2", dim: "BEG", layer: "code", title: "Max Sentence Ceiling", cond: "Zero sentences exceed 25 words in length." },
    { id: "BEG-3", dim: "BEG", layer: "code", title: "Readability Score", cond: "Flesch Reading Ease score >= 65.0 (plain, easy-to-read English)." },
    { id: "BEG-4", dim: "BEG", layer: "judge", title: "Zero Idioms / Western Slang", cond: "No obscure metaphors or academic tech slang." },
    { id: "EX-1", dim: "EX", layer: "judge", title: "Everyday Indian Analogy", cond: "Relatable life analogy (open-book exam, librarian, chai-stall)." },
    { id: "EX-2", dim: "EX", layer: "code & judge", title: "Clear Worked Example", cond: "3-step format: Learner Question -> Retrieved Chunk -> Final Answer." },
    { id: "JAR-1", dim: "JAR", layer: "judge", title: "Plain Definition at First Use", cond: "Every technical term defined in brackets in plain words on first use." },
    { id: "JAR-2", dim: "JAR", layer: "code", title: "No Unexpanded Acronyms", cond: "Key acronyms (RAG, LLM, DB, API) expanded on first mention." },
    { id: "COV-1", dim: "COV", layer: "code", title: "Core Triad Coverage", cond: "Explicit sections for What it is, Why it matters, How it works." },
    { id: "COV-2", dim: "COV", layer: "judge", title: "Key Concepts Completeness", cond: "Knowledge cutoff, chunking, embeddings, vector DB, retrieval, generation." },
    { id: "COV-3", dim: "COV", layer: "judge", title: "Real-World Limitations", cond: "Discusses at least two failure modes (bad data, retrieval misses, speed)." },
    { id: "FLOW-1", dim: "FLOW", layer: "judge", title: "Coherent Teaching Flow", cond: "Logical sequence: Problem -> Analogy -> Steps -> Example -> Summary." },
    { id: "FLOW-2", dim: "FLOW", layer: "code", title: "Summary & Self-Check", cond: "Ends with summary and 3-5 practice questions with answers." }
  ];

  grid.innerHTML = checkpoints.map(cp => `
    <div class="checkpoint-card">
      <div class="cp-top">
        <span class="cp-id">${cp.id}</span>
        <span class="tag tag-neutral">${cp.dim}</span>
      </div>
      <div class="cp-title">${cp.title}</div>
      <div class="cp-condition">${cp.cond}</div>
      <div class="cp-bottom">
        <span class="cp-layer">${cp.layer}</span>
        <span class="tag tag-success">PASS</span>
      </div>
    </div>
  `).join("");
}

// Pipeline Execution Handler
async function handleRunPipeline() {
  const topic = document.getElementById("topicInput").value;
  const mode = document.getElementById("modeSelect").value;
  const injectError = document.getElementById("errorSelect").value || null;
  const retries = parseInt(document.getElementById("retriesInput").value, 10);

  const runBtn = document.getElementById("sidebarRunBtn");
  const spinner = document.getElementById("runSpinner");
  const btnText = document.getElementById("runBtnText");

  runBtn.disabled = true;
  spinner.style.display = "inline-block";
  btnText.textContent = "Executing LangGraph...";

  animateStepper(true);

  try {
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic: topic,
        mock: mode === "mock",
        inject_error: injectError,
        retries: retries
      })
    });

    if (!res.ok) {
      const err = await res.json();
      alert(`Pipeline error: ${err.detail || 'Execution failed'}`);
      return;
    }

    const result = await res.json();
    await fetchOutputs();
    await fetchMemory();

    // Update tags
    document.getElementById("lessonStatusTag").textContent = `STATUS: ${result.final_status}`;
    document.getElementById("lessonAttemptsTag").textContent = `Attempts: ${result.attempts_used}`;
    if (result.metrics && result.metrics.avg_sentence_length) {
      document.getElementById("lessonSentenceLenTag").textContent = result.metrics.avg_sentence_length;
    }

    // Switch to lesson tab
    document.querySelector('.tab-btn[data-tab="tabLesson"]').click();

  } catch (err) {
    console.error("Execution error:", err);
    alert("Execution error occurred: " + err.message);
  } finally {
    runBtn.disabled = false;
    spinner.style.display = "none";
    btnText.textContent = "🚀 Execute Pipeline";
    animateStepper(false);
  }
}

function animateStepper(running) {
  const steps = ["stepPlanner", "stepGenerator", "stepEvaluator", "stepReflector", "stepFinalizer"];
  if (running) {
    let i = 0;
    const interval = setInterval(() => {
      steps.forEach((s, idx) => {
        const el = document.getElementById(s);
        if (idx === i) {
          el.classList.add("active");
        } else if (idx < i) {
          el.classList.remove("active");
          el.classList.add("completed");
        }
      });
      i++;
      if (i >= steps.length) clearInterval(interval);
    }, 700);
  } else {
    steps.forEach(s => {
      const el = document.getElementById(s);
      el.classList.remove("active");
      el.classList.add("completed");
    });
  }
}

function handleCopyMarkdown() {
  const content = document.getElementById("lessonContent").innerText;
  navigator.clipboard.writeText(content).then(() => {
    alert("Markdown copied to clipboard!");
  });
}

async function handleSubmitFeedback() {
  const runId = document.getElementById("feedbackRunId").value;
  const text = document.getElementById("feedbackText").value;
  if (!text) {
    alert("Please enter feedback text.");
    return;
  }
  try {
    const res = await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ run_id: runId || "run_manual_review", text: text })
    });
    if (res.ok) {
      alert("Feedback submitted and distilled into memory/learned_rules.json!");
      document.getElementById("feedbackText").value = "";
      fetchMemory();
    }
  } catch (e) {
    alert("Error submitting feedback: " + e.message);
  }
}

async function handleEvolve(approve) {
  try {
    const res = await fetch("/api/evolve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ threshold: 1.0, approve: approve })
    });
    if (res.ok) {
      const data = await res.json();
      document.getElementById("evolutionPreview").textContent = data.changelog || "Evolution completed.";
      alert(approve ? "Rubric v2 approved & promoted to active rubric!" : "Evolution proposal generated (Dry Run).");
      fetchKnowledge();
    }
  } catch (e) {
    alert("Error running evolution: " + e.message);
  }
}
