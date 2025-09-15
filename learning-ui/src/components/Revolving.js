import { motion, useMotionValue, useAnimationFrame, useTransform } from "framer-motion";
import React from "react";

export default function Revolving() {
  const angle1 = useMotionValue(0);
  const angle2 = useMotionValue(120);
  const angle3 = useMotionValue(240);

  useAnimationFrame((t) => {
    const speed = 0.0015; // lower = slower
    angle1.set((t * speed) % 360);
    angle2.set((t * speed + 120) % 360);
    angle3.set((t * speed + 240) % 360);
  });

  const radius = 300; // orbit size

  const x1 = useTransform(angle1, (a) => radius * Math.cos((a * Math.PI) / 180));
  const y1 = useTransform(angle1, (a) => radius * Math.sin((a * Math.PI) / 180));

  const x2 = useTransform(angle2, (a) => radius * Math.cos((a * Math.PI) / 180));
  const y2 = useTransform(angle2, (a) => radius * Math.sin((a * Math.PI) / 180));

  const x3 = useTransform(angle3, (a) => radius * Math.cos((a * Math.PI) / 180));
  const y3 = useTransform(angle3, (a) => radius * Math.sin((a * Math.PI) / 180));

  return (
    <>
      {/* 📚 */}
      <motion.div
        style={{ position: "absolute", fontSize: "60px", x: x1, y: y1 }}
        transition={{ ease: "linear", duration: 0 }}
      >
        📚
      </motion.div>

      {/* 🎓 */}
      <motion.div
        style={{ position: "absolute", fontSize: "60px", x: x2, y: y2 }}
        transition={{ ease: "linear", duration: 0 }}
      >
        🎓
      </motion.div>

      {/* 💡 */}
      <motion.div
        style={{ position: "absolute", fontSize: "50px", x: x3, y: y3 }}
        transition={{ ease: "linear", duration: 0 }}
      >
        💡
      </motion.div>
    </>
  );
}
