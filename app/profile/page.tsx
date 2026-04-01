"use client";

import { useState } from "react";
import { 
  Award, ShieldCheck, Map, ScanEye, Bookmark, FileBadge, 
  Download, Edit3, Settings, Share2, Grid, Layers 
} from "lucide-react";
import { SidebarNav } from "@/components/ui/SidebarNav";
import { GlassCard } from "@/components/ui/GlassCard";
import { TruthFeedCard } from "@/components/community/TruthFeedCard";
import { RiskLevel } from "@/types";
import { cn } from "@/lib/utils";

// Mock Data
const userProfile = {
  name: "Marcus L.",
  handle: "marcus_truth",
  avatar: "https://i.pravatar.cc/150?u=a042581f4e29026704d",
  bio: "Digital forensics enthusiast and fact-checker. Focused on debunking political and financial deepfakes in real-time.",
  role: "Truth Sentinel",
  trustIndex: 98,
  stats: [
    { label: "Analyses Performed", value: "342", icon: ScanEye, color: "text-blue-400" },
    { label: "Public Posts", value: "128", icon: Layers, color: "text-purple-400" },
    { label: "Saved Posts", value: "56", icon: Bookmark, color: "text-yellow-400" },
    { label: "Trust Index Score", value: "98%", icon: ShieldCheck, color: "text-green-400" },
  ],
  achievements: [
    { label: "Truth Seeker", icon: Map },
    { label: "Fact Defender", icon: ShieldCheck },
    { label: "Community Educator", icon: Share2 },
    { label: "Early Beta Tester", icon: Award },
    { label: "100+ Debunks", icon: FileBadge },
  ],
  analyses: [
    { id: "a1", title: "Suspicious CEO Voicemail", date: "2 days ago", score: 12, label: "Synthetic" },
    { id: "a2", title: "Protest Video Verification", date: "1 week ago", score: 95, label: "Authentic" },
    { id: "a3", title: "Fake Stock Announcement", date: "2 weeks ago", score: 4, label: "Deceptive" },
    { id: "a4", title: "Political Rally Image 04", date: "1 month ago", score: 45, label: "Manipulated" },
  ],
  publicPosts: [
    {
      id: "post1",
      user: {
        name: "Marcus L.",
        avatar: "https://i.pravatar.cc/150?u=a042581f4e29026704d",
        trustIndex: 98,
        handle: "marcus_truth",
        timeAgo: "2h",
      },
      content: {
        title: "Found this circulating on X regarding the new zoning laws. Very clear visual artifacts on the speaker's face.",
        thumbnail: "https://images.unsplash.com/photo-1557804506-669a67965ba0?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80",
        riskLevel: "high" as RiskLevel,
        authenticityScore: 12,
        modalities: ["video", "audio"],
        upvotes: 342,
        comments: 56,
      }
    }
  ]
};

export default function ProfilePage() {
  const [activeTab, setActiveTab] = useState<"analyses" | "posts">("analyses");

  return (
    <div className="flex min-h-screen bg-[#020817] text-white">
      <SidebarNav />

      <main className="flex-1 w-full max-w-6xl mx-auto p-4 md:p-8 lg:p-10 flex flex-col items-center relative z-10">
        
        {/* Background Gradients */}
        <div className="absolute top-0 right-[20%] w-[40%] h-[30%] bg-blue-500/10 blur-[130px] rounded-full pointer-events-none" />

        {/* Hero Banner Area */}
        <div className="w-full relative rounded-3xl overflow-hidden mb-20 md:mb-24 mt-4 border border-white/5 shadow-2xl">
          {/* Cover Glass Gradient */}
          <div className="h-48 md:h-64 w-full bg-gradient-to-r from-blue-600/20 via-indigo-500/20 to-purple-600/20 relative overflow-hidden backdrop-blur-3xl">
            <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10 mix-blend-overlay" />
            <div className="absolute inset-0 bg-gradient-to-b from-transparent to-[#020817]/90" />
            
            {/* Header Actions */}
            <div className="absolute top-6 right-6 flex items-center gap-3">
              <button className="p-2.5 rounded-full bg-white/10 hover:bg-white/20 backdrop-blur-md transition-colors text-white">
                <Share2 className="w-4 h-4" />
              </button>
              <button className="p-2.5 rounded-full bg-white/10 hover:bg-white/20 backdrop-blur-md transition-colors text-white">
                <Settings className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Avatar & Info */}
          <div className="px-6 md:px-10 pb-10 relative">
            <div className="flex flex-col md:flex-row gap-6 md:items-end -mt-16 md:-mt-20">
              
              <div className="relative shrink-0">
                <div className="w-32 h-32 md:w-40 md:h-40 rounded-full border-4 border-[#020817] bg-slate-800 overflow-hidden shadow-2xl relative z-10">
                  <img src={userProfile.avatar} alt={userProfile.name} className="w-full h-full object-cover" />
                </div>
                {/* Online indicator */}
                <div className="absolute bottom-4 right-4 w-5 h-5 rounded-full bg-green-500 border-4 border-[#020817] z-20" />
              </div>

              <div className="flex-1 flex flex-col md:flex-row justify-between items-start md:items-end gap-6 mb-2">
                <div className="flex flex-col">
                  <div className="flex items-center gap-3 mb-1">
                    <h1 className="text-[28px] md:text-[36px] font-heading font-bold tracking-tight text-white leading-none">
                      {userProfile.name}
                    </h1>
                    <div className="px-2.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
                      <span className="text-[12px] font-bold text-blue-400 uppercase tracking-widest">{userProfile.role}</span>
                    </div>
                  </div>
                  <p className="text-[14px] md:text-[16px] text-slate-400 mt-1">@{userProfile.handle}</p>
                </div>

                <div className="shrink-0 flex items-center gap-3">
                  <button className="px-6 py-2.5 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 text-[14px] font-semibold transition-colors flex items-center gap-2">
                    <Edit3 className="w-4 h-4" /> Edit Profile
                  </button>
                </div>
              </div>
            </div>

            <p className="text-[15px] text-slate-300 max-w-2xl mt-6 leading-relaxed">
              {userProfile.bio}
            </p>
          </div>
        </div>

        {/* Stats Row */}
        <div className="w-full grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          {userProfile.stats.map((stat, i) => (
            <GlassCard key={i} className="p-5 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="text-[13px] text-slate-400 font-medium">{stat.label}</span>
                <div className={cn("p-2 rounded-lg bg-white/5", stat.color)}>
                  <stat.icon className="w-4 h-4" />
                </div>
              </div>
              <span className="text-[28px] font-heading font-bold text-white tracking-tight">
                {stat.value}
              </span>
            </GlassCard>
          ))}
        </div>

        {/* Achievement Badges Row */}
        <div className="w-full mb-12">
          <h3 className="text-[16px] font-bold text-white mb-4 px-2">Earned Achievements</h3>
          <div className="flex gap-3 overflow-x-auto pb-4 scrollbar-hide px-2">
            {userProfile.achievements.map((badge, i) => (
              <div 
                key={i} 
                className="flex items-center gap-2 px-4 py-2.5 shrink-0 rounded-full bg-[#0B1221]/80 backdrop-blur-md border border-white/10 hover:border-blue-500/30 hover:bg-white/5 transition-all text-slate-200 cursor-default shadow-sm"
              >
                <badge.icon className="w-4 h-4 text-blue-400" />
                <span className="text-[13px] font-semibold">{badge.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="w-full grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-8 pb-20">
          {/* Main Feed Column */}
          <div className="flex flex-col gap-6">
            
            {/* Tabs */}
            <div className="flex items-center gap-8 border-b border-white/[0.06] px-2 mb-2">
              <button 
                onClick={() => setActiveTab("analyses")}
                className={cn(
                  "pb-3 text-[15px] font-bold border-b-2 transition-colors flex items-center gap-2 relative top-[1px]",
                  activeTab === "analyses" ? "text-blue-400 border-blue-400" : "text-slate-400 border-transparent hover:text-slate-200"
                )}
              >
                <Grid className="w-4 h-4" /> My Analyses
              </button>
              <button 
                onClick={() => setActiveTab("posts")}
                className={cn(
                  "pb-3 text-[15px] font-bold border-b-2 transition-colors flex items-center gap-2 relative top-[1px]",
                  activeTab === "posts" ? "text-blue-400 border-blue-400" : "text-slate-400 border-transparent hover:text-slate-200"
                )}
              >
                <Layers className="w-4 h-4" /> Public Posts
              </button>
            </div>

            {/* Content Based on Tab */}
            {activeTab === "analyses" ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {userProfile.analyses.map((item) => (
                  <GlassCard key={item.id} className="p-5 hover:bg-white/5 transition-colors cursor-pointer group">
                    <div className="flex justify-between items-start mb-4">
                      <div 
                        className={cn(
                          "px-2.5 py-1 rounded-[6px] text-[11px] font-bold uppercase tracking-wider",
                          item.score < 40 ? "bg-red-500/10 text-red-400" : item.score > 80 ? "bg-green-500/10 text-green-400" : "bg-orange-500/10 text-orange-400"
                        )}
                      >
                        {item.label}
                      </div>
                      <span className="text-[12px] text-slate-500">{item.date}</span>
                    </div>
                    <h4 className="text-[16px] font-semibold text-white mb-2 group-hover:text-blue-400 transition-colors">
                      {item.title}
                    </h4>
                    <div className="flex items-center gap-1.5 mt-4">
                      <span className="text-[13px] text-slate-400">Auth Score:</span>
                      <span className={cn(
                        "text-[14px] font-bold",
                        item.score < 40 ? "text-red-400" : item.score > 80 ? "text-green-400" : "text-orange-400"
                      )}>{item.score}%</span>
                    </div>
                  </GlassCard>
                ))}
              </div>
            ) : (
              <div className="flex flex-col gap-6">
                {userProfile.publicPosts.map((post) => (
                  <TruthFeedCard key={post.id} id={post.id} content={post.content} user={post.user} />
                ))}
              </div>
            )}
          </div>

          {/* Right Sidebar: Authenticity Certificate */}
          {userProfile.trustIndex > 90 && (
            <div className="w-full flex flex-col gap-6">
              <GlassCard className="p-6 relative overflow-hidden group border-white/10 shadow-[0_0_30px_rgba(59,130,246,0.05)]">
                {/* Background glow lines */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/20 blur-[50px] rounded-full pointer-events-none" />
                
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2.5 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-400 shrink-0">
                    <Award className="w-5 h-5" />
                  </div>
                  <h3 className="text-[16px] font-bold text-white leading-tight">Authenticity Certificate</h3>
                </div>

                <div className="w-full aspect-[4/3] rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 border border-white/5 flex flex-col items-center justify-center p-6 text-center shadow-inner relative overflow-hidden mb-6">
                  {/* Subtle watermarks */}
                  <ShieldCheck className="absolute -right-8 -bottom-8 w-40 h-40 text-white/[0.02]" />
                  
                  <ShieldCheck className="w-12 h-12 text-blue-400 mb-3" />
                  <h4 className="text-[18px] font-heading font-bold text-slate-200">Verified Analyst</h4>
                  <p className="text-[12px] text-slate-500 mt-1 uppercase tracking-wider">TruthLens Trust Network</p>
                  <div className="w-full border-t border-white/[0.05] my-4" />
                  <span className="text-[11px] text-slate-500 font-mono">ID: TL-994-0AX</span>
                </div>

                <button className="w-full py-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-[13px] font-semibold text-white transition-all flex items-center justify-center gap-2">
                  <Download className="w-4 h-4 text-blue-400" />
                  Download Certificate
                </button>
              </GlassCard>
            </div>
          )}
        </div>

      </main>
    </div>
  );
}
