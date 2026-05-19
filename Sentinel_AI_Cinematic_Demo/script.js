import { createCursorEffects } from './animations/cursor-effects.js';
import { createTransitions } from './animations/transitions.js';
import { createParticles } from './animations/particles.js';
import { createCinematicEffects } from './animations/cinematic-effects.js';
import { createNarration } from './voice/narration.js';
import { createSubtitles } from './voice/subtitles.js';
import { createIntroScene } from './scenes/intro.js';
import { createDashboardScene } from './scenes/dashboard.js';
import { createDetectionScene } from './scenes/detection.js';
import { createRetailScene } from './scenes/retail.js';
import { createAnalyticsScene } from './scenes/analytics.js';
import { createAssistantScene } from './scenes/assistant.js';
import { createOutroScene } from './scenes/outro.js';

// Minimal UI kit injected at runtime to keep CSS changes local to this file.
function ensureExtraStyles() {
  const id = 'sentinel-cinematic-extra-styles';
  if (document.getElementById(id)) return;

  const css = `
    .hudCard{margin-top:10px; border-radius:16px; padding:12px 12px; background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.12); backdrop-filter: blur(14px); box-shadow:0 0 22px rgba(124,255,233,.08)}
    .hudCard__title{font-size:11px; letter-spacing:.22em; font-weight:900; color:rgba(233,251,255,.62)}
    .hudCard__value{font-size:34px; font-weight:900; margin-top:6px; line-height:1}
    .hudCard__bar{height:8px; border-radius:999px; background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.10); overflow:hidden; margin-top:10px}
    .hudCard__barFill{height:100%; background:linear-gradient(90deg, rgba(124,255,233,.85), rgba(122,167,255,.85)); box-shadow:0 0 22px rgba(124,255,233,.26)}
    .hudCard__hint{margin-top:8px; font-weight:800; font-size:12px; color:rgba(233,251,255,.56)}
    .hudStack{display:flex; flex-direction:column; gap:10px; padding:12px}
    .hudStack__title{font-weight:900; letter-spacing:.26em; font-size:11px; color:rgba(124,255,233,.88)}

    .chip{display:inline-flex; align-items:center; justify-content:center; padding:6px 10px; border-radius:999px; border:1px solid rgba(255,255,255,.14); font-size:12px; font-weight:900; letter-spacing:.04em; backdrop-filter:blur(10px)}
    .chip--live{color:rgba(70,255,147,.96); background:rgba(70,255,147,.10); border-color:rgba(70,255,147,.26); box-shadow:0 0 18px rgba(70,255,147,.12)}
    .chip--ghost{color:rgba(233,251,255,.74); background:rgba(255,255,255,.04)}

    .hudStack__chipRow{display:flex; gap:8px; flex-wrap:wrap}
    .hudStack__metric{font-weight:900; letter-spacing:.06em; color:rgba(233,251,255,.64); display:flex; justify-content:space-between; align-items:baseline; gap:10px}
    .metricNum{color:rgba(124,255,233,.92); text-shadow:0 0 18px rgba(124,255,233,.2)}
    .hudStack__bar{height:10px; border-radius:999px; overflow:hidden; background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.10)}
    .hudStack__barFill{height:100%; width:50%; background:linear-gradient(90deg, rgba(255,79,216,.85), rgba(124,255,233,.85)); box-shadow:0 0 22px rgba(255,79,216,.18)}

    .alertFeed{display:flex; flex-direction:column; gap:8px; margin-top:6px}
    .alertLine{display:flex; align-items:center; justify-content:space-between; gap:10px; padding:8px 10px; border-radius:14px; background:rgba(0,0,0,.22); border:1px solid rgba(255,255,255,.10); backdrop-filter: blur(12px)}
    .alertDot{width:10px; height:10px; border-radius:50%; flex:0 0 auto}
    .alertLabel{font-weight:900; font-size:12px; color:rgba(233,251,255,.82); flex:1 1 auto}
    .alertTime{font-weight:900; font-size:12px; color:rgba(124,255,233,.9); flex:0 0 auto}

    .rightStack{padding:12px; border-radius:16px; background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.12); backdrop-filter: blur(16px); box-shadow:0 0 24px rgba(122,167,255,.08)}
    .rightStack--dense{padding:14px}
    .rightStack__title{font-weight:950; letter-spacing:.26em; font-size:11px; color:rgba(124,255,233,.9); margin-bottom:10px}

    .pulseRow{display:flex; gap:10px; align-items:center; margin-bottom:10px}
    .chipRow{display:flex; gap:10px; flex-wrap:wrap; margin-top:10px}
    .bigMetric{margin-top:10px; font-size:42px; font-weight:1000; color:rgba(124,255,233,.95); text-shadow:0 0 22px rgba(124,255,233,.18)}
    .bigMetric--right{color:rgba(122,167,255,.95)}

    .smallRow{display:flex; align-items:baseline; justify-content:space-between; gap:10px; padding:4px 0}
    .key{font-weight:900; font-size:12px; letter-spacing:.18em; color:rgba(233,251,255,.56)}
    .val{font-weight:950; font-size:14px; color:rgba(233,251,255,.86)}
    .rightHint{margin-top:8px; font-weight:900; color:rgba(233,251,255,.56)}
    .rightSeparator{height:1px; background:rgba(255,255,255,.10); margin:12px 0}
    .rightSmall{font-weight:900; color:rgba(233,251,255,.58)}
    .rightGlow{position:absolute; width:280px; height:280px; right:-120px; top:50%; transform:translateY(-50%); border-radius:50%; background:radial-gradient(circle, rgba(124,255,233,.18), rgba(124,255,233,0) 60%); filter:blur(10px); mix-blend-mode:screen}

    .zoomHud{position:absolute; right:0; bottom:18px; font-weight:1000; letter-spacing:.18em; font-size:12px; color:rgba(124,255,233,.9); padding:8px 12px; border-radius:999px; border:1px solid rgba(124,255,233,.25); background:rgba(0,0,0,.25); backdrop-filter:blur(14px)}

    .chartMock{position:relative; height:160px; border-radius:16px; background:rgba(0,0,0,.18); border:1px solid rgba(255,255,255,.10); overflow:hidden}
    .chartMock__grid{position:absolute; inset:0; background:
      repeating-linear-gradient(90deg, rgba(255,255,255,.06), rgba(255,255,255,.06) 1px, transparent 1px, transparent 40px),
      repeating-linear-gradient(180deg, rgba(255,255,255,.05), rgba(255,255,255,.05) 1px, transparent 1px, transparent 24px);
      opacity:.6}
    .chartMock__line{position:absolute; left:0; right:0; top:0; bottom:0;
      background:linear-gradient(90deg, rgba(124,255,233,.85), rgba(122,167,255,.85));
      clip-path: polygon(0% 80%, 20% 66%, 40% calc(66% - 18%*var(--p)), 60% calc(64% - 26%*var(--p)), 80% calc(62% - 22%*var(--p)), 100% calc(60% - 18%*var(--p)));
      opacity:.8;
      filter: drop-shadow(0 0 18px rgba(124,255,233,.18))}
    .chartMock__glow{position:absolute; inset:-20px; background:radial-gradient(500px 260px at 50% 70%, rgba(124,255,233,.18), rgba(124,255,233,0) 60%); opacity:.8}

    .analyticsMeta{display:flex; flex-direction:column; gap:8px}
    .metaRow{display:flex; justify-content:space-between; align-items:baseline; gap:10px}
    .metaKey{font-weight:900; letter-spacing:.18em; font-size:12px; color:rgba(233,251,255,.56)}
    .metaVal{font-weight:1000; color:rgba(124,255,233,.9)}

    .retailGrid{display:grid; grid-template-columns:1fr 1fr; gap:10px}
    .kpi{padding:10px; border-radius:16px; background:rgba(0,0,0,.18); border:1px solid rgba(255,255,255,.10)}
    .kpi__label{font-weight:900; letter-spacing:.14em; font-size:11px; color:rgba(233,251,255,.56)}
    .kpi__value{margin-top:8px; font-size:22px; font-weight:1000; color:rgba(124,255,233,.95)}

    .assistantWrap__title{font-weight:950; letter-spacing:.26em; font-size:11px; color:rgba(124,255,233,.9)}
    .assistantChat{display:flex; flex-direction:column; gap:10px; margin-top:12px}
    .chatBubble{display:flex; gap:10px; align-items:flex-start; padding:12px; border-radius:16px; background:var(--bg); border:1px solid var(--stroke); backdrop-filter: blur(14px)}
    .chatBubble__avatar{width:14px; height:14px; border-radius:50%; background:rgba(124,255,233,.85); box-shadow:0 0 18px rgba(124,255,233,.2); margin-top:4px}
    .chatBubble__text{font-weight:900; color:rgba(233,251,255,.86); font-size:12px; line-height:1.4}

    .assistantPrompt{margin-top:14px; padding:10px 12px; border-radius:16px; background:rgba(0,0,0,.22); border:1px solid rgba(255,255,255,.10)}
    .assistantPrompt__label{font-weight:1000; letter-spacing:.22em; font-size:10px; color:rgba(233,251,255,.56)}
    .assistantPrompt__text{display:block; margin-top:6px; font-weight:950; color:rgba(124,255,233,.9)}

    .explainList{display:flex; flex-direction:column; gap:8px; margin-top:6px}
    .explainItem{font-weight:900; font-size:12px; color:rgba(233,251,255,.74); display:flex; gap:10px; align-items:center}
    .explainDot{width:10px; height:10px; border-radius:50%; box-shadow:0 0 18px rgba(124,255,233,.2)}

    .ctaBox{margin-top:10px; padding:12px; border-radius:18px; background:rgba(0,0,0,.22); border:1px solid rgba(255,255,255,.10)}
    .ctaBox__line{font-weight:900; color:rgba(233,251,255,.74); margin:8px 0; font-size:12px}
    .ctaPulse{position:absolute; right:-60px; top:70%; width:220px; height:220px; border-radius:50%; background:radial-gradient(circle, rgba(124,255,233,.18), rgba(124,255,233,0) 62%); filter:blur(10px); animation: pulse 1.6s ease-in-out infinite alternate}
    @keyframes pulse{from{transform:translateY(-8px) scale(.98)}to{transform:translateY(8px) scale(1.02)}}

    .hudStack__metric span{font-variant-numeric: tabular-nums}
  `;

  const style = document.createElement('style');
  style.id = id;
  style.textContent = css;
  document.head.appendChild(style);
}

function formatTime(sec) {
  const s = Math.max(0, sec);
  const mm = String(Math.floor(s / 60)).padStart(2, '0');
  const ss = String(Math.floor(s % 60)).padStart(2, '0');
  return `${mm}:${ss}`;
}

function createPanZoomController({ panZoomEl }) {
  const state = {
    active: false,
    start: { x: 0, y: 0, s: 1 },
    mid: { x: 0, y: 0, s: 1.07 },
    end: { x: 0, y: 0, s: 1.03 },
  };

  function setPlan({ start, mid, end }) {
    if (start) state.start = start;
    if (mid) state.mid = mid;
    if (end) state.end = end;
    state.active = true;
  }

  function tick(p) {
    if (!state.active || !panZoomEl) return;
    // Piecewise interpolate: 0..1 with slight bias to mid
    const split = 0.58;
    let a;
    if (p < split) {
      a = p / split;
      a = 1 - Math.pow(1 - a, 3);
      const x = state.start.x + (state.mid.x - state.start.x) * a;
      const y = state.start.y + (state.mid.y - state.start.y) * a;
      const s = state.start.s + (state.mid.s - state.start.s) * a;
      panZoomEl.style.transform = `translate(${x * 100}%, ${y * 100}%) scale(${s})`;
    } else {
      a = (p - split) / (1 - split);
      a = a < 0.5 ? 2 * a * a : 1 - Math.pow(-2 * a + 2, 2) / 2;
      const x = state.mid.x + (state.end.x - state.mid.x) * a;
      const y = state.mid.y + (state.end.y - state.mid.y) * a;
      const s = state.mid.s + (state.end.s - state.mid.s) * a;
      panZoomEl.style.transform = `translate(${x * 100}%, ${y * 100}%) scale(${s})`;
    }
  }

  return { setPlan, tick, state };
}

function createBgRenderer({ sceneBgEl, panZoomEl }) {
  function applyBgImage(url) {
    if (!url) return;
    sceneBgEl.style.backgroundImage = `url(${url})`;
  }

  function applyBgMedia(url) {
    if (!url) {
      panZoomEl.innerHTML = '';
      sceneBgEl.style.backgroundImage = '';
      return;
    }

    const isVideo = url.toLowerCase().endsWith('.mp4') || url.toLowerCase().endsWith('.webm');

    panZoomEl.innerHTML = '';

    if (isVideo) {
      const v = document.createElement('video');
      v.src = url;
      v.autoplay = true;
      v.muted = true;
      v.playsInline = true;
      v.loop = true;
      v.preload = 'auto';
      v.style.position = 'absolute';
      v.style.inset = '0';
      v.style.width = '100%';
      v.style.height = '100%';
      v.style.objectFit = 'cover';
      v.style.filter = 'contrast(1.06) saturate(1.12)';
      panZoomEl.appendChild(v);
    } else {
      const img = document.createElement('img');
      img.src = url;
      img.alt = '';
      img.style.position = 'absolute';
      img.style.inset = '0';
      img.style.width = '100%';
      img.style.height = '100%';
      img.style.objectFit = 'cover';
      img.style.opacity = '0.92';
      img.style.filter = 'contrast(1.08) saturate(1.10)';
      panZoomEl.appendChild(img);
    }
  }

  function applyBgImageUrl(url) {
    if (!url) return;
    sceneBgEl.style.backgroundImage = `url(${url})`;
    sceneBgEl.style.backgroundSize = 'cover';
    sceneBgEl.style.backgroundPosition = 'center';
  }

  return { applyBgMedia, applyBgImage: applyBgImageUrl };
}

function getAssets() {
  // IMPORTANT: We reuse existing project media that exists in ./artifacts.
  // For images specified in the task but missing in artifacts, we provide a best-effort mapping.
  // You can replace these by dropping exact filenames into the assets/ folder.
  return {
    logo: './assets/logo.png',

    // Best-effort mappings from available artifacts; copied into demo assets below.
    dashboardBg: './assets/dashboard-alerts.png',
    detectionBg: './assets/live-detection.png',
    retailBg: './assets/retail-monitoring.png',
    analyticsBg: './assets/dashboard-alerts.png',
    assistantBg: './assets/ai-assistant.png',
    outroBg: './assets/dashboard-alerts.png',

    video: './assets/demo-video.mp4',
    bgMusic: './assets/bg-music.mp3',
  };
}

function tryCopyAssetsInstruction() {
  // Non-op. Assets should exist in demo assets folder.
}

function buildTimeline() {
  // 15–20s total.
  // durations: intro 2.6 + dashboard 2.4 + detection 2.5 + retail 2.4 + analytics 2.6 + assistant 2.8 + outro 2.4 = 17.7s
  return [
    { key: 'intro', startMs: 0, durationMs: 2600 },
    { key: 'dashboard', startMs: 2600, durationMs: 2400 },
    { key: 'detection', startMs: 5000, durationMs: 2500 },
    { key: 'retail', startMs: 7500, durationMs: 2400 },
    { key: 'analytics', startMs: 9900, durationMs: 2600 },
    { key: 'assistant', startMs: 12500, durationMs: 2800 },
    { key: 'outro', startMs: 15300, durationMs: 2400 },
  ];
}

function buildSubtitleCues(totalMs) {
  const cues = [
    { id: 1, startMs: 400, endMs: 1850, text: 'Sentinel AI — enterprise cinematic monitoring.' },
    { id: 2, startMs: 2450, endMs: 4300, text: 'Telemetry that feels instant. Decisions that feel inevitable.' },
    { id: 3, startMs: 5200, endMs: 6800, text: 'Live detection — intrusion, stabilization, vector fusion.' },
    { id: 4, startMs: 7800, endMs: 9600, text: 'Retail operations — anomalies, crowd flow, asset proximity.' },
    { id: 5, startMs: 10250, endMs: 12250, text: 'Analytics — turn events into audit-ready intelligence.' },
    { id: 6, startMs: 12650, endMs: 14550, text: 'AI assistant — ask, explain, and generate stakeholder briefs.' },
    { id: 7, startMs: 15050, endMs: totalMs - 1, text: 'Deploy faster. Respond smarter. Sentinel AI.' },
  ];
  return cues;
}

function buildNarrationCues() {
  return [
    { startMs: 450, text: 'Sentinel AI — enterprise cinematic monitoring. ' },
    { startMs: 2600, text: 'Telemetry that feels instant. Decisions that feel inevitable. ' },
    { startMs: 5200, text: 'Live detection — intrusion, stabilization, vector fusion. ' },
    { startMs: 7900, text: 'Retail operations — anomalies, crowd flow, asset proximity. ' },
    { startMs: 10100, text: 'Analytics — turn events into audit-ready intelligence. ' },
    { startMs: 12650, text: 'AI assistant — ask, explain, and generate stakeholder briefs. ' },
    { startMs: 15000, text: 'Deploy faster. Respond smarter. Sentinel AI. ' },
  ];
}

ensureExtraStyles();

const stageEl = document.getElementById('stage');
const fxCanvas = document.getElementById('fx');
const ctx2d = fxCanvas.getContext('2d');

const ui = {
  left: document.getElementById('leftHud'),
  right: document.getElementById('rightHud'),
  centerPanel: document.getElementById('centerPanel'),
  centerKicker: document.getElementById('centerKicker'),
  centerHeadline: document.getElementById('centerHeadline'),
  centerSubhead: document.getElementById('centerSubhead'),
  panZoomEl: document.getElementById('panZoom'),
  letterbox: document.querySelector('.letterbox'),
  letterboxTweak: null,
};

const toastEl = document.getElementById('toast');
const cursorGlow = document.getElementById('cursorGlow');
const sceneBgEl = document.getElementById('sceneBg');

const timecodeEl = document.getElementById('timecode');

const assets = getAssets();

// If assets missing, demo still runs with gradients/background.
try {
  // noop
} catch {
  // ignore
}

// FX systems
let width = 0;
let height = 0;

function resizeAll() {
  width = fxCanvas.clientWidth;
  height = fxCanvas.clientHeight;

  const dpr = Math.min(2, window.devicePixelRatio || 1);
  fxCanvas.width = Math.floor(width * dpr);
  fxCanvas.height = Math.floor(height * dpr);
  ctx2d.setTransform(dpr, 0, 0, dpr, 0, 0);

  particles.reset(width, height);
}

const cursorFx = createCursorEffects({ canvas: fxCanvas });
const transitions = createTransitions({ stageEl });
const particles = createParticles({ canvas: fxCanvas });
const fx = createCinematicEffects({ stageEl });
const narr = createNarration({ toastEl });
const subs = createSubtitles({ subtitlesEl: document.getElementById('subtitles') });

const bg = createBgRenderer({ sceneBgEl, panZoomEl: ui.panZoomEl });
const panZoom = createPanZoomController({ panZoomEl: ui.panZoomEl });

function applyBgMedia(url) {
  bg.applyBgMedia(url);
}

function applyBgImage(url) {
  bg.applyBgImage(url);
}

const scenes = {
  intro: createIntroScene(),
  dashboard: createDashboardScene(),
  detection: createDetectionScene(),
  retail: createRetailScene(),
  analytics: createAnalyticsScene(),
  assistant: createAssistantScene(),
  outro: createOutroScene(),
};

const timeline = buildTimeline();
const totalMs = timeline[timeline.length - 1].startMs + timeline[timeline.length - 1].durationMs;
subs.setCues(buildSubtitleCues(totalMs));
const narrationCues = buildNarrationCues();

function setTitle({ kicker, headline, subhead }) {
  if (ui.centerKicker) ui.centerKicker.textContent = kicker ?? ui.centerKicker.textContent;
  if (ui.centerHeadline) ui.centerHeadline.textContent = headline ?? ui.centerHeadline.textContent;
  if (ui.centerSubhead) ui.centerSubhead.textContent = subhead ?? ui.centerSubhead.textContent;
}

function showToast(msg) {
  if (!toastEl) return;
  toastEl.textContent = msg;
  toastEl.classList.add('toast--show');
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toastEl.classList.remove('toast--show'), 1800);
}

function getSceneKeyAt(nowMs) {
  for (let i = timeline.length - 1; i >= 0; i--) {
    const s = timeline[i];
    if (nowMs >= s.startMs) return s.key;
  }
  return timeline[0].key;
}

let raf = 0;
let running = false;
let startPerf = 0;
let lastNow = 0;
let lastSceneKey = null;
const playedNarration = new Set();

function frame(now) {
  if (!running) return;

  const nowMs = now - startPerf;
  const dt = now - lastNow;
  lastNow = now;

  // Update timecode
  const sec = nowMs / 1000;
  timecodeEl.textContent = `${formatTime(sec)} / ${formatTime(totalMs / 1000)}`;

  // Determine scene
  const sceneKey = getSceneKeyAt(nowMs);
  const scene = scenes[sceneKey];
  const entry = timeline.find((t) => t.key === sceneKey);
  const localMs = nowMs - entry.startMs;

  // Scene enter
  if (sceneKey !== lastSceneKey) {
    try {
      scenes[lastSceneKey]?.exit?.(ctx);
    } catch {
      // ignore
    }
    try {
      scene.enter(ctx);
    } catch {
      // ignore
    }

    lastSceneKey = sceneKey;
  }

  // Tick scene
  scene.tick(ctx, nowMs, localMs);

  // Subtitles
  subs.tick(nowMs);

  // Narration cues
  if (narr.state.enabled) {
    for (const cue of narrationCues) {
      if (nowMs >= cue.startMs && !playedNarration.has(cue.startMs)) {
        playedNarration.add(cue.startMs);
        narr.speakCue({ text: cue.text });
      }
    }
  }

  // FX
  ctx2d.clearRect(0, 0, width, height);
  const t = now;
  const intensity = 0.65 + 0.35 * Math.sin(t * 0.0015);
  particles.draw(ctx2d, t, dt, intensity);
  cursorFx.draw(ctx2d, t, dt);

  raf = requestAnimationFrame(frame);

  if (nowMs >= totalMs) {
    stop();
  }
}

const ctx = {
  ui,
  assets,
  fx,
  transitions,
  panZoom,
  applyBgMedia,
  applyBgImage,
  setTitle,
};

function start() {
  stop();
  running = true;
  startPerf = performance.now();
  lastNow = startPerf;
  lastSceneKey = null;
  playedNarration.clear?.();
  playedNarration.clear && playedNarration.clear();

  // Reset styles
  subs.clear();
  if (ui.panZoomEl) ui.panZoomEl.style.opacity = '1';
  fx.enterTrailer?.();

  // First scene enter immediately
  const firstKey = timeline[0].key;
  scenes[firstKey].enter(ctx);
  lastSceneKey = firstKey;

  lastSceneKey = firstKey;
  raf = requestAnimationFrame(frame);
}

function stop() {
  running = false;
  if (raf) cancelAnimationFrame(raf);
  narr.stop();
}

function bindControls() {
  document.getElementById('btnReplay').addEventListener('click', () => {
    showToast('Replaying…');
    start();
  });

  const btnVoice = document.getElementById('btnVoice');
  btnVoice.addEventListener('click', () => {
    const next = btnVoice.getAttribute('aria-pressed') !== 'true';
    btnVoice.setAttribute('aria-pressed', String(next));
    narr.setEnabled(next);
    btnVoice.textContent = `Voice: ${next ? 'On' : 'Off'}`;
    if (next) showToast('Voice enabled');
    else showToast('Voice disabled');

    // Stop current speech to match new mode
    narr.stop();
    // Reset narration timeline triggers for a clean experience
    playedNarration.clear();
  });

  const btnSubs = document.getElementById('btnSubs');
  btnSubs.addEventListener('click', () => {
    const next = btnSubs.getAttribute('aria-pressed') !== 'true';
    btnSubs.setAttribute('aria-pressed', String(next));
    subs.setEnabled(next);
    btnSubs.textContent = `Subtitles: ${next ? 'On' : 'Off'}`;
  });
}

// Ensure pointer glow div follows cursor
if (cursorGlow) {
  const glow = cursorGlow;
  window.addEventListener('pointermove', (e) => {
    glow.style.left = `${e.clientX}px`;
    glow.style.top = `${e.clientY}px`;
  }, { passive: true });
}

window.addEventListener('resize', resizeAll);
resizeAll();
subs.setEnabled(true);

bindControls();

// Preload background assets lightly (best-effort)
for (const k of Object.keys(assets)) {
  const v = assets[k];
  if (!v || typeof v !== 'string') continue;
  if (v.includes('.png') || v.includes('.jpg') || v.includes('.jpeg') || v.includes('.gif')) {
    const img = new Image();
    img.src = v;
  }
}

start();

