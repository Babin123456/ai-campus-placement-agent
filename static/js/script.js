// Frontend interactions - AI Campus Placement Agent

document.addEventListener("DOMContentLoaded", () => {
  initFormUpload();
  initCircularProgress();
  initMockInterview();
});

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
    if (!fileInput.files || fileInput.files.length === 0) {
      alert("Please upload a PDF resume first.");
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
        appendChatBubble("<b>Congratulations! You have completed all mock interview questions.</b><br/>Please return to the dashboard to review your overall results.", "agent");
        resetInputs(true); // Disable form inputs permanently
        document.getElementById("btnBackToDashboard")?.classList.remove("btn-outline-secondary");
        document.getElementById("btnBackToDashboard")?.classList.add("btn-primary");
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

    const progPercent = Math.round((totalAnswered / 15) * 100);
    document.getElementById("interviewProgressText").innerText = `${totalAnswered}/15 Questions Answered (${progPercent}%)`;
    document.getElementById("interviewProgressBar").style.width = `${progPercent}%`;
  }
}
