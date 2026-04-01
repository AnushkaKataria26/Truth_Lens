"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud, FileVideo, ImageIcon, Mic, Type, X, Link, ArrowRight, ScanLine } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { GlassCard } from "@/components/ui/GlassCard";
import { cn } from "@/lib/utils";

const types = [
  { id: "video", label: "Upload Video", icon: FileVideo, accept: "video/*" },
  { id: "image", label: "Upload Image", icon: ImageIcon, accept: "image/*" },
  { id: "audio", label: "Upload Audio", icon: Mic,       accept: "audio/*" },
  { id: "text",  label: "Paste Text",   icon: Type,      accept: ".txt"    },
];

export function UploadPanel({ onAnalyze }: { onAnalyze: () => void }) {
  const [activeType, setActiveType] = useState("video");
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState("");

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setIsDragging(true);
    else if (e.type === "dragleave") setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="w-full max-w-2xl mx-auto"
    >
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-blue-500/20 bg-blue-500/10 mb-5">
          <ScanLine className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-[11px] font-bold text-blue-400 uppercase tracking-wider">
            Verification Engine
          </span>
        </div>
        <h1 className="text-[32px] md:text-[40px] font-heading font-bold text-white mb-3 tracking-tight">
          Analyze Content
        </h1>
        <p className="text-[16px] text-slate-400 max-w-md mx-auto leading-relaxed">
          Upload media or paste a link to accurately detect deepfakes, AI generation, and digital manipulation.
        </p>
      </div>

      <GlassCard className="p-8">
        {/* Drag Drop Zone */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={cn(
            "relative w-full h-[240px] rounded-2xl border-2 border-dashed flex flex-col items-center justify-center transition-all duration-300 overflow-hidden group",
            isDragging
              ? "border-blue-500 bg-blue-500/10 shadow-[0_0_30px_rgba(59,130,246,0.2)]"
              : file 
                ? "border-white/10 bg-white/5"
                : "border-[rgba(59,130,246,0.3)] bg-white/[0.02] hover:bg-white/[0.04] hover:border-[rgba(59,130,246,0.5)]"
          )}
        >
          {/* Background glow logic inside dropzone */}
          <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 to-transparent pointer-events-none" />

          <AnimatePresence mode="wait">
            {file ? (
              <motion.div
                key="file"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="flex flex-col items-center justify-center w-full z-10"
              >
                <div className="w-16 h-16 rounded-full bg-green-500/20 border border-green-500/30 flex items-center justify-center mb-4">
                  <FileVideo className="w-7 h-7 text-green-400" />
                </div>
                <div className="text-[16px] font-bold text-white mb-1 truncate max-w-[80%]">
                  {file.name}
                </div>
                <div className="text-[13px] text-slate-400 mb-6 font-medium">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB • {file.type || "Unknown"}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => { e.stopPropagation(); setFile(null); }}
                  className="gap-2 text-red-400 hover:text-red-300 hover:bg-red-500/10"
                >
                  <X className="w-4 h-4" /> Remove File
                </Button>
              </motion.div>
            ) : (
              <motion.div
                key="upload"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="flex flex-col items-center justify-center pointer-events-none z-10"
              >
                <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4 group-hover:scale-110 group-hover:bg-blue-500/10 group-hover:text-blue-400 transition-all duration-300">
                  <UploadCloud className={cn("w-7 h-7 text-slate-400 group-hover:text-blue-400 transition-colors", isDragging && "text-blue-400")} />
                </div>
                <div className="text-[16px] font-bold text-white mb-1">
                  Drag and drop media file to upload
                </div>
                <div className="text-[13px] text-slate-400">
                  or click anywhere in this area to browse
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          
          {/* Hidden file input stretching full absolute area */}
          {!file && (
            <input
              type="file"
              onChange={handleFileSelect}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              accept={types.find(t => t.id === activeType)?.accept}
            />
          )}
        </div>

        {/* Type pills */}
        <div className="flex items-center justify-center gap-3 mt-8 mb-8 flex-wrap">
          {types.map((type) => {
            const active = activeType === type.id;
            return (
              <button
                key={type.id}
                onClick={() => setActiveType(type.id)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-full text-[13px] font-medium transition-all duration-200 border",
                  active
                    ? "bg-blue-500 text-white border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.3)]"
                    : "bg-white/5 text-slate-300 border-white/10 hover:bg-white/10 hover:border-white/20"
                )}
              >
                <type.icon className={cn("w-4 h-4", active ? "text-white" : "text-slate-400")} />
                {type.label}
              </button>
            );
          })}
        </div>

        <div className="relative flex items-center mb-8">
          <div className="flex-grow border-t border-white/[0.06]" />
          <span className="flex-shrink-0 mx-4 text-slate-500 text-[12px] uppercase tracking-widest font-semibold">
            OR
          </span>
          <div className="flex-grow border-t border-white/[0.06]" />
        </div>

        {/* URL Input */}
        <div className="flex items-center gap-3 mb-10">
          <div className="relative flex-1">
            <Link className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Paste suspicious URL or link..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full h-12 bg-[rgba(255,255,255,0.03)] border border-white/10 rounded-xl pl-11 pr-4 text-white text-[14px] placeholder:text-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all font-medium"
            />
          </div>
          <Button
            onClick={() => { if(url) setFile(new File([], "Pasted URL content")); }}
            disabled={!url && !file}
            className="h-12 border-white/10 bg-white/5 hover:bg-white/10 text-white"
          >
            Upload
          </Button>
        </div>

        {/* CTA */}
        <Button
          size="lg"
          disabled={!file}
          onClick={onAnalyze}
          className="w-full h-14 text-[16px] font-bold group relative overflow-hidden disabled:opacity-50"
        >
          {/* Glow effect inside button */}
          <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-indigo-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          <span className="relative z-10 flex items-center gap-2">
            Run Agentic Analysis
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </span>
        </Button>
      </GlassCard>
    </motion.div>
  );
}

