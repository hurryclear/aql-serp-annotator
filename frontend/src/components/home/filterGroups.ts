import type { AnnotationGroup } from "../../types/editor";

// the groups the start page's form points at: an empty field doesn't filter.
// The form says "Google", the backend "google", so names are compared ignoring case.
export function filterGroups(groups: AnnotationGroup[], provider: string, year: string): AnnotationGroup[] {
  return groups.filter(
    (g) =>
      (provider === "" || g.provider.toLowerCase() === provider.toLowerCase()) &&
      (year === "" || g.year === Number(year)),
  );
}
