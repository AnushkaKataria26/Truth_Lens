"use client";

import { motion } from "framer-motion";
import { 
  ArrowUp, MessageSquare, Share2, Bookmark, Flag, 
  ShieldCheck, ShieldAlert, Image as ImageIcon,
  Video, Mic, Type, MoreHorizontal, TrendingUp
} from "lucide-react";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { RiskLevel } from "@/types";
import { cn } from "@/lib/utils";

interface FeedCardProps {
  id: string;
  user: {
    name: string;
    avatar: string;
    trustIndex: number;
    handle: string;
    timeAgo: string;
  };
  content: {
    title: string;
    thumbnail: string;
    riskLevel: RiskLevel;
    authenticityScore: number;
    modalities: string[];
    upvotes: number;
    comments: number;
  };
}

export function TruthFeedCard({ user, content }: FeedCardProps) {
  const isFake = content.authenticityScore < 50;

  const renderModalityIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "video": return <Video className="w-3.5 h-3.5" />;
      case "image": return <ImageIcon className="w-3.5 h-3.5" />;
      case "audio": return <Mic className="w-3.5 h-3.5" />;
      case "text": return <Type className="w-3.5 h-3.5" />;
      default: return null;
    }
  };

  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="relative group w-full bg-[#0B1221]/80 backdrop-blur-md border border-white/5 rounded-2xl overflow-hidden shadow-lg transition-all duration-300 hover:border-blue-500/30 hover:shadow-[0_8px_30px_rgba(59,130,246,0.12)] cursor-pointer"
    >
      {/* Subtle Glow Behind Card on Hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/0 via-transparent to-purple-500/0 opacity-0 group-hover:opacity-10 transition-opacity duration-500 pointer-events-none" />

      <div className="p-5 flex flex-col gap-4 relative z-10">
        {/* Header: User Info */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-slate-800 border-2 border-slate-700 overflow-hidden shrink-0">
              <img src={user.avatar} alt="Avatar" className="w-full h-full object-cover" />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-[14px] text-white hover:underline">
                  {user.name}
                </span>
                <span className="text-[13px] text-slate-400">@{user.handle}</span>
                <span className="text-[13px] text-slate-500">· {user.timeAgo}</span>
              </div>
              <div className="flex items-center gap-1 mt-0.5">
                <ShieldCheck className="w-3 h-3 text-blue-400" />
                <span className="text-[12px] font-semibold text-blue-400">
                  Trust Index {user.trustIndex}%
                </span>
              </div>
            </div>
          </div>
          <button className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-white/5 text-slate-400 hover:text-white transition-colors">
            <MoreHorizontal className="w-5 h-5" />
          </button>
        </div>

        {/* Content Title */}
        <h3 className="text-[16px] font-medium text-slate-200 leading-snug">
          {content.title}
        </h3>

        {/* Media Thumbnail */}
        <div className="relative w-full aspect-video rounded-xl bg-slate-900 border border-white/5 overflow-hidden group/media">
          <img 
            src={content.thumbnail} 
            alt="Content Thumbnail" 
            className="w-full h-full object-cover brightness-90 group-hover/media:scale-105 transition-transform duration-700 ease-out"
          />
          {/* Overlay gradient */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent flex flex-col justify-end p-4">
            <div className="flex flex-wrap items-center gap-2">
              <RiskBadge level={content.riskLevel} />
              
              <div className={cn(
                "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[12px] font-bold backdrop-blur-md border",
                isFake ? "bg-red-500/20 text-red-400 border-red-500/30" : "bg-green-500/20 text-green-400 border-green-500/30"
              )}>
                {content.authenticityScore}% Authentic
              </div>

              {content.modalities.map(mod => (
                <div key={mod} className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-black/40 border border-white/10 text-[11px] font-medium text-slate-300 backdrop-blur-md">
                  {renderModalityIcon(mod)}
                  <span className="capitalize">{mod}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Action Row */}
        <div className="flex items-center justify-between pt-2 border-t border-white/[0.06] mt-2">
          <div className="flex items-center gap-6">
            <button className="flex items-center gap-1.5 text-slate-400 hover:text-blue-400 transition-colors group/btn">
              <div className="w-8 h-8 rounded-full flex items-center justify-center group-hover/btn:bg-blue-500/10">
                <ArrowUp className="w-4 h-4" />
              </div>
              <span className="text-[13px] font-semibold">{content.upvotes}</span>
            </button>
            <button className="flex items-center gap-1.5 text-slate-400 hover:text-indigo-400 transition-colors group/btn">
              <div className="w-8 h-8 rounded-full flex items-center justify-center group-hover/btn:bg-indigo-500/10">
                <MessageSquare className="w-4 h-4" />
              </div>
              <span className="text-[13px] font-semibold">{content.comments}</span>
            </button>
            <button className="flex items-center gap-1.5 text-slate-400 hover:text-green-400 transition-colors group/btn">
              <div className="w-8 h-8 rounded-full flex items-center justify-center group-hover/btn:bg-green-500/10">
                <Share2 className="w-4 h-4" />
              </div>
            </button>
          </div>
          
          <div className="flex items-center gap-2 text-slate-400">
            <button className="w-8 h-8 rounded-full flex items-center justify-center hover:bg-white/5 hover:text-white transition-colors">
              <Bookmark className="w-4 h-4" />
            </button>
            <button className="w-8 h-8 rounded-full flex items-center justify-center hover:bg-red-500/10 hover:text-red-400 transition-colors">
              <Flag className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
