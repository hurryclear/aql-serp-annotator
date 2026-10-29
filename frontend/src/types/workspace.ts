// handed from the landing page to /workspace/:cartId as router state
export type WorkspaceState = {
  serpIds: string[];
  provider: string;
  language: string;
  year: number;
};
