// Mark the page as "JavaScript is running" right away, so CSS can safely
// hide elements that will be animated in (see .js [data-reveal] in input.css).
document.documentElement.classList.add("js");

const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

document.addEventListener("DOMContentLoaded", () => {
  setupSmoothScroll();
  setupScrollChoreography();
  setupMobileMenu();
  setupRotatingWords();
  setupScrollReveal();
  setupWorkFilter();
  setupCursorSpotlight();
  setupMagneticButtons();
});

// Smooth "inertia" scrolling with Lenis (public/static/js/vendor/lenis.min.js):
// responsive enough for macOS trackpads without input mushiness, paired with
// gentle desktop-only proximity snapping once scroll momentum settles.
function setupSmoothScroll() {
  if (prefersReducedMotion || typeof window.Lenis !== "function") return;

  window.lenis = new window.Lenis({
    autoRaf: true,
    lerp: 0.16,
    wheelMultiplier: 1.05,
    smoothWheel: true,
    anchors: true,
  });

  setupSectionSnap(window.lenis);
}

// Gentle desktop/laptop directional snapping:
// - Only activates on multi-chapter pages (>= 3 snap sections: Home & About)
//   and only on desktop/laptop viewports (>= 1024px with a mouse/trackpad).
// - Only responds to actual wheel/trackpad momentum, so scrollbar dragging,
//   keyboard navigation, and anchor jumps stay completely uninhibited.
// - Advances cleanly into the next chapter once you scroll ~26% past the
//   boundary in your scroll direction, or re-centers on the current edge.
function setupSectionSnap(lenis) {
  const desktopQuery = window.matchMedia("(min-width: 1024px) and (pointer: fine)");
  const sections = [...document.querySelectorAll("[data-snap-section]")];
  if (sections.length < 2) return;

  let settleTimer;
  let snapping = false;
  let hasWheelIntent = false;
  let lastDirection = 1;

  lenis.on("virtual-scroll", () => {
    hasWheelIntent = true;
    snapping = false;
    clearTimeout(settleTimer);
  });

  lenis.on("scroll", ({ direction, velocity }) => {
    if (!desktopQuery.matches || !hasWheelIntent) return;
    if (direction) lastDirection = direction;
    if (snapping) return;

    clearTimeout(settleTimer);
    const delay = Math.abs(velocity) > 0.4 ? 150 : 100;
    settleTimer = setTimeout(tryDirectionalSnap, delay);
  });

  function tryDirectionalSnap() {
    if (!desktopQuery.matches || !hasWheelIntent || snapping) return;
    if (Math.abs(lenis.velocity) > 0.35) {
      settleTimer = setTimeout(tryDirectionalSnap, 90);
      return;
    }

    const y = lenis.scroll;
    const vh = window.innerHeight;
    const maxY = Math.max(0, document.documentElement.scrollHeight - vh);
    if (maxY < 40) return;

    const snapPoints = [
      ...new Set(
        sections.map((el) => Math.min(Math.max(0, Math.round(el.getBoundingClientRect().top + y)), maxY))
      ),
      maxY,
    ].sort((a, b) => a - b);

    // Already cleanly aligned to a section boundary
    if (snapPoints.some((p) => Math.abs(p - y) <= 2)) {
      hasWheelIntent = false;
      return;
    }

    const curr = [...snapPoints].reverse().find((p) => p <= y + 2);
    const next = snapPoints.find((p) => p > y + 2);
    if (curr === undefined || next === undefined) {
      hasWheelIntent = false;
      return;
    }

    const span = next - curr;
    let target;

    if (span > vh * 1.15) {
      // Oversized band fallback: only tidy-align within 10% of an edge
      if (y - curr <= vh * 0.1) target = curr;
      else if (next - y <= vh * 0.1) target = next;
    } else if (lastDirection > 0) {
      target = y - curr > span * 0.26 ? next : curr;
    } else {
      target = next - y > span * 0.26 ? curr : next;
    }

    if (target === undefined || Math.abs(target - y) <= 2) {
      hasWheelIntent = false;
      return;
    }

    snapping = true;
    hasWheelIntent = false;
    lenis.scrollTo(target, {
      duration: 0.7,
      easing: (t) => 1 - Math.pow(1 - t, 4),
      onComplete: () => {
        snapping = false;
      },
    });
  }
}

// Drive lightweight GPU-composited feedback (scroll progress hairline, header
// elevation, and subtle ambient layer parallax) from Lenis or native scroll.
function setupScrollChoreography() {
  const header = document.querySelector("[data-header]");
  const progress = document.querySelector("[data-scroll-progress]");
  const parallaxEls = prefersReducedMotion ? [] : [...document.querySelectorAll("[data-parallax]")];
  if (!header && !progress && !parallaxEls.length) return;

  const update = (scrollY) => {
    const y = typeof scrollY === "number" ? scrollY : window.scrollY;
    const maxScroll = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);

    if (header) {
      header.classList.toggle("is-scrolled", y > 24);
    }

    if (progress) {
      const ratio = Math.min(1, Math.max(0, y / maxScroll));
      progress.style.transform = `scaleX(${ratio.toFixed(4)})`;
    }

    if (parallaxEls.length && y < window.innerHeight * 1.5) {
      parallaxEls.forEach((el) => {
        const speed = Number(el.dataset.parallax || 0);
        el.style.transform = `translate3d(0, ${(y * speed).toFixed(1)}px, 0)`;
      });
    }
  };

  if (window.lenis) {
    window.lenis.on("scroll", ({ scroll }) => update(scroll));
  } else {
    let ticking = false;
    window.addEventListener(
      "scroll",
      () => {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(() => {
          update();
          ticking = false;
        });
      },
      { passive: true }
    );
  }

  window.addEventListener("resize", () => update(), { passive: true });
  window.addEventListener("work:filtered", () => update());
  update();
}

// Open/close the navigation menu on small screens.
function setupMobileMenu() {
  const button = document.querySelector("[data-menu-button]");
  const menu = document.querySelector("[data-menu]");
  const header = document.querySelector("[data-header]");
  if (!button || !menu) return;

  button.addEventListener("click", () => {
    const isOpen = button.getAttribute("aria-expanded") === "true";
    button.setAttribute("aria-expanded", String(!isOpen));
    menu.classList.toggle("hidden", isOpen);
    if (header) header.classList.toggle("is-menu-open", !isOpen);
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

// Fade elements in cleanly as they enter the viewport.
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
    { threshold: 0.04, rootMargin: "0px 0px -20px 0px" }
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
        if (show) {
          card.classList.add("is-visible");
        }
      });

      if (window.lenis) {
        window.lenis.resize();
      }
      window.dispatchEvent(new Event("work:filtered"));
    });
  });
}

// Track mouse position across .spotlight-card elements to render a soft
// radial light follow effect.
function setupCursorSpotlight() {
  if (prefersReducedMotion || !window.matchMedia("(pointer: fine)").matches) return;
  const cards = document.querySelectorAll(".spotlight-card");
  if (!cards.length) return;

  cards.forEach((card) => {
    card.addEventListener("pointermove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.setProperty("--mouse-x", `${x}px`);
      card.style.setProperty("--mouse-y", `${y}px`);
    });
  });
}

// Subtle magnetic pull on primary buttons and CTAs when hovered with a mouse.
function setupMagneticButtons() {
  if (prefersReducedMotion || !window.matchMedia("(pointer: fine)").matches) return;
  const magnets = document.querySelectorAll("[data-magnetic]");

  magnets.forEach((el) => {
    el.addEventListener("pointermove", (e) => {
      const rect = el.getBoundingClientRect();
      const x = (e.clientX - rect.left - rect.width / 2) * 0.18;
      const y = (e.clientY - rect.top - rect.height / 2) * 0.22;
      el.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`;
    });

    el.addEventListener("pointerleave", () => {
      el.style.transform = "";
    });
  });
}
