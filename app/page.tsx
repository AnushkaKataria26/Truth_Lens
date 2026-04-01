import { Navbar } from "@/components/ui/Navbar";
import { Footer } from "@/components/ui/Footer";
import { HeroSection } from "@/components/sections/HeroSection";
import { StatsBar } from "@/components/sections/StatsBar";
import { HowItWorksSection } from "@/components/sections/HowItWorksSection";
import { FeaturesSection } from "@/components/sections/FeaturesSection";
import { TrendingFigures } from "@/components/sections/TrendingFigures";

export default function Home() {
  return (
    <main className="flex flex-col w-full relative overflow-hidden">
      <Navbar />
      <HeroSection />
      <StatsBar />
      <HowItWorksSection />
      <FeaturesSection />
      <TrendingFigures />
      <Footer />
    </main>
  );
}
