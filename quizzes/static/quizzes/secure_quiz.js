(function () {
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop().split(";").shift();
    }
    return "";
  }

  document.addEventListener("DOMContentLoaded", function () {
    const page = document.getElementById("secureQuizPage");
    if (!page) {
      return;
    }

    const formEl = document.getElementById("quizForm");
    const startBtn = document.getElementById("startSecureQuizBtn");
    const startOverlay = document.getElementById("secureStartOverlay");
    const warningBox = document.getElementById("secureWarningBox");
    const autoSubmitReason = document.getElementById("securityAutoSubmitReason");

    const config = {
      quizTitle: page.dataset.quizTitle || "Quiz",
      logUrl: page.dataset.logUrl || "",
      autoSubmitThreshold: Number(page.dataset.autoSubmitThreshold || "3"),
    };

    let secureStarted = false;
    let submitting = false;
    let serverViolationCount = 0;
    const violationCooldownMs = 1500;
    const lastViolationTimes = {};

    function showWarning(message, highRisk) {
      if (!warningBox) {
        return;
      }
      warningBox.hidden = false;
      warningBox.textContent = message;
      warningBox.classList.toggle("high-risk", Boolean(highRisk));
    }

    function hideStartOverlay() {
      if (startOverlay) {
        startOverlay.style.display = "none";
      }
    }

    function autoSubmit(reason, resultUrl) {
      if (!formEl || submitting) {
        return;
      }
      submitting = true;
      if (autoSubmitReason) {
        autoSubmitReason.value = reason;
      }
      showWarning("Too many suspicious actions were detected. Your quiz is being submitted.", true);
      setTimeout(function () {
        if (resultUrl) {
          window.location.href = resultUrl;
          return;
        }
        formEl.submit();
      }, 900);
    }

    async function logViolation(violationType, details) {
      if (!secureStarted || submitting || !config.logUrl) {
        return;
      }
      const currentTime = Date.now();
      const lastTime = lastViolationTimes[violationType] || 0;
      if (currentTime - lastTime < violationCooldownMs) {
        return;
      }
      lastViolationTimes[violationType] = currentTime;

      try {
        const response = await fetch(config.logUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify({
            violation_type: violationType,
            details: details || "",
          }),
        });

        if (!response.ok) {
          return;
        }

        const payload = await response.json();
        serverViolationCount = Number(payload.violation_count || serverViolationCount);

        if (payload.should_auto_submit || serverViolationCount >= config.autoSubmitThreshold) {
          autoSubmit(
            `${violationType}: ${details || "threshold reached"}`,
            payload.result_url || ""
          );
          return;
        }

        const remaining = Math.max(config.autoSubmitThreshold - serverViolationCount, 0);
        const warningMessage = remaining > 0
          ? `Suspicious action recorded. ${remaining} more violation${remaining === 1 ? "" : "s"} before auto-submit.`
          : "Suspicious action recorded.";
        showWarning(warningMessage, serverViolationCount >= config.autoSubmitThreshold - 1);
      } catch (error) {
        // Keep quiz usable even if logging fails temporarily.
      }
    }

    async function requestFullscreenSafe() {
      const element = document.documentElement;
      const requestFullscreen =
        element.requestFullscreen ||
        element.webkitRequestFullscreen ||
        element.msRequestFullscreen;

      if (!requestFullscreen) {
        showWarning("Fullscreen is not supported in this browser. Monitoring will continue without it.", false);
        return false;
      }

      try {
        await requestFullscreen.call(element);
        return true;
      } catch (error) {
        showWarning("Fullscreen was not enabled. Monitoring will continue and exits will still be recorded.", false);
        return false;
      }
    }

    function activateSecureMode() {
      if (secureStarted) {
        return;
      }
      secureStarted = true;
      hideStartOverlay();
      showWarning("Secure Quiz Mode is active. Stay on this page until you submit.", false);
    }

    if (startBtn) {
      startBtn.addEventListener("click", async function () {
        await requestFullscreenSafe();
        activateSecureMode();
      });
    } else {
      activateSecureMode();
    }

    document.addEventListener("contextmenu", function (event) {
      if (!secureStarted) {
        return;
      }
      event.preventDefault();
      showWarning("Right-click is disabled during the quiz. This action has been recorded.", false);
      logViolation("RIGHT_CLICK", "Context menu was opened.");
    });

    ["copy", "cut", "paste"].forEach(function (eventName) {
      document.addEventListener(eventName, function (event) {
        if (!secureStarted) {
          return;
        }
        event.preventDefault();
        showWarning("Copying and pasting are disabled during the quiz. This action has been recorded.", false);
        logViolation("COPY_ATTEMPT", `${eventName} event blocked.`);
      });
    });

    document.addEventListener("selectstart", function (event) {
      if (!secureStarted) {
        return;
      }
      const target = event.target;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA")) {
        return;
      }
      event.preventDefault();
    });

    document.addEventListener("dragstart", function (event) {
      if (!secureStarted) {
        return;
      }
      event.preventDefault();
    });

    document.addEventListener("keydown", function (event) {
      if (!secureStarted) {
        return;
      }

      const key = String(event.key || "").toLowerCase();
      const commandPressed = event.ctrlKey || event.metaKey;
      const shiftPressed = event.shiftKey;

      const isCopyShortcut = commandPressed && ["c", "x", "v", "a"].includes(key);
      const isPrintShortcut = commandPressed && key === "p";
      const isDevtoolsShortcut =
        key === "f12" ||
        (commandPressed && key === "u") ||
        (commandPressed && key === "s") ||
        (commandPressed && shiftPressed && ["i", "j", "c"].includes(key));

      if (isCopyShortcut) {
        event.preventDefault();
        showWarning("Copy-related shortcuts are disabled during the quiz. This action has been recorded.", false);
        logViolation("COPY_ATTEMPT", `Keyboard shortcut blocked: ${event.key}`);
      } else if (isPrintShortcut) {
        event.preventDefault();
        showWarning("Printing is disabled during the quiz. This action has been recorded.", false);
        logViolation("PRINT_ATTEMPT", "Keyboard print shortcut blocked.");
      } else if (isDevtoolsShortcut) {
        event.preventDefault();
        showWarning("Developer-tool and save shortcuts are disabled during the quiz. This action has been recorded.", false);
        logViolation("DEVTOOLS_SHORTCUT", `Developer shortcut blocked: ${event.key}`);
      }
    });

    document.addEventListener("visibilitychange", function () {
      if (!secureStarted || !document.hidden) {
        return;
      }
      showWarning("You left the quiz page. This action has been recorded.", true);
      logViolation("TAB_SWITCH", "Page became hidden.");
    });

    window.addEventListener("blur", function () {
      if (!secureStarted || submitting) {
        return;
      }
      setTimeout(function () {
        if (!document.hasFocus() && !document.hidden) {
          showWarning("The quiz window lost focus. This action has been recorded.", false);
          logViolation("WINDOW_BLUR", "Window lost focus.");
        }
      }, 120);
    });

    document.addEventListener("fullscreenchange", function () {
      if (!secureStarted) {
        return;
      }
      if (!document.fullscreenElement) {
        showWarning("You exited fullscreen mode. This action has been recorded.", true);
        logViolation("FULLSCREEN_EXIT", "Student exited fullscreen mode.");
      }
    });

    window.addEventListener("beforeprint", function () {
      if (!secureStarted) {
        return;
      }
      showWarning("Printing is disabled during the quiz. This action has been recorded.", false);
      logViolation("PRINT_ATTEMPT", "beforeprint event fired.");
    });

    window.addEventListener("beforeunload", function (event) {
      if (!secureStarted || submitting) {
        return;
      }
      event.preventDefault();
      event.returnValue = "";
    });

    window.addEventListener("popstate", function () {
      if (!secureStarted || submitting) {
        return;
      }
      history.pushState(null, "", window.location.href);
      showWarning("Leaving the quiz page is blocked during the attempt.", false);
      logViolation("TAB_SWITCH", "Browser back navigation attempted.");
    });

    history.pushState(null, "", window.location.href);
  });
})();
