import type { ParserSummary } from "../../types/parser";

export function filterSummary( rows: ParserSummary[], provider: string): ParserSummary[] {
    return rows.filter(
    (r) => provider === "" || r.provider_name.toLowerCase() === provider.toLowerCase());
}