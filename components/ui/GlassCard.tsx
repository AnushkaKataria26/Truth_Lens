"use client";

import { motion, HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/utils";

interface GlassCardProps extends HTMLMotionProps<"div"> {
  className?: string;
  glowColor?: string;
  children: React.ReactNode;
}

export function GlassCard({ className, glowColor = "rgba(59,130,246,0.3)", children, ...props }: GlassCardProps) {
  return (
    <motion.div
      whileHover={{ boxShadow: `0 0 30px ${glowColor}`, borderColor: glowColor }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className={cn(
        "bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.08)] backdrop-blur-[20px] rounded-2xl",
        "shadow-[0_0_40px_rgba(59,130,246,0.05)]",
        className
      )}
      {...props}
    >
      {children}
    </motion.div>
  );
}
