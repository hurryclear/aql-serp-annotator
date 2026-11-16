import type { ParserOutput, TryOutput } from "../types/parser";
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
