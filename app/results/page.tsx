"use client";

import { useState } from "react";
import Link from "next/link";
import { SidebarNav } from "@/components/ui/SidebarNav";
import { ScoreGauge } from "@/components/ui/ScoreGauge";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { GlassCard } from "@/components/ui/GlassCard";
import { Button } from "@/components/ui/Button";
import { ModalityBreakdown } from "@/components/results/ModalityBreakdown";
import { Layers, Image as ImageIcon, Volume2, Share2, Lock } from "lucide-react";
import { cn } from "@/lib/utils";

export default function ResultsPage() {
  const [showHeatmap, setShowHeatmap] = useState(false);

  return (
    <div className="flex min-h-screen bg-[#020817] text-white">
      <SidebarNav />

      <main className="flex-1 p-6 lg:p-10 lg:pl-0 flex justify-center relative overflow-hidden overflow-y-auto">
        {/* Background Gradients */}
        <div className="absolute top-[-10%] left-[20%] w-[30%] h-[30%] bg-blue-500/10 blur-[120px] rounded-full pointer-events-none" />
        <div className="absolute bottom-[10%] right-[-5%] w-[40%] h-[40%] bg-indigo-500/10 blur-[120px] rounded-full pointer-events-none" />

        <div className="w-full max-w-6xl mx-auto z-10 grid grid-cols-1 lg:grid-cols-2 gap-8 items-start mt-8 pb-20">
          
          {/* Left Column: Media & Spectrogram */}
          <div className="flex flex-col gap-6">
            <GlassCard className="p-1 flex flex-col">
              {/* Toggle controls */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
                <h3 className="text-[16px] font-bold text-white flex items-center gap-2">
                  <ImageIcon className="w-4 h-4 text-blue-400" />
                  Visual Analysis
                </h3>
                <div className="flex bg-slate-900/50 rounded-lg p-1 border border-white/5">
                  <button
                    onClick={() => setShowHeatmap(false)}
                    className={cn(
                      "px-3 py-1 text-[12px] font-semibold rounded-md transition-all",
                      !showHeatmap ? "bg-white/10 text-white shadow-sm" : "text-slate-400 hover:text-white"
                    )}
                  >
                    Original
                  </button>
                  <button
                    onClick={() => setShowHeatmap(true)}
                    className={cn(
                      "flex items-center gap-1.5 px-3 py-1 text-[12px] font-semibold rounded-md transition-all",
                      showHeatmap ? "bg-blue-500/20 text-blue-400 shadow-sm" : "text-slate-400 hover:text-white"
                    )}
                  >
                    <Layers className="w-3 h-3" />
                    Heatmap
                  </button>
                </div>
              </div>

              {/* Media Preview Area */}
              <div className="relative w-full aspect-video bg-slate-900 rounded-b-2xl overflow-hidden flex items-center justify-center">
                {/* Placeholder Image */}
                <div className="absolute inset-0 bg-slate-800 flex items-center justify-center">
                  <span className="text-slate-500 font-medium">Original Media Source</span>
                </div>
                
                {/* Heatmap Overlay */}
                <div
                  className={cn(
                    "absolute inset-0 transition-opacity duration-500 pointer-events-none",
                    showHeatmap ? "opacity-100" : "opacity-0"
                  )}
                >
                  {/* Fake heatmap spots */}
                  <div className="absolute top-[20%] left-[30%] w-32 h-32 bg-red-500/40 blur-[30px] rounded-full mix-blend-screen" />
                  <div className="absolute top-[40%] right-[25%] w-40 h-40 bg-orange-500/40 blur-[40px] rounded-full mix-blend-screen" />
                  <div className="absolute bottom-[10%] left-[45%] w-24 h-24 bg-yellow-500/30 blur-[25px] rounded-full mix-blend-screen" />
                </div>
              </div>
            </GlassCard>

            <GlassCard className="p-6">
              <h3 className="text-[16px] font-bold text-white flex items-center gap-2 mb-6">
                <Volume2 className="w-4 h-4 text-indigo-400" />
                Spectrogram Forensics
              </h3>
              <div className="w-full h-32 rounded-xl bg-slate-900/50 border border-white/5 flex items-end justify-between px-2 pb-2 gap-1 overflow-hidden">
                {/* Fake static waveform bars */}
                {Array.from({ length: 40 }).map((_, i) => {
                  const height = Math.random() * 80 + 10;
                  return (
                    <div
                      key={i}
                      className="flex-1 bg-gradient-to-t from-indigo-600 to-indigo-400 rounded-t-sm opacity-80"
                      style={{ height: `${height}%` }}
                    />
                  );
                })}
              </div>
            </GlassCard>
          </div>

          {/* Right Column: Score & Details */}
          <div className="flex flex-col gap-6">
            <GlassCard className="p-8 flex flex-col items-center justify-center relative text-center">
              <div className="absolute top-6 right-6">
                <RiskBadge level="medium" />
              </div>
              
              <ScoreGauge score={68} size={200} className="mb-6" />
              
              <h2 className="text-[24px] font-heading font-bold text-white mb-2 tracking-tight">
                Authenticity Score
              </h2>
              <p className="text-slate-400 text-[14px] max-w-xs">
                Multiple highly suspicious artifacts detected in visual and text layers.
              </p>
            </GlassCard>

            <GlassCard className="p-6">
              <h3 className="text-[18px] font-bold text-white mb-4">
                AI Analysis Summary
              </h3>
              <p className="text-[14px] text-slate-300 leading-relaxed mb-6">
                Our models detected significant anomalies in the visual layer, consistent with generative AI inpainting techniques around the subject's face. The audio track remains intact with no evidence of synthetic voice cloning, but the text verification indicates a 55% probability of automated script generation.
              </p>
              
              {/* Modality Breakdown */}
              <ModalityBreakdown />
            </GlassCard>

            {/* Actions */}
            <div className="flex gap-4 w-full mt-2">
              <Link href="/profile" className="flex-1">
                <Button variant="ghost" className="w-full h-12 gap-2 text-slate-300 hover:text-white border border-white/10">
                  <Lock className="w-4 h-4" /> Keep Private
                </Button>
              </Link>
              <Link href="/community" className="flex-1">
                <Button className="w-full h-12 gap-2 bg-blue-600 hover:bg-blue-500 text-white border-0 shadow-[0_0_20px_rgba(37,99,235,0.4)]">
                  <Share2 className="w-4 h-4" /> Post to Community
                </Button>
              </Link>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}
