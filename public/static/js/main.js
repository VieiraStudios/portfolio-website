// Mark the page as "JavaScript is running" right away, so CSS can safely
// hide elements that will be animated in (see .js [data-reveal] in input.css).
document.documentElement.classList.add("js");

const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

document.addEventListener("DOMContentLoaded", () => {
  setupSmoothScroll();
  setupMobileMenu();
  setupRotatingWords();
  setupScrollReveal();
  setupWorkFilter();
});

// Smooth "inertia" scrolling with Lenis (public/static/js/vendor/lenis.min.js):
// wheel and trackpad scrolling glides and eases to a stop. Phones and tablets
// keep their native touch scrolling, which already feels smooth.
function setupSmoothScroll() {
  if (prefersReducedMotion || typeof window.Lenis !== "function") return;

  window.lenis = new window.Lenis({
    autoRaf: true, // run Lenis's animation loop automatically
    lerp: 0.1, // how quickly scrolling catches up (lower = floatier)
    anchors: true, // smooth-scroll to #links such as "Skip to content"
  });

  setupSectionSnap(window.lenis);
}

// Section snapping: when you stop scrolling and the next section (in the
// direction you were scrolling) is already well into view, the page glides the
// rest of the way so that section lines up with the top of the screen.
// If no section edge is close, nothing happens, so you can stop anywhere
// inside a tall section to read it. Tweak the two numbers to taste.
const SNAP_AHEAD = 0.6; // snap if the next section's top is within 60% of the screen height
const SNAP_ALIGN = 0.06; // also tidy up if you stop within 6% of any section top

function setupSectionSnap(lenis) {
  const sections = [...document.querySelectorAll("main > section, body > section, body > footer")];
  if (sections.length < 2) return;

  let timer;
  let snapping = false;
  let lastDirection = 1; // 1 = scrolling down, -1 = scrolling up

  // Any new wheel/trackpad input cancels a snap in progress.
  lenis.on("virtual-scroll", () => {
    snapping = false;
  });

  lenis.on("scroll", ({ direction }) => {
    if (direction) lastDirection = direction;
    if (snapping) return;
    clearTimeout(timer);
    timer = setTimeout(snapToNearbySection, 140); // runs once scrolling has stopped
  });

  function snapToNearbySection() {
    const y = lenis.scroll;
    const screen = window.innerHeight;
    const maxY = document.documentElement.scrollHeight - screen;
    const tops = sections.map((s) => Math.min(Math.round(s.getBoundingClientRect().top + y), maxY));

    const ahead =
      lastDirection > 0
        ? tops.filter((t) => t > y + 1).sort((a, b) => a - b)[0]
        : tops.filter((t) => t < y - 1).sort((a, b) => b - a)[0];

    let target;
    if (ahead !== undefined && Math.abs(ahead - y) <= screen * SNAP_AHEAD) {
      target = ahead;
    } else {
      target = tops.find((t) => Math.abs(t - y) > 1 && Math.abs(t - y) <= screen * SNAP_ALIGN);
    }
    if (target === undefined) return;

    snapping = true;
    lenis.scrollTo(target, {
      duration: 0.8,
      easing: (t) => 1 - Math.pow(1 - t, 3), // fast start, gentle finish
      onComplete: () => {
        snapping = false;
      },
    });
  }
}

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
