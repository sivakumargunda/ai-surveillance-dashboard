// Timed subtitles renderer.

export function createSubtitles({ subtitlesEl }) {
  const cues = [];
  let enabled = true;

  function setEnabled(v) {
    enabled = !!v;
    subtitlesEl.style.opacity = enabled ? '1' : '0';
  }

  function clear() {
    subtitlesEl.textContent = '';
  }

  function setCues(nextCues) {
    cues.length = 0;
    cues.push(...nextCues);
  }

  function tick(nowMs) {
    if (!enabled) return;

    // Find most recent cue whose start <= now < end
    const cue = cues.find((c) => nowMs >= c.startMs && nowMs < c.endMs);
    if (!cue) {
      if (subtitlesEl.dataset.last === '1') {
        subtitlesEl.textContent = '';
        subtitlesEl.dataset.last = '0';
      }
      return;
    }

    if (subtitlesEl.dataset.last !== String(cue.id)) {
      subtitlesEl.innerHTML = '';
      const box = document.createElement('div');
      box.className = 'subtitle__box';
      box.textContent = cue.text;
      subtitlesEl.appendChild(box);
      subtitlesEl.dataset.last = String(cue.id);
    }
  }

  return {
    setEnabled,
    clear,
    setCues,
    tick,
  };
}

