import type { FeatureInput } from "../types/workspace";
import { apiClient } from "./client";

// an empty features list saves "No features": the SERP counts as done
export async function createAnnotation(serpId: string, createdBy: string, features: FeatureInput[]): Promise<void> {
  await apiClient.post("/annotations", { serp_id: serpId, created_by: createdBy, features });
}
