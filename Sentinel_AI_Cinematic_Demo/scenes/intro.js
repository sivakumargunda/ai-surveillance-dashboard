// Intro scene: product positioning + cyberpunk ambiance.

export function createIntroScene() {
  const durationMs = 2600;

  function enter(ctx) {
    const { ui, setTitle, fx, transitions } = ctx;
    ui.left && (ui.left.style.opacity = '0');
    ui.right && (ui.right.style.opacity = '0');

    setTitle({
      kicker: 'SENTINEL AI',
      headline: 'Enterprise AI Surveillance',
      subhead: 'Cinematic intelligence for real-time decisions.',
    });

    fx.setStrength?.({ chroma: 0.25, bloomAmount: 0.35 });
    transitions?.start?.({ mode: 'glitch', duration: 650 });
  }

  function tick(ctx, nowMs, localMs) {
    const { ui } = ctx;
    const p = Math.min(1, localMs / durationMs);

    // Left HUD telemetry shimmer
    if (ui.left) {
      ui.left.innerHTML = `
        <div class="hudCard">
          <div class="hudCard__title">SIGNAL INTEGRITY</div>
          <div class="hudCard__value">${Math.floor(92 + 8 * p)}%</div>
          <div class="hudCard__bar"><div class="hudCard__barFill" style="width:${92 + 8 * p}%"></div></div>
          <div class="hudCard__hint">Neural fusion: Active</div>
        </div>
      `;
    }

    if (ui.panZoomEl) {
      const scale = 1.02 + 0.03 * p;
      ui.panZoomEl.style.transform = `scale(${scale}) translate(${(p - 0.5) * -18}px, ${(p - 0.5) * -10}px)`;
    }
  }

  function exit(ctx) {
    ctx.fx.setStrength?.({ chroma: 0.0, bloomAmount: 0.0 });
  }

  return { durationMs, enter, tick, exit };
}

