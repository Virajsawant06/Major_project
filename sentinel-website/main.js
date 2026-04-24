// ═══════════════════════════════════════════════════
//  MAIN.JS — Loader · Cursor · Hero Reveal · 
//            Sticky Process · Scroll Reveal · Count-up
// ═══════════════════════════════════════════════════

// ─── Interactive Background ───────────────────────
const glow = document.getElementById('interactive-glow');
let gX = 0, gY = 0, curX = 0, curY = 0;

document.addEventListener('mousemove', e => {
  gX = e.clientX;
  gY = e.clientY;
});

(function animateGlow() {
  curX += (gX - curX) * 0.1;
  curY += (gY - curY) * 0.1;
  if (glow) glow.style.transform = `translate(${curX}px, ${curY}px) translate(-50%, -50%)`;
  requestAnimationFrame(animateGlow);
})();

// ─── Navbar scroll ────────────────────────────────
const navbar = document.querySelector('.nav-outer');
const commandCenter = document.getElementById('command-center');
let isMorphed = false;

window.addEventListener('scroll', () => {
  const scrolled = window.scrollY > 150;
  
  if (scrolled && !isMorphed) {
    isMorphed = true;
    if (navbar) navbar.classList.add('morphed');
    if (commandCenter) commandCenter.classList.add('active');
  } else if (!scrolled && isMorphed) {
    isMorphed = false;
    if (navbar) navbar.classList.remove('morphed');
    if (commandCenter) commandCenter.classList.remove('active');
  }
}, { passive: true });

// ─── Hero parallax ────────────────────────────────
const heroCanvas = document.getElementById('hero-canvas');
const heroInner = document.querySelector('.hero-inner');
const frags = document.querySelectorAll('.p-frag');

window.addEventListener('scroll', () => {
  const scrolled = window.scrollY;
  
  if (heroCanvas) {
    heroCanvas.style.transform = `translateY(${scrolled * 0.4}px)`;
  }
  
  if (heroInner) {
    heroInner.style.transform = `translateY(${scrolled * 0.15}px)`;
  }
  
  frags.forEach(f => {
    const speed = parseFloat(f.dataset.speed) || 0.5;
    f.style.transform = `translateY(${scrolled * speed}px)`;
  });
}, { passive: true });

// ─── Loader & Hero Reveal ────────────────────────
const loader = document.getElementById('loader');

function runHeroAnimations() {
  // Make all hero-anim elements visible
  const heroAnims = document.querySelectorAll('.hero-anim');
  heroAnims.forEach(el => {
    const delay = parseFloat(el.dataset.delay || 0) * 120;
    setTimeout(() => {
      el.classList.add('in');
      // If it's a word-wrap, also animate the inner .word
      if (el.classList.contains('word-wrap')) el.classList.add('in');
    }, delay);
  });
}

// ─── High-Tech Loader Logic ───────────────────────
const stages = [
  { pct: 15,  label: 'BOOT SEQUENCE',        status: 'INITIALIZING CORE SYSTEMS...' },
  { pct: 35,  label: 'KERNEL LOAD',           status: 'LOADING THREAT DATABASE...' },
  { pct: 55,  label: 'NEURAL SYNC',           status: 'CALIBRATING NEURAL NETWORKS...' },
  { pct: 75,  label: 'PROTOCOL HANDSHAKE',    status: 'ESTABLISHING SECURE CHANNELS...' },
  { pct: 90,  label: 'FINAL CHECKS',          status: 'VERIFYING SYSTEM INTEGRITY...' },
  { pct: 100, label: 'ONLINE',                status: 'SENTINEL ONLINE. STANDING BY.' },
];

const fill    = document.getElementById('progressFill');
const pct     = document.getElementById('progressPct');
const label   = document.getElementById('progressLabel');
const status  = document.getElementById('statusText');
const readoutStatus = document.getElementById('readoutStatus');
// 'loader' and 'navbar' are already declared above

function animateTo(target, duration, cb) {
  if (!fill || !pct) return cb(); // Failsafe if elements missing
  const start = parseFloat(fill.style.width) || 0;
  const startTime = performance.now();
  function step(now) {
    const t = Math.min((now - startTime) / duration, 1);
    const ease = t < 0.5 ? 2*t*t : -1+(4-2*t)*t;
    const val = start + (target - start) * ease;
    if (fill) fill.style.width = val + '%';
    if (pct) pct.textContent = Math.round(val) + '%';
    if (t < 1) requestAnimationFrame(step);
    else if (cb) cb();
  }
  requestAnimationFrame(step);
}

function runStage(i) {
  if (i >= stages.length) {
    // Reveal Page
    setTimeout(() => {
      loader.classList.add('out');
      document.body.classList.remove('loading');
      if (navbar) navbar.classList.add('in');
      setTimeout(runHeroAnimations, 100);
    }, 300);
    return;
  }
  const s = stages[i];
  if (label) label.textContent = s.label;
  if (status) status.textContent = s.status;
  if (readoutStatus) {
    if (i === 0) readoutStatus.textContent = 'BOOTING...';
    else if (i === stages.length - 1) readoutStatus.textContent = 'ONLINE';
    else readoutStatus.textContent = 'UPLOADING...';
  }
  const duration = i === stages.length - 1 ? 400 : 150 + Math.random() * 200;
  animateTo(s.pct, duration, () => {
    const delay = i === stages.length - 1 ? 0 : 50 + Math.random() * 100;
    setTimeout(() => runStage(i + 1), delay);
  });
}

window.addEventListener('load', () => {
  setTimeout(() => runStage(0), 100);
});

// ─── Generic Scroll Reveal ────────────────────────
const revEls = document.querySelectorAll('.reveal');
const revObs = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      // Stagger siblings in same parent
      const siblings = [...entry.target.parentElement.querySelectorAll('.reveal:not(.in)')];
      const idx = siblings.indexOf(entry.target);
      setTimeout(() => entry.target.classList.add('in'), idx * 80);
      revObs.unobserve(entry.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
revEls.forEach(el => revObs.observe(el));

// ─── Count-up Utility ─────────────────────────────
function countUp(el, target, duration, suffix) {
  let n = 0;
  const step = target / (duration / 16);
  const t = setInterval(() => {
    n = Math.min(n + step, target);
    el.textContent = Math.floor(n) + (suffix || '');
    if (n >= target) clearInterval(t);
  }, 16);
}

// Stats bar count-up
const statNums = document.querySelectorAll('.sval[data-target]');
const statObs = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      countUp(e.target, parseInt(e.target.dataset.target), 1200);
      statObs.unobserve(e.target);
    }
  });
}, { threshold: 0.5 });
statNums.forEach(el => statObs.observe(el));

// ─── PROCESS SECTION — Sticky Scroll Logic ────────
const processOuter = document.querySelector('.process-outer');
const processCards = document.querySelectorAll('.process-card');
const processTitles = document.querySelectorAll('.process-step-text');
const processNavItems = document.querySelectorAll('.ps-nav-item');
const STEPS = 4;
let currentStep = -1;

// Animate each card's contents when it becomes active
function activateStepCard(step) {
  if (step === 0) animateScanCard();
  if (step === 1) animateAnalyzeCard();
  if (step === 2) animatePatchCard();
  if (step === 3) animateReportCard();
}

function setStep(step) {
  if (step === currentStep) return;
  currentStep = step;

  processCards.forEach((c, i) => c.classList.toggle('active', i === step));
  processTitles.forEach((t, i) => t.classList.toggle('active', i === step));
  processNavItems.forEach((n, i) => n.classList.toggle('active', i === step));

  activateStepCard(step);
}

function onProcessScroll() {
  if (!processOuter) return;
  const rect = processOuter.getBoundingClientRect();
  const outerH = processOuter.offsetHeight;
  const scrolled = -rect.top; // px scrolled into section
  if (scrolled < 0 || scrolled > outerH) return;

  // Each step occupies (outerH / STEPS) px
  const stepH = outerH / STEPS;
  const step = Math.min(Math.floor(scrolled / stepH), STEPS - 1);
  setStep(step);
}

window.addEventListener('scroll', onProcessScroll, { passive: true });
// Init
setTimeout(() => setStep(0), 100);

// ── Step 0: Scan animation ──────────────────────
let scanAnimated = false;
function animateScanCard() {
  if (scanAnimated) return; scanAnimated = true;
  const epCount = document.getElementById('ep-count');
  const scanPct  = document.getElementById('scan-pct');
  const scanBar  = document.getElementById('scan-bar');
  if (!epCount) return;
  countUp(epCount, 247, 1800);
  let pct = 0;
  const t = setInterval(() => {
    pct = Math.min(pct + 0.8, 73);
    if (scanPct) scanPct.textContent = Math.floor(pct) + '%';
    if (scanBar) scanBar.style.width = pct + '%';
    if (pct >= 73) clearInterval(t);
  }, 20);
}

// ── Step 1: Analyze animation ───────────────────
let analyzeAnimated = false;
function animateAnalyzeCard() {
  if (analyzeAnimated) return; analyzeAnimated = true;
  const findings = document.querySelectorAll('.process-card[data-step="1"] .ai-finding');
  findings.forEach((f, i) => {
    setTimeout(() => {
      f.classList.add('reveal-finding');
      const bar = f.querySelector('.aif-bar');
      if (bar) setTimeout(() => bar.classList.add('animate'), 200);
    }, i * 150);
  });
}

// ── Step 2: Patch animation ─────────────────────
let patchAnimated = false;
function animatePatchCard() {
  if (patchAnimated) return; patchAnimated = true;
  const diffLines = document.querySelectorAll('.process-card[data-step="2"] .diff-line');
  diffLines.forEach((l, i) => {
    setTimeout(() => l.classList.add('show'), i * 220);
  });
  const patchPct = document.getElementById('patch-pct');
  if (patchPct) {
    let n = 0;
    const t = setInterval(() => {
      n = Math.min(n + 2, 68);
      patchPct.textContent = n + '%';
      if (n >= 68) clearInterval(t);
    }, 25);
  }
}

// ── Step 3: Report animation ────────────────────
let reportAnimated = false;
function animateReportCard() {
  if (reportAnimated) return; reportAnimated = true;
  const el = (id, target) => {
    const e = document.getElementById(id);
    if (e) countUp(e, target, 900);
  };
  el('rvc1', 2); el('rvc2', 5); el('rvc3', 11); el('rvc4', 8);
}

// ─── Copy CLI ─────────────────────────────────────
window.copyCli = function() {
  navigator.clipboard.writeText('npm install -g sentinel-security').then(() => {
    const btn = document.getElementById('copy-btn');
    if (!btn) return;
    btn.textContent = '✓ Copied!';
    setTimeout(() => btn.textContent = 'Copy', 2000);
  });
};

// ─── Smooth Scroll Nav ────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth' }); }
  });
});

// ─── Process Section Cursor Guide ─────────────────
const processSection = document.getElementById('process');
const cursorGuide = document.getElementById('process-cursor-guide');

if (processSection && cursorGuide) {
  processSection.addEventListener('mousemove', e => {
    cursorGuide.style.left = e.clientX + 'px';
    cursorGuide.style.top = e.clientY + 'px';
  });

  processSection.addEventListener('mouseenter', () => {
    cursorGuide.classList.add('active');
  });

  processSection.addEventListener('mouseleave', () => {
    cursorGuide.classList.remove('active');
  });
}
