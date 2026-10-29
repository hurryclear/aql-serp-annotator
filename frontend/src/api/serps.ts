import type { AnnotatedFeatureInput } from "../types/workspace";
import { apiClient } from "./client";

export async function getSerpHtml(serpId: string): Promise<string> {
  const response = await apiClient.get<string>(`/serps/${serpId}`, { responseType: "text" });
  return response.data;
}

export async function saveAnnotation(serpId: string, cartId: string, features: AnnotatedFeatureInput[]): Promise<void> {
  await apiClient.post(`/serps/${serpId}/annotation`, { cart_id: cartId, features });
}
