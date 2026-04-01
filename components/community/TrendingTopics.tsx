"use client";

import { TrendingUp, Flame, AlertCircle } from "lucide-react";
import { GlassCard } from "@/components/ui/GlassCard";

const trendingTopics = [
  { id: 1, topic: "Senator XYZ Deepfake Video", count: "12.4K views", risk: "Critical", spike: true },
  { id: 2, topic: "AI Generated Hurricane Images", count: "8.1K views", risk: "High", spike: true },
  { id: 3, pop: false, topic: "Synthetic CEO Earnings Call", count: "5.3K views", risk: "Medium", spike: false },
  { id: 4, topic: "Fake Protest Voice Notes", count: "3.2K views", risk: "High", spike: true },
  { id: 5, topic: "Automated Stock Rumors text", count: "1.5K views", risk: "Medium", spike: false },
];

export function TrendingTopics() {
  return (
    <GlassCard className="w-full p-6 sticky top-6">
      <div className="flex items-center gap-2 mb-6">
        <Flame className="w-5 h-5 text-orange-500" />
        <h2 className="text-[16px] font-bold text-white tracking-tight">
          Trending Fake Topics
        </h2>
      </div>

      <div className="flex flex-col gap-4">
        {trendingTopics.map((item, i) => (
          <div 
            key={item.id} 
            className="flex items-start gap-3 p-3 rounded-xl hover:bg-white/5 transition-colors cursor-pointer group"
          >
            <span className="text-[14px] font-bold text-slate-600 mt-0.5 group-hover:text-blue-500 transition-colors">
              0{i + 1}
            </span>
            <div className="flex flex-col flex-1 gap-1">
              <h4 className="text-[14px] font-semibold text-slate-200 leading-tight group-hover:text-white transition-colors">
                {item.topic}
              </h4>
              <div className="flex items-center gap-2 text-[12px]">
                <span className="text-slate-500">{item.count}</span>
                <span className="w-1 h-1 rounded-full bg-slate-700" />
                <span className={item.risk === "Critical" ? "text-red-400" : item.risk === "High" ? "text-orange-400" : "text-yellow-400"}>
                  {item.risk} Risk
                </span>
              </div>
            </div>
            {item.spike && (
              <div className="w-6 h-6 rounded-full bg-blue-500/10 flex items-center justify-center shrink-0">
                <TrendingUp className="w-3.5 h-3.5 text-blue-400" />
              </div>
            )}
          </div>
        ))}
      </div>
      
      <button className="w-full mt-6 py-3 rounded-xl border border-white/10 text-[13px] font-semibold text-slate-300 hover:text-white hover:bg-white/5 transition-all">
        Show More
      </button>
    </GlassCard>
  );
}
