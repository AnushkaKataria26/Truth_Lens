"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Eye } from "lucide-react";
import { Button } from "./Button";
import { cn } from "@/lib/utils";

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const links = [
    { name: "Home",        href: "/" },
    { name: "Analyze",     href: "/analyze" },
    { name: "Community",   href: "/community" },
    { name: "Leaderboard", href: "/leaderboard" },
  ];

  return (
    <nav
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300 border-b",
        "backdrop-blur-[12px]",
        scrolled
          ? "bg-[rgba(2,8,23,0.9)] border-white/[0.06]"
          : "bg-transparent border-white/[0.06]"
      )}
    >
      <div className="container mx-auto px-6 h-[68px] flex items-center justify-between max-w-7xl">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group shrink-0">
          <Eye className="w-5 h-5 text-white group-hover:text-blue-400 transition-colors duration-200" />
          <span
            className="font-heading font-bold text-[20px] text-white tracking-tight"
            style={{ fontFamily: "var(--font-heading)" }}
          >
            TruthLens
          </span>
        </Link>

        {/* Center nav links */}
        <div className="hidden md:flex items-center gap-8 absolute left-1/2 -translate-x-1/2">
          {links.map((link) => (
            <Link
              key={link.name}
              href={link.href}
              className={cn(
                "text-[14px] font-medium transition-colors duration-200 hover:text-white",
                pathname === link.href ? "text-white" : "text-slate-400"
              )}
            >
              {link.name}
            </Link>
          ))}
        </div>

        {/* Right CTA */}
        <div className="hidden md:flex items-center gap-3 shrink-0">
          <Link href="/login">
            <Button variant="ghost" size="md" className="text-[14px] px-4">
              Sign In
            </Button>
          </Link>
          <Link href="/register">
            <Button variant="primary" size="md" className="text-[14px] px-5 glow-blue">
              Get Started
            </Button>
          </Link>
        </div>
      </div>
    </nav>
  );
}
