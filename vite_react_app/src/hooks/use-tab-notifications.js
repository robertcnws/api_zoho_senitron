// src/hooks/use-tab-notifications.js
import { useEffect, useMemo, useRef } from 'react';
import { CONFIG } from 'src/config-global';

export function useTabNotifications(
  count,
  {
    appName = CONFIG.appName || 'My App',
    soundEnabled = false,
    soundSrc = '/sounds/notify.mp3',
    playOnEveryPositiveUpdate = false,
  } = {}
) {
  const previousCountRef = useRef(0);
  const audioRef = useRef(null);
  const baseTitle = useMemo(() => appName, [appName]);
  const originalFaviconHrefRef = useRef(null);

  // ---- Título de la pestaña ----
  useEffect(() => {
    document.title = count > 0 ? `(${count}) ${baseTitle}` : baseTitle;
  }, [count, baseTitle]);

  // ---- Favicon con badge ----
  useEffect(() => {
    const link =
      document.querySelector("link[rel='icon']") ||
      document.querySelector("link[rel='shortcut icon']");

    if (!link) return;

    if (!originalFaviconHrefRef.current) {
      originalFaviconHrefRef.current = link.href;
    }

    if (count <= 0) {
      // Reset al favicon original
      link.href = originalFaviconHrefRef.current;
      return;
    }

    const img = new Image();
    // Si tu favicon está en tu mismo dominio, puedes omitir esto:
    img.crossOrigin = 'anonymous';

    img.onload = () => {
      const size = 64;
      const canvas = document.createElement('canvas');
      canvas.width = size;
      canvas.height = size;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // Dibuja base
      ctx.clearRect(0, 0, size, size);
      ctx.drawImage(img, 0, 0, size, size);

      // Badge
      const radius = 18;
      const cx = size - radius + 2;
      const cy = radius - 2;

      ctx.beginPath();
      ctx.fillStyle = '#E53935';
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.fill();

      // Texto
      const text = count > 99 ? '99+' : String(count);
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 24px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(text, cx, cy + 1);

      link.href = canvas.toDataURL('image/png');
    };

    img.src = originalFaviconHrefRef.current || link.href;
  }, [count]);

  // ---- Sonido ----
  useEffect(() => {
    if (!soundEnabled) {
      previousCountRef.current = count;
      return;
    }

    if (!audioRef.current) {
      audioRef.current = new Audio(soundSrc);
      audioRef.current.preload = 'auto';
    }

    const prev = previousCountRef.current;
    const becamePositive = prev <= 0 && count > 0;
    const shouldPlay = playOnEveryPositiveUpdate ? count > 0 : becamePositive;

    if (shouldPlay && audioRef.current) {
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch(() => {
        // Autoplay bloqueado: habilita sonido con un toggle/click del usuario
      });
    }

    previousCountRef.current = count;
  }, [count, soundEnabled, soundSrc, playOnEveryPositiveUpdate]);
}
