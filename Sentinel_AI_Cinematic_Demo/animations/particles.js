// Cyberpunk particles + scanlines.

export function createParticles({ canvas }) {
  const state = {
    dots: [],
    enabled: true,
    spawnAcc: 0,
  };

  function reset(width, height) {
    state.dots = [];
    const count = Math.max(18, Math.floor((width * height) / 50000));
    for (let i = 0; i < count; i++) {
      state.dots.push(spawn(width, height));
    }
  }

  function spawn(width, height) {
    const speed = 18 + Math.random() * 60;
    const size = 1 + Math.random() * 2.2;
    const x = Math.random() * width;
    const y = Math.random() * height;
    const drift = (Math.random() - 0.5) * 0.5;
    return {
      x,
      y,
      vx: (Math.random() - 0.5) * speed * 0.12,
      vy: speed,
      size,
      drift,
      life: 0,
      ttl: 2.2 + Math.random() * 3.2,
      hue: Math.random() < 0.65 ? 170 : 270,
    };
  }

  function draw(ctx, t, dt, intensity = 1) {
    if (!state.enabled) return;

    const w = ctx.canvas.width;
    const h = ctx.canvas.height;

    // Scanlines
    ctx.save();
    ctx.globalAlpha = 0.13 * intensity;
    ctx.fillStyle = 'rgba(255,255,255,0.10)';
    const step = 4;
    for (let y = 0; y < h; y += step) {
      ctx.fillRect(0, y, w, 1);
    }
    ctx.globalAlpha = 1;
    ctx.restore();

    // Particles
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';

    for (const d of state.dots) {
      d.life += dt / 1000;
      if (d.life > d.ttl) {
        Object.assign(d, spawn(w, h));
        d.life = 0;
      }

      d.x += d.vx * (dt / 1000);
      d.y += d.vy * (dt / 1000);
      d.x += d.drift * Math.sin((t + d.y) * 0.002) * (dt / 1000) * 18;

      if (d.y > h + 10) {
        Object.assign(d, spawn(w, h));
        d.life = 0;
      }

      const a = Math.max(0, 1 - d.life / d.ttl);
      ctx.globalAlpha = 0.65 * a * intensity;

      const grad = ctx.createRadialGradient(d.x, d.y, 0, d.x, d.y, d.size * 6);
      grad.addColorStop(0, `hsla(${d.hue}, 95%, 70%, 0.55)`);
      grad.addColorStop(1, `hsla(${d.hue}, 95%, 70%, 0)`);
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(d.x, d.y, d.size * 6, 0, Math.PI * 2);
      ctx.fill();

      ctx.globalAlpha = 0.9 * a * intensity;
      ctx.fillStyle = `hsla(${d.hue}, 95%, 75%, 0.65)`;
      ctx.fillRect(d.x, d.y, d.size, d.size);
    }

    ctx.restore();
  }

  return {
    reset,
    draw,
    state,
  };
}

