// Retail scene: monitoring + smart alerts for enterprise retail ops.

function makeKpi({ label, value, tone }) {
  const glow = tone === 'ok' ? 'rgba(70,255,147,.45)' : tone === 'hot' ? 'rgba(255,79,216,.55)' : 'rgba(124,255,233,.45)';
  return `
    <div class="kpi">
      <div class="kpi__label">${label}</div>
      <div class="kpi__value" style="text-shadow:0 0 22px ${glow}">${value}</div>
    </div>
  `;
}

export function createRetailScene() {
  const durationMs = 2400;

  function enter(ctx) {
    const { ui, assets, transitions } = ctx;
    ui.panZoomEl && (ui.panZoomEl.style.opacity = '1');

    ctx.applyBgMedia?.(assets.retailBg);

    ui.centerHeadline && (ui.centerHeadline.textContent = 'RETAIL MONITORING');
    ui.centerSubhead && (ui.centerSubhead.textContent = 'Inventory, safety, and anomalies — unified.' );

    transitions?.start?.({ mode: 'crossfade', duration: 650 });

    if (ctx.fx?.setStrength) ctx.fx.setStrength({ chroma: 0.3, bloomAmount: 0.5 });
  }

  function tick(ctx, nowMs, localMs) {
    const p = Math.min(1, Math.max(0, localMs / durationMs));
    const { ui } = ctx;

    if (ui.left) {
      const confidence = Math.floor(78 + 22 * p);
      const coverage = Math.floor(60 + 40 * p);
      ui.left.innerHTML = `
        <div class="hudStack">
          <div class="hudStack__title">SMART RETAIL OPS</div>
          <div class="retailGrid">
            ${makeKpi({ label: 'Anomaly Confidence', value: confidence + '%', tone: confidence > 90 ? 'ok' : 'cool' })}
            ${makeKpi({ label: 'Zone Coverage', value: coverage + '%', tone: 'ok' })}
          </div>
          <div class="alertFeed">
            <div class="alertLine">
              <span class="alertDot" style="background:rgba(255,79,216,.9); box-shadow: 0 0 18px rgba(255,79,216,.9)"></span>
              <span class="alertLabel">High-value asset proximity</span>
              <span class="alertTime">${Math.floor(900 + (1 - p) * 600)}ms</span>
            </div>
            <div class="alertLine">
              <span class="alertDot" style="background:rgba(70,255,147,.95); box-shadow: 0 0 18px rgba(70,255,147,.95)"></span>
              <span class="alertLabel">Crowd flow stabilized</span>
              <span class="alertTime">${Math.floor(650 + (1 - p) * 500)}ms</span>
            </div>
            <div class="alertLine">
              <span class="alertDot" style="background:rgba(124,255,233,.95); box-shadow: 0 0 18px rgba(124,255,233,.95)"></span>
              <span class="alertLabel">Predictive restock window</span>
              <span class="alertTime">${Math.floor(420 + p * 260)}ms</span>
            </div>
          </div>
        </div>
      `;
    }

    if (ui.right) {
      ui.right.innerHTML = `
        <div class="rightStack">
          <div class="bigMetric">${(0.72 + p * 0.21).toFixed(2)}x</div>
          <div class="rightHint">Operational throughput</div>
          <div class="rightSeparator"></div>
          <div class="rightSmall">Explainable actions generated</div>
          <div class="chipRow">
            <span class="chip chip--ghost">Auto-brief</span>
            <span class="chip chip--live">Human-in-loop</span>
          </div>
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

