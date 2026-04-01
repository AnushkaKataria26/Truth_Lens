"use client";

import { useState } from "react";
import { Search, ChevronDown, Filter } from "lucide-react";
import { SidebarNav } from "@/components/ui/SidebarNav";
import { TruthFeedCard } from "@/components/community/TruthFeedCard";
import { TrendingTopics } from "@/components/community/TrendingTopics";
import { cn } from "@/lib/utils";
import { RiskLevel } from "@/types";

const mockFeed = [
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
  },
  {
    id: "post2",
    user: {
      name: "Sarah Chen",
      avatar: "https://i.pravatar.cc/150?u=a042581f4e29026704e",
      trustIndex: 92,
      handle: "schen_verify",
      timeAgo: "5h",
    },
    content: {
      title: "Audio leak claiming to be CEO of TechCorp—ran it through TruthLens and 100% synthetic generation detected.",
      thumbnail: "https://images.unsplash.com/photo-1620021609384-0610f4d3fcbb?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80",
      riskLevel: "high" as RiskLevel,
      authenticityScore: 5,
      modalities: ["audio"],
      upvotes: 890,
      comments: 112,
    }
  },
  {
    id: "post3",
    user: {
      name: "Journalist Desk",
      avatar: "https://i.pravatar.cc/150?u=a04258114e29026702d",
      trustIndex: 99,
      handle: "jdesk_official",
      timeAgo: "8h",
    },
    content: {
      title: "Verifying the viral protest images from downtown. TruthLens confirms these are actual, unmodified photographs.",
      thumbnail: "https://images.unsplash.com/photo-1529158334543-85e7fc2642da?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80",
      riskLevel: "authentic" as RiskLevel,
      authenticityScore: 98,
      modalities: ["image"],
      upvotes: 1205,
      comments: 89,
    }
  }
];

const tabs = ["All", "Deepfakes", "Audio", "Images", "Text"];

export default function CommunityPage() {
  const [activeTab, setActiveTab] = useState("All");

  return (
    <div className="flex min-h-screen bg-[#020817] text-white">
      <SidebarNav />

      <main className="flex-1 w-full max-w-7xl mx-auto p-4 md:p-8 lg:p-10 flex flex-col items-center">
        
        {/* Page Head & Filter Bar */}
        <div className="w-full flex justify-between items-end mb-8 pt-4">
          <div>
            <h1 className="text-[32px] md:text-[40px] font-heading font-bold tracking-tight text-white mb-6">
              Community Truth Feed
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
        </div>

        {/* Secondary Filter Row: Search & Sort */}
        <div className="w-full flex flex-col sm:flex-row items-center justify-between gap-4 mb-8">
          <div className="relative w-full sm:max-w-md">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input 
              type="text" 
              placeholder="Search community analysis..." 
              className="w-full h-11 bg-white/5 border border-white/10 rounded-xl pl-11 pr-4 text-[14px] text-white placeholder:text-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
            />
          </div>

          <button className="h-11 px-4 flex items-center justify-between gap-3 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-colors shrink-0 w-full sm:w-auto">
            <div className="flex items-center gap-2 text-slate-300">
              <Filter className="w-4 h-4" />
              <span className="text-[13px] font-semibold">Sort by: Trust Score</span>
            </div>
            <ChevronDown className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        {/* Content Area: Two Column Layout on Desktop */}
        <div className="w-full grid grid-cols-1 lg:grid-cols-[1fr_340px] xl:grid-cols-[1fr_380px] gap-8 pb-20">
          
          {/* Feed Column */}
          <div className="flex flex-col gap-6">
            {mockFeed.map((post) => (
              <TruthFeedCard key={post.id} id={post.id} user={post.user} content={post.content} />
            ))}
          </div>

          {/* Right Sidebar: Trending Topics */}
          <div className="hidden lg:block relative">
            <TrendingTopics />
          </div>

        </div>
      </main>
    </div>
  );
}
