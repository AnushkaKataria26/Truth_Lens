"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Eye, Home, ScanSearch, Users, Trophy, Settings, HelpCircle, LayoutDashboard, User } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { label: "Home",        href: "/",           icon: Home       },
  { label: "Analyze",     href: "/analyze",    icon: ScanSearch },
  { label: "Community",   href: "/community",  icon: Users      },
  { label: "Leaderboard", href: "/leaderboard",icon: Trophy     },
  { label: "Admin",       href: "/admin",      icon: LayoutDashboard },
  { label: "Profile",     href: "/profile",    icon: User },
];

const bottomItems = [
  { label: "Settings", href: "/settings", icon: Settings   },
  { label: "Help",     href: "/help",     icon: HelpCircle },
];

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <>
      {/* Desktop Sidebar Navigation */}
      <aside className="hidden lg:flex flex-col w-[240px] shrink-0 h-screen sticky top-0 border-r border-white/[0.06] bg-[rgba(2,8,23,0.8)] backdrop-blur-xl z-50">
        <div className="flex items-center gap-2.5 px-6 h-[68px] border-b border-white/[0.06] shrink-0">
          <Eye className="w-5 h-5 text-white" />
          <span className="font-heading font-bold text-[18px] text-white tracking-tight">
            TruthLens
          </span>
        </div>

        <nav className="flex-1 flex flex-col gap-1 p-4 overflow-y-auto">
          {navItems.map(({ label, href, icon: Icon }) => {
            const active = pathname === href || (pathname.startsWith(href) && href !== "/");
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-xl text-[14px] font-medium transition-all duration-200 group",
                  active
                    ? "bg-blue-500/10 text-white border border-blue-500/20 shadow-[0_0_12px_rgba(59,130,246,0.12)]"
                    : "text-slate-400 hover:text-white hover:bg-white/5"
                )}
              >
                <Icon className={cn("w-[18px] h-[18px] shrink-0 transition-colors", active ? "text-blue-400" : "text-slate-500 group-hover:text-slate-300")} />
                {label}
                {active && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-400" />}
              </Link>
            );
          })}
        </nav>

        <div className="flex flex-col gap-1 p-4 border-t border-white/[0.06]">
          {bottomItems.map(({ label, href, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-[14px] font-medium text-slate-500 hover:text-white hover:bg-white/5 transition-all duration-200 group"
            >
              <Icon className="w-[18px] h-[18px] shrink-0 text-slate-600 group-hover:text-slate-300 transition-colors" />
              {label}
            </Link>
          ))}
        </div>
      </aside>

      {/* Mobile Bottom Tab Bar Navigation */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 h-[64px] bg-[#020817]/90 backdrop-blur-xl border-t border-white/[0.06] z-50 flex items-center justify-around px-2 pb-safe">
        {navItems.slice(0, 5).map(({ label, href, icon: Icon }) => {
          const active = pathname === href || (pathname.startsWith(href) && href !== "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex flex-col items-center justify-center w-full h-full gap-1 transition-colors",
                active ? "text-blue-400" : "text-slate-500 hover:text-white"
              )}
            >
              <Icon className={cn("w-5 h-5", active ? "text-blue-400" : "")} />
              <span className="text-[10px] font-medium">{label}</span>
            </Link>
          );
        })}
      </nav>
    </>
  );
}
