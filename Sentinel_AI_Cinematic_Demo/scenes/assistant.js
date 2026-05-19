// Assistant scene: AI copilot chat + explainability.

function chatBubble({ tone, text }) {
  const col = tone === 'hot' ? 'rgba(255,79,216,.28)' : tone === 'ok' ? 'rgba(70,255,147,.22)' : 'rgba(124,255,233,.22)';
  const stroke = tone === 'hot' ? 'rgba(255,79,216,.28)' : tone === 'ok' ? 'rgba(70,255,147,.25)' : 'rgba(124,255,233,.25)';
  return `
    <div class="chatBubble" style="--bg:${col}; --stroke:${stroke}">
      <div class="chatBubble__avatar"></div>
      <div class="chatBubble__text">${text}</div>
    </div>
  `;
}

export function createAssistantScene() {
  const durationMs = 2800;

  function enter(ctx) {
    const { ui, assets, transitions } = ctx;
    ui.panZoomEl && (ui.panZoomEl.style.opacity = '1');

    ctx.applyBgMedia?.(assets.assistantBg);

    ui.centerHeadline && (ui.centerHeadline.textContent = 'AI ASSISTANT');
    ui.centerSubhead && (ui.centerSubhead.textContent = 'Ask. Explain. Act — in one fluent workflow.' );

    if (ctx.transitions) transitions.start({ mode: 'glitch', duration: 700 });
    ctx.fx?.setStrength?.({ chroma: 0.35, bloomAmount: 0.6 });
  }

  function tick(ctx, nowMs, localMs) {
    const p = Math.min(1, Math.max(0, localMs / durationMs));
    const { ui } = ctx;

    if (ui.left) {
      const step = Math.floor(p * 3);
      const messages = [
        chatBubble({ tone: 'cool', text: 'System health looks strong. Summarize active alerts for me.' }),
        chatBubble({ tone: 'ok', text: 'Top event: Zone intrusion. Confidence is stabilizing; recommended response is authorized.' }),
        chatBubble({ tone: 'hot', text: 'Create a brief for stakeholders with audit-ready evidence.' }),
      ];
      ui.left.innerHTML = `
        <div class="assistantWrap">
          <div class="assistantWrap__title">CINEMATIC COPILOT</div>
          <div class="assistantChat">
            ${messages.slice(0, step + 1).join('')}
          </div>
          <div class="assistantPrompt">
            <span class="assistantPrompt__label">Prompt</span>
            <span class="assistantPrompt__text">"What should I do next?"</span>
          </div>
        </div>
      `;
    }

    if (ui.right) {
      ui.right.innerHTML = `
        <div class="rightStack">
          <div class="rightStack__title">EXPLAINABILITY</div>
          <div class="explainList">
            <div class="explainItem"><span class="explainDot" style="background:rgba(124,255,233,.9)"></span> Vector fusion updated</div>
            <div class="explainItem"><span class="explainDot" style="background:rgba(70,255,147,.95)"></span> Confidence stabilized</div>
            <div class="explainItem"><span class="explainDot" style="background:rgba(255,79,216,.9)"></span> Priority escalation</div>
          </div>
          <div class="rightGlow" style="opacity:${0.25 + 0.7 * p}"></div>
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

