import React from 'react';
import { motion, useMotionValue, useSpring, animate } from "framer-motion";
import { useRef, useEffect, useState } from "react";
import Revolving from './Revolving';

// 🧠 Optimized 3D Brain Component (with better depth & lighting)
const MassiveBrain = () => {
  return (
    <motion.div
      style={{
        position: "absolute",
        width: "700px",
        height: "500px",
        left: "50%",
        top: "45%",
        transform: "translate(-50%, -50%)",
        transformStyle: "preserve-3d",
        zIndex: 2,
      }}
      animate={{
        rotateY: [0, 360],
        rotateX: [0, 8, 0, -8, 0],
      }}
      transition={{
        duration: 30,
        repeat: Infinity,
        ease: "linear",
      }}
    >
      {/* Left Hemisphere */}
      <motion.div
        style={{
          position: "absolute",
          width: "320px",
          height: "400px",
          background: `radial-gradient(ellipse at center,
            rgba(147, 197, 253, 0.15) 0%,
            rgba(96, 165, 250, 0.3) 40%,
            rgba(59, 130, 246, 0.25) 70%,
            transparent 100%
          )`,
          borderRadius: "60% 40% 55% 45%",
          left: "40px",
          top: "30px",
          transform: "rotateY(-25deg) translateZ(50px)",
          boxShadow: "inset 0 0 100px rgba(96, 165, 250, 0.5), 0 0 40px rgba(147, 197, 253, 0.3)",
          backfaceVisibility: "hidden",
        }}
        animate={{
          scale: [1, 1.06, 1],
          opacity: [0.8, 1, 0.8],
        }}
        transition={{
          duration: 4.5,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      {/* Right Hemisphere */}
      <motion.div
        style={{
          position: "absolute",
          width: "320px",
          height: "400px",
          background: `radial-gradient(ellipse at center,
            rgba(147, 197, 253, 0.15) 0%,
            rgba(96, 165, 250, 0.3) 40%,
            rgba(59, 130, 246, 0.25) 70%,
            transparent 100%
          )`,
          borderRadius: "40% 60% 45% 55%",
          right: "40px",
          top: "30px",
          transform: "rotateY(25deg) translateZ(50px)",
          boxShadow: "inset 0 0 100px rgba(96, 165, 250, 0.5), 0 0 40px rgba(147, 197, 253, 0.3)",
          backfaceVisibility: "hidden",
        }}
        animate={{
          scale: [1, 1.06, 1],
          opacity: [0.8, 1, 0.8],
        }}
        transition={{
          duration: 4.5,
          repeat: Infinity,
          delay: 0.6,
          ease: "easeInOut",
        }}
      />

      {/* Neural Bridge (Corpus Callosum) */}
      <motion.div
        style={{
          position: "absolute",
          width: "250px",
          height: "18px",
          background: "linear-gradient(90deg, transparent, #60a5fa, #3b82f6, #60a5fa, transparent)",
          left: "50%",
          top: "50%",
          transform: "translate(-50%, -50%) translateZ(60px)",
          borderRadius: "30px",
          boxShadow: "0 0 50px rgba(96, 165, 250, 0.9)",
          zIndex: 3,
        }}
        animate={{
          scaleX: [1, 1.5, 1],
          opacity: [0.7, 1, 0.7],
        }}
        transition={{
          duration: 3.5,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      {/* Brain Stem */}
      <motion.div
        style={{
          position: "absolute",
          width: "55px",
          height: "110px",
          background: "linear-gradient(to bottom, rgba(96, 165, 250, 0.5), rgba(59, 130, 246, 0.7))",
          left: "50%",
          bottom: "-30px",
          transform: "translateX(-50%) translateZ(40px)",
          borderRadius: "30px 30px 15px 15px",
        }}
        animate={{
          scaleY: [1, 1.15, 1],
          opacity: [0.7, 1, 0.7],
        }}
        transition={{
          duration: 5,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      {/* Brain Folds (Optimized: fewer, more impactful) */}
      {[...Array(8)].map((_, i) => {
        const angle = Math.random() * 60 - 30;
        const delay = i * 0.3;
        return (
          <motion.div
            key={i}
            style={{
              position: "absolute",
              width: `${70 + Math.random() * 80}px`,
              height: "4px",
              background: "rgba(147, 197, 253, 0.7)",
              borderRadius: "8px",
              left: `${25 + Math.random() * 50}%`,
              top: `${30 + Math.random() * 40}%`,
              transform: `rotate(${angle}deg) translateZ(55px)`,
              zIndex: 1,
            }}
            animate={{
              opacity: [0.4, 0.9, 0.4],
              scaleX: [1, 1.3, 1],
            }}
            transition={{
              duration: 3 + Math.random(),
              repeat: Infinity,
              delay,
              ease: "easeInOut",
            }}
          />
        );
      })}
    </motion.div>
  );
};

// 🔗 Neural Network: Optimized with canvas-like layering
const NeuralNetwork = () => {
  const [neurons] = useState(() => {
    const arr = [];
    for (let i = 0; i < 25; i++) {
      const angle = (i / 25) * Math.PI * 2;
      const radius = 30 + Math.random() * 15;
      const x = 50 + Math.cos(angle) * radius;
      const y = 45 + Math.sin(angle) * radius * 0.6;

      arr.push({
        id: i,
        x,
        y,
        delay: Math.random() * 3,
        size: 5 + Math.random() * 3,
      });
    }
    return arr;
  });

  return (
    <div style={{ position: "absolute", width: "100%", height: "100%", zIndex: 5, pointerEvents: "none" }}>
      {/* Connections (optimized count) */}
      {neurons.slice(0, 12).map((n, i) => {
        const target = neurons[(i + 4) % neurons.length];
        const dx = target.x - n.x;
        const dy = target.y - n.y;
        const length = Math.sqrt(dx * dx + dy * dy) * 0.8;
        const angle = (Math.atan2(dy, dx) * 180) / Math.PI;

        return (
          <motion.div
            key={`conn-${i}`}
            style={{
              position: "absolute",
              left: `${n.x}%`,
              top: `${n.y}%`,
              width: `${length}%`,
              height: "1.5px",
              background: "linear-gradient(90deg, transparent, #60a5fa, #3b82f6, transparent)",
              transformOrigin: "left center",
              transform: `rotate(${angle}deg)`,
              zIndex: 3,
            }}
            animate={{
              scaleX: [0, 1, 0],
              opacity: [0, 0.7, 0],
            }}
            transition={{
              duration: 2.5,
              repeat: Infinity,
              delay: i * 0.4,
              ease: "easeInOut",
            }}
          />
        );
      })}

      {/* Neurons */}
      {neurons.map((n) => (
        <motion.div
          key={n.id}
          style={{
            position: "absolute",
            left: `${n.x}%`,
            top: `${n.y}%`,
            width: `${n.size}px`,
            height: `${n.size}px`,
            background: "radial-gradient(circle, #60a5fa, #3b82f6, #1e40af)",
            borderRadius: "50%",
            boxShadow: "0 0 20px rgba(96, 165, 250, 0.8)",
            zIndex: 6,
            translateX: -n.size / 2,
            translateY: -n.size / 2,
          }}
          animate={{
            scale: [1, 1.8, 1],
            opacity: [0.7, 1, 0.7],
          }}
          transition={{
            duration: 2 + Math.random(),
            repeat: Infinity,
            delay: n.delay,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
};

// 📚 Knowledge Flow: Use fewer, faster particles
const KnowledgeFlow = () => {
  return (
    <motion.div
      style={{
        position: "absolute",
        width: "100%",
        height: "100%",
        zIndex: 1,
        pointerEvents: "none",
      }}
    >
      {[...Array(15)].map((_, i) => (
        <motion.div
          key={i}
          style={{
            position: "absolute",
            width: "6px",
            height: "6px",
            background: "#fbbf24",
            borderRadius: "50%",
            boxShadow: "0 0 15px rgba(251, 191, 36, 0.7)",
            top: "100%",
            left: `${Math.random() * 100}%`,
          }}
          animate={{
            y: [-100, -400],
            x: [(Math.random() - 0.5) * 150],
            opacity: [0, 1, 0],
            scale: [0.5, 1.2, 0],
          }}
          transition={{
            duration: 4 + Math.random() * 3,
            repeat: Infinity,
            delay: i * 0.4,
            ease: "easeOut",
          }}
        />
      ))}
    </motion.div>
  );
};

// 🌟 Floating Orbs with depth
const FloatingOrbs = () => {
  return (
    <>
      {[...Array(6)].map((_, i) => {
        const size = 60 + Math.random() * 80;
        return (
          <motion.div
            key={i}
            style={{
              position: "absolute",
              width: `${size}px`,
              height: `${size}px`,
              background: `radial-gradient(circle, 
                rgba(251, 191, 36, 0.3) 0%, 
                rgba(147, 197, 253, 0.15) 50%, 
                transparent 70%
              )`,
              borderRadius: "50%",
              zIndex: 0,
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              transform: `translateZ(${-40 - i * 5}px)`,
            }}
            animate={{
              scale: [1, 1.4, 1],
              opacity: [0.2, 0.6, 0.2],
              x: [0, Math.random() * 100 - 50],
              y: [0, Math.random() * 100 - 50],
            }}
            transition={{
              duration: 12 + Math.random() * 6,
              repeat: Infinity,
              delay: i * 1,
              ease: "easeInOut",
            }}
          />
        );
      })}
    </>
  );
};

// 🔤 Floating Alphabets Component
const FloatingAlphabets = () => {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  const [letters] = useState(() => {
    return Array.from({ length: 30 }, (_, i) => ({
      id: i,
      char: alphabet[Math.floor(Math.random() * alphabet.length)],
      left: Math.random() * 100,
      delay: Math.random() * 5,
      duration: 8 + Math.random() * 10,
      size: 12 + Math.random() * 8,
      opacity: 0.2 + Math.random() * 0.5,
    }));
  });

  return (
    <div style={{ position: "absolute", width: "100%", height: "100%", zIndex: 4, pointerEvents: "none" }}>
      {letters.map((letter) => (
        <motion.div
          key={letter.id}
          style={{
            position: "absolute",
            left: `${letter.left}%`,
            bottom: "-50px",
            fontSize: `${letter.size}px`,
            color: `rgba(147, 197, 253, ${letter.opacity})`,
            fontWeight: "bold",
            zIndex: 4,
          }}
          initial={{ y: 0, opacity: 0 }}
          animate={{
            y: [-50, -window.innerHeight - 100],
            opacity: [0, letter.opacity, 0],
            x: [0, (Math.random() - 0.5) * 100],
            rotate: [0, Math.random() * 360],
          }}
          transition={{
            duration: letter.duration,
            repeat: Infinity,
            delay: letter.delay,
            ease: "linear",
          }}
        >
          {letter.char}
        </motion.div>
      ))}
    </div>
  );
};

// ⚡ Enhanced Sparks Component
const EnhancedSparks = () => {
  return (
    <div style={{ position: "absolute", width: "100%", height: "100%", zIndex: 8, pointerEvents: "none" }}>
      {[...Array(20)].map((_, i) => (
        <motion.div
          key={i}
          style={{
            position: "absolute",
            width: `${2 + Math.random() * 4}px`,
            height: `${2 + Math.random() * 4}px`,
            background: "#fbbf24",
            borderRadius: "50%",
            boxShadow: "0 0 15px rgba(251, 191, 36, 0.9)",
            zIndex: 8,
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
          animate={{
            scale: [0, 1.5 + Math.random(), 0],
            opacity: [0, 1, 0],
            x: [(Math.random() - 0.5) * 100],
            y: [(Math.random() - 0.5) * 100],
          }}
          transition={{
            duration: 1.5 + Math.random() * 2,
            repeat: Infinity,
            delay: i * 0.3,
            ease: "easeOut",
          }}
        />
      ))}
    </div>
  );
};

// 🎯 Camera Parallax Hook
const useParallax = (strength = 20) => {
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMove = (e) => {
      const x = (window.innerWidth / 2 - e.clientX) / window.innerWidth;
      const y = (window.innerHeight / 2 - e.clientY) / window.innerHeight;
      setOffset({ x, y });
    };
    window.addEventListener("mousemove", handleMove);
    return () => window.removeEventListener("mousemove", handleMove);
  }, []);

  return {
    x: offset.x * strength,
    y: offset.y * strength,
  };
};

// 🧠 Main Landing Page
const LandingPage = () => {
  const mouseX = useMotionValue(-100);
  const mouseY = useMotionValue(-100);
  const cursorRef = useRef(null);

  const springConfig = { stiffness: 500, damping: 28 };
  const xs = useSpring(mouseX, springConfig);
  const ys = useSpring(mouseY, springConfig);

  const { x: parallaxX, y: parallaxY } = useParallax(15);

  // Mouse tracking
  useEffect(() => {
    const handleMouseMove = (e) => {
      mouseX.set(e.clientX);
      mouseY.set(e.clientY);
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [mouseX, mouseY]);

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #0a0118 0%, #1a0b3d 25%, #0f172a 50%, #1e1b4b 75%, #0a0118 100%)",
        overflow: "hidden",
        position: "relative",
        perspective: "3000px",
        color: "#e2e8f0",
        transformStyle: "preserve-3d",
      }}
    >
      {/* 🌌 Background with parallax */}
      <motion.div
        style={{
          position: "absolute",
          width: "300%",
          height: "300%",
          top: "-100%",
          left: "-100%",
          background: `
            radial-gradient(circle at 25% 35%, rgba(251, 191, 36, 0.1) 0%, transparent 40%),
            radial-gradient(circle at 75% 65%, rgba(147, 197, 253, 0.12) 0%, transparent 40%),
            radial-gradient(circle at 50% 85%, rgba(96, 165, 250, 0.06) 0%, transparent 40%)
          `,
          zIndex: 0,
          transform: `translateZ(-100px) rotateY(${parallaxX / 2}deg) rotateX(${parallaxY / 2}deg)`,
        }}
        animate={{ rotate: 360 }}
        transition={{ duration: 60, repeat: Infinity, ease: "linear" }}
      />

      {/* 🌟 Floating Orbs with depth */}
      <FloatingOrbs />

      {/* 🔤 Floating Alphabets */}
      <FloatingAlphabets />

      {/* ⚡ Enhanced Sparks */}
      <EnhancedSparks />

      {/* 🧠 3D Brain */}
      <div style={{ transform: `translateZ(100px)` }}>
        <MassiveBrain />
      </div>

      {/* 🔗 Neural Network (floating above brain) */}
      <div style={{ position: "absolute", width: "100%", height: "100%", transform: "translateZ(120px)" }}>
        <NeuralNetwork />
      </div>

      {/* 📚 Knowledge Flow */}
      <KnowledgeFlow />

      {/* 💡 Floating Icons with depth */}
      <Revolving />

      {/* 🧠 Custom Cursor */}
      <motion.div
        ref={cursorRef}
        style={{
          position: "fixed",
          left: xs,
          top: ys,
          x: -20,
          y: -20,
          fontSize: "32px",
          pointerEvents: "none",
          zIndex: 50,
          filter: "drop-shadow(0 0 15px rgba(251, 191, 36, 0.8))",
          transform: "translateZ(200px)",
        }}
        animate={{ rotate: [0, 10, -10, 0], scale: [1, 1.3, 1] }}
        transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
      >
        🧠
      </motion.div>

      {/* 🎯 Title with 3D depth */}
      <motion.h1
        initial={{ y: -150, opacity: 0, rotateX: -90 }}
        animate={{ y: 0, opacity: 1, rotateX: 0 }}
        transition={{ duration: 1.8, ease: "backOut" }}
        style={{
          fontSize: "5.5rem",
          background: "linear-gradient(45deg, #fbbf24, #f59e0b, #60a5fa, #3b82f6, #9333ea)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          backgroundSize: "400% 400%",
          fontWeight: 900,
          zIndex: 10,
          textAlign: "center",
          textShadow: "0 0 40px rgba(251, 191, 36, 0.5)",
          transformStyle: "preserve-3d",
          position: "relative",
          letterSpacing: "0.03em",
          marginBottom: "1rem",
          transform: "translateZ(100px)",
        }}
        animate={{
          backgroundPosition: ["0% 0%", "100% 100%", "0% 0%"],
        }}
        transition={{
          backgroundPosition: { duration: 8, repeat: Infinity, ease: "linear" },
        }}
        whileHover={{
          scale: 1.08,
          rotateY: 15,
          textShadow: "0 0 60px rgba(251, 191, 36, 0.8)",
        }}
      >
        Welcome to EduAI
      </motion.h1>

      {/* Subtitle */}
      <motion.p
        initial={{ opacity: 0, scale: 0.8, z: -100 }}
        animate={{ opacity: 1, scale: 1, z: 0 }}
        transition={{ duration: 1.8, delay: 0.8 }}
        style={{
          fontSize: "2rem",
          color: "#e2e8f0",
          marginBottom: "3.5rem",
          textAlign: "center",
          maxWidth: "800px",
          zIndex: 10,
          fontWeight: 500,
          letterSpacing: "0.05em",
          textShadow: "0 0 25px rgba(96, 165, 250, 0.4)",
          background: "rgba(15, 23, 42, 0.4)",
          padding: "1.2rem 2.5rem",
          borderRadius: "30px",
          backdropFilter: "blur(25px)",
          border: "2px solid rgba(147, 197, 253, 0.3)",
          boxShadow: "0 15px 50px rgba(0, 0, 0, 0.2)",
          transform: "translateZ(80px)",
        }}
      >
        Supercharge Your Learning with AI-Powered Personlized learning
      </motion.p>

      {/* Buttons */}
      <motion.div
        initial={{ opacity: 0, y: 100, rotateX: -45 }}
        animate={{ opacity: 1, y: 0, rotateX: 0 }}
        transition={{ duration: 1.8, delay: 1.2 }}
        style={{ 
          display: "flex", 
          gap: "3rem", 
          zIndex: 10,
          transform: "translateZ(90px)",
        }}
      >
        <motion.a
          href="/register"
          whileHover={{
            scale: 1.2,
            y: -18,
            rotateY: 12,
            boxShadow: "0 30px 80px rgba(251, 191, 36, 0.7)",
          }}
          whileTap={{ scale: 0.9 }}
          style={{
            background: "linear-gradient(135deg, #fbbf24, #f59e0b)",
            color: "#000",
            padding: "1.4rem 3.2rem",
            borderRadius: "28px",
            fontWeight: 800,
            fontSize: "1.4rem",
            textDecoration: "none",
            boxShadow: "0 20px 50px rgba(251, 191, 36, 0.5)",
            position: "relative",
            overflow: "hidden",
            display: "flex",
            alignItems: "center",
            gap: "1rem",
          }}
        >
          Start Learning Journey
        </motion.a>

        <motion.a
          href="/login"
          whileHover={{
            scale: 1.2,
            y: -18,
            rotateY: -12,
            boxShadow: "0 30px 80px rgba(147, 197, 253, 0.5)",
          }}
          whileTap={{ scale: 0.9 }}
          style={{
            background: "rgba(15, 23, 42, 0.85)",
            backdropFilter: "blur(30px)",
            color: "#e2e8f0",
            padding: "1.4rem 3.2rem",
            borderRadius: "28px",
            fontWeight: 800,
            fontSize: "1.4rem",
            textDecoration: "none",
            border: "3px solid rgba(147, 197, 253, 0.6)",
            boxShadow: "0 20px 50px rgba(59, 130, 246, 0.4)",
            display: "flex",
            alignItems: "center",
            gap: "1rem",
          }}
        >
          Login
        </motion.a>
      </motion.div>
    </div>
  );
};

export default LandingPage;