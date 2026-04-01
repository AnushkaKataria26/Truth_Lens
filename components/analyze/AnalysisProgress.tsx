"use client";

import { motion } from "framer-motion";
import { CheckCircle2, Circle, FileVideo, Video, Mic, Type, Activity } from "lucide-react";
import { useEffect, useState } from "react";
import { GlassCard } from "@/components/ui/GlassCard";
import { cn } from "@/lib/utils";

const steps = [
  { id: 1, label: "Media Ingestion", icon: FileVideo },
  { id: 2, label: "Visual Analysis", icon: Video },
  { id: 3, label: "Audio Forensics", icon: Mic },
  { id: 4, label: "Text Verification", icon: Type },
  { id: 5, label: "Score Fusion", icon: Activity },
];

export function AnalysisProgress({ onComplete }: { onComplete: () => void }) {
  const [currentStep, setCurrentStep] = useState(1);

  // Simulate progress
  useEffect(() => {
    if (currentStep <= steps.length) {
      const timer = setTimeout(() => {
        if (currentStep === steps.length) {
          onComplete();
        } else {
          setCurrentStep((prev) => prev + 1);
        }
      }, 2000); // 2 seconds per step
      return () => clearTimeout(timer);
    }
  }, [currentStep, onComplete]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-2xl mx-auto"
    >
      <div className="text-center mb-10">
        <h2 className="text-[32px] md:text-[40px] font-heading font-bold text-white mb-3 tracking-tight">
          Analyzing Content...
        </h2>
        <p className="text-[16px] text-slate-400 max-w-md mx-auto leading-relaxed">
          Please wait while our models scan the media.
        </p>
      </div>

      <GlassCard className="p-8">
        <div className="flex flex-col gap-6 relative">
          {/* Vertical connecting line */}
          <div className="absolute left-[23px] top-[24px] bottom-[24px] w-[2px] bg-slate-800/50 -z-10" />

          {steps.map((step) => {
            const isCompleted = currentStep > step.id;
            const isActive = currentStep === step.id;
            const isPending = currentStep < step.id;

            return (
              <div key={step.id} className="relative z-10">
                <div className="flex items-center gap-4">
                  {/* Status Indicator */}
                  <div className="shrink-0">
                    {isCompleted ? (
                      <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center shadow-[0_0_15px_rgba(34,197,94,0.3)]">
                        <CheckCircle2 className="w-6 h-6 text-green-400" />
                      </div>
                    ) : isActive ? (
                      <div className="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center shadow-[0_0_20px_rgba(59,130,246,0.4)] animate-pulse border border-blue-500/50">
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                        >
                          <step.icon className="w-5 h-5 text-blue-400" />
                        </motion.div>
                      </div>
                    ) : (
                      <div className="w-12 h-12 rounded-full bg-slate-800/50 flex items-center justify-center border border-white/5">
                        <Circle className="w-5 h-5 text-slate-500" />
                      </div>
                    )}
                  </div>

                  {/* Step Info */}
                  <div className="flex-1">
                    <h3
                      className={cn(
                        "text-[16px] font-semibold transition-colors duration-300",
                        isCompleted ? "text-slate-300" : isActive ? "text-white" : "text-slate-500"
                      )}
                    >
                      {step.label}
                    </h3>
                    
                    {/* Active Loading Bar */}
                    {isActive && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        className="mt-2 h-1.5 w-full bg-slate-800/50 rounded-full overflow-hidden"
                      >
                        <motion.div
                          initial={{ width: "0%" }}
                          animate={{ width: "100%" }}
                          transition={{ duration: 2, ease: "easeInOut" }}
                          className="h-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]"
                        />
                      </motion.div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </GlassCard>
    </motion.div>
  );
}
