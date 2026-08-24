import type { CartInput, CartOutput } from "../types/cart";
import { apiClient } from "./client";

export async function createCart(input: CartInput): Promise<CartOutput> {
    const response = await apiClient.post<CartOutput>("/carts", input);
    return response.data;
}
