export type RiskLevel = "high" | "medium" | "authentic";

export interface User {
  id?: string | number;
  name: string;
  avatar: string;
  trustIndex: number;
  handle: string;
  timeAgo?: string;
}

export interface AnalysisContent {
  title: string;
  thumbnail: string;
  riskLevel: RiskLevel;
  authenticityScore: number;
  modalities: string[];
  upvotes: number;
  comments: number;
}

export interface TruthFeedPost {
  id: string;
  user: User;
  content: AnalysisContent;
}

export interface TrendingTopic {
  id: number;
  topic: string;
  count: string;
  risk: string;
  spike: boolean;
}

export interface SystemLog {
  id: string;
  timestamp: string;
  level: "INFO" | "WARN" | "ERROR" | "ALERT";
  source: string;
  message: string;
}

export interface ProfileStats {
  label: string;
  value: string;
  iconName: string;
  color: string;
}

export interface Achievement {
  label: string;
  iconName: string;
}

export interface PastAnalysis {
  id: string;
  title: string;
  date: string;
  score: number;
  label: string;
}
