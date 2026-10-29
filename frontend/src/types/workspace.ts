// handed from the landing page to /workspace/:cartId as router state
export type WorkspaceState = {
  serpIds: string[];
  provider: string;
  language: string;
  year: number;
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
  content: string;
};

// one feature as POST /serps/{id}/annotation expects it
export type AnnotatedFeatureInput = {
  type: string;
  content: string;
  xpath: string | null;
};
