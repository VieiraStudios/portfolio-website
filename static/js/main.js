// Mark the page as "JavaScript is running" right away, so CSS can safely
// hide elements that will be animated in (see .js [data-reveal] in input.css).
document.documentElement.classList.add("js");

const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

document.addEventListener("DOMContentLoaded", () => {
  setupMobileMenu();
  setupRotatingWords();
  setupScrollReveal();
  setupWorkFilter();
});

// Open/close the navigation menu on small screens.
function setupMobileMenu() {
  const button = document.querySelector("[data-menu-button]");
  const menu = document.querySelector("[data-menu]");
  if (!button || !menu) return;

  button.addEventListener("click", () => {
    const isOpen = button.getAttribute("aria-expanded") === "true";
    button.setAttribute("aria-expanded", String(!isOpen));
    menu.classList.toggle("hidden", isOpen);
  });
}

// Cycle through words: "We build [mobile apps -> web apps -> AI products]".
function setupRotatingWords() {
  const el = document.querySelector("[data-rotator]");
  if (!el || prefersReducedMotion) return;

  const words = JSON.parse(el.dataset.words);
  let index = 0;

  setInterval(() => {
    el.classList.add("is-out"); // slide the current word up and out

    setTimeout(() => {
      index = (index + 1) % words.length;
      el.textContent = words[index];
      el.classList.remove("is-out");
      el.classList.add("is-prep"); // jump below, invisible, without animating
      void el.offsetWidth; // force the browser to apply that position first
      el.classList.remove("is-prep"); // then animate up into place
    }, 450);
  }, 2600);
}

// Fade elements in as they scroll into view.
function setupScrollReveal() {
  const items = document.querySelectorAll("[data-reveal]");
  if (!("IntersectionObserver" in window)) {
    items.forEach((item) => item.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const delay = Number(entry.target.dataset.revealDelay || 0);
        entry.target.style.transitionDelay = `${delay}ms`;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target); // only animate once
      });
    },
    { threshold: 0.15 }
  );

  items.forEach((item) => observer.observe(item));
}

// Filter project cards on the Work page by category.
function setupWorkFilter() {
  const buttons = document.querySelectorAll("[data-filter]");
  const cards = document.querySelectorAll("[data-category]");
  if (!buttons.length) return;

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const filter = button.dataset.filter;

      buttons.forEach((b) => b.setAttribute("aria-pressed", String(b === button)));
      cards.forEach((card) => {
        const show = filter === "all" || card.dataset.category === filter;
        card.classList.toggle("hidden", !show);
      });
    });
  });
}
