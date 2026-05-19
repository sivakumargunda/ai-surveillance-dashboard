// Analytics scene: enterprise reporting visuals.

function tag(colorClass, text) {
  return `<span class="chip ${colorClass}">${text}</span>`;
}

export function createAnalyticsScene() {
  const durationMs = 2600;

  function enter(ctx) {
    const { ui, assets, transitions } = ctx;
    ui.panZoomEl && (ui.panZoomEl.style.opacity = '1');

    ctx.applyBgMedia?.(assets.analyticsBg);

    ui.centerHeadline && (ui.centerHeadline.textContent = 'AI ANALYTICS');
    ui.centerSubhead && (ui.centerSubhead.textContent = 'Turn events into measurable intelligence.' );

    transitions?.start?.({ mode: 'iris', duration: 700 });
    ctx.fx?.setStrength?.({ chroma: 0.25, bloomAmount: 0.45 });
  }

  function tick(ctx, nowMs, localMs) {
    const p = Math.min(1, Math.max(0, localMs / durationMs));
    const { ui } = ctx;

    if (ui.left) {
      const events = Math.floor(124 + p * 310);
      const anomalies = Math.floor(7 + p * 18);
      const savings = (0.34 + p * 0.22).toFixed(2);

      ui.left.innerHTML = `
        <div class="hudStack">
          <div class="hudStack__title">ENTERPRISE INSIGHTS</div>
          <div class="chartMock">
            <div class="chartMock__grid"></div>
            <div class="chartMock__line" style="--p:${p}"></div>
            <div class="chartMock__glow"></div>
          </div>
          <div class="analyticsMeta">
            <div class="metaRow"><span class="metaKey">EVENTS</span><span class="metaVal">${events}</span></div>
            <div class="metaRow"><span class="metaKey">ANOMALIES</span><span class="metaVal">${anomalies}</span></div>
            <div class="metaRow"><span class="metaKey">IMPACT</span><span class="metaVal">${savings}x</span></div>
          </div>
          <div class="chipRow">
            ${tag('chip--ghost', 'Audit-ready logs')}
            ${tag('chip--live', 'Decision explainability')}
          </div>
        </div>
      `;
    }

    if (ui.right) {
      const latency = Math.floor(72 - p * 28);
      ui.right.innerHTML = `
        <div class="rightStack">
          <div class="smallRow"><span class="key">DECISION LATENCY</span><span class="val">${latency}ms</span></div>
          <div class="smallRow"><span class="key">MODEL ENSEMBLE</span><span class="val">3x</span></div>
          <div class="smallRow"><span class="key">UPTIME</span><span class="val">99.${Math.floor(70 + p * 29)}</span></div>
          <div class="rightGlow" style="opacity:${0.25 + 0.7 * p}"></div>
          <div class="bigMetric bigMetric--right">ROI SIGNAL</div>
        </div>
      `;
    }

    ctx.panZoom?.tick?.(p);
  }

  function exit(ctx) {
    ctx.applyBgMedia?.(null);
    ctx.fx?.setStrength?.({ chroma: 0, bloomAmount: 0 });
  }

  return { durationMs, enter, tick, exit };
}

