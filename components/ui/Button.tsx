import { ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", children, ...props }, ref) => {
    
    // cubic-bezier hover transition as required
    const baseStyles = "inline-flex items-center justify-center rounded-xl font-semibold transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#020817] disabled:opacity-50 disabled:pointer-events-none";
    
    const variants = {
      primary: "bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:shadow-[0_0_20px_rgba(37,99,235,0.4)] border border-transparent",
      secondary: "bg-[rgba(255,255,255,0.05)] text-white border border-blue-500/30 hover:bg-[rgba(255,255,255,0.1)] hover:border-blue-400 backdrop-blur-md",
      ghost: "bg-transparent text-white border border-transparent hover:border-white/20 hover:bg-white/5",
    };

    const sizes = {
      sm: "h-9 px-4 text-[13px]",
      md: "h-11 px-6 text-[14px]",
      lg: "h-14 px-8 text-[16px]",
    };

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      >
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";
