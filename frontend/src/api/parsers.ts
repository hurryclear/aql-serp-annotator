import type { LinkOutput, ParserOutput, ParserSummary, TryOutput } from "../types/parser";
import { apiClient } from "./client";

// a provider's parsers of every year; without a type, all of them
export async function listParsers(providerId: string, featureType?: string): Promise<ParserOutput[]> {
  const response = await apiClient.get<ParserOutput[]>("/parsers", {
    params: { provider_id: providerId, feature_type: featureType },
  });
  return response.data;
}

export async function tryXpath(serpId: string, featureType: string, xpath: string): Promise<TryOutput> {
  const response = await apiClient.post<TryOutput>("/parsers/try", { serp_id: serpId, feature_type: featureType, xpath });
  return response.data;
}

// a new xpath that works on this SERP becomes a parser, linked to this SERP's blocks it finds
export async function createParser(serpId: string, featureType: string, xpath: string): Promise<ParserOutput> {
  const response = await apiClient.post<ParserOutput>("/parsers", { serp_id: serpId, feature_type: featureType, xpath });
  return response.data;
}

// use an existing parser on this SERP (not named "use…": React reserves that prefix for hooks)
export async function linkParser(parserId: string, serpId: string): Promise<LinkOutput> {
  const response = await apiClient.put<LinkOutput>(`/parsers/${parserId}/serps/${serpId}`);
  return response.data;
}

export async function deleteParser(parserId: string): Promise<void> {
  await apiClient.delete(`/parsers/${parserId}`);
}

export async function getParserSummary(): Promise<ParserSummary[]> {
  const response = await apiClient.get<ParserSummary[]>("/parsers/summary");
  return response.data;
}