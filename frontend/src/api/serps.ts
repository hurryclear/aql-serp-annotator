import type { SerpSummary, SerpQuery } from "../types/workspace";
import { apiClient } from "./client";

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
