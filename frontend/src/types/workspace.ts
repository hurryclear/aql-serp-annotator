// the start page's choices, as GET /serps expects them
export type SerpQuery = {
  provider: string;
  language: string;
  year: number;
};

// one item of GET /serps
export type SerpSummary = {
  serp_id: string;
  query: string;
};

// handed from the start page to /workspace as router state
export type WorkspaceState = SerpQuery & {
  serpIds: string[];
  createdBy: string;
};

export type FeatureType = {
  id: string;
  label: string;
};

// a block accepted on the current SERP, not saved yet
export type AcceptedBlock = {
  index: number;
  type: string;
  label: string;
  node: number; // the element's aqlqa-node number in the snapshot
};

// one feature as POST /annotations expects it
export type FeatureInput = {
  feature_type: string;
  node: number;
};
