"use client";

import { motion } from "framer-motion";
import { GlassCard } from "@/components/ui/GlassCard";
import { UploadCloud, Cpu, ShieldCheck, Share2 } from "lucide-react";

const steps = [
  {
    num: "01",
    title: "Upload Media",
    description: "Drop a video, image, or audio clip directly into TruthLens. We support all major formats.",
    icon: UploadCloud,
  },
  {
    num: "02",
    title: "AI Multimodal Analysis",
    description: "Our agentic models cross-reference visual artifacts, audio waveforms, and metadata inconsistencies.",
    icon: Cpu,
  },
  {
    num: "03",
    title: "Authenticity Score Generated",
    description: "Get a detailed breakdown of manipulations, spoofing attempts, and an overall 0–100 trust score.",
    icon: ShieldCheck,
  },
  {
    num: "04",
    title: "Review & Share",
    description: "Export the analysis report or share the verified Truth Tag with your community.",
    icon: Share2,
  },
];

export function HowItWorksSection() {
  return (
    <section className="py-28 relative z-10">
      <div className="container mx-auto px-6 max-w-7xl">
        {/* Section heading */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="text-center mb-16"
        >
          <h2 className="text-[36px] md:text-[52px] font-heading font-bold text-white tracking-tight mb-4">
            How TruthLens Works
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto text-[18px] leading-relaxed">
            A seamless four-step process to verify any piece of media in under 10 seconds.
          </p>
        </motion.div>

        {/* Step cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, i) => (
            <motion.div
              key={step.num}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.55, delay: i * 0.1, ease: "easeOut" }}
              className="h-full"
            >
              <GlassCard
                className="h-full relative overflow-hidden group flex flex-col p-8"
                style={{ transition: "transform 0.3s ease, box-shadow 0.3s ease" }}
              >
                {/* Ghost background icon */}
                <div className="absolute top-6 right-6 text-white/[0.04] group-hover:text-blue-500/10 transition-colors duration-300 group-hover:-translate-y-1 group-hover:rotate-6 transform transition-transform duration-300">
                  <step.icon className="w-24 h-24" />
                </div>

                {/* Numbered circle */}
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center font-bold text-white text-[15px] mb-8 shadow-[0_0_20px_rgba(59,130,246,0.35)] group-hover:scale-105 group-hover:shadow-[0_0_32px_rgba(59,130,246,0.55)] transition-all duration-300 shrink-0">
                  {step.num}
                </div>

                <h3 className="text-[18px] font-bold text-white mb-3 tracking-tight relative z-10">
                  {step.title}
                </h3>
                <p className="text-slate-400 text-[15px] leading-relaxed relative z-10">
                  {step.description}
                </p>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
