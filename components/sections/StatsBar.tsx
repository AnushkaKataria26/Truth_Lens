"use client";

import { useEffect, useState, useRef } from "react";
import { motion, useInView, animate } from "framer-motion";

interface StatItemProps {
  label: string;
  value: number;
  suffix?: string;
  index: number;
}

function StatItem({ label, value, suffix = "", index }: StatItemProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-60px" });
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    if (isInView) {
      const controls = animate(0, value, {
        duration: 2.2,
        delay: index * 0.12,
        ease: "easeOut",
        onUpdate: (val) => setDisplayValue(Math.round(val)),
      });
      return controls.stop;
    }
  }, [isInView, value, index]);

  return (
    <div
      ref={ref}
      className="flex flex-col items-center justify-center py-8 px-6 text-center flex-1 min-w-0"
    >
      <div className="text-[40px] md:text-[52px] font-heading font-bold text-white mb-1 leading-none tracking-tight">
        {displayValue.toLocaleString()}
        <span className="text-blue-400">{suffix}</span>
      </div>
      <div className="text-[12px] text-slate-400 font-semibold uppercase tracking-[0.15em] mt-1">
        {label}
      </div>
    </div>
  );
}

export function StatsBar() {
  const stats = [
    { label: "Total Analyses",    value: 2145,  suffix: "K+" },
    { label: "Deepfakes Flagged", value: 1842,  suffix: "K+" },
    { label: "Active Users",      value: 85000, suffix: "+"  },
    { label: "Accuracy Rate",     value: 99,    suffix: "%"  },
  ];

  return (
    <section className="py-6 relative z-10 w-full px-4 md:px-6">
      <div className="container mx-auto max-w-6xl">
        <div className="glass-card flex flex-col md:flex-row items-stretch justify-around divide-y md:divide-y-0 overflow-hidden p-0">
          {stats.map((stat, i) => (
            <div key={stat.label} className="flex-1 flex">
              <StatItem
                label={stat.label}
                value={stat.value}
                suffix={stat.suffix}
                index={i}
              />
              {i < stats.length - 1 && (
                <div className="hidden md:block w-px bg-[rgba(255,255,255,0.08)] my-6 shrink-0" />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
