"use client";

import { motion } from "framer-motion";
import { GlassCard } from "@/components/ui/GlassCard";
import { ScoreGauge } from "@/components/ui/ScoreGauge";
import { RiskBadge } from "@/components/ui/RiskBadge";
import {
  Video, AudioLines, ImageIcon, FileText,
  Map, MessageSquare, Shield, BrainCircuit, Activity,
} from "lucide-react";

function SmallCard({
  title,
  desc,
  icon: Icon,
  color,
  delay,
}: {
  title: string;
  desc: string;
  icon: React.ElementType;
  color: string;
  delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.5, delay, ease: [0.4, 0, 0.2, 1] }}
      className="col-span-1 row-span-1 h-full"
    >
      <GlassCard className="w-full h-full flex flex-col group p-6">
        <Icon
          className={`w-8 h-8 ${color} mb-5 group-hover:scale-110 group-hover:rotate-3 transition-transform duration-300`}
        />
        <h4 className="text-[16px] font-bold text-white mb-2">{title}</h4>
        <p className="text-slate-400 text-[13px] leading-relaxed">{desc}</p>
      </GlassCard>
    </motion.div>
  );
}

export function FeaturesSection() {
  return (
    <section className="py-28 relative z-10 w-full overflow-hidden">
      <div className="container mx-auto px-6 max-w-7xl">
        {/* Heading */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
          className="text-center mb-16"
        >
          <h2 className="text-[36px] md:text-[52px] font-heading font-bold text-white tracking-tight mb-4">
            Everything You Need to Fight Misinformation
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto text-[18px] leading-relaxed">
            Enterprise-grade detection tools distilled into an intuitive, agentic platform.
          </p>
        </motion.div>

        {/* Bento grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 auto-rows-[230px]">

          {/* Large Card 1 — Multimodal Detection */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="md:col-span-2 row-span-2 h-full"
          >
            <GlassCard
              className="w-full h-full flex flex-col relative overflow-hidden group p-8"
            >
              <div className="flex flex-col mb-auto relative z-10">
                <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20 mb-6 group-hover:bg-blue-500/20 transition-colors duration-300">
                  <BrainCircuit className="w-6 h-6 text-blue-400" />
                </div>
                <h3 className="text-[22px] font-bold text-white mb-3">Multimodal Detection</h3>
                <p className="text-slate-400 text-[15px] max-w-sm leading-relaxed">
                  Simultaneously cross-reference video lip-sync, audio spectrograms, image noise patterns, and text semantics.
                </p>
              </div>

              {/* Animated icon constellation */}
              <div className="absolute bottom-6 right-6 md:bottom-10 md:right-10 w-52 h-52 md:w-64 md:h-64 opacity-50 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
                <svg className="absolute inset-0 w-full h-full" fill="none" viewBox="0 0 200 200">
                  {/* Connecting lines */}
                  <motion.line x1="40"  y1="40"  x2="100" y2="100" stroke="rgba(59,130,246,0.35)" strokeWidth="1.5" strokeDasharray="4 4" initial={{ pathLength: 0 }} whileInView={{ pathLength: 1 }} transition={{ duration: 1.4, delay: 0.2 }} />
                  <motion.line x1="160" y1="45"  x2="100" y2="100" stroke="rgba(59,130,246,0.35)" strokeWidth="1.5" strokeDasharray="4 4" initial={{ pathLength: 0 }} whileInView={{ pathLength: 1 }} transition={{ duration: 1.4, delay: 0.4 }} />
                  <motion.line x1="45"  y1="160" x2="100" y2="100" stroke="rgba(59,130,246,0.35)" strokeWidth="1.5" strokeDasharray="4 4" initial={{ pathLength: 0 }} whileInView={{ pathLength: 1 }} transition={{ duration: 1.4, delay: 0.6 }} />
                  <motion.line x1="155" y1="160" x2="100" y2="100" stroke="rgba(59,130,246,0.35)" strokeWidth="1.5" strokeDasharray="4 4" initial={{ pathLength: 0 }} whileInView={{ pathLength: 1 }} transition={{ duration: 1.4, delay: 0.8 }} />
                </svg>

                {/* Center node */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-14 h-14 bg-indigo-500/20 rounded-full border border-indigo-500/40 flex items-center justify-center shadow-[0_0_24px_rgba(99,102,241,0.5)]">
                  <BrainCircuit className="w-6 h-6 text-indigo-400" />
                </div>

                {/* Satellite nodes */}
                {[
                  { top: "20%", left: "20%", Icon: Video,     color: "text-blue-400"   },
                  { top: "22%", left: "80%", Icon: AudioLines, color: "text-pink-400"   },
                  { top: "78%", left: "22%", Icon: ImageIcon,  color: "text-green-400"  },
                  { top: "78%", left: "78%", Icon: FileText,   color: "text-orange-400" },
                ].map(({ top, left, Icon, color }) => (
                  <div
                    key={color}
                    className="absolute -translate-x-1/2 -translate-y-1/2 w-10 h-10 bg-black/70 rounded-full border border-white/10 flex items-center justify-center backdrop-blur-md"
                    style={{ top, left }}
                  >
                    <Icon className={`w-4 h-4 ${color}`} />
                  </div>
                ))}
              </div>
            </GlassCard>
          </motion.div>

          {/* Large Card 2 — Authenticity Score */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.5, delay: 0.1, ease: [0.4, 0, 0.2, 1] }}
            className="md:col-span-2 row-span-2 h-full"
          >
            <GlassCard
              className="w-full h-full flex flex-col items-center justify-center relative overflow-hidden group text-center p-8"
            >
              <div className="absolute inset-0 bg-gradient-to-b from-green-500/5 to-transparent pointer-events-none" />
              <div className="mb-6 relative z-10">
                <RiskBadge level="authentic" className="shadow-[0_0_20px_rgba(34,197,94,0.25)] px-4 py-1.5" />
              </div>
              <ScoreGauge score={76} size={190} className="mb-8 relative z-10" />
              <h3 className="text-[22px] font-bold text-white mb-3 relative z-10">
                Authenticity Score
              </h3>
              <p className="text-slate-400 text-[15px] max-w-[280px] relative z-10 leading-relaxed">
                Instantly understand media reliability with a unified 0–100 authenticity metric.
              </p>
            </GlassCard>
          </motion.div>

          {/* Small cards */}
          <SmallCard title="Heatmap Visualization" desc="Targeted overlays showing localized pixel manipulations." icon={Map}           color="text-orange-400" delay={0.2} />
          <SmallCard title="Community Truth Feed"  desc="Crowdsourced fact-checking enhanced by AI verification."  icon={MessageSquare}  color="text-blue-400"   delay={0.3} />
          <SmallCard title="Trust Index API"       desc="Integrate our detection engine directly into your platform." icon={Shield}      color="text-indigo-400" delay={0.4} />
          <SmallCard title="Agentic Learning"      desc="Models that adapt to evolving generation techniques automatically." icon={Activity} color="text-pink-400" delay={0.5} />
        </div>
      </div>
    </section>
  );
}
