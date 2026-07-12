// Global JS for AI Freelancer Assistant.
// Day 2+ modules (proposal generator, cover letter generator, etc.)
// will add their AJAX calls to the Flask API here.

document.addEventListener("DOMContentLoaded", function () {
  // Auto-dismiss flash messages after 5 seconds
  const flashes = document.querySelectorAll(".flash");
  flashes.forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.5s ease";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 500);
    }, 5000);
  });

  // Show a loading state on submit buttons for forms that trigger an AI
  // call or a longer server operation, so the person gets feedback instead
  // of wondering if their click registered. Opt out with data-no-loading.
  document.querySelectorAll("form").forEach((form) => {
    if (form.hasAttribute("data-no-loading")) return;

    form.addEventListener("submit", function (event) {
      if (event.defaultPrevented) return;

      const btn = form.querySelector('button[type="submit"], input[type="submit"]');
      if (!btn || btn.disabled) return;

      btn.disabled = true;
      btn.dataset.originalText = btn.tagName === "INPUT" ? btn.value : btn.textContent;

      const loadingText = "Working...";
      if (btn.tagName === "INPUT") {
        btn.value = loadingText;
      } else {
        btn.textContent = loadingText;
      }
    });
  });
});
