import React, { useEffect, useRef } from "react";

export default function Confetti({ active }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!active) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let animationFrameId;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    // Dynamic colors
    const colors = [
      "#f59e0b", // Amber/Gold
      "#d97706", // Dark Amber
      "#f43f5e", // Rose
      "#10b981", // Emerald
      "#3b82f6", // Blue
      "#8b5cf6", // Purple
      "#06b6d4", // Cyan
    ];

    const particles = [];
    const particleCount = 150;

    // Create particles shooting upward from the bottom center/sides
    for (let i = 0; i < particleCount; i++) {
      const isLeft = Math.random() < 0.5;
      particles.push({
        // Shoot from bottom corners or center
        x: isLeft ? canvas.width * 0.1 : canvas.width * 0.9,
        y: canvas.height + 20,
        vx: isLeft ? Math.random() * 12 + 4 : -(Math.random() * 12 + 4),
        vy: -Math.random() * 18 - 12,
        size: Math.random() * 6 + 5,
        color: colors[Math.floor(Math.random() * colors.length)],
        rotation: Math.random() * 360,
        rotationSpeed: (Math.random() - 0.5) * 8,
        opacity: 1,
        gravity: 0.35,
        friction: 0.985,
        shape: Math.random() < 0.5 ? "circle" : "rect",
      });
    }

    // Add some particles from center bottom
    for (let i = 0; i < 50; i++) {
      particles.push({
        x: canvas.width / 2,
        y: canvas.height + 20,
        vx: (Math.random() - 0.5) * 12,
        vy: -Math.random() * 22 - 10,
        size: Math.random() * 6 + 5,
        color: colors[Math.floor(Math.random() * colors.length)],
        rotation: Math.random() * 360,
        rotationSpeed: (Math.random() - 0.5) * 8,
        opacity: 1,
        gravity: 0.35,
        friction: 0.985,
        shape: Math.random() < 0.5 ? "circle" : "rect",
      });
    }

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      let anyAlive = false;

      particles.forEach((p) => {
        if (p.opacity <= 0) return;
        anyAlive = true;

        p.vy += p.gravity;
        p.vx *= p.friction;
        p.vy *= p.friction;
        p.x += p.vx;
        p.y += p.vy;
        p.rotation += p.rotationSpeed;

        if (p.y > canvas.height * 0.4) {
          // Slow fade out as it drops back down
          p.opacity -= 0.008;
        }

        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rotation * Math.PI) / 180);
        ctx.globalAlpha = p.opacity;
        ctx.fillStyle = p.color;

        if (p.shape === "circle") {
          ctx.beginPath();
          ctx.arc(0, 0, p.size / 2, 0, Math.PI * 2);
          ctx.fill();
        } else {
          ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.6);
        }
        ctx.restore();
      });

      if (anyAlive) {
        animationFrameId = requestAnimationFrame(animate);
      }
    };

    animate();

    return () => {
      window.removeEventListener("resize", resizeCanvas);
      cancelAnimationFrame(animationFrameId);
    };
  }, [active]);

  if (!active) return null;

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        pointerEvents: "none",
        zIndex: 99999,
      }}
    />
  );
}
