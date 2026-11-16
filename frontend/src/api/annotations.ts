import type { FeatureInput } from "../types/workspace";
import type { AnnotationGroup, AnnotationOutput, AnnotationSummary } from "../types/editor";
import { apiClient } from "./client";

// an empty features list saves "No features": the SERP counts as done
export async function createAnnotation(serpId: string, createdBy: string, features: FeatureInput[]): Promise<void> {
  await apiClient.post("/annotations", { serp_id: serpId, created_by: createdBy, features });
}

export async function getAnnotationGroups(): Promise<AnnotationGroup[]> {
  const response = await apiClient.get<AnnotationGroup[]>("/annotations/groups");
  return response.data;
}

export async function listAnnotations(providerId: string, year: number): Promise<AnnotationSummary[]> {
  const response = await apiClient.get<AnnotationSummary[]>("/annotations", { params: { provider_id: providerId, year } });
  return response.data;
}

export async function getAnnotation(serpId: string): Promise<AnnotationOutput> {
  const response = await apiClient.get<AnnotationOutput>(`/annotations/${serpId}`);
  return response.data;
}
