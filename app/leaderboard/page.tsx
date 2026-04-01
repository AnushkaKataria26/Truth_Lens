"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Crown, ShieldCheck, Flame, Medal, Search } from "lucide-react";
import { SidebarNav } from "@/components/ui/SidebarNav";
import { GlassCard } from "@/components/ui/GlassCard";
import { cn } from "@/lib/utils";

// Mock Data
const topUsers = [
  { id: 2, rank: 2, name: "Sarah Chen", handle: "schen_verify", avatar: "https://i.pravatar.cc/150?u=a042581f4e29026704e", score: 98, badge: "Fact Defender", color: "from-slate-400 to-slate-200" },
  { id: 1, rank: 1, name: "Marcus L.", handle: "marcus_truth", avatar: "https://i.pravatar.cc/150?u=a042581f4e29026704d", score: 99, badge: "Truth Sentinel", color: "from-yellow-500 to-yellow-300" },
  { id: 3, rank: 3, name: "Dr. A. Patel", handle: "apatel_forensics", avatar: "https://i.pravatar.cc/150?u=a042581f4e29026702d", score: 96, badge: "Master Analyst", color: "from-orange-600 to-orange-400" },
];

const remainingUsers = [
  { rank: 4, name: "Journalist Desk", avatar: "https://i.pravatar.cc/150?u=a04258114e29026702d", score: 95, analyses: "1,240", impact: "High", badge: "Truth Seeker" },
  { rank: 5, name: "Tech Observer", avatar: "https://i.pravatar.cc/150?u=a04258214e29026702d", score: 93, analyses: "892", impact: "High", badge: "Fact Defender" },
  { rank: 6, name: "Elena V.", avatar: "https://i.pravatar.cc/150?u=a04258114e21026702d", score: 91, analyses: "534", impact: "Medium", badge: "Investigator" },
  { rank: 7, name: "David Kim", avatar: "https://i.pravatar.cc/150?u=a04258114e29026701d", score: 89, analyses: "412", impact: "Medium", badge: "Investigator" },
  { rank: 8, name: "FactCheck UK", avatar: "https://i.pravatar.cc/150?u=a04298114e29026702d", score: 88, analyses: "1,450", impact: "High", badge: "Fact Defender" },
];

const tabs = ["Weekly", "Monthly", "All-Time"];

export default function LeaderboardPage() {
  const [activeTab, setActiveTab] = useState("Weekly");

  return (
    <div className="flex min-h-screen bg-[#020817] text-white overflow-hidden">
      <SidebarNav />

      <main className="flex-1 w-full max-w-6xl mx-auto p-4 md:p-8 lg:p-10 flex flex-col items-center relative z-10">
        {/* Background Gradients */}
        <div className="absolute top-[-10%] left-[20%] w-[30%] h-[30%] bg-blue-500/10 blur-[120px] rounded-full pointer-events-none" />
        <div className="absolute bottom-[20%] right-[-5%] w-[40%] h-[40%] bg-purple-500/10 blur-[120px] rounded-full pointer-events-none" />

        {/* Page Head & Filter Bar */}
        <div className="w-full flex flex-col md:flex-row justify-between items-start md:items-end mb-16 pt-4 gap-6">
          <div>
            <h1 className="text-[32px] md:text-[40px] font-heading font-bold tracking-tight text-white mb-6">
              Top Truth Defenders
            </h1>
            
            {/* Tabs */}
            <div className="flex flex-wrap items-center gap-2">
              {tabs.map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={cn(
                    "px-4 py-1.5 rounded-full text-[13px] font-semibold transition-all border",
                    activeTab === tab
                      ? "bg-blue-500 text-white border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.3)]"
                      : "bg-white/5 text-slate-300 border-white/10 hover:bg-white/10 hover:border-white/20"
                  )}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>
          
          <div className="relative w-full md:max-w-xs shrink-0 mt-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input 
              type="text" 
              placeholder="Search users..." 
              className="w-full h-11 bg-white/5 border border-white/10 rounded-xl pl-11 pr-4 text-[14px] text-white placeholder:text-slate-500 focus:outline-none focus:border-blue-500 transition-all"
            />
          </div>
        </div>

        {/* Podium Display */}
        <div className="w-full max-w-4xl mx-auto flex flex-col md:flex-row items-end justify-center gap-4 md:gap-6 lg:gap-8 mb-20 px-4 md:px-0">
          {topUsers.map((user, i) => {
            const isCenter = user.rank === 1;
            
            return (
              <motion.div
                key={user.id}
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: isCenter ? 0 : 0.2, ease: "easeOut" }}
                className={cn(
                  "relative w-full md:w-1/3 flex flex-col items-center",
                  isCenter ? "order-first md:order-none z-10 md:-translate-y-8" : "md:opacity-90"
                )}
              >
                <GlassCard className={cn(
                  "w-full flex flex-col items-center p-6 pt-10 text-center relative overflow-hidden group",
                  isCenter ? "border-yellow-500/30 shadow-[0_0_40px_rgba(234,179,8,0.15)]" : "border-white/5 shadow-lg"
                )}>
                  {/* Backdrop Glow */}
                  {isCenter && (
                    <div className="absolute inset-0 bg-gradient-to-b from-yellow-500/5 to-transparent pointer-events-none" />
                  )}

                  {/* Crown Icon / Rank Badge */}
                  <div className="absolute -top-4 w-full flex justify-center">
                    <div className={cn(
                      "w-10 h-10 rounded-full flex items-center justify-center border-4 border-[#020817] shadow-xl",
                      isCenter ? "bg-gradient-to-br from-yellow-500 to-orange-500" : 
                      user.rank === 2 ? "bg-gradient-to-br from-slate-400 to-slate-300" :
                      "bg-gradient-to-br from-orange-700 to-orange-500"
                    )}>
                      {isCenter ? (
                        <Crown className="w-5 h-5 text-white" />
                      ) : (
                        <span className="text-[14px] font-bold text-white">#{user.rank}</span>
                      )}
                    </div>
                  </div>

                  {/* Avatar */}
                  <div className={cn(
                    "w-20 h-20 rounded-full border-2 overflow-hidden mb-4 shrink-0 transition-transform duration-500 group-hover:scale-105",
                    isCenter ? "w-24 h-24 border-yellow-500/50" : "border-white/10"
                  )}>
                    <img src={user.avatar} alt={user.name} className="w-full h-full object-cover" />
                  </div>

                  {/* User Data */}
                  <h3 className="text-[18px] font-bold text-white mb-1 leading-tight">{user.name}</h3>
                  <p className="text-[12px] text-slate-400 mb-4">@{user.handle}</p>

                  <div className="w-full flex items-center justify-between mb-4 bg-black/40 px-4 py-2 rounded-xl border border-white/5">
                    <div className="flex flex-col items-start pr-4 border-r border-white/5">
                      <span className="text-[10px] text-slate-500 uppercase font-semibold tracking-wider">Score</span>
                      <span className="text-[18px] font-bold text-white">{user.score}</span>
                    </div>
                    <div className="flex flex-col items-end pl-4">
                      <ShieldCheck className={cn("w-5 h-5 mb-1", isCenter ? "text-yellow-400" : "text-blue-400")} />
                    </div>
                  </div>

                  {/* Badge Label */}
                  <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-white/5 border border-white/10 rounded-full">
                    <Medal className={cn("w-3.5 h-3.5", isCenter ? "text-yellow-400" : "text-slate-400")} />
                    <span className="text-[12px] font-semibold text-slate-300">{user.badge}</span>
                  </div>
                </GlassCard>
              </motion.div>
            );
          })}
        </div>

        {/* List Table for Rank 4+ */}
        <div className="w-full bg-[#0B1221]/80 backdrop-blur-md rounded-2xl border border-white/5 overflow-hidden">
          <div className="w-full overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[700px]">
              <thead>
                <tr className="border-b border-white/[0.06] bg-black/20 text-slate-400 text-[12px] uppercase tracking-wider font-semibold">
                  <th className="py-4 px-6 rounded-tl-xl w-24 text-center">Rank</th>
                  <th className="py-4 px-6 w-1/3">User</th>
                  <th className="py-4 px-6">Trust Index</th>
                  <th className="py-4 px-6">Analyses Run</th>
                  <th className="py-4 px-6">Debunk Impact</th>
                  <th className="py-4 px-6 rounded-tr-xl">Badge</th>
                </tr>
              </thead>
              <tbody>
                {remainingUsers.map((user) => (
                  <tr 
                    key={user.rank} 
                    className="border-b border-white/[0.06] last:border-0 hover:bg-white/[0.02] hover:shadow-[inset_0_0_20px_rgba(59,130,246,0.05)] transition-all cursor-pointer group"
                  >
                    <td className="py-4 px-6 text-center">
                      <span className="text-[14px] font-bold text-slate-500 group-hover:text-blue-400 transition-colors">
                        #{user.rank}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-3">
                        <img src={user.avatar} alt="User" className="w-9 h-9 rounded-full object-cover border border-white/10" />
                        <span className="text-[14px] font-bold text-white group-hover:text-blue-400 transition-colors">
                          {user.name}
                        </span>
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400">
                        <span className="text-[12px] font-bold">{user.score}%</span>
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <span className="text-[13px] font-medium text-slate-300">{user.analyses}</span>
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-1.5">
                        <Flame className={cn("w-3.5 h-3.5", user.impact === "High" ? "text-orange-500" : "text-yellow-500")} />
                        <span className={cn("text-[13px] font-medium", user.impact === "High" ? "text-orange-400" : "text-yellow-400")}>
                          {user.impact}
                        </span>
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <span className="text-[13px] font-semibold text-slate-400 px-3 py-1 bg-white/5 rounded-full inline-block">
                        {user.badge}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </main>
    </div>
  );
}
