import Link from "next/link";
import { Eye, Twitter, Github, Linkedin } from "lucide-react";

const navLinks = [
  { name: "Home",        href: "/" },
  { name: "Analyze",     href: "/analyze" },
  { name: "Community",   href: "/community" },
  { name: "Leaderboard", href: "/leaderboard" },
];

const socials = [
  { icon: Twitter,  href: "#" },
  { icon: Github,   href: "#" },
  { icon: Linkedin, href: "#" },
];

export function Footer() {
  return (
    <footer className="border-t border-white/[0.06] pt-10 pb-10">
      <div className="container mx-auto px-6 max-w-7xl flex flex-col md:flex-row items-center justify-between gap-6">
        {/* Logo */}
        <div className="flex items-center gap-2 shrink-0">
          <Eye className="w-4 h-4 text-slate-500" />
          <span className="font-heading font-bold text-[16px] text-slate-400">TruthLens</span>
        </div>

        {/* Nav links */}
        <div className="flex items-center gap-6 flex-wrap justify-center">
          {navLinks.map((link) => (
            <Link
              key={link.name}
              href={link.href}
              className="text-[13px] text-slate-600 hover:text-slate-400 transition-colors duration-200 font-medium"
            >
              {link.name}
            </Link>
          ))}
        </div>

        {/* Social icons */}
        <div className="flex items-center gap-4">
          {socials.map(({ icon: Icon, href }, i) => (
            <Link
              key={i}
              href={href}
              className="text-slate-600 hover:text-white transition-colors duration-200"
            >
              <Icon className="w-4 h-4" />
            </Link>
          ))}
        </div>
      </div>
    </footer>
  );
}
