(function () {
  "use strict";

  document.querySelectorAll("[data-copy-target]").forEach(function (button) {
    button.addEventListener("click", async function () {
      var target = document.getElementById(button.dataset.copyTarget);
      if (!target) return;

      try {
        await navigator.clipboard.writeText(target.innerText);
        var original = button.textContent;
        button.textContent = "Copied";
        button.setAttribute("aria-live", "polite");
        window.setTimeout(function () {
          button.textContent = original;
        }, 1800);
      } catch (_error) {
        window.getSelection().selectAllChildren(target);
        button.textContent = "Selected";
      }
    });
  });
})();
