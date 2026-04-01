"use client";

import { motion } from "framer-motion";
import { AlertCircle } from "lucide-react";

const alerts = [
  "HIGH RISK DETECTED: Synthesized audio masquerading as corporate announcement (ID: 9X44-23)",
  "VIRAL OUTBREAK: Gen-AI protest images rapidly sharing in US region (Confidence: 98%)",
  "SYSTEM ALERT: Scraping node 4 latency > 500ms",
  "DEEPFAKE UPDATE: New video-facial-mapping signature added to verification cluster",
  "HIGH RISK DETECTED: Synthesized audio masquerading as corporate announcement (ID: 9X44-23)",
  "VIRAL OUTBREAK: Gen-AI protest images rapidly sharing in US region (Confidence: 98%)",
];

export function ViralAlertTicker() {
  return (
    <div className="w-full bg-red-500/10 border-b border-red-500/20 py-2.5 overflow-hidden flex items-center shrink-0">
      <div className="shrink-0 px-4 flex items-center gap-2 bg-black/40 z-10 shadow-[10px_0_20px_rgba(0,0,0,0.8)] border-r border-red-500/20 h-full">
        <AlertCircle className="w-4 h-4 text-red-500 animate-pulse" />
        <span className="text-[12px] font-bold text-red-400 uppercase tracking-widest bg-red-500/10 px-2 py-0.5 rounded-sm">Live Alerts</span>
      </div>
      
      <div className="flex-1 overflow-hidden flex items-center relative mask-image-edges">
        <motion.div
          initial={{ x: "0%" }}
          animate={{ x: "-50%" }}
          transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
          className="flex items-center gap-12 whitespace-nowrap pl-6"
        >
          {alerts.map((alert, i) => (
            <div key={i} className="flex items-center gap-3">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
              <span className="text-[13px] font-mono text-red-300/80">{alert}</span>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  );
}
