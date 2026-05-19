// Cinematic overlay effects (letterbox tweaks + chromatic aberration + bloom-ish overlays)

export function createCinematicEffects({ stageEl }) {
  const wrap = document.createElement('div');
  wrap.style.position = 'absolute';
  wrap.style.inset = '0';
  wrap.style.pointerEvents = 'none';
  wrap.style.zIndex = '24';
  wrap.style.mixBlendMode = 'screen';
  stageEl.appendChild(wrap);

  const vignette = document.createElement('div');
  vignette.style.position = 'absolute';
  vignette.style.inset = '0';
  vignette.style.background =
    'radial-gradient(1000px 700px at 50% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,.55) 100%)';
  vignette.style.opacity = '0.65';
  wrap.appendChild(vignette);

  const aberr = document.createElement('div');
  aberr.style.position = 'absolute';
  aberr.style.inset = '0';
  aberr.style.background =
    'linear-gradient(90deg, rgba(124,255,233,.06), rgba(122,167,255,.06))';
  aberr.style.filter = 'blur(10px)';
  aberr.style.opacity = '0';
  wrap.appendChild(aberr);

  const bloom = document.createElement('div');
  bloom.style.position = 'absolute';
  bloom.style.inset = '0';
  bloom.style.background =
    'radial-gradient(900px 600px at 50% 40%, rgba(124,255,233,.08), rgba(124,255,233,0) 60%)';
  bloom.style.opacity = '0.0';
  wrap.appendChild(bloom);

  function setStrength({ chroma = 0, bloomAmount = 0 }) {
    aberr.style.opacity = String(0.15 + 0.55 * chroma);
    bloom.style.opacity = String(0.05 + 0.85 * bloomAmount);
    const shift = 1.5 * chroma;
    aberr.style.transform = `translate(${shift}px, ${-shift}px)`;
  }

  function enterTrailer() {
    setStrength({ chroma: 0.35, bloomAmount: 0.3 });
  }

  function exitTrailer() {
    setStrength({ chroma: 0, bloomAmount: 0 });
  }

  return { setStrength, enterTrailer, exitTrailer, wrap };
}

