"use client";

import { useEffect, useState } from "react";
import { motion, animate } from "framer-motion";
import { cn } from "@/lib/utils";

interface ScoreGaugeProps {
  score: number;
  className?: string;
  size?: number;
}

export function ScoreGauge({ score, className, size = 160 }: ScoreGaugeProps) {
  const [displayScore, setDisplayScore] = useState(0);
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  // 240 degree arc ratio is 240 / 360 = 2/3
  const arcLength = circumference * (240 / 360);
  const gapLength = circumference - arcLength;
  
  useEffect(() => {
    const controls = animate(0, score, {
      duration: 1.5,
      ease: [0.4, 0, 0.2, 1],
      onUpdate: (val) => setDisplayScore(Math.round(val)),
    });
    return controls.stop;
  }, [score]);

  const getColor = (val: number) => {
    if (val < 40) return "#EF4444";
    if (val < 70) return "#F97316";
    return "#22C55E";
  };

  const targetOffset = circumference - (score / 100) * arcLength;

  return (
    <div
      className={cn("relative flex items-center justify-center", className)}
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="transform rotate-150 origin-center absolute">
        {/* Background track arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgba(255,255,255,0.05)"
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeLinecap="round"
          strokeDasharray={`${arcLength} ${gapLength}`}
          strokeDashoffset={0}
          className="transform -rotate-[150deg] origin-center"
        />
        {/* Animated fill arc */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={getColor(displayScore)}
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeLinecap="round"
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: targetOffset }}
          transition={{ duration: 1.5, ease: [0.4, 0, 0.2, 1] }}
          strokeDasharray={`${circumference} ${circumference}`}
          className="transform -rotate-[150deg] origin-center"
        />
      </svg>
      
      {/* Center Value */}
      <div className="flex flex-col items-center justify-center translate-y-2">
        <div className="flex items-baseline gap-1">
          <span className="font-heading text-[48px] font-bold text-white leading-none tracking-tight">
            {displayScore}
          </span>
          <span className="text-[16px] text-slate-400 font-semibold">
            / 100
          </span>
        </div>
      </div>
    </div>
  );
}
