import { cn } from "@/lib/utils";
import { ShieldCheck, AlertTriangle, XCircle } from "lucide-react";
import { RiskLevel } from "@/types";

interface RiskBadgeProps {
  level: RiskLevel;
  className?: string;
}

export function RiskBadge({ level, className }: RiskBadgeProps) {
  const config = {
    high: {
      label: "High Risk",
      icon: XCircle,
      textColor: "text-[#EF4444]",
      bgColor: "bg-[#EF4444]/10",
      borderColor: "border-[#EF4444]/20",
      dot: "bg-[#EF4444]",
    },
    medium: {
      label: "Medium Risk",
      icon: AlertTriangle,
      textColor: "text-[#F97316]",
      bgColor: "bg-[#F97316]/10",
      borderColor: "border-[#F97316]/20",
      dot: "bg-[#F97316]",
    },
    authentic: {
      label: "Authentic",
      icon: ShieldCheck,
      textColor: "text-[#22C55E]",
      bgColor: "bg-[#22C55E]/10",
      borderColor: "border-[#22C55E]/20",
      dot: "bg-[#22C55E]",
    },
  };

  const { label, textColor, bgColor, borderColor, dot } = config[level];

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-[13px] font-semibold border backdrop-blur-md transition-all",
        textColor,
        bgColor,
        borderColor,
        className
      )}
    >
      <span className={cn("w-2 h-2 rounded-full", dot)} />
      {label}
    </div>
  );
}
