export interface CartInput{
    provider: string;
    language: string;
    year: number;
    created_by: string;
    batch_size: number;
}


export interface CartOutput{
    id: string | null;
    serp_ids: string[];
    total: number;
}