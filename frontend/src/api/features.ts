import type { FeatureType } from "../types/workspace";
import { apiClient } from "./client";

export async function getFeatureTypes(): Promise<FeatureType[]> {
  const response = await apiClient.get<FeatureType[]>("/features/type");
  return response.data;
}
