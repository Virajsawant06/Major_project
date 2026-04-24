/* ── SENTINEL HEX CURSOR ──────────────────────────────────────────────────
   Drop this script anywhere on your page:
   <script src="sentinel-cursor.js"></script>
   No dependencies. Works on any dark background site.
──────────────────────────────────────────────────────────────────────── */

(function () {
  const cursor = document.createElement('div');
  cursor.id = 'hex-cursor';
  cursor.innerHTML = `
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 164 188" width="36" height="41" style="overflow:visible;display:block">
    <defs>
      <radialGradient id="crg" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stop-color="#4af0d0" stop-opacity="0.2"/>
        <stop offset="100%" stop-color="#070910" stop-opacity="1"/>
      </radialGradient>
      <radialGradient id="cglow" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stop-color="#ffffff" stop-opacity="0.6"/>
        <stop offset="35%" stop-color="#4af0d0" stop-opacity="0.25"/>
        <stop offset="100%" stop-color="#4af0d0" stop-opacity="0"/>
      </radialGradient>
    </defs>
    <polygon fill="#0a0e15" points="82 14 154 56 154 140 82 182 10 140 10 56 82 14"/>
    <polygon fill="url(#crg)" points="82 14 154 56 154 140 82 182 10 140 10 56 82 14"/>
    <polygon class="c-glow" fill="url(#cglow)" points="82 14 154 56 154 140 82 182 10 140 10 56 82 14"/>
    <polygon fill="none" stroke="#4af0d0" stroke-width="1" opacity="0.22" points="82 20 148 60 148 136 82 176 16 136 16 60 82 20"/>
    <polygon class="c-border" fill="none" stroke="#4af0d0" stroke-width="2.5" points="82 14 154 56 154 140 82 182 10 140 10 56 82 14"/>
    <polygon class="c-trace" fill="none" stroke="#ffffff" stroke-width="3" stroke-linecap="round"
      stroke-dasharray="50 420" stroke-dashoffset="0"
      points="82 14 154 56 154 140 82 182 10 140 10 56 82 14"/>
    <polygon class="c-trace2" fill="none" stroke="#4af0d0" stroke-width="5" stroke-linecap="round"
      stroke-dasharray="80 390" stroke-dashoffset="0"
      points="82 14 154 56 154 140 82 182 10 140 10 56 82 14"/>
    <line class="c-corner" fill="none" stroke="#37b9ff" stroke-width="2" stroke-linecap="round" x1="82"  y1="12"  x2="68"  y2="20"/>
    <line class="c-corner" fill="none" stroke="#37b9ff" stroke-width="2" stroke-linecap="round" x1="82"  y1="12"  x2="96"  y2="20"/>
    <line class="c-corner" fill="none" stroke="#37b9ff" stroke-width="2" stroke-linecap="round" x1="154" y1="56"  x2="154" y2="68"/>
    <line class="c-corner" fill="none" stroke="#37b9ff" stroke-width="2" stroke-linecap="round" x1="154" y1="56"  x2="142" y2="49"/>
    <line class="c-corner" fill="none" stroke="#37b9ff" stroke-width="2" stroke-linecap="round" x1="154" y1="140" x2="154" y2="128"/>
    <line class="c-corner" fill="none" stroke="#37b9ff" stroke-width="2" stroke-linecap="round" x1="154" y1="140" x2="142" y2="147"/>
    <line class="c-corner" fill="none" stroke="#37b9ff" stroke-width="2" stroke-linecap="round" x1="82"  y1="184" x2="68"  y2="176"/>
    <line class="c-corner" fill="none" stroke="#37b9ff" stroke-width="2" stroke-linecap="round" x1="82"  y1="184" x2="96"  y2="176"/>
    <line class="c-corner" fill="none" stroke="#37b9ff" stroke-width="2" stroke-linecap="round" x1="10"  y1="140" x2="10"  y2="128"/>
    <line class="c-corner" fill="none" stroke="#37b9ff" stroke-width="2" stroke-linecap="round" x1="10"  y1="140" x2="22"  y2="147"/>
    <line class="c-corner" fill="none" stroke="#37b9ff" stroke-width="2" stroke-linecap="round" x1="10"  y1="56"  x2="10"  y2="68"/>
    <line class="c-corner" fill="none" stroke="#37b9ff" stroke-width="2" stroke-linecap="round" x1="10"  y1="56"  x2="22"  y2="49"/>
    <circle class="c-dot" fill="#ffffff" cx="82"  cy="14"  r="2"/>
    <circle class="c-dot" fill="#ffffff" cx="154" cy="56"  r="2"/>
    <circle class="c-dot" fill="#ffffff" cx="154" cy="140" r="2"/>
    <circle class="c-dot" fill="#ffffff" cx="82"  cy="182" r="2"/>
    <circle class="c-dot" fill="#ffffff" cx="10"  cy="140" r="2"/>
    <circle class="c-dot" fill="#ffffff" cx="10"  cy="56"  r="2"/>
    <circle class="c-ripple" cx="82" cy="98" r="10" fill="none" stroke="#4af0d0"/>
  </svg>`;

  const style = document.createElement('style');
  style.textContent = `
    * { cursor: none !important; }

    #hex-cursor {
      position: fixed;
      top: 0; left: 0;
      width: 36px; height: 41px;
      pointer-events: none;
      z-index: 999999;
      transform: translate(-50%, -50%);
      will-change: transform;
      transition: scale 0.12s cubic-bezier(0.34, 1.56, 0.64, 1);
      scale: 1;
    }

    #hex-cursor.clicking {
      scale: 0.55;
      transition: scale 0.08s cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    #hex-cursor.hovering {
      scale: 1.35;
    }

    @keyframes _c-outer-pulse {
      0%,100% { opacity: 0.55; }
      50%     { opacity: 1; }
    }
    #hex-cursor .c-border {
      animation: _c-outer-pulse 2.4s ease-in-out infinite;
    }

    @keyframes _c-breathe {
      0%,100% { opacity: 0.1; }
      50%     { opacity: 0.8; }
    }
    #hex-cursor .c-glow {
      animation: _c-breathe 2.4s ease-in-out infinite;
    }

    @keyframes _c-trace {
      0%   { stroke-dashoffset: 0;    opacity: 0; }
      4%   { opacity: 1; }
      72%  { opacity: 1; }
      92%  { opacity: 0; }
      100% { stroke-dashoffset: -470; opacity: 0; }
    }
    @keyframes _c-trace2 {
      0%   { stroke-dashoffset: 0;    opacity: 0; }
      4%   { opacity: 0.85; }
      72%  { opacity: 0.85; }
      92%  { opacity: 0; }
      100% { stroke-dashoffset: -470; opacity: 0; }
    }
    #hex-cursor .c-trace  { animation: _c-trace  2.4s cubic-bezier(0.4,0,0.2,1) infinite; opacity: 0; }
    #hex-cursor .c-trace2 { animation: _c-trace2 2.4s cubic-bezier(0.4,0,0.2,1) infinite; opacity: 0; animation-delay: -0.05s; }

    #hex-cursor .c-corner { opacity: 0.45; }
    #hex-cursor .c-dot    { opacity: 0.2; }

    #hex-cursor.clicking .c-border { opacity: 1; stroke: #ffffff; }
    #hex-cursor.clicking .c-corner { opacity: 1; stroke: #ffffff; }
    #hex-cursor.clicking .c-dot    { opacity: 1; fill: #ffffff; }
    #hex-cursor.clicking .c-glow   { opacity: 1; animation: none; }

    @keyframes _c-ripple {
      0%   { r: 10; opacity: 0.8; stroke-width: 2; }
      100% { r: 55; opacity: 0;   stroke-width: 0.5; }
    }
    #hex-cursor .c-ripple { opacity: 0; }
    #hex-cursor.clicking .c-ripple {
      animation: _c-ripple 0.4s ease-out forwards;
    }
  `;

  document.head.appendChild(style);

  function mount() {
    document.body.appendChild(cursor);

    document.addEventListener('mousemove', e => {
      cursor.style.transform = `translate(calc(${e.clientX}px - 50%), calc(${e.clientY}px - 50%))`;
    });

    document.addEventListener('mousedown', () => {
      cursor.classList.remove('clicking');
      void cursor.offsetWidth; // restart animation
      cursor.classList.add('clicking');
    });

    document.addEventListener('mouseup', () => {
      cursor.classList.remove('clicking');
    });

    const HOVER_TARGETS = 'a, button, [role="button"], input, label, select, textarea, [tabindex]';

    document.addEventListener('mouseover', e => {
      if (e.target.closest(HOVER_TARGETS)) cursor.classList.add('hovering');
    });

    document.addEventListener('mouseout', e => {
      if (e.target.closest(HOVER_TARGETS)) cursor.classList.remove('hovering');
    });

    document.addEventListener('mouseleave', () => { cursor.style.opacity = '0'; });
    document.addEventListener('mouseenter', () => { cursor.style.opacity = '1'; });
  }

  if (document.body) {
    mount();
  } else {
    document.addEventListener('DOMContentLoaded', mount);
  }
})();
