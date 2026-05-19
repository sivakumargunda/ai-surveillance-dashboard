// Scene transitions: crossfade, iris wipe, and glitch blend.

function easeInOutCubic(x) {
  return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
}

export function createTransitions({ stageEl }) {
  const state = {
    mode: 'none',
    t0: 0,
    duration: 900,
    active: false,
  };

  // Overlay layers
  const overlay = document.createElement('div');
  overlay.style.position = 'absolute';
  overlay.style.inset = '0';
  overlay.style.pointerEvents = 'none';
  overlay.style.zIndex = '30';
  overlay.style.opacity = '0';
  overlay.style.background = 'black';
  overlay.style.transition = 'none';
  stageEl.appendChild(overlay);

  const iris = document.createElement('div');
  iris.style.position = 'absolute';
  iris.style.inset = '0';
  iris.style.pointerEvents = 'none';
  iris.style.zIndex = '31';
  iris.style.background = 'black';
  iris.style.opacity = '0';
  iris.style.clipPath = 'circle(0% at 50% 50%)';
  stageEl.appendChild(iris);

  const glitch = document.createElement('div');
  glitch.style.position = 'absolute';
  glitch.style.inset = '0';
  glitch.style.pointerEvents = 'none';
  glitch.style.zIndex = '32';
  glitch.style.opacity = '0';
  glitch.style.background = 'transparent';
  glitch.style.mixBlendMode = 'screen';
  stageEl.appendChild(glitch);

  function buildGlitchFrame(alpha) {
    glitch.style.opacity = String(alpha);
    glitch.innerHTML = '';
    // scanlines
    for (let i = 0; i < 10; i++) {
      const y = 15 + i * 8;
      const d = document.createElement('div');
      d.style.position = 'absolute';
      d.style.left = '0';
      d.style.right = '0';
      d.style.top = y + '%';
      d.style.height = '2px';
      d.style.background = i % 2 === 0 ? 'rgba(124,255,233,.55)' : 'rgba(255,79,216,.45)';
      d.style.filter = 'blur(0.2px)';
      d.style.transform = `translateX(${(Math.random() - 0.5) * 24}px)`;
      glitch.appendChild(d);
    }
    // bar
    const bar = document.createElement('div');
    bar.style.position = 'absolute';
    bar.style.left = '-10%';
    bar.style.right = '-10%';
    bar.style.top = '35%';
    bar.style.height = '16%';
    bar.style.background = 'rgba(255,255,255,.08)';
    bar.style.transform = `translateX(${(Math.random() - 0.5) * 60}px) skewX(-12deg)`;
    glitch.appendChild(bar);
  }

  function start({ mode = 'crossfade', duration = 900 } = {}) {
    state.mode = mode;
    state.t0 = performance.now();
    state.duration = duration;
    state.active = true;
    overlay.style.opacity = '1';
    iris.style.opacity = '1';
    glitch.style.opacity = '0';
  }

  function tick(now) {
    if (!state.active) return;
    const elapsed = now - state.t0;
    const p = Math.min(1, Math.max(0, elapsed / state.duration));
    const e = easeInOutCubic(p);

    if (state.mode === 'crossfade') {
      overlay.style.opacity = String(1 - e);
      iris.style.opacity = '0';
      glitch.style.opacity = '0';
    } else if (state.mode === 'iris') {
      const r = Math.max(0, 1 - e);
      iris.style.opacity = String(1);
      iris.style.clipPath = `circle(${(1 - r) * 120}% at 50% 50%)`;
      overlay.style.opacity = '0';
      glitch.style.opacity = '0';
    } else if (state.mode === 'glitch') {
      overlay.style.opacity = String(0.55 * (1 - e));
      iris.style.opacity = '0';
      buildGlitchFrame(0.8 * (1 - e));
    }

    if (p >= 1) {
      state.active = false;
      overlay.style.opacity = '0';
      iris.style.opacity = '0';
      glitch.style.opacity = '0';
    }
  }

  return { start, tick, state };
}

