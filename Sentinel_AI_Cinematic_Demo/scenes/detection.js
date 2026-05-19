// Detection scene: cinematic surveillance frames + zoom/pan + alert callouts.

function safeInt(v) {
  return String(Math.max(0, Math.min(9999, Math.floor(v))));
}

function createAlertLine({ label, time, tone }) {
  const col = tone === 'hot' ? 'rgba(255,79,216,.9)' : tone === 'ok' ? 'rgba(70,255,147,.95)' : 'rgba(124,255,233,.95)';
  return `
    <div class="alertLine">
      <span class="alertDot" style="background:${col}; box-shadow: 0 0 18px ${col}"></span>
      <span class="alertLabel">${label}</span>
      <span class="alertTime">${time}</span>
    </div>
  `;
}

export function createDetectionScene() {
  const durationMs = 2500;

  function enter(ctx) {
    const { ui, assets, panZoom } = ctx;

    ui.panZoomEl && (ui.panZoomEl.style.opacity = '1');

    // If we have a video, use it; otherwise use an image background.
    ctx.applyBgMedia?.(assets.detectionBg);

    if (panZoom) {
      panZoom.setPlan?.({
        start: { x: -0.03, y: 0.02, s: 1.06 },
        mid: { x: 0.02, y: -0.01, s: 1.14 },
        end: { x: 0.00, y: 0.00, s: 1.10 },
      });
    }

    if (ctx.fx && ctx.fx.setStrength) ctx.fx.setStrength({ chroma: 0.45, bloomAmount: 0.65 });

    // Load a small “detection sequence” from available frames if any.
    ui.centerHeadline && (ui.centerHeadline.textContent = 'LIVE DETECTION');
    ui.centerSubhead && (ui.centerSubhead.textContent = 'Neural surveillance — fast, consistent, explainable.');

    ctx.transitions?.start?.({ mode: 'crossfade', duration: 650 });
  }

  function tick(ctx, nowMs, localMs) {
    const p = Math.min(1, Math.max(0, localMs / durationMs));
    const { ui } = ctx;

    if (ui.left) {
      const t = (p * durationMs) / 1000;
      const ms = Math.floor(t * 1000);
      const risk = Math.floor(20 + 75 * Math.sin(p * Math.PI));

      ui.left.innerHTML = `
        <div class="hudStack">
          <div class="hudStack__title">DETECTION FEED</div>
          <div class="hudStack__chipRow">
            <span class="chip chip--live">TRACKING</span>
            <span class="chip chip--ghost">EXPLAINABILITY</span>
          </div>
          <div class="hudStack__metric">RISK SCORE <span class="metricNum">${safeInt(risk)}</span></div>
          <div class="hudStack__bar"><div class="hudStack__barFill" style="width:${risk}%"></div></div>
          <div class="alertFeed">
            ${createAlertLine({ label: 'Zone intrusion detected', time: `${safeInt(ms)}ms`, tone: 'hot' })}
            ${createAlertLine({ label: 'Confidence stabilized', time: `${safeInt(80 + p * 20)}ms`, tone: 'ok' })}
            ${createAlertLine({ label: 'Vector fusion updated', time: `${safeInt(60 + (1 - p) * 30)}ms`, tone: 'cool' })}
          </div>
        </div>
      `;
    }

    if (ui.right) {
      const zoom = (1.02 + p * 0.18);
      ui.right.innerHTML = `
        <div class="rightStack rightStack--dense">
          <div class="smallRow"><span class="key">ACTIVE CAMS</span><span class="val">${3 + Math.floor(p * 4)}</span></div>
          <div class="smallRow"><span class="key">OBJECTS</span><span class="val">${6 + Math.floor(4 * p)}</span></div>
          <div class="smallRow"><span class="key">FRAME RATE</span><span class="val">${Math.floor(18 + 10 * p)} fps</span></div>
          <div class="rightGlow" style="opacity:${0.25 + 0.65 * p}"></div>
          <div class="bigMetric bigMetric--right" style="font-size:clamp(20px,2.4vw,34px)">${Math.floor(0.82 + 0.15 * p)}x</div>
          <div class="rightHint">Cinematic zoom factor</div>
          <div class="zoomHud" style="transform: scale(${zoom})">ZOOM</div>
        </div>
      `;
    }

    ctx.panZoom?.tick?.(p);

    // Fade the center glass to make HUD feel “alive”
    if (ctx.ui.centerPanel) {
      ctx.ui.centerPanel.style.opacity = String(1 - 0.2 * p);
    }

    // Add letterbox emphasis near the middle
    if (ctx.ui.letterbox && ctx.ui.letterboxTweak) {
      const e = Math.sin(p * Math.PI);
      ctx.ui.letterboxTweak(e);
    }

    // Voice cues are driven by timeline (script.js), not scene.
  }

  function exit(ctx) {
    ctx.applyBgMedia?.(null);
    ctx.fx?.setStrength?.({ chroma: 0, bloomAmount: 0 });
  }

  return { durationMs, enter, tick, exit };
}

