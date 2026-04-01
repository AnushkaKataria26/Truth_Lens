"use client";

import { motion } from "framer-motion";
import { Video, Mic, Type, Shuffle } from "lucide-react";
import { cn } from "@/lib/utils";

const modalities = [
  { id: "visual", label: "Visual", icon: Video, score: 92, color: "bg-green-500", glow: "shadow-[0_0_10px_rgba(34,197,94,0.4)]" },
  { id: "audio", label: "Audio", icon: Mic, score: 85, color: "bg-green-500", glow: "shadow-[0_0_10px_rgba(34,197,94,0.4)]" },
  { id: "text", label: "Text", icon: Type, score: 45, color: "bg-orange-500", glow: "shadow-[0_0_10px_rgba(249,115,22,0.4)]" },
  { id: "cross", label: "Cross-Modal", icon: Shuffle, score: 96, color: "bg-green-500", glow: "shadow-[0_0_10px_rgba(34,197,94,0.4)]" },
];

export function ModalityBreakdown() {
  return (
    <div className="flex flex-col gap-4 w-full">
      {modalities.map((item, index) => (
        <div key={item.id} className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <item.icon className="w-4 h-4 text-slate-400" />
              <span className="text-[14px] font-semibold text-slate-300">
                {item.label}
              </span>
            </div>
            <span className="text-[14px] font-bold text-white">
              {item.score}%
            </span>
          </div>

          {/* Progress Bar Track */}
          <div className="w-full h-2 rounded-full bg-slate-800/50 border border-white/5 overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${item.score}%` }}
              transition={{ duration: 1, delay: 0.2 + index * 0.1, ease: "easeOut" }}
              className={cn("h-full rounded-full", item.color, item.glow)}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
