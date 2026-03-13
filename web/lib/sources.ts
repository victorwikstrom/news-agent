import { Source } from "./types";

export const SOURCES: Source[] = [
  { id: "svt-nyheter", name: "SVT Nyheter", category: "Sweden" },
  { id: "techcrunch", name: "TechCrunch", category: "Tech" },
  { id: "hacker-news", name: "Hacker News", category: "Tech" },
  { id: "the-verge", name: "The Verge", category: "Tech" },
  { id: "omni-ekonomi", name: "Omni Ekonomi", category: "Economy" },
];

export const CATEGORIES = [...new Set(SOURCES.map((s) => s.category))];
