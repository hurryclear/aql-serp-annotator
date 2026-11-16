import type { SerpCount, SerpSummary, SerpQuery } from "../types/workspace";
import { apiClient } from "./client";

// the line above the Start button: how many SERPs these choices find;
// a choice left undefined isn't sent, and the backend then counts every value of it
export async function countSerps(query: Partial<SerpQuery>): Promise<SerpCount> {
  const response = await apiClient.get<SerpCount>("/serps/count", { params: query });
  return response.data;
}

// the Start button: candidate SERPs for these choices that nobody has annotated yet
export async function listSerps(query: SerpQuery): Promise<SerpSummary[]> {
  const response = await apiClient.get<SerpSummary[]>("/serps", {
    params: { ...query, annotated: false, limit: 25 },
  });
  return response.data;
}

export async function getSerpHtml(serpId: string): Promise<string> {
  const response = await apiClient.get<string>(`/serps/${serpId}`, { responseType: "text" });
  return response.data;
}
