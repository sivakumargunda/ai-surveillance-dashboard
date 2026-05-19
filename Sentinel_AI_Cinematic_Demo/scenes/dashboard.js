// Dashboard scene: telemetry + alert widgets.

function hudCardHtml({ title, value, color, hint }) {
  const glow = color === 'hot'
    ? 'rgba(255,79,216,.55)'
    : color === 'ok'
      ? 'rgba(70,255,147,.45)'
      : 'rgba(124,255,233,.45)';

  return `
    <div class="hudCard hudCard--${color}">
      <div class="hudCard__title">${title}</div>
      <div class="hudCard__value" style="text-shadow:0 0 20px ${glow}">${value}</div>
      <div class="hudCard__bar"><div class="hudCard__barFill" style="width:${value}%"></div></div>
      <div class="hudCard__hint">${hint}</div>
    </div>
  `;
}

export function createDashboardScene() {
  const durationMs = 2400;

  function enter(ctx) {
    const { ui, assets } = ctx;
    ui.panZoomEl && (ui.panZoomEl.style.opacity = '1');

    // Use an uploaded visual as a dashboard background if available.
    // This demo expects assets/dashboard-alerts.png but will fall back gracefully.
    ctx.applyBgImage?.(assets.dashboardBg);

    if (ctx.transitions) ctx.transitions.start({ mode: 'iris', duration: 750 });

    // Scene content
    setHud(ctx, 0);
  }

  function setHud(ctx, p) {
    const { ui } = ctx;
    if (!ui.left) return;

    const signal = Math.floor(70 + 30 * p);
    const coverage = Math.floor(58 + 40 * p);
    const risk = Math.floor(18 + 10 * (1 - p));

    ui.left.innerHTML = `
      ${hudCardHtml({ title: 'SIGNAL INTEGRITY', value: signal, color: 'cool', hint: 'Encrypted links' })}
      ${hudCardHtml({ title: 'SENSOR COVERAGE', value: coverage, color: 'ok', hint: 'Multi-camera mesh' })}
      ${hudCardHtml({ title: 'RISK PRIORITY', value: risk, color: 'hot', hint: 'Detections prioritized' })}
    `;

    if (ui.right) {
      ui.right.innerHTML = `
        <div class="rightStack">
          <div class="pulseRow">
            <span class="chip chip--live">LIVE</span>
            <span class="chip chip--ghost">VECTOR FUSION</span>
          </div>
          <div class="bigMetric">${Math.floor(320 + 240 * p)} ms</div>
          <div class="rightHint">Average decision latency</div>
        </div>
      `;
    }
  }

  function tick(ctx, nowMs, localMs) {
    const p = Math.min(1, Math.max(0, localMs / durationMs));
    setHud(ctx, p);

    // Subtle parallax
    const { ui } = ctx;
    if (ui.panZoomEl) {
      ui.panZoomEl.style.transform = `scale(${1.02 + p * 0.03}) translateX(${(p - 0.5) * -12}px) translateY(${(p - 0.5) * -6}px)`;
    }
  }

  function exit(ctx) {
    const { ui } = ctx;
    if (ui.panZoomEl) ui.panZoomEl.style.opacity = '0';
    ctx.applyBgImage?.(null);
  }

  return { durationMs, enter, tick, exit };
}

