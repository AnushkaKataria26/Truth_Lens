"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { GlassCard } from "@/components/ui/GlassCard";
import { ShieldAlert, PlayCircle, Users } from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.6 } },
};

const container = {
  hidden: {},
  show:   { transition: { staggerChildren: 0.13 } },
};

const stats = [
  { icon: ShieldAlert, color: "text-red-400",    bg: "bg-red-500/10",    border: "border-red-500/20",    value: "4.1K",  label: "Deepfakes Detected" },
  { icon: PlayCircle,  color: "text-blue-400",   bg: "bg-blue-500/10",   border: "border-blue-500/20",   value: "12.3K", label: "Analyses Run" },
  { icon: Users,       color: "text-indigo-400", bg: "bg-indigo-500/10", border: "border-indigo-500/20", value: "9.8K",  label: "Community Posts" },
];

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden pt-[68px]">
      {/* Animated background orbs */}
      <div
        className="orb-1 pointer-events-none absolute top-0 right-0 w-[640px] h-[640px] rounded-full -translate-y-1/3 translate-x-1/4"
        style={{ background: "radial-gradient(circle, rgba(59,130,246,0.12) 0%, transparent 70%)", filter: "blur(60px)" }}
      />
      <div
        className="orb-2 pointer-events-none absolute bottom-0 left-0 w-[640px] h-[640px] rounded-full translate-y-1/3 -translate-x-1/4"
        style={{ background: "radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%)", filter: "blur(60px)" }}
      />

      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="container mx-auto px-6 relative z-10 flex flex-col items-center text-center max-w-5xl"
      >
        {/* Pill badge */}
        <motion.div variants={fadeUp} className="mb-8">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-blue-500/30 bg-blue-500/[0.07] backdrop-blur-md shadow-[0_0_18px_rgba(59,130,246,0.18)]">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
            <span className="text-[12px] uppercase tracking-[0.2em] font-bold text-blue-400">
              Powered by Multimodal AI
            </span>
          </div>
        </motion.div>

        {/* Main heading */}
        <motion.h1
          variants={fadeUp}
          className="text-[60px] md:text-[76px] font-bold text-white leading-[1.05] tracking-[-0.03em] mb-6"
          style={{ fontFamily: "var(--font-heading)" }}
        >
          Verify Before
          <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-blue-300 to-indigo-400">
            You Believe.
          </span>
        </motion.h1>

        {/* Sub-heading */}
        <motion.p
          variants={fadeUp}
          className="text-[20px] text-slate-400 max-w-[560px] mb-10 leading-relaxed font-medium"
        >
          TruthLens detects deepfakes, synthetic audio, and misleading media in real time — before misinformation spreads.
        </motion.p>

        {/* CTA row */}
        <motion.div variants={fadeUp} className="flex flex-col sm:flex-row items-center gap-4 mb-16">
          <Link href="/analyze" className="w-full sm:w-auto">
            <Button
              size="lg"
              className="w-full glow-blue transition-shadow duration-300"
            >
              Analyze Media
            </Button>
          </Link>
          <Link href="#how-it-works" className="w-full sm:w-auto">
            <Button
              variant="ghost"
              size="lg"
              className="w-full bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20"
            >
              See How It Works
            </Button>
          </Link>
        </motion.div>

        {/* Micro-stat pills */}
        <motion.div
          variants={fadeUp}
          className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full max-w-2xl"
        >
          {stats.map(({ icon: Icon, color, bg, border, value, label }) => (
            <GlassCard
              key={label}
              className="p-4 flex items-center justify-center gap-3"
            >
              <div className={`w-10 h-10 rounded-full ${bg} flex items-center justify-center border ${border} shrink-0`}>
                <Icon className={`w-4.5 h-4.5 ${color}`} size={18} />
              </div>
              <div className="text-left">
                <div className="text-white font-bold text-[20px] leading-tight">{value}</div>
                <div className="text-[13px] text-slate-400 font-medium">{label}</div>
              </div>
            </GlassCard>
          ))}
        </motion.div>
      </motion.div>
    </section>
  );
}
