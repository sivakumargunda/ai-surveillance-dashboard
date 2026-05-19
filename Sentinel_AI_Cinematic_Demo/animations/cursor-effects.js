// Cursor & glow effects: tracks pointer and renders neon bloom + subtle trailing.

export function createCursorEffects({ canvas }) {
  const state = {
    x: 0,
    y: 0,
    tx: 0,
    ty: 0,
    enabled: true,
    lastMoveTs: 0,
  };

  const onMove = (e) => {
    state.tx = e.clientX;
    state.ty = e.clientY;
    state.lastMoveTs = performance.now();
  };

  window.addEventListener('pointermove', onMove, { passive: true });

  function resize() {
    // Canvas is sized in script.js; we only need pointer-relative behavior here.
  }

  function draw(ctx, t, dt) {
    if (!state.enabled) return;

    // Smooth follow
    const follow = 1 - Math.pow(0.001, dt / 16.666);
    state.x += (state.tx - state.x) * follow;
    state.y += (state.ty - state.y) * follow;

    const w = ctx.canvas.width;
    const h = ctx.canvas.height;

    const idle = performance.now() - state.lastMoveTs;
    const idleFactor = Math.min(1, Math.max(0.25, idle / 600));

    // Background-ish bloom
    const cx = state.x;
    const cy = state.y;

    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = 0.55 * idleFactor;

    const pulse = 0.5 + 0.5 * Math.sin(t * 0.008);
    const r1 = 34 + 18 * pulse;

    // Soft radial
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, r1 * 4);
    g.addColorStop(0, 'rgba(124,255,233,0.35)');
    g.addColorStop(0.35, 'rgba(124,255,233,0.14)');
    g.addColorStop(1, 'rgba(124,255,233,0)');
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(cx, cy, r1 * 4, 0, Math.PI * 2);
    ctx.fill();

    // Cursor ring
    ctx.globalAlpha = 0.85 * idleFactor;
    ctx.lineWidth = 1.2;
    ctx.strokeStyle = 'rgba(122,167,255,0.55)';
    ctx.beginPath();
    ctx.arc(cx, cy, 18 + 6 * pulse, 0, Math.PI * 2);
    ctx.stroke();

    // Small trailing streak
    ctx.globalAlpha = 0.45 * idleFactor;
    ctx.lineWidth = 2;
    ctx.strokeStyle = 'rgba(124,255,233,0.5)';
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx - (state.x - state.tx) * 1.2, cy - (state.y - state.ty) * 1.2);
    ctx.stroke();

    ctx.restore();

    // Clamp (safety)
    state.x = Math.max(0, Math.min(w, state.x));
    state.y = Math.max(0, Math.min(h, state.y));
  }

  return { resize, draw, state };
}

