"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { SidebarNav } from "@/components/ui/SidebarNav";
import { UploadPanel } from "@/components/analyze/UploadPanel";
import { AnalysisProgress } from "@/components/analyze/AnalysisProgress";

export default function AnalyzePage() {
  const router = useRouter();
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  // Optional: keep track of completion if we want to show a result view later.
  // const [isCompleted, setIsCompleted] = useState(false);

  return (
    <div className="flex min-h-screen bg-[#020817] text-white overflow-hidden relative">
      {/* Sidebar Nav */}
      <SidebarNav />
      
      {/* Main Content Area */}
      <main className="flex-1 flex flex-col items-center justify-center p-4 md:p-8 lg:p-10 relative z-10 w-full">
        {/* Background Gradients */}
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-blue-500/10 blur-[120px] rounded-full pointer-events-none mix-blend-screen" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-indigo-500/10 blur-[120px] rounded-full pointer-events-none mix-blend-screen" />
        
        <div className="w-full max-w-4xl mx-auto mt-12 mb-20">
          {!isAnalyzing ? (
            <UploadPanel onAnalyze={() => setIsAnalyzing(true)} />
          ) : (
            <AnalysisProgress onComplete={() => {
              router.push("/results");
            }} />
          )}
        </div>
      </main>
    </div>
  );
}
