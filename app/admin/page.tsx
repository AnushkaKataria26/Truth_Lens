"use client";

import { useState, useEffect } from "react";
import { 
  ShieldAlert, Activity, Users, AlertTriangle, 
  Search, ShieldX, PlayCircle, Lock
} from "lucide-react";
import { SidebarNav } from "@/components/ui/SidebarNav";
import { GlassCard } from "@/components/ui/GlassCard";
import { ViralAlertTicker } from "@/components/admin/ViralAlertTicker";
import { RiskChart } from "@/components/admin/RiskChart";
import { cn } from "@/lib/utils";

const mockLogs = [
  "[17:42:01] INFO  [Node 4] Audio spectrogram analysis complete (ID: 8092X)",
  "[17:42:04] WARN  [API Gateway] High latency detected on validation endpoint",
  "[17:42:12] ERROR [Deepfake Model] Confidence threshold failure (Obj: 22A)",
  "[17:42:15] INFO  [Modality Sync] Cross-modal score calculated: 12%",
  "[17:42:22] INFO  [Community] User @marcus_truth reported media item 55B",
  "[17:42:30] ALERT [Heuristics] Potential synthetic watermark pattern recognized",
  "[17:42:31] INFO  [Node 2] Image extraction routine finished (90ms)",
  "[17:42:40] INFO  [Database] Syncing flagged items to distributed ledger",
  "[17:42:44] WARN  [Node 3] Memory usage > 85%, scaling workers...",
];

export default function AdminDashboard() {
  const [isAdmin] = useState(true); // Mock state
  const [logs, setLogs] = useState<string[]>(mockLogs);

  // Auto-generate logs simulation
  useEffect(() => {
    if (!isAdmin) return;
    const interval = setInterval(() => {
      setLogs(prev => {
        const newLogs = [...prev, `[17:${new Date().getMinutes()}:${Math.floor(Math.random()*60)}] INFO  [Worker ${Math.floor(Math.random()*5)}] Processing new batch...`];
        return newLogs.slice(-15);
      });
    }, 4000);
    return () => clearInterval(interval);
  }, [isAdmin]);

  if (!isAdmin) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-[#020817] text-white">
        <GlassCard className="p-10 flex flex-col items-center justify-center max-w-sm text-center border-red-500/20 shadow-[0_0_50px_rgba(239,68,68,0.1)]">
          <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center mb-6">
            <Lock className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-[20px] font-bold text-white mb-2">Admin Access Required</h2>
          <p className="text-slate-400 text-[14px]">You do not have the necessary permissions to view this dashboard.</p>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-[#020817] text-white overflow-hidden">
      <SidebarNav />

      <main className="flex-1 w-full flex flex-col relative overflow-hidden">
        {/* Viral Content Ticker */}
        <ViralAlertTicker />

        <div className="flex-1 overflow-y-auto p-4 md:p-8 lg:p-10">
          <div className="w-full max-w-7xl mx-auto flex flex-col relative z-10">
            {/* Background Gradients */}
            <div className="absolute top-0 right-[10%] w-[30%] h-[30%] bg-red-500/10 blur-[130px] rounded-full pointer-events-none" />

            <div className="flex items-center justify-between mb-8">
              <h1 className="text-[28px] md:text-[36px] font-heading font-bold tracking-tight text-white flex items-center gap-3">
                <ShieldX className="w-8 h-8 text-red-500" />
                Command Center
              </h1>
              
              <div className="px-4 py-2 bg-slate-900 border border-white/10 rounded-xl flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-[12px] font-mono text-slate-300">SYSTEM: ONLINE (v2.4.1)</span>
              </div>
            </div>

            {/* Metrics Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <GlassCard className="p-5 flex flex-col group hover:border-blue-500/50 transition-colors">
                <div className="flex justify-between items-start mb-4">
                  <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                  <span className="text-[12px] font-semibold text-green-400 bg-green-500/10 px-2 py-0.5 rounded-full">+12%</span>
                </div>
                <h3 className="text-[28px] font-heading font-bold text-white leading-none mb-1">2,419</h3>
                <span className="text-[13px] text-slate-400 font-medium tracking-wide">Total Flagged Today</span>
              </GlassCard>

              <GlassCard className="p-5 flex flex-col group hover:border-red-500/50 transition-colors">
                <div className="flex justify-between items-start mb-4">
                  <div className="p-2 rounded-lg bg-red-500/10 text-red-400">
                    <ShieldAlert className="w-5 h-5" />
                  </div>
                  <span className="text-[12px] font-semibold text-red-400 bg-red-500/10 px-2 py-0.5 rounded-full">+4%</span>
                </div>
                <h3 className="text-[28px] font-heading font-bold text-white leading-none mb-1">842</h3>
                <span className="text-[13px] text-slate-400 font-medium tracking-wide">High Risk Media</span>
              </GlassCard>

              <GlassCard className="p-5 flex flex-col group hover:border-purple-500/50 transition-colors">
                <div className="flex justify-between items-start mb-4">
                  <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
                    <Users className="w-5 h-5" />
                  </div>
                  <span className="text-[12px] font-semibold text-green-400 bg-green-500/10 px-2 py-0.5 rounded-full">+21%</span>
                </div>
                <h3 className="text-[28px] font-heading font-bold text-white leading-none mb-1">14.2k</h3>
                <span className="text-[13px] text-slate-400 font-medium tracking-wide">Active Users</span>
              </GlassCard>

              <GlassCard className="p-5 flex flex-col group hover:border-green-500/50 transition-colors">
                <div className="flex justify-between items-start mb-4">
                  <div className="p-2 rounded-lg bg-green-500/10 text-green-400">
                    <Activity className="w-5 h-5" />
                  </div>
                  <span className="text-[12px] font-semibold text-slate-400 bg-white/5 px-2 py-0.5 rounded-full">Stable</span>
                </div>
                <h3 className="text-[28px] font-heading font-bold text-white leading-none mb-1">98.4%</h3>
                <span className="text-[13px] text-slate-400 font-medium tracking-wide">System Health</span>
              </GlassCard>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 pb-10">
              
              {/* Flagged Media Log Table */}
              <GlassCard className="lg:col-span-2 p-0 overflow-hidden flex flex-col h-[500px]">
                <div className="p-5 border-b border-white/5 flex items-center justify-between shrink-0">
                  <h3 className="text-[16px] font-bold text-white">Flagged Media Log</h3>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
                    <input 
                      type="text" 
                      placeholder="Search ID or Reporter" 
                      className="h-8 bg-black/40 border border-white/10 rounded-md pl-9 pr-3 text-[12px] text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>
                
                <div className="flex-1 overflow-auto">
                  <table className="w-full text-left border-collapse">
                    <thead className="sticky top-0 bg-[#0B1221] backdrop-blur-md z-10 border-b border-white/5">
                      <tr className="text-slate-400 text-[11px] uppercase tracking-wider font-semibold">
                        <th className="py-3 px-5 font-medium">Media</th>
                        <th className="py-3 px-5 font-medium">Type</th>
                        <th className="py-3 px-5 font-medium">Risk Level</th>
                        <th className="py-3 px-5 font-medium">Reported By</th>
                        <th className="py-3 px-5 font-medium">Timestamp</th>
                        <th className="py-3 px-5 font-medium text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[1, 2, 3, 4, 5, 6].map((i) => (
                        <tr key={i} className="border-b border-white/[0.03] last:border-0 hover:bg-white/[0.02] transition-colors group">
                          <td className="py-3 px-5">
                            <div className="w-12 h-8 bg-slate-800 rounded overflow-hidden relative group-hover:ring-1 ring-blue-500/50 cursor-pointer">
                              <img src={`https://images.unsplash.com/photo-${1550000000000 + i}?ixlib=rb-4.0.3&auto=format&fit=crop&w=100&q=80`} className="w-full h-full object-cover opacity-80" alt="" />
                              <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                <PlayCircle className="w-4 h-4 text-white" />
                              </div>
                            </div>
                          </td>
                          <td className="py-3 px-5 text-[13px] font-medium text-slate-300">
                            {i % 2 === 0 ? "Video" : "Audio"}
                          </td>
                          <td className="py-3 px-5">
                            <span className={cn(
                              "text-[11px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide",
                              i % 3 === 0 ? "bg-red-500/10 text-red-400 border border-red-500/20" : "bg-orange-500/10 text-orange-400 border border-orange-500/20"
                            )}>
                              {i % 3 === 0 ? "High" : "Medium"}
                            </span>
                          </td>
                          <td className="py-3 px-5 text-[13px] text-slate-400">@user_{i}2x</td>
                          <td className="py-3 px-5 text-[12px] text-slate-500">10 mins ago</td>
                          <td className="py-3 px-5">
                            <div className="flex justify-end gap-2">
                              <button className="text-[11px] font-semibold text-blue-400 hover:text-blue-300 transition-colors uppercase tracking-wider px-2 py-1 bg-blue-500/10 rounded">Review</button>
                              <button className="text-[11px] font-semibold text-red-400 hover:text-red-300 transition-colors uppercase tracking-wider px-2 py-1 bg-red-500/10 rounded">Remove</button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </GlassCard>

              {/* Charts & Logs column */}
              <div className="flex flex-col gap-6 h-[530px]">
                
                {/* Risk Distribution Chart */}
                <GlassCard className="p-5 flex flex-col h-[270px] shrink-0">
                  <h3 className="text-[14px] font-bold text-white mb-2 shrink-0">Risk Distribution</h3>
                  <div className="flex-1 min-h-0 relative">
                    <RiskChart />
                  </div>
                  {/* Legend */}
                  <div className="flex justify-center gap-4 mt-2 shrink-0">
                    <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-indigo-400" /><span className="text-[11px] text-slate-400">High</span></div>
                    <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-orange-400" /><span className="text-[11px] text-slate-400">Mod</span></div>
                    <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-green-400" /><span className="text-[11px] text-slate-400">Auth</span></div>
                  </div>
                </GlassCard>

                {/* System Logs */}
                <GlassCard className="p-0 flex-1 flex flex-col overflow-hidden">
                  <div className="p-3 border-b border-white/5 bg-black/40 shrink-0">
                    <h3 className="text-[13px] font-bold text-white flex items-center gap-2">
                      <Activity className="w-4 h-4 text-green-400 animate-pulse" />
                      Live System Logs
                    </h3>
                  </div>
                  <div className="bg-[#050B14] flex-1 p-4 overflow-y-auto font-mono text-[11px] leading-relaxed relative scrollbar-hide">
                    <div className="flex flex-col gap-1.5 justify-end min-h-full">
                      {logs.map((log, index) => {
                        const isError = log.includes("ERROR");
                        const isWarn = log.includes("WARN");
                        const isAlert = log.includes("ALERT");
                        return (
                          <div 
                            key={index} 
                            className={cn(
                              "transition-opacity duration-300 opacity-90 hover:opacity-100",
                              isError ? "text-red-400" : isWarn ? "text-yellow-400" : isAlert ? "text-orange-400" : "text-slate-400"
                            )}
                          >
                            {log}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </GlassCard>

              </div>
            </div>

          </div>
        </div>
      </main>
    </div>
  );
}
