// Voice narration support using Web Speech API.
// Works without extra assets. For best results, use Chrome with autoplay permission from user gesture.

export function createNarration({ toastEl }) {
  const state = {
    enabled: false,
    speaking: false,
    rate: 1.02,
    pitch: 1.02,
    voiceURI: null,
    queue: [],
  };

  function setEnabled(v) {
    state.enabled = !!v;
  }

  function stop() {
    try {
      window.speechSynthesis?.cancel?.();
    } catch {
      // ignore
    }
    state.speaking = false;
  }

  function speakCue({ text, startAt, onStart, onEnd } = {}) {
    if (!state.enabled) return;
    if (!text) return;

    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = state.rate;
    utter.pitch = state.pitch;
    if (state.voiceURI && window.speechSynthesis?.getVoices) {
      const voices = window.speechSynthesis.getVoices();
      const match = voices.find((v) => v.voiceURI === state.voiceURI);
      if (match) utter.voice = match;
    }

    utter.onstart = () => {
      state.speaking = true;
      onStart?.();
    };
    utter.onend = () => {
      state.speaking = false;
      onEnd?.();
    };
    utter.onerror = () => {
      state.speaking = false;
      toastEl?.textContent && (toastEl.textContent = 'Voice engine error — check browser settings');
    };

    // Cancel anything currently speaking to keep sync with timeline
    stop();
    window.speechSynthesis.speak(utter);
  }

  return {
    state,
    setEnabled,
    stop,
    speakCue,
  };
}

