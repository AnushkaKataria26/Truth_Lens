"use client";

import { motion } from "framer-motion";
import { GlassCard } from "@/components/ui/GlassCard";
import { ShieldAlert, Users, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";

const riskGradients: Record<string, string> = {
  high:      "from-red-500/20 to-red-600/10 border-red-500/25",
  medium:    "from-orange-500/20 to-orange-600/10 border-orange-500/25",
  authentic: "from-green-500/20 to-green-600/10 border-green-500/25",
};

const riskDotColor: Record<string, string> = {
  high:      "bg-red-400",
  medium:    "bg-orange-400",
  authentic: "bg-green-400",
};

const figures = [
  { name: "Global Politician", role: "Politician",  fakes: "1,204", posts: "8.4K",  risk: "high",      avatar: "P", initials: "GP" },
  { name: "Tech CEO",          role: "Executive",   fakes: "845",   posts: "3.2K",  risk: "medium",    avatar: "C", initials: "TC" },
  { name: "Pop Icon",          role: "Artist",      fakes: "3,120", posts: "12.5K", risk: "high",      avatar: "A", initials: "PI" },
  { name: "News Anchor",       role: "Journalist",  fakes: "142",   posts: "4.1K",  risk: "authentic", avatar: "J", initials: "NA" },
  { name: "Financial Analyst", role: "Analyst",     fakes: "650",   posts: "2.1K",  risk: "medium",    avatar: "F", initials: "FA" },
  { name: "Senator Blake",     role: "Politician",  fakes: "1,100", posts: "6.4K",  risk: "high",      avatar: "B", initials: "SB" },
];

export function TrendingFigures() {
  return (
    <section className="py-28 relative w-full overflow-hidden">
      {/* Section header */}
      <div className="container mx-auto px-6 max-w-7xl mb-10">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ duration: 0.55, ease: "easeOut" }}
          className="flex items-center gap-4"
        >
          <div className="w-11 h-11 rounded-full bg-red-500/10 flex items-center justify-center border border-red-500/20 shadow-[0_0_16px_rgba(239,68,68,0.2)] shrink-0">
            <TrendingUp className="w-5 h-5 text-red-400" />
          </div>
          <div>
            <h2 className="text-[28px] md:text-[36px] font-heading font-bold text-white tracking-tight">
              Trending Public Figures
            </h2>
            <p className="text-slate-400 text-[14px] mt-0.5">Most scrutinized subjects this week</p>
          </div>
        </motion.div>
      </div>

      {/* Horizontal scroll strip — no scrollbar */}
      <div className="flex w-full overflow-x-auto pb-6 pt-2 no-scrollbar">
        <div className="flex gap-5 px-6 w-max md:pl-[max(1.5rem,calc((100vw-80rem)/2+1.5rem))]">
          {figures.map((fig, i) => (
            <motion.div
              key={i}
              className="shrink-0"
              initial={{ opacity: 0, x: 40 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ duration: 0.5, delay: i * 0.08, ease: [0.4, 0, 0.2, 1] }}
            >
              <GlassCard
                className={cn(
                  "w-[300px] flex flex-col p-6 group bg-gradient-to-br border",
                  riskGradients[fig.risk]
                )}
              >
                {/* Avatar row */}
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 rounded-full bg-white/6 border border-white/10 flex items-center justify-center text-[16px] font-heading font-bold text-white tracking-wide shrink-0">
                    {fig.initials}
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-white font-bold text-[15px] truncate">{fig.name}</h3>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <div className={`w-1.5 h-1.5 rounded-full ${riskDotColor[fig.risk]}`} />
                      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-[0.12em]">
                        {fig.role}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Stats */}
                <div className="flex items-center justify-between pt-5 border-t border-white/[0.07] mt-auto">
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-1.5 text-[10px] text-slate-400 uppercase tracking-[0.12em] font-semibold">
                      <ShieldAlert className="w-3 h-3 text-red-400" />
                      Fakes Detected
                    </div>
                    <span className="text-white font-bold text-[20px]">{fig.fakes}</span>
                  </div>
                  <div className="w-px h-10 bg-white/8 mx-3" />
                  <div className="flex flex-col gap-1 items-end">
                    <div className="flex items-center gap-1.5 text-[10px] text-slate-400 uppercase tracking-[0.12em] font-semibold flex-row-reverse">
                      <Users className="w-3 h-3 text-blue-400" />
                      Community
                    </div>
                    <span className="text-white font-bold text-[20px]">{fig.posts}</span>
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
