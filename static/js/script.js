// Frontend interactions - AI Campus Placement Agent

document.addEventListener("DOMContentLoaded", () => {
  initThemeToggle();
  initFormUpload();
  initCircularProgress();
  initMockInterview();
  initCompanyExplorer();
  initSkillGapFilter();
  initRecentAnalysesDrawer();
});

function initThemeToggle() {
  const currentTheme = localStorage.getItem("theme") || "light";
  document.documentElement.setAttribute("data-bs-theme", currentTheme);

  const toggleBtns = document.querySelectorAll(".theme-toggle-btn");
  toggleBtns.forEach((btn) => {
    updateThemeIcon(btn, currentTheme);
    btn.addEventListener("click", () => {
      const activeTheme = document.documentElement.getAttribute("data-bs-theme");
      const newTheme = activeTheme === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-bs-theme", newTheme);
      localStorage.setItem("theme", newTheme);
      toggleBtns.forEach((b) => updateThemeIcon(b, newTheme));
    });
  });
}

function updateThemeIcon(btn, theme) {
  if (theme === "dark") {
    btn.innerHTML = '<i class="fa-solid fa-sun text-warning"></i>';
    btn.title = "Switch to Light Mode";
  } else {
    btn.innerHTML = '<i class="fa-solid fa-moon text-secondary"></i>';
    btn.title = "Switch to Dark Mode";
  }
}

/**
 * Filter and search controls for the Skill Gap assessment table on the dashboard
 */
function initSkillGapFilter() {
  const searchInput = document.getElementById("skillSearchInput");
  const priorityFilter = document.getElementById("skillPriorityFilter");
  const table = document.getElementById("skillGapTable");
  const countBadge = document.getElementById("skillFilterCount");
  const emptyState = document.getElementById("skillGapEmptyState");

  if (!table || !searchInput || !priorityFilter) return;

  const rows = table.querySelectorAll("tbody tr.skill-gap-row");
  const totalRows = rows.length;

  function applyFilter() {
    const q = searchInput.value.toLowerCase().trim();
    const p = priorityFilter.value;
    let visibleCount = 0;

    rows.forEach((row) => {
      const skillName = (row.getAttribute("data-skill") || "").toLowerCase();
      const priority = (row.getAttribute("data-priority") || "").toLowerCase();
      const fullText = row.innerText.toLowerCase();

      const matchesSearch = !q || skillName.includes(q) || fullText.includes(q);
      const matchesPriority = p === "ALL" || priority === p.toLowerCase();

      if (matchesSearch && matchesPriority) {
        row.style.display = "";
        visibleCount++;
      } else {
        row.style.display = "none";
      }
    });

    if (emptyState) {
      if (visibleCount === 0 && totalRows > 0) {
        emptyState.classList.remove("d-none");
      } else {
        emptyState.classList.add("d-none");
      }
    }

    if (countBadge) {
      if (q || p !== "ALL") {
        countBadge.innerText = `Showing ${visibleCount} of ${totalRows} Skills`;
      } else {
        countBadge.innerText = `${totalRows} Skills`;
      }
    }
  }

  searchInput.addEventListener("input", applyFilter);
  priorityFilter.addEventListener("change", applyFilter);

  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && searchInput.value) {
      searchInput.value = "";
      applyFilter();
    }
  });
}

/**
 * Tracks interactive checklist tasks on the 6-Week Learning Roadmap
 * and persists completed task IDs in localStorage per analysis session.
 */
function initRoadmapTracker() {
  const container = document.getElementById("dashboardContainer");
  if (!container) return;

  const analysisId = container.getAttribute("data-analysis-id");
  if (!analysisId) return;

  const storageKey = `roadmap_tasks_${analysisId}`;
  let completedTasks = new Set();
  try {
    const saved = localStorage.getItem(storageKey);
    if (saved) {
      completedTasks = new Set(JSON.parse(saved));
    }
  } catch (e) {
    console.warn("Could not load roadmap progress from localStorage:", e);
  }

  const allCheckboxes = document.querySelectorAll(".roadmap-task-check");
  const weekCards = document.querySelectorAll(".week-card");
  const overallLabel = document.getElementById("overallRoadmapProgressLabel");
  const overallBar = document.getElementById("overallRoadmapProgressBar");

  function updateVisuals() {
    let totalAll = allCheckboxes.length;
    let checkedAll = 0;

    weekCards.forEach((card) => {
      const checksInWeek = card.querySelectorAll(".roadmap-task-check");
      let checkedInWeek = 0;
      checksInWeek.forEach((cb) => {
        if (cb.checked) checkedInWeek++;
      });

      const pct = checksInWeek.length > 0 ? Math.round((checkedInWeek / checksInWeek.length) * 100) : 0;
      const bar = card.querySelector(".week-progress-bar");
      const label = card.querySelector(".week-progress-label");
      if (bar) bar.style.width = `${pct}%`;
      if (label) label.innerText = `${pct}%`;

      checkedAll += checkedInWeek;
    });

    const overallPct = totalAll > 0 ? Math.round((checkedAll / totalAll) * 100) : 0;
    if (overallLabel) overallLabel.innerText = `${overallPct}%`;
    if (overallBar) overallBar.style.width = `${overallPct}%`;
  }

  allCheckboxes.forEach((cb) => {
    const taskId = cb.getAttribute("data-task-id");
    if (taskId && completedTasks.has(taskId)) {
      cb.checked = true;
      const span = cb.parentElement?.querySelector("span");
      if (span) span.style.textDecoration = "line-through";
    }

    cb.addEventListener("change", () => {
      const span = cb.parentElement?.querySelector("span");
      if (cb.checked) {
        if (taskId) completedTasks.add(taskId);
        if (span) span.style.textDecoration = "line-through";
      } else {
        if (taskId) completedTasks.delete(taskId);
        if (span) span.style.textDecoration = "none";
      }

      try {
        localStorage.setItem(storageKey, JSON.stringify(Array.from(completedTasks)));
      } catch (e) {
        console.warn("Failed saving roadmap task progress to localStorage:", e);
      }

      updateVisuals();
    });
  });

  updateVisuals();
}

function initCompanyExplorer() {
  const btn = document.getElementById("btnExploreCompany");
  const select = document.getElementById("companySelect");
  const modalEl = document.getElementById("companyModal");
  const modalBody = document.getElementById("companyModalBody");
  if (!btn || !select || !modalEl) return;

  btn.addEventListener("click", async () => {
    const company = select.value;
    if (!company || company === "General") {
      alert("Please select a specific company (e.g. Google, Microsoft, Amazon) to explore its hiring guide.");
      return;
    }
    const bsModal = new bootstrap.Modal(modalEl);
    modalBody.innerHTML = '<div class="text-center py-4"><span class="spinner-border text-primary" role="status"></span></div>';
    bsModal.show();

    try {
      const res = await fetch(`/api/company/${encodeURIComponent(company)}`);
      const data = await res.json();
      if (data.success && data.details) {
        const d = data.details;
        modalBody.innerHTML = `
          <h4 class="fw-bold text-primary mb-3">${data.company}</h4>
          <p class="text-secondary">${d.overview || ""}</p>
          <hr/>
          <h6 class="fw-bold"><i class="fa-solid fa-list-check text-primary me-2"></i>Hiring Process:</h6>
          <p class="small text-muted mb-3">${d.hiring_process || "N/A"}</p>
          <h6 class="fw-bold"><i class="fa-solid fa-laptop-code text-primary me-2"></i>Technical Rounds:</h6>
          <p class="small text-muted mb-3">${d.technical_rounds || "N/A"}</p>
          <h6 class="fw-bold"><i class="fa-solid fa-lightbulb text-warning me-2"></i>Preparation Tips:</h6>
          <div class="alert alert-light border small text-dark">${d.prep_tips || "N/A"}</div>
        `;
      } else {
        modalBody.innerHTML = `<div class="alert alert-warning">No details found for ${company}.</div>`;
      }
    } catch (err) {
      modalBody.innerHTML = '<div class="alert alert-danger">Error loading company details.</div>';
    }
  });
}

/**
 * Handlers for landing page upload forms & progress panel animations
 */
function initFormUpload() {
  const uploadForm = document.getElementById("analysisForm");
  if (!uploadForm) return;

  const fileInput = document.getElementById("resumeInput");
  const uploadArea = document.getElementById("uploadArea");
  const progressOverlay = document.getElementById("progressOverlay");

  // Highlight upload area on dragover
  if (uploadArea && fileInput) {
    uploadArea.addEventListener("click", () => fileInput.click());
    
    fileInput.addEventListener("change", () => {
      if (fileInput.files.length > 0) {
        uploadArea.querySelector("p").innerHTML = `Selected File: <b>${fileInput.files[0].name}</b>`;
        uploadArea.style.borderColor = "var(--primary-blue)";
        uploadArea.style.backgroundColor = "var(--secondary-light)";
      }
    });

    ["dragenter", "dragover"].forEach(eventName => {
      uploadArea.addEventListener(eventName, (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = "var(--primary-blue)";
        uploadArea.style.backgroundColor = "var(--secondary-light)";
      }, false);
    });

    ["dragleave", "drop"].forEach(eventName => {
      uploadArea.addEventListener(eventName, (e) => {
        e.preventDefault();
        if (fileInput.files.length === 0) {
          uploadArea.style.borderColor = "var(--border-color)";
          uploadArea.style.backgroundColor = "#ffffff";
        }
      }, false);
    });

    uploadArea.addEventListener("drop", (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files.length > 0 && files[0].name.toLowerCase().endsWith(".pdf")) {
        fileInput.files = files;
        uploadArea.querySelector("p").innerHTML = `Selected File: <b>${files[0].name}</b>`;
        uploadArea.style.borderColor = "var(--primary-blue)";
        uploadArea.style.backgroundColor = "var(--secondary-light)";
      }
    });
  }

  // Intercept form submit to show animated Agent Progress panel
  uploadForm.addEventListener("submit", (e) => {
    const textInput = document.getElementById("resumeTextInput");
    const hasFile = fileInput && fileInput.files && fileInput.files.length > 0;
    const hasText = textInput && textInput.value.trim().length > 0;

    if (!hasFile && !hasText) {
      alert("Please upload a PDF resume or paste your resume text first.");
      e.preventDefault();
      return;
    }

    // Display progress overlay
    progressOverlay.classList.remove("d-none");

    const steps = [
      { id: "step1", delay: 0 },
      { id: "step2", delay: 1500 },
      { id: "step3", delay: 3200 },
      { id: "step4", delay: 4800 },
      { id: "step5", delay: 6500 },
      { id: "step6", delay: 8000 }
    ];

    // Trigger step updates sequentially
    steps.forEach((step, idx) => {
      setTimeout(() => {
        const element = document.getElementById(step.id);
        if (element) {
          element.classList.remove("text-muted");
          
          // Mark previous steps as completed
          if (idx > 0) {
            const prevElement = document.getElementById(steps[idx - 1].id);
            if (prevElement) {
              prevElement.classList.remove("active");
              prevElement.classList.add("completed");
              const indicator = prevElement.querySelector(".step-indicator");
              if (indicator) indicator.innerHTML = "✓";
            }
          }
          
          element.classList.add("active");
        }
      }, step.delay);
    });
  });
}

/**
 * Renders the circular SVG progress dials
 */
function initCircularProgress() {
  const circles = document.querySelectorAll(".circular-fill-ring");
  circles.forEach(circle => {
    const score = circle.getAttribute("data-score");
    if (score) {
      const radius = circle.r.baseVal.value;
      const circumference = 2 * Math.PI * radius;
      const offset = circumference - (score / 100) * circumference;
      
      // Animate circular transition
      setTimeout(() => {
        circle.style.strokeDasharray = `${circumference} ${circumference}`;
        circle.style.strokeDashoffset = offset;
      }, 300);
    }
  });
}

/**
 * Manages the live interactive mock interview simulation
 */
function initMockInterview() {
  const chatForm = document.getElementById("chatForm");
  if (!chatForm) return;

  const chatContainer = document.getElementById("chatContainer");
  const answerInput = document.getElementById("answerInput");
  const submitBtn = chatForm.querySelector("button[type='submit']");
  const evaluationPanel = document.getElementById("evaluationPanel");
  const btnMic = document.getElementById("btnMic");

  // Voice recording / speech recognition integration
  if (btnMic) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      btnMic.title = "Speech recognition not supported in this browser.";
      btnMic.style.opacity = "0.5";
    } else {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      let isRecording = false;

      btnMic.addEventListener("click", () => {
        if (!isRecording) {
          try {
            recognition.start();
            isRecording = true;
            btnMic.classList.remove("btn-outline-secondary");
            btnMic.classList.add("btn-danger");
            btnMic.innerHTML = '<i class="fa-solid fa-circle-stop"></i>';
          } catch (e) {
            console.warn(e);
          }
        } else {
          recognition.stop();
          isRecording = false;
          btnMic.classList.remove("btn-danger");
          btnMic.classList.add("btn-outline-secondary");
          btnMic.innerHTML = '<i class="fa-solid fa-microphone"></i>';
        }
      });

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          answerInput.value = answerInput.value ? `${answerInput.value} ${transcript}` : transcript;
        }
      };

      recognition.onend = () => {
        isRecording = false;
        btnMic.classList.remove("btn-danger");
        btnMic.classList.add("btn-outline-secondary");
        btnMic.innerHTML = '<i class="fa-solid fa-microphone"></i>';
      };

      recognition.onerror = () => {
        isRecording = false;
        btnMic.classList.remove("btn-danger");
        btnMic.classList.add("btn-outline-secondary");
        btnMic.innerHTML = '<i class="fa-solid fa-microphone"></i>';
      };
    }
  }

  // Live word counter and Ctrl+Enter keyboard submission
  if (answerInput) {
    const wordCountBadge = document.getElementById("wordCountBadge");
    answerInput.addEventListener("input", () => {
      const text = answerInput.value.trim();
      const words = text ? text.split(/\s+/).filter(Boolean).length : 0;
      if (wordCountBadge) {
        wordCountBadge.innerText = `${words} word${words === 1 ? "" : "s"}`;
        if (words >= 30) {
          wordCountBadge.className = "text-success fw-bold";
        } else {
          wordCountBadge.className = "text-secondary fw-semibold";
        }
      }
    });

    answerInput.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        chatForm.requestSubmit();
      }
    });
  }

  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const answer = answerInput.value.strip ? answerInput.value.strip() : answerInput.value.trim();
    if (!answer) {
      alert("Please enter a response before submitting.");
      return;
    }

    const questionIndex = parseInt(chatForm.getAttribute("data-question-index"));
    const analysisId = chatForm.getAttribute("data-analysis-id");

    // Disable UI inputs
    answerInput.disabled = true;
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span>`;

    // Append user answer bubble to chat log
    appendChatBubble(answer, "user");
    answerInput.value = "";

    // Append loader bubble from Interview Agent
    const loaderBubble = appendChatBubble("<i>Interview Agent is evaluating your response...</i>", "agent");

    try {
      const response = await fetch(`/interview/${analysisId}/submit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest"
        },
        body: JSON.stringify({
          answer: answer,
          question_index: questionIndex
        })
      });

      const result = await response.json();
      loaderBubble.remove(); // Remove wait loading bubble

      if (result.error) {
        appendChatBubble(`Error: ${result.error}`, "agent");
        resetInputs();
        return;
      }

      // Display dynamic feedback scores on dashboard panels
      renderEvaluationDetails(result.evaluation, questionIndex + 1);

      // Append feedback bubble to chat log
      const feedbackText = `
        <b>Feedback:</b> ${result.evaluation.feedback}<br/>
        <b>Technical Accuracy:</b> ${result.evaluation.technical_accuracy}/100<br/>
        <b>Communication Score:</b> ${result.evaluation.communication_score}/100<br/>
        <b>Confidence Score:</b> ${result.evaluation.confidence_score}/100<br/>
        <b>Suggestions:</b><br/>
        <ul>
          ${result.evaluation.suggestions.map(s => `<li>${s}</li>`).join("")}
        </ul>
      `;
      appendChatBubble(feedbackText, "agent");

      if (result.completed) {
        appendChatBubble("<b>Congratulations! You have completed all mock interview questions.</b><br/>Please review your performance summary and export your transcript.", "agent");
        resetInputs(true); // Disable form inputs permanently
        document.getElementById("btnBackToDashboard")?.classList.remove("btn-outline-secondary");
        document.getElementById("btnBackToDashboard")?.classList.add("btn-primary");

        // Display completion modal if summary data is available
        if (result.summary) {
          showCompletionModal(result.summary);
        }
      } else {
        // Move to next question
        const nextQ = result.next_question;
        setTimeout(() => {
          appendChatBubble(`[<b>Question ${nextQ.index + 1} - ${nextQ.type}</b>]<br/>${nextQ.question}`, "agent");
          chatForm.setAttribute("data-question-index", nextQ.index);
          resetInputs();
        }, 1200);
      }

    } catch (err) {
      loaderBubble.remove();
      appendChatBubble("Could not evaluate response. Check your network connection or API configs.", "agent");
      resetInputs();
    }
  });

  function appendChatBubble(text, sender) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble chat-bubble-${sender} fade-in`;
    bubble.innerHTML = text;
    chatContainer.appendChild(bubble);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return bubble;
  }

  function resetInputs(disableAll = false) {
    answerInput.disabled = disableAll;
    submitBtn.disabled = disableAll;
    submitBtn.innerHTML = "Submit Answer";
  }

  function renderEvaluationDetails(evaluation, totalAnswered) {
    if (evaluationPanel) {
      evaluationPanel.classList.remove("d-none");
    }

    // Update gauges
    document.getElementById("confScore").innerText = `${evaluation.confidence_score}%`;
    document.getElementById("confBar").style.width = `${evaluation.confidence_score}%`;

    document.getElementById("commScore").innerText = `${evaluation.communication_score}%`;
    document.getElementById("commBar").style.width = `${evaluation.communication_score}%`;

    document.getElementById("techScore").innerText = `${evaluation.technical_accuracy}%`;
    document.getElementById("techBar").style.width = `${evaluation.technical_accuracy}%`;

    const totalQuestions = parseInt(chatForm.getAttribute("data-total-questions")) || 15;
    const progPercent = totalQuestions > 0 ? Math.round((totalAnswered / totalQuestions) * 100) : 0;
    document.getElementById("interviewProgressText").innerText = `${totalAnswered}/${totalQuestions} Questions Answered (${progPercent}%)`;
    document.getElementById("interviewProgressBar").style.width = `${progPercent}%`;
  }

  function showCompletionModal(summary) {
    const modalEl = document.getElementById("completionModal");
    if (!modalEl || typeof bootstrap === "undefined") return;

    const overallScoreEl = document.getElementById("modalOverallScore");
    const verdictBadge = document.getElementById("modalVerdictBadge");
    const feedbackEl = document.getElementById("modalSummaryFeedback");
    const hrScoreEl = document.getElementById("modalHrScore");
    const techScoreEl = document.getElementById("modalTechScore");
    const behScoreEl = document.getElementById("modalBehScore");

    if (overallScoreEl) overallScoreEl.innerText = summary.overall_score || "0";
    if (verdictBadge) verdictBadge.innerText = summary.readiness_verdict || "Completed";
    if (feedbackEl && summary.summary_feedback) feedbackEl.innerText = summary.summary_feedback;

    const cats = summary.category_scores || {};
    if (hrScoreEl && cats.HR) hrScoreEl.innerText = `${cats.HR.average_score}%`;
    if (techScoreEl && cats.Technical) techScoreEl.innerText = `${cats.Technical.average_score}%`;
    if (behScoreEl && cats.Behavioral) behScoreEl.innerText = `${cats.Behavioral.average_score}%`;

    const bsModal = new bootstrap.Modal(modalEl);
    bsModal.show();
  }
}

/**
 * Loads recent analyses from /api/analyses/recent and renders them inside the offcanvas drawer.
 */
function initRecentAnalysesDrawer() {
  const drawerEl = document.getElementById("offcanvasRecentAnalyses");
  const listEl = document.getElementById("recentAnalysesList");
  if (!drawerEl || !listEl) return;

  async function loadRecentAnalyses() {
    listEl.innerHTML = `
      <div class="text-center py-5 text-muted">
        <div class="spinner-border text-primary spinner-border-sm mb-2" role="status"></div>
        <p class="small mb-0">Loading recent evaluations...</p>
      </div>
    `;

    try {
      const response = await fetch("/api/analyses/recent?limit=10");
      if (!response.ok) throw new Error("Network response was not ok");
      const data = await response.json();

      if (!data.analyses || data.analyses.length === 0) {
        listEl.innerHTML = `
          <div class="text-center py-5 text-secondary">
            <i class="fa-solid fa-folder-open fa-2x mb-3 text-muted"></i>
            <h6 class="fw-bold mb-1">No Recent Analyses</h6>
            <p class="small text-muted mb-0">Upload a resume to generate your first placement report.</p>
          </div>
        `;
        return;
      }

      listEl.innerHTML = "";
      data.analyses.forEach((a) => {
        const card = document.createElement("div");
        card.className = "card border rounded-3 p-3 shadow-sm bg-body";
        const dateStr = a.created_at ? new Date(a.created_at).toLocaleDateString() : "";

        card.innerHTML = `
          <div class="d-flex justify-content-between align-items-start mb-2">
            <div>
              <span class="badge bg-primary-subtle text-primary fw-bold me-1">${escapeHtml(a.company_name)}</span>
              <span class="badge bg-secondary-subtle text-secondary small">${dateStr}</span>
            </div>
            <button class="btn btn-outline-danger btn-sm border-0 rounded-circle delete-analysis-btn" data-id="${a.id}" title="Delete Analysis">
              <i class="fa-solid fa-trash-can"></i>
            </button>
          </div>
          <div class="small text-truncate fw-semibold mb-2" title="${escapeHtml(a.resume_filename)}">
            <i class="fa-solid fa-file-pdf text-danger me-1"></i> ${escapeHtml(a.resume_filename)}
          </div>
          <div class="d-flex align-items-center gap-2 mb-3 small">
            <span class="badge bg-success-subtle text-success">ATS: ${a.ats_score}%</span>
            <span class="badge bg-info-subtle text-info">Match: ${a.match_percentage}%</span>
          </div>
          <a href="/dashboard/${a.id}" class="btn btn-sm btn-outline-primary rounded-pill w-100">
            <i class="fa-solid fa-chart-pie me-1"></i> View Report
          </a>
        `;
        listEl.appendChild(card);
      });

      // Hook up delete buttons
      listEl.querySelectorAll(".delete-analysis-btn").forEach((btn) => {
        btn.addEventListener("click", async (e) => {
          e.stopPropagation();
          const analysisId = btn.getAttribute("data-id");
          if (!confirm("Are you sure you want to delete this placement analysis?")) return;

          try {
            const delRes = await fetch(`/api/analysis/${analysisId}`, { method: "DELETE" });
            if (delRes.ok) {
              loadRecentAnalyses();
            } else {
              alert("Failed to delete the analysis record.");
            }
          } catch (err) {
            console.error("Error deleting analysis:", err);
            alert("Error deleting analysis.");
          }
        });
      });
    } catch (err) {
      console.warn("Could not load recent analyses:", err);
      listEl.innerHTML = `
        <div class="text-center py-4 text-muted">
          <p class="small mb-0">No past sessions found or service unavailable.</p>
        </div>
      `;
    }
  }

  drawerEl.addEventListener("show.bs.offcanvas", loadRecentAnalyses);
}

function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.innerText = text;
  return div.innerHTML;
}
