import { TruthFeedPost, TrendingTopic } from "../types";

export const MOCK_COMMUNITY_FEED: TruthFeedPost[] = [
  {
    id: "post1",
    user: {
      name: "Marcus L.",
      avatar: "https://i.pravatar.cc/150?u=a042581f4e29026704d",
      trustIndex: 98,
      handle: "marcus_truth",
      timeAgo: "2h",
    },
    content: {
      title: "Found this circulating on X regarding the new zoning laws. Very clear visual artifacts on the speaker's face.",
      thumbnail: "https://images.unsplash.com/photo-1557804506-669a67965ba0?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80",
      riskLevel: "high",
      authenticityScore: 12,
      modalities: ["video", "audio"],
      upvotes: 342,
      comments: 56,
    }
  },
  {
    id: "post2",
    user: {
      name: "Sarah Chen",
      avatar: "https://i.pravatar.cc/150?u=a042581f4e29026704e",
      trustIndex: 92,
      handle: "schen_verify",
      timeAgo: "5h",
    },
    content: {
      title: "Audio leak claiming to be CEO of TechCorp—ran it through TruthLens and 100% synthetic generation detected.",
      thumbnail: "https://images.unsplash.com/photo-1620021609384-0610f4d3fcbb?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80",
      riskLevel: "high",
      authenticityScore: 5,
      modalities: ["audio"],
      upvotes: 890,
      comments: 112,
    }
  },
  {
    id: "post3",
    user: {
      name: "Journalist Desk",
      avatar: "https://i.pravatar.cc/150?u=a04258114e29026702d",
      trustIndex: 99,
      handle: "jdesk_official",
      timeAgo: "8h",
    },
    content: {
      title: "Verifying the viral protest images from downtown. TruthLens confirms these are actual, unmodified photographs.",
      thumbnail: "https://images.unsplash.com/photo-1529158334543-85e7fc2642da?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80",
      riskLevel: "authentic",
      authenticityScore: 98,
      modalities: ["image"],
      upvotes: 1205,
      comments: 89,
    }
  }
];

export const MOCK_TRENDING_TOPICS: TrendingTopic[] = [
  { id: 1, topic: "Senator XYZ Deepfake Video", count: "12.4K views", risk: "Critical", spike: true },
  { id: 2, topic: "AI Generated Hurricane Images", count: "8.1K views", risk: "High", spike: true },
  { id: 3, topic: "Synthetic CEO Earnings Call", count: "5.3K views", risk: "Medium", spike: false },
  { id: 4, topic: "Fake Protest Voice Notes", count: "3.2K views", risk: "High", spike: true },
  { id: 5, topic: "Automated Stock Rumors text", count: "1.5K views", risk: "Medium", spike: false },
];
