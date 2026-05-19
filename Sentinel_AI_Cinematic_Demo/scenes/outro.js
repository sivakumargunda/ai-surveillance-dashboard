// Outro scene: closing call to action.

export function createOutroScene() {
  const durationMs = 2400;

  function enter(ctx) {
    const { ui, assets, transitions } = ctx;
    ui.panZoomEl && (ui.panZoomEl.style.opacity = '1');

    ctx.applyBgMedia?.(assets.outroBg);

    ui.centerHeadline && (ui.centerHeadline.textContent = 'SENTINEL AI');
    ui.centerSubhead && (ui.centerSubhead.textContent = 'Security intelligence built for enterprise speed.' );
    ui.centerKicker && (ui.centerKicker.textContent = 'READY TO DEPLOY');

    transitions?.start?.({ mode: 'glitch', duration: 800 });
    ctx.fx?.setStrength?.({ chroma: 0.25, bloomAmount: 0.35 });
  }

  function tick(ctx, nowMs, localMs) {
    const p = Math.min(1, Math.max(0, localMs / durationMs));
    const { ui } = ctx;

    if (ui.right) {
      ui.right.innerHTML = `
        <div class="rightStack">
          <div class="rightStack__title">NEXT ACTION</div>
          <div class="ctaBox">
            <div class="ctaBox__line">Request a demo • Integrate in weeks</div>
            <div class="ctaBox__line">Deploy across cameras & sites</div>
            <div class="ctaBox__line">Audit-ready explainability</div>
          </div>
          <div class="ctaPulse"></div>
        </div>
      `;
    }

    if (ui.left) {
      ui.left.innerHTML = `
        <div class="hudStack">
          <div class="hudStack__title">TRAILER RUNTIME</div>
          <div class="runtimeRow">${Math.floor(15 + p * 5)}s</div>
          <div class="hudCard__hint">Neon bloom • Glass UI • Smooth transitions</div>
        </div>
      `;
    }

    // Bring center panel focus at the end
    if (ctx.ui.centerPanel) {
      ctx.ui.centerPanel.style.opacity = String(0.9 + 0.1 * p);
    }
  }

  function exit(ctx) {
    ctx.applyBgMedia?.(null);
    ctx.fx?.setStrength?.({ chroma: 0, bloomAmount: 0 });
  }

  return { durationMs, enter, tick, exit };
}

