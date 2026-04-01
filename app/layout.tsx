import type { Metadata } from "next";
import { Inter, Sora } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const sora = Sora({
  variable: "--font-sora",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TruthLens — Verify Before You Believe",
  description:
    "TruthLens detects deepfakes, synthetic audio, and misleading media in real time — before misinformation spreads.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${sora.variable} dark`}>
      <body className="min-h-screen antialiased bg-[#020817] text-slate-100 selection:bg-blue-500/30">
        {children}
      </body>
    </html>
  );
}
