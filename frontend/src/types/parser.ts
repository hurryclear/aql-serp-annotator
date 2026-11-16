// POST /parsers/try: what one xpath does on one SERP, compared with its annotated
// blocks of the type (aqlqa-node numbers)
export type TryOutput = {
  serp_id: string;
  found: number[];
  matched: number[]; // annotated and found
  missed: number[];  // annotated, not found
  extra: number[];   // found, not annotated
};

export type ParserOutput = {
  id: string;
  provider_id: string;
  feature_type: string;
  xpath: string;
  created_at: string;
  updated_at: string;
  serps: number;   // SERPs whose blocks are linked to it
  years: number[]; // the years of those SERPs
};
