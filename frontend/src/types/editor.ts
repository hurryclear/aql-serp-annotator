// one row of GET /annotations/groups
export type AnnotationGroup = {
  provider_id: string;
  provider: string;
  year: number;
  annotations: number;
  ground_truth: number;
};

// one row of GET /annotations?provider_id=…&year=…
export type AnnotationSummary = {
  serp_id: string;
  created_by: string;
  ground_truth: boolean;
  feature_count: number;
};

export type FeatureOutput = {
  id: string;
  feature_type: string;
  node: number | null; // null: saved before element marking existed, so not on the page
  parser_id: string | null;
};

// GET / PUT / PATCH /annotations/{serp_id}
export type AnnotationOutput = {
  serp_id: string;
  provider_id: string;
  provider: string;
  language: string;
  year: number;
  created_by: string;
  ground_truth: boolean;
  created_at: string;
  updated_at: string;
  features: FeatureOutput[]; // in page order
};

// a feature as the editor holds it while you work, not saved yet
export type EditorBlock = {
  index: number; // stable key while editing, also written as aqlqa-sf-index
  type: string;
  node: number;
};
